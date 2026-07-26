"""HTTP klient ABRA Flexi (FlexiBee) REST API.

Retry, backoff, mapování chyb a percent-encoding segmentů řeší
``openmcp_sdk.http.UpstreamClient``. Tady zůstává jen to, co je specifické
pro Flexi: validace per-zákazník URL, XML transport (``winstrom`` obálka)
a bezpečné skládání filtrů do URL cesty.

Filtr Flexi patří do CESTY v závorce — ``/faktura-vydana/(expr).xml`` — což
z něj dělá injection kanál do URL. Proto tu není žádný „raw filter" vstup:
hodnoty se validují proti uzavřeným množinám znaků (bez ``'`` a závorek,
takže z literálu ani závorky nejde vyskočit) a výraz skládá výhradně klient.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Any

import httpx
from openmcp_sdk.envelope import ConnectorError, ErrorCode
from openmcp_sdk.http import UpstreamClient

from connector.xml_codec import build_flexibee_xml, parse_flexibee_xml

logger = logging.getLogger(__name__)

#: Jediný port, na kterém běží cloudové instance ABRA Flexi.
FLEXI_PORT = 5434

# -- validace vstupů do filtru/cesty ------------------------------------------

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Bez `'`, `(`, `)` — z filtru v cestě se nedá vyskočit. Mezery jsou legální
# (kódy typů dokladů je obsahují), dvojtečka kvůli prefixům `code:`/`ext:`.
_CODE_RE = re.compile(r"^[A-Za-z0-9 :_.,/+-]{1,64}$")
_ORDER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,40}@[AD]$")
# Strojový název evidence (`faktura-vydana`). Obrana v hloubce: volající sice
# evidence validují proti allowlistu, ale cesta se nesmí dát ohnout ani z
# budoucího nástroje, který by na to zapomněl.
_EVIDENCE_RE = re.compile(r"^[a-z][a-z0-9-]{0,60}$")


def require_date(value: str, label: str) -> str:
    """Datum YYYY-MM-DD — jediný tvar, který pouštíme do filtru."""
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value.strip()):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT, f"{label} musí být datum ve formátu YYYY-MM-DD"
        )
    return value.strip()


def require_code(value: str, label: str) -> str:
    """Kód/identifikátor do filtru — uzavřená množina znaků."""
    if not isinstance(value, str) or not _CODE_RE.fullmatch(value.strip()):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT,
            f"{label} smí obsahovat jen písmena, číslice, mezery a ._,/+- (max 64 znaků)",
        )
    return value.strip()


def require_order(value: str) -> str:
    """Řazení ``pole@A``/``pole@D`` — tvar, který Flexi čeká v query."""
    if not isinstance(value, str) or not _ORDER_RE.fullmatch(value.strip()):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT, "order musí mít tvar pole@A nebo pole@D (např. datVyst@D)"
        )
    return value.strip()


def _validated_api_url(raw: object) -> str:
    """Přivaž Basic credentials k rodině hostů ABRA Flexi cloudu.

    Kubernetes NetworkPolicy neumí vynutit FQDN. Bez téhle aplikační kontroly
    by zákazníkem řízená ``api_url`` mohla exfiltrovat jméno a heslo Flexi na
    libovolný host. Self-hosted instance mimo ``*.flexibee.eu`` jsou vědomě
    mimo rozsah (viz README).
    """
    if not isinstance(raw, str) or raw != raw.strip() or any(
        ord(char) < 32 or ord(char) == 127 for char in raw
    ):
        raise ConnectorError(ErrorCode.INVALID_INPUT, "Neplatná URL ABRA Flexi serveru.")
    parsed = urllib.parse.urlsplit(raw)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ConnectorError(
            ErrorCode.INVALID_INPUT, "Neplatná URL ABRA Flexi serveru."
        ) from exc
    hostname = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or not hostname.endswith(".flexibee.eu")
        or hostname == ".flexibee.eu"
        or port != FLEXI_PORT
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != ""
    ):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT,
            "URL musí být HTTPS adresa cloudové instance *.flexibee.eu "
            f"s portem {FLEXI_PORT} a bez cesty, např. https://firma.flexibee.eu:{FLEXI_PORT}",
        )
    return f"https://{hostname}:{FLEXI_PORT}"


class Client(UpstreamClient):
    """Klient Flexi API — XML transport nad sdíleným ``UpstreamClient``.

    Zápisy se v SDK neopakují automaticky (default pro non-GET): po 5xx nebo
    timeoutu nevíme, zda požadavek neprošel, nebo se ztratila jen odpověď.
    """

    def __init__(
        self, api_url: str, company: str, username: str, password: str, **kwargs: Any
    ) -> None:
        base = _validated_api_url(api_url)
        super().__init__(
            base_url=f"{base}/c",
            auth=(username, password),
            headers={"Accept": "application/xml"},
            **kwargs,
        )
        # `seg()` percent-encodingem zneškodní `/` i `..` — company je vstup
        # z aktivace, ne konstanta.
        self._company_seg = self.seg(company, "company")
        #: Validovaný origin serveru (veřejný — pro seznam firem mimo base_url `/c`).
        self.server_base = base
        #: Základ pro provenance.source_url (bez credentials).
        self.public_base = f"{base}/c/{self._company_seg}"

    # -- skládání cest ---------------------------------------------------------

    @staticmethod
    def _safe_evidence(evidence: str) -> str:
        if not _EVIDENCE_RE.fullmatch(evidence):
            # Interní chyba volajícího (evidence jsou konstanty/allowlist),
            # ne vstup od LLM — proto INTERNAL.
            raise ConnectorError(ErrorCode.INTERNAL, "neplatný název evidence v cestě")
        return evidence

    def evidence_path(self, evidence: str, *, record: str | None = None) -> str:
        """Cesta evidence, volitelně s ID/kódem záznamu (percent-encoded)."""
        safe = self._safe_evidence(evidence)
        if record is not None:
            return f"/{self._company_seg}/{safe}/{self.seg(record, 'id')}.xml"
        return f"/{self._company_seg}/{safe}.xml"

    @staticmethod
    def _filter_segment(conditions: list[str]) -> str:
        expr = " and ".join(conditions)
        return urllib.parse.quote(f"({expr})", safe="()")

    def filter_path(self, evidence: str, conditions: list[str]) -> str:
        """Cesta s filtrem v závorce.

        Hodnoty v ``conditions`` už musí být validované (`require_date`,
        `require_code`, čísla) — tahle metoda je jen skládá a percent-encoduje
        jako jeden hotový segment. Ochrana žije v klientovi, ne u volajícího.
        """
        safe = self._safe_evidence(evidence)
        return f"/{self._company_seg}/{safe}/{self._filter_segment(conditions)}.xml"

    def sum_path(self, evidence: str, conditions: list[str]) -> str:
        """Cesta sumace ``$sum`` — volitelně nad filtrovanou podmnožinou."""
        safe = self._safe_evidence(evidence)
        if conditions:
            return (
                f"/{self._company_seg}/{safe}/"
                f"{self._filter_segment(conditions)}/$sum.xml"
            )
        return f"/{self._company_seg}/{safe}/$sum.xml"

    def properties_path(self, evidence: str) -> str:
        """Cesta samodokumentace polí evidence (``/properties``)."""
        return f"/{self._company_seg}/{self._safe_evidence(evidence)}/properties.xml"

    def get_sum(self, evidence: str, conditions: list[str]) -> dict[str, Any]:
        """Souhrn ``$sum`` — vrací obsah ``winstrom`` obálky odpovědi."""
        payload = self.get_parsed(self.sum_path(evidence, conditions))
        return self._winstrom(payload)

    def companies(self) -> list[dict[str, Any]]:
        """Seznam firem (databází) na serveru — ``GET /c.xml``.

        Absolutní URL míří na tentýž validovaný origin, jen mimo base_url
        ``/c`` (kořenový seznam nemá firmu v cestě). Odpověď má kořen
        ``<companies><company>…`` stejně jako info o firmě.
        """
        payload = self.get_parsed(f"{self.server_base}/c.xml", {"limit": 0})
        companies = payload.get("companies")
        if isinstance(companies, dict):
            rows = companies.get("company")
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
        return []

    # -- čtení -----------------------------------------------------------------

    def get_parsed(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        same_origin_redirects: int = 0,
    ) -> dict[str, Any]:
        """GET + parse XML odpovědi na dict (včetně ``winstrom`` obálky).

        ``same_origin_redirects`` je pro adresování externím ID — Flexi na
        ``ext:`` URL odpovídá 301 na kanonickou URL záznamu (stejný origin).
        """
        response = self.request(
            "GET", path, params=params, same_origin_redirects=same_origin_redirects
        )
        return self._parse(response)

    def company_info(self, *, detail: str = "summary") -> list[dict[str, Any]]:
        """Info o firmě — zároveň nejlevnější autentizované volání pro test.

        Pozor: tenhle endpoint jako jediný NEvrací ``winstrom`` obálku, ale
        kořen ``<companies><company>…`` (ověřeno na živé instanci). Winstrom
        se zkouší jen jako fallback pro případné jiné verze API.
        """
        payload = self.get_parsed(f"/{self._company_seg}.xml", {"detail": detail})
        companies = payload.get("companies")
        if isinstance(companies, dict):
            rows = companies.get("company")
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
        try:
            return self.unwrap(payload, "company")
        except ConnectorError:
            return []

    def unwrap(self, payload: dict[str, Any], evidence: str) -> list[dict[str, Any]]:
        """Vytáhni seznam záznamů evidence z ``winstrom`` obálky."""
        winstrom = self._winstrom(payload)
        rows = winstrom.get(evidence)
        if rows is None:
            return []
        if not isinstance(rows, list):
            rows = [rows]
        return [self._normalize_ids(row) for row in rows if isinstance(row, dict)]

    @staticmethod
    def _normalize_ids(row: dict[str, Any]) -> dict[str, Any]:
        """Rozděl vícenásobné ``<id>`` elementy na interní ID a externí ID.

        Záznam s externími ID exportuje víc ``<id>`` elementů
        (``ext:SHOP:123`` + interní ``2736``) — parser z nich udělá seznam
        a model by nevěděl, kterým identifikátorem se ptát dál. Interní
        (číselné) zůstává v ``id``, zbytek jde do ``externalIds``.
        """
        ids = row.get("id")
        if not isinstance(ids, list):
            return row
        internal = next(
            (i for i in ids if isinstance(i, str) and i.isascii() and i.isdigit()), None
        )
        external = [i for i in ids if i != internal]
        if internal is not None:
            row["id"] = internal
            if external:
                row["externalIds"] = external
        return row

    @classmethod
    def row_count(cls, payload: dict[str, Any]) -> int | None:
        """Celkový počet záznamů z ``add-row-count=true`` (atribut obálky)."""
        try:
            raw = cls._winstrom(payload).get("@rowCount")
        except ConnectorError:
            return None
        try:
            return int(str(raw))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _winstrom(payload: dict[str, Any]) -> dict[str, Any]:
        """Obálka ``winstrom`` s tolerancí k prázdné odpovědi.

        Prázdný element jen s atributy se ve ``flatten_attributes`` zploští na
        ``winstrom@version`` a klíč ``winstrom`` zmizí — prázdný výsledek
        evidence je ale legitimní odpověď, ne chyba obálky.
        """
        winstrom = payload.get("winstrom")
        if isinstance(winstrom, dict):
            return winstrom
        if winstrom is None and any(
            key == "winstrom" or key.startswith("winstrom@") for key in payload
        ):
            return {
                f"@{key.split('@', 1)[1]}": value
                for key, value in payload.items()
                if "@" in key
            }
        raise ConnectorError(
            ErrorCode.INTERNAL, "upstream vrátil odpověď bez winstrom obálky"
        )

    # -- zápis -----------------------------------------------------------------

    def write_evidence(
        self, evidence: str, body: dict[str, Any], *, record: str | None = None
    ) -> dict[str, Any]:
        """POST (nový záznam) nebo PUT (update) s XML ``winstrom`` tělem.

        Úspěch se pozná z ``winstrom.success == "true"`` (string!), ne z HTTP
        stavu — 200/201 samo o sobě úspěch nezaručuje.
        """
        xml_body = build_flexibee_xml({"winstrom": {evidence: [body]}})
        method = "POST" if record is None else "PUT"
        path = self.evidence_path(evidence, record=record)
        response = self.request(
            method,
            path,
            content=xml_body,
            headers={"Content-Type": "application/xml"},
        )
        parsed = self._parse(response)
        self._ensure_write_ok(parsed)
        return parsed

    @staticmethod
    def _ensure_write_ok(parsed: dict[str, Any]) -> None:
        winstrom = parsed.get("winstrom")
        success = winstrom.get("success") if isinstance(winstrom, dict) else None
        if success == "true":
            return
        # Chybové zprávy Flexi jdou do logu, ne do zprávy pro model — jsou to
        # data z cizího systému a tedy injection kanál.
        messages: list[str] = []
        results = winstrom.get("results") if isinstance(winstrom, dict) else None
        if isinstance(results, dict):
            results = results.get("result")
        if isinstance(results, list):
            for result in results:
                if not isinstance(result, dict):
                    continue
                errors = result.get("errors")
                if isinstance(errors, dict):
                    errors = errors.get("error", errors)
                if isinstance(errors, dict):
                    errors = [errors]
                if isinstance(errors, list):
                    for error in errors:
                        if isinstance(error, dict) and error.get("message"):
                            messages.append(str(error["message"]))
        logger.warning("Flexi zápis odmítla: %s", "; ".join(messages) or "bez chybové zprávy")
        raise ConnectorError(
            ErrorCode.UPSTREAM_ERROR,
            "ABRA Flexi zápis odmítla — zkontroluj vstupní data (detail je v logu konektoru)",
        )

    # -- interní ---------------------------------------------------------------

    @staticmethod
    def _parse(response: httpx.Response) -> dict[str, Any]:
        try:
            return parse_flexibee_xml(response.text)
        except Exception:
            # Tělo může nést PII i credentials — nepatří do zprávy ani logu,
            # korelace přes request stačí.
            logger.warning("upstream vrátil neplatné XML")
            raise ConnectorError(
                ErrorCode.INTERNAL, "upstream vrátil odpověď, která není platné XML"
            ) from None
