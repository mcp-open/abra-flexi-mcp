"""FastMCP server konektoru ABRA Flexi.

Vzor registrace: ``@tool(mcp, read_only=...)`` z ``openmcp_sdk.tools``.
Dekorátor vrací **původní funkci**, takže se dá v unit testu zavolat přímo,
a ``read_only`` je povinný keyword — nástroj se nedá zaregistrovat bez
rozhodnutí o anotaci. Ta anotace je bezpečnostní hranice: SDK při startu
fail-closed odregistruje vše, co nemá ``readOnlyHint=True``.

Doménová pravidla Flexi (winstrom obálka, filtry v cestě, invarianty
zaúčtování) jsou z ``docs/MCP_PODKLAD.md`` — u zápisů je vynucuje server,
ne volající.
"""

from __future__ import annotations

import logging
import math
import re
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from openmcp_sdk import current_context
from openmcp_sdk.envelope import ConnectorError, ErrorCode, Provenance, now_utc_iso
from openmcp_sdk.http import NO_RETRY
from openmcp_sdk.pii import Pseudonymizer, pseudonymizer_for_request
from openmcp_sdk.tools import tool
from openmcp_sdk.write import WriteBudget, WriteTarget, build_payload, execute_write
from pydantic import Field

from connector.client import Client, require_code, require_date, require_order
from connector.pii_fields import POLICY
from connector.registry import EVIDENCES
from connector.schemas import (
    FilterCondition,
    RecordEnvelope,
    RowsEnvelope,
    StockItemInput,
    StockItemPriceInput,
)
from connector.xml_codec import code_ref, strip_code

logger = logging.getLogger(__name__)

mcp: FastMCP = FastMCP(
    "abraflexi",
    instructions=(
        "Čtecí a zapisovací přístup k účetnictví ABRA Flexi (FlexiBee): vydané "
        "faktury a jejich zaúčtování, účetní deník, přijaté objednávky, skladové "
        "pohyby, stav skladu a ceník. Osobní údaje kontaktů (e-maily, telefony, "
        "adresy a bankovní spojení) jsou pseudonymizovány stabilními tokeny typu "
        "<EMAIL_3f9c1a2b4d5e> "
        "— token nejde rozklíčovat zpět; IČ, DIČ a názvy firem zůstávají čitelné. "
        "Referenční pole mají prefix code: (např. mena: code:CZK), částky jsou "
        "řetězce s desetinnou tečkou, booleany řetězce true/false. Seznamy jsou "
        "stránkované parametry limit a offset. Kromě specializovaných nástrojů "
        "je k dispozici generické čtení všech evidencí: katalog dá "
        "list_evidences, data list_records/get_record se strukturovaným "
        "filtrem, souhrny sum_records a popis polí get_evidence_properties. "
        "Zapisovací nástroje vyžadují potvrzení uživatele s konkrétním diffem."
    ),
)

# Stropy chrání kontextové okno modelu i upstream. Centrální clamp znamená,
# že se `limit` nedá obejít z volání nástroje.
MAX_LIMIT = 100
DEFAULT_LIMIT = 20

# Klientské filtrování (skladové pohyby, ceník) prochází evidenci po
# stránkách — strop drží počet requestů na jedno volání nástroje.
_SCAN_PAGE = 100
_SCAN_MAX_PAGES = 10

SOURCE_ID = "abraflexi"


def _clamp(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    return max(1, min(int(limit), MAX_LIMIT))


class _Session:
    """Klient a pseudonymizér na jedno volání nástroje.

    Záměrně NE globální pool: credentials se v multi-tenantu liší per request,
    sdílený klient by míchal identity.
    """

    def __init__(self, **client_options: Any) -> None:
        ctx = current_context()
        api_url = str(ctx.config.get("api_url") or "")
        company = str(ctx.config.get("company") or "")
        username = str(ctx.config.get("username") or "")
        password = ctx.secrets.get("password")
        if not (api_url and company and username and password):
            raise ConnectorError(
                ErrorCode.FORBIDDEN,
                "chybí přihlašovací údaje Flexi — zkontroluj aktivaci konektoru",
            )
        self.company = company
        self.client = Client(api_url, company, username, password, **client_options)
        self.pii: Pseudonymizer | None = pseudonymizer_for_request(POLICY, ctx)

    def sanitize(self, data: Any) -> Any:
        return self.pii.sanitize(data) if self.pii is not None else data

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.client.close()


def _provenance(session: _Session, suffix: str) -> Provenance:
    return Provenance(
        source_id=SOURCE_ID,
        source_url=f"{session.client.public_base}{suffix}",
        retrieved_at=now_utc_iso(),
        freshness="live",
    )


def _rows_envelope(
    session: _Session,
    rows: list[dict[str, Any]],
    *,
    total: int | None,
    size: int,
    start: int,
    suffix: str,
    truncated: bool | None = None,
    extra_warnings: list[str] | None = None,
) -> RowsEnvelope:
    # Strop se vynucuje TADY, nejen se posílá upstreamu — API, které `limit`
    # ignoruje, by jinak zaplnilo kontextové okno modelu bez ohledu na MAX_LIMIT.
    shown = rows[:size]
    if truncated is None:
        # Oříznuté je to jen tehdy, když opravdu něco následuje — `len == size`
        # samo o sobě nestačí, model by podle lživého „pokračuje" zbytečně
        # stránkoval. Scan-nástroje si truncated počítají samy a předávají ho.
        truncated = (
            start + len(shown) < total if isinstance(total, int) else len(shown) == size
        )
    clean = [row for row in session.sanitize(shown) if isinstance(row, dict)]
    warnings = list(extra_warnings or [])
    if truncated:
        warnings.append(f"Zobrazeno {len(shown)} záznamů, seznam pokračuje dále.")
    return RowsEnvelope(
        items=clean,
        total=total,
        truncated=truncated,
        provenance=_provenance(session, suffix),
        warnings=warnings,
    )


def _mask_contact_names(
    session: _Session, evidence: str, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Evidence ``kontakt`` nese jméno osoby i v poli ``nazev`` (label záznamu).

    Plošné ``NAME_FIELDS`` ho krýt nemůžou — v ``adresar`` je ``nazev`` název
    firmy a ten má zůstat čitelný. Tokenizuje se tedy evidence-aware, jen při
    zapnutém ``redact_names``.
    """
    if evidence != "kontakt" or session.pii is None or not session.pii.redact_names:
        return rows
    masked: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict) and row.get("nazev"):
            row = {**row, "nazev": session.pii.token("NAME", str(row["nazev"]))}
        masked.append(row)
    return masked


def _list_evidence(
    evidence: str,
    conditions: list[str],
    *,
    params: dict[str, Any] | None = None,
    limit: int | None,
    offset: int,
) -> RowsEnvelope:
    """Společná cesta serverově filtrovaných seznamů."""
    size = _clamp(limit)
    start = max(0, offset)
    with _Session() as session:
        path = (
            session.client.filter_path(evidence, conditions)
            if conditions
            else session.client.evidence_path(evidence)
        )
        query: dict[str, Any] = {
            "limit": size,
            "start": start,
            "add-row-count": "true",
            "detail": "summary",
            **(params or {}),
        }
        payload = session.client.get_parsed(path, query)
        rows = _mask_contact_names(session, evidence, session.client.unwrap(payload, evidence))
        total = session.client.row_count(payload)
        return _rows_envelope(
            session, rows, total=total, size=size, start=start, suffix=f"/{evidence}"
        )


def _scan_evidence(
    session: _Session,
    evidence: str,
    conditions: list[str],
    *,
    matches: Any,
    needed: int,
) -> tuple[list[dict[str, Any]], bool, bool]:
    """Stránkovaný průchod evidence s klientským filtrem.

    Serverové ad-hoc filtry jsou na některých evidencích nespolehlivé
    (ověřeno na ``skladovy-pohyb``) — robustní vzor je stáhnout evidenci po
    stránkách a filtrovat u nás.

    Vrací ``(nalezené, dočteno, strop)``:
      * ``dočteno=True`` — evidence je přečtená celá; JEN tehdy je
        ``len(nalezené)`` skutečný celkový počet shod,
      * předčasné zastavení „máme dost" NENÍ dočteno — total by lhal,
      * ``strop=True`` — narazilo se na strop stránek, výsledek může být
        neúplný a volající to NESMÍ zamlčet.
    """
    path = (
        session.client.filter_path(evidence, conditions)
        if conditions
        else session.client.evidence_path(evidence)
    )
    matched: list[dict[str, Any]] = []
    for page in range(_SCAN_MAX_PAGES):
        payload = session.client.get_parsed(
            path,
            {"limit": _SCAN_PAGE, "start": page * _SCAN_PAGE, "detail": "summary"},
        )
        rows = session.client.unwrap(payload, evidence)
        matched.extend(row for row in rows if matches(row))
        if len(rows) < _SCAN_PAGE:
            return matched, True, False
        if len(matched) > needed:
            # Máme víc než potřebný počet (o jeden navíc kvůli poctivému
            # `truncated`) — ale evidence dočtená není.
            return matched, False, False
    return matched, False, True


#: Externí identifikátor Flexi — `ext:NAMESPACE:hodnota`.
_EXT_ID_RE = re.compile(r"^ext:[A-Za-z0-9:_.\-]{1,120}$")


def _fetch_detail(
    session: _Session, evidence: str, identifier: str, *, params: dict[str, Any]
) -> dict[str, Any]:
    """Detail záznamu podle číselného ID, externího ID (``ext:``), nebo kódu."""
    ident = str(identifier).strip()
    if not ident:
        raise ConnectorError(ErrorCode.INVALID_INPUT, "chybí identifikátor záznamu")
    redirects = 0
    if _RECORD_ID_RE.fullmatch(ident):
        path = session.client.evidence_path(evidence, record=ident)
    elif _EXT_ID_RE.fullmatch(ident):
        # Externí ID adresuje záznam v cestě; Flexi odpovídá 301 na kanonickou
        # URL záznamu — same-origin redirect se následuje (ověřeno živě).
        path = session.client.evidence_path(evidence, record=ident)
        redirects = 1
    else:
        code = require_code(ident, "identifikátor")
        path = session.client.filter_path(evidence, [f"kod='{code}'"])
    payload = session.client.get_parsed(path, params, same_origin_redirects=redirects)
    rows = session.client.unwrap(payload, evidence)
    if not rows:
        raise ConnectorError(
            ErrorCode.NOT_FOUND, f"záznam v evidenci {evidence} nebyl nalezen"
        )
    return rows[0]


def _record_envelope(
    session: _Session, evidence: str, record: dict[str, Any]
) -> RecordEnvelope:
    clean = session.sanitize(record)
    return RecordEnvelope(
        record=clean if isinstance(clean, dict) else {},
        provenance=_provenance(session, f"/{evidence}"),
        warnings=[],
    )


# -- sdílené popisy parametrů (LLM je vidí ve schématu) ------------------------

_D_DATE_FROM = Field(description="Od data vystavení včetně (YYYY-MM-DD).")
_D_DATE_TO = Field(description="Do data vystavení včetně (YYYY-MM-DD).")
_D_LIMIT = Field(description=f"Počet záznamů (výchozí {DEFAULT_LIMIT}, max {MAX_LIMIT}).")
_D_OFFSET = Field(description="Kolik záznamů přeskočit (stránkování).", ge=0)
_D_ORDER = Field(description="Řazení pole@A (vzestupně) nebo pole@D, např. datVyst@D.")


# -- čtecí nástroje ------------------------------------------------------------


@tool(mcp, read_only=True)
def get_company_info() -> RecordEnvelope:
    """Základní informace o firmě (účetní jednotce) ve Flexi."""
    with _Session() as session:
        rows = session.client.company_info(detail="full")
        return _record_envelope(session, "company", rows[0] if rows else {})


@tool(mcp, read_only=True)
def list_issued_invoices(
    date_from: Annotated[str | None, _D_DATE_FROM] = None,
    date_to: Annotated[str | None, _D_DATE_TO] = None,
    payment_status: Annotated[
        Literal["uhrazeno", "castUhr", "neuhrazeno"] | None,
        Field(description="Filtr stavu úhrady (stavUhrK)."),
    ] = None,
    order: Annotated[str | None, _D_ORDER] = None,
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Seznam vydaných faktur s filtry podle data vystavení a stavu úhrady.

    Vrací souhrnná pole; detail včetně položek a zaúčtování dá
    `get_issued_invoice`.
    """
    conditions: list[str] = []
    if date_from:
        conditions.append(f"datVyst>='{require_date(date_from, 'date_from')}'")
    if date_to:
        conditions.append(f"datVyst<='{require_date(date_to, 'date_to')}'")
    if payment_status:
        conditions.append(f"stavUhrK='stavUhr.{payment_status}'")
    params = {"order": require_order(order) if order else "datVyst@D"}
    return _list_evidence(
        "faktura-vydana", conditions, params=params, limit=limit, offset=offset
    )


@tool(mcp, read_only=True)
def get_issued_invoice(
    invoice_id: Annotated[
        str, Field(description="ID faktury (číselné), nebo kód dokladu (kod).")
    ],
    include_items: Annotated[
        bool, Field(description="Přibalit položky faktury (polozkyFaktury).")
    ] = True,
) -> RecordEnvelope:
    """Detail vydané faktury včetně položek a polí zaúčtování.

    Účet DAL hlavičky je pole `protiUcet` (pole jménem `ucetDal` neexistuje);
    zaúčtování řídí předpis `typUcOp`. Zápisy účetního deníku k dokladu dá
    `get_invoice_journal`.
    """
    params: dict[str, Any] = {"detail": "full"}
    if include_items:
        # Položky přibaluje `relations=polozky` (`includes` je na referencované
        # objekty, kolekci položek nevrátí — ověřeno na živé instanci).
        params["relations"] = "polozky"
    with _Session() as session:
        record = _fetch_detail(session, "faktura-vydana", invoice_id, params=params)
        return _record_envelope(session, "faktura-vydana", record)


@tool(mcp, read_only=True)
def list_invoice_types(
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Typy vydaných faktur včetně vazby na předpis zaúčtování.

    Pole `typUcOpPrijem` odkazuje na předpis zaúčtování — řetězec odvození je
    typ dokladu → předpis → hlavičkové účty a daňový režim.
    """
    return _list_evidence(
        "typ-faktury-vydane", [], params={"detail": "full"}, limit=limit, offset=offset
    )


@tool(mcp, read_only=True)
def get_invoice_journal(
    invoice_id: Annotated[str, Field(description="Číselné ID dokladu (faktury).")],
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Zápisy účetního deníku k dokladu (účty MD `madatiUcet` / DAL `dalUcet`).

    Deník se ve Flexi generuje dynamicky z předpisu (`typUcOp`) HLAVIČKY
    dokladu — tohle je pohled na skutečné zaúčtování, ne na pole dokladu.
    """
    ident = _require_record_id(invoice_id, "invoice_id")
    return _list_evidence(
        "ucetni-denik",
        [f"idDokl={int(ident)}"],
        params={"detail": "full"},
        limit=limit,
        offset=offset,
    )


@tool(mcp, read_only=True)
def list_received_orders(
    date_from: Annotated[str | None, _D_DATE_FROM] = None,
    date_to: Annotated[str | None, _D_DATE_TO] = None,
    order: Annotated[str | None, _D_ORDER] = None,
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Seznam přijatých objednávek s filtry podle data vystavení."""
    conditions: list[str] = []
    if date_from:
        conditions.append(f"datVyst>='{require_date(date_from, 'date_from')}'")
    if date_to:
        conditions.append(f"datVyst<='{require_date(date_to, 'date_to')}'")
    params = {"order": require_order(order) if order else "datVyst@D"}
    return _list_evidence(
        "objednavka-prijata", conditions, params=params, limit=limit, offset=offset
    )


@tool(mcp, read_only=True)
def get_received_order(
    order_id: Annotated[
        str, Field(description="ID objednávky (číselné), nebo kód dokladu (kod).")
    ],
    include_items: Annotated[
        bool, Field(description="Přibalit položky (polozkyObchDokladu).")
    ] = True,
) -> RecordEnvelope:
    """Detail přijaté objednávky včetně položek."""
    params: dict[str, Any] = {"detail": "full"}
    if include_items:
        params["relations"] = "polozky"
    with _Session() as session:
        record = _fetch_detail(session, "objednavka-prijata", order_id, params=params)
        return _record_envelope(session, "objednavka-prijata", record)


@tool(mcp, read_only=True)
def list_stock_movements(
    date_from: Annotated[str, _D_DATE_FROM],
    date_to: Annotated[str, _D_DATE_TO],
    direction: Annotated[
        Literal["prijem", "vydej"] | None,
        Field(description="Směr pohybu (typPohybuK): prijem = příjemka, vydej = výdejka."),
    ] = None,
    warehouse: Annotated[
        str | None, Field(description="Kód skladu (bez prefixu code:).")
    ] = None,
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Seznam skladových pohybů (příjemky a výdejky) za období.

    Období je povinné: filtr směru a skladu se vyhodnocuje u nás (serverové
    ad-hoc filtry jsou na této evidenci nespolehlivé) a bez omezení rozsahu
    by jedno volání procházelo celou evidenci.
    """
    size = _clamp(limit)
    start = max(0, offset)
    conditions = [
        f"datVyst>='{require_date(date_from, 'date_from')}'",
        f"datVyst<='{require_date(date_to, 'date_to')}'",
    ]
    wanted_direction = f"typPohybu.{direction}" if direction else None
    wanted_warehouse = require_code(warehouse, "warehouse") if warehouse else None

    def matches(row: dict[str, Any]) -> bool:
        if wanted_direction and str(row.get("typPohybuK") or "") != wanted_direction:
            return False
        return not (
            wanted_warehouse and strip_code(row.get("sklad")) != wanted_warehouse
        )

    with _Session() as session:
        matched, exhausted, capped = _scan_evidence(
            session,
            "skladovy-pohyb",
            conditions,
            matches=matches,
            needed=start + size,
        )
        shown = matched[start : start + size]
        extra = (
            [
                f"Prohledáno jen prvních {_SCAN_PAGE * _SCAN_MAX_PAGES} pohybů v "
                "období — zužte rozsah dat."
            ]
            if capped
            else []
        )
        return _rows_envelope(
            session,
            shown,
            # total je poctivý jen po dočtení celé evidence.
            total=len(matched) if exhausted else None,
            size=size,
            start=0,
            suffix="/skladovy-pohyb",
            truncated=len(matched) > start + len(shown) or not exhausted,
            extra_warnings=extra,
        )


@tool(mcp, read_only=True)
def get_stock_movement(
    movement_id: Annotated[
        str, Field(description="ID pohybu (číselné), nebo kód dokladu (kod).")
    ],
) -> RecordEnvelope:
    """Detail skladového pohybu včetně položek (`skladovePolozky`)."""
    with _Session() as session:
        record = _fetch_detail(
            session, "skladovy-pohyb", movement_id, params={"detail": "full"}
        )
        return _record_envelope(session, "skladovy-pohyb", record)


@tool(mcp, read_only=True)
def get_stock_status(
    date: Annotated[str, Field(description="Stav zásob k tomuto datu (YYYY-MM-DD).")],
    warehouse: Annotated[str, Field(description="Kód skladu (bez prefixu code:).")],
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Stav zásob na skladě k zadanému datu (`stavMJ` po položkách ceníku)."""
    size = _clamp(limit)
    start = max(0, offset)
    with _Session() as session:
        payload = session.client.get_parsed(
            session.client.evidence_path("stav-skladu-k-datu"),
            {
                "sklad": code_ref(require_code(warehouse, "warehouse")),
                "datum": require_date(date, "date"),
                "detail": "full",
                "limit": size,
                "start": start,
                "add-row-count": "true",
            },
        )
        rows = session.client.unwrap(payload, "stav-skladu-k-datu")
        total = session.client.row_count(payload)
        return _rows_envelope(
            session, rows, total=total, size=size, start=start, suffix="/stav-skladu-k-datu"
        )


@tool(mcp, read_only=True)
def list_products(
    name_contains: Annotated[
        str | None,
        Field(description="Podřetězec názvu (hledá se u nás, přesná shoda podřetězce)."),
    ] = None,
    group: Annotated[
        str | None, Field(description="Kód skupiny zboží (skupZboz, bez prefixu code:).")
    ] = None,
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Seznam produktů a služeb z ceníku.

    Filtr názvu a skupiny se vyhodnocuje u nás nad stránkovaným průchodem
    ceníku — produkt typu sada (`sada`) nesmí do skladových pohybů, pole je
    v odpovědi.
    """
    size = _clamp(limit)
    start = max(0, offset)
    # `name_contains` se vyhodnocuje výhradně u nás (nikdy nejde do URL),
    # takže tu uzavřená množina znaků nemá důvod — diakritika je legitimní.
    needle = str(name_contains).strip().lower() if name_contains else None
    if needle is not None and not (0 < len(needle) <= 64):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT, "name_contains musí mít 1 až 64 znaků"
        )
    wanted_group = require_code(group, "group") if group else None

    def matches(row: dict[str, Any]) -> bool:
        if needle and needle not in str(row.get("nazev") or "").lower():
            return False
        return not (wanted_group and strip_code(row.get("skupZboz")) != wanted_group)

    with _Session() as session:
        if needle is None and wanted_group is None:
            # Bez filtru stačí obyčejné serverové stránkování.
            payload = session.client.get_parsed(
                session.client.evidence_path("cenik"),
                {"limit": size, "start": start, "add-row-count": "true", "detail": "summary"},
            )
            rows = session.client.unwrap(payload, "cenik")
            total = session.client.row_count(payload)
            return _rows_envelope(
                session, rows, total=total, size=size, start=start, suffix="/cenik"
            )
        matched, exhausted, capped = _scan_evidence(
            session, "cenik", [], matches=matches, needed=start + size
        )
        shown = matched[start : start + size]
        extra = (
            [
                f"Prohledáno jen prvních {_SCAN_PAGE * _SCAN_MAX_PAGES} položek "
                "ceníku — zpřesněte filtr."
            ]
            if capped
            else []
        )
        return _rows_envelope(
            session,
            shown,
            total=len(matched) if exhausted else None,
            size=size,
            start=0,
            suffix="/cenik",
            truncated=len(matched) > start + len(shown) or not exhausted,
            extra_warnings=extra,
        )


@tool(mcp, read_only=True)
def get_product(
    product_id: Annotated[
        str, Field(description="ID položky ceníku (číselné), nebo kód (kod).")
    ],
) -> RecordEnvelope:
    """Detail položky ceníku podle ID nebo kódu."""
    with _Session() as session:
        record = _fetch_detail(session, "cenik", product_id, params={"detail": "full"})
        return _record_envelope(session, "cenik", record)


# =============================================================================
# Generické čtení všech evidencí
# =============================================================================
#
# Vzor raynetu (`raynet_list`/`raynet_get`): registry allowlist + strukturovaný
# filtr místo volné syntaxe. Filtr Flexi jde do URL cesty — proto se výraz
# skládá výhradně tady z validovaných kousků (pole, operátor z uzavřené
# množiny, hodnota bez `'` a závorek) a spojuje jen přes AND.

_FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,40}(\.[A-Za-z][A-Za-z0-9]{0,40}){0,3}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{1,3})?)?$")
_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")

_BINARY_OPS = {
    "eq": "=",
    "neq": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
    "like": "like",
    "like_similar": "like similar",
    "begins": "begins",
    "begins_similar": "begins similar",
    "ends": "ends",
}
_UNARY_OPS = {
    "is_null": "is null",
    "is_not_null": "is not null",
    "is_true": "is true",
    "is_false": "is false",
    "is_empty": "is empty",
    "is_not_empty": "is not empty",
}


def _require_evidence(name: str) -> str:
    evidence = str(name).strip()
    if evidence not in EVIDENCES:
        raise ConnectorError(
            ErrorCode.INVALID_INPUT,
            "neznámá nebo nepodporovaná evidence — seznam dá nástroj list_evidences",
        )
    return evidence


def _require_field(name: str) -> str:
    field = str(name).strip()
    if not _FIELD_RE.fullmatch(field):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT,
            "název pole musí být camelCase identifikátor, případně tečkovaná "
            "vazba (např. firma.skupFir)",
        )
    return field


#: Textové operátory — hodnota se vždy quotuje jako řetězcový literál.
#: Zástupné znaky (`%`) Flexi u těchto operátorů NEpoužívá — `like similar
#: 's.r.o.'` hledá podřetězec sám o sobě, kdežto `%` v hodnotě se bere
#: doslovně a nenajde nic (ověřeno na živé instanci).
_TEXT_OPS = frozenset({"like", "like_similar", "begins", "begins_similar", "ends"})


def _literal(value: str | int | float | bool, *, force_quote: bool = False) -> str:
    """Hodnota podmínky jako literál filtračního jazyka.

    Čísla, data a booleany jdou bez uvozovek; všechno ostatní jako řetězcový
    literál v `'…'` s uzavřenou množinou znaků (bez `'` a závorek — z literálu
    nejde vyskočit). ``force_quote`` quotuje i číselně vypadající hodnoty —
    textové operátory potřebují řetězec vždy.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _number(value)
    text = value.strip()
    if not force_quote and (_NUMBER_RE.fullmatch(text) or _DATETIME_RE.fullmatch(text)):
        return text
    return f"'{require_code(text, 'value')}'"


def _conditions(filters: list[FilterCondition] | None) -> list[str]:
    conditions: list[str] = []
    for item in filters or []:
        field = _require_field(item.field)
        if item.op in _UNARY_OPS:
            if item.value is not None:
                raise ConnectorError(
                    ErrorCode.INVALID_INPUT,
                    f"operátor {item.op} nemá hodnotu — pole value vynech",
                )
            conditions.append(f"{field} {_UNARY_OPS[item.op]}")
            continue
        if item.value is None:
            raise ConnectorError(
                ErrorCode.INVALID_INPUT, f"operátor {item.op} vyžaduje hodnotu value"
            )
        if item.op in _TEXT_OPS and not isinstance(item.value, str):
            raise ConnectorError(
                ErrorCode.INVALID_INPUT,
                f"operátor {item.op} vyžaduje řetězcovou hodnotu",
            )
        literal = _literal(item.value, force_quote=item.op in _TEXT_OPS)
        conditions.append(f"{field} {_BINARY_OPS[item.op]} {literal}")
    return conditions


def _custom_detail(fields: list[str] | None) -> str | None:
    if not fields:
        return None
    return "custom:" + ",".join(_require_field(field) for field in fields)


_E_NOTATION_RE = re.compile(r"^-?\d+(\.\d+)?[eE][+-]?\d+$")


def _normalize_numbers(obj: Any) -> Any:
    """Převeď exponenciální zápis čísel na běžný.

    Flexi v souhrnech vrací velké částky jako ``2.183981677E7`` — model z toho
    snadno udělá chybný řád; ``21839816.77`` je jednoznačné.
    """
    if isinstance(obj, list):
        return [_normalize_numbers(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _normalize_numbers(value) for key, value in obj.items()}
    if isinstance(obj, str) and _E_NOTATION_RE.fullmatch(obj):
        try:
            return format(Decimal(obj), "f")
        except InvalidOperation:  # pragma: no cover — regex tvar Decimal umí
            return obj
    return obj


_D_EVIDENCE = Field(
    description="Strojový název evidence (viz list_evidences), např. adresar, banka."
)
_D_FILTERS = Field(
    description="Podmínky filtru spojené operátorem AND; hodnoty bez uvozovek."
)
_D_FIELDS = Field(
    description="Jen tato pole výstupu (detail=custom); bez zadání souhrnná pole."
)


@tool(mcp, read_only=True)
def list_evidences(
    area: Annotated[
        str | None,
        Field(description="Filtr oblasti: partneri, crm, prodej, nakup, sklad, ceny, "
                          "penize, ucetnictvi, reporty, dph, smlouvy, ciselniky, typy, "
                          "rady, stitky, majetek."),
    ] = None,
) -> RowsEnvelope:
    """Katalog evidencí dostupných přes generické nástroje.

    Je to allowlist konektoru (ne živý `/evidence-list` instance) — skutečná
    pole a práva dané instance ověří `get_evidence_properties`.
    """
    wanted = str(area).strip() if area else None
    rows = [
        {"evidence": name, "area": info.area, "description": info.description}
        for name, info in EVIDENCES.items()
        if wanted is None or info.area == wanted
    ]
    if wanted is not None and not rows:
        raise ConnectorError(ErrorCode.INVALID_INPUT, "neznámá oblast evidencí")
    return RowsEnvelope(
        items=rows,
        total=len(rows),
        truncated=False,
        provenance=Provenance(
            source_id=SOURCE_ID,
            source_url="https://www.flexibee.eu/api/dokumentace/",
            retrieved_at=now_utc_iso(),
            freshness="cached",
        ),
        warnings=[],
    )


@tool(mcp, read_only=True)
def list_records(
    evidence: Annotated[str, _D_EVIDENCE],
    filters: Annotated[list[FilterCondition] | None, _D_FILTERS] = None,
    order: Annotated[str | None, _D_ORDER] = None,
    fields: Annotated[list[str] | None, _D_FIELDS] = None,
    limit: Annotated[int | None, _D_LIMIT] = None,
    offset: Annotated[int, _D_OFFSET] = 0,
) -> RowsEnvelope:
    """Generický seznam záznamů libovolné podporované evidence.

    Podmínky se spojují přes AND; hodnoty typu datum (YYYY-MM-DD), číslo a
    boolean se předávají bez uvozovek, reference na číselník jako `code:X`.
    Položky dokladů mají vlastní evidence (`faktura-vydana-polozka`, …) —
    filtruj je tam, ne přes hlavičku.
    """
    checked = _require_evidence(evidence)
    params: dict[str, Any] = {}
    if order:
        params["order"] = require_order(order)
    detail = _custom_detail(fields)
    if detail:
        params["detail"] = detail
    return _list_evidence(
        checked, _conditions(filters), params=params, limit=limit, offset=offset
    )


@tool(mcp, read_only=True)
def get_record(
    evidence: Annotated[str, _D_EVIDENCE],
    record_id: Annotated[
        str,
        Field(
            description="Číselné ID záznamu, externí ID (ext:SYSTEM:hodnota), "
            "nebo kód (kod) evidence."
        ),
    ],
    fields: Annotated[list[str] | None, _D_FIELDS] = None,
    relations: Annotated[
        list[Literal["polozky", "prilohy", "vazby"]] | None,
        Field(
            description="Přibalit kolekce: polozky (položky dokladu), prilohy "
            "(metadata příloh), vazby (párování s jinými doklady, např. úhrady)."
        ),
    ] = None,
) -> RecordEnvelope:
    """Generický detail záznamu libovolné podporované evidence.

    `relations=["vazby"]` vrátí i vazby na související doklady — třeba kterou
    bankovní platbou je faktura uhrazená.
    """
    checked = _require_evidence(evidence)
    params: dict[str, Any] = {"detail": _custom_detail(fields) or "full"}
    if relations:
        params["relations"] = ",".join(dict.fromkeys(relations))
    with _Session() as session:
        record = _fetch_detail(session, checked, record_id, params=params)
        record = next(iter(_mask_contact_names(session, checked, [record])), record)
        return _record_envelope(session, checked, record)


@tool(mcp, read_only=True)
def list_companies() -> RowsEnvelope:
    """Seznam firem (databází) na připojeném Flexi serveru.

    Hodí se, když si nejsi jistý identifikátorem firmy (`dbNazev` — přesně ten
    patří do aktivace konektoru); server jich může hostovat víc včetně záloh.
    """
    with _Session() as session:
        rows = session.client.companies()
        clean = [row for row in session.sanitize(rows) if isinstance(row, dict)]
        return RowsEnvelope(
            items=clean,
            total=len(clean),
            truncated=False,
            provenance=Provenance(
                source_id=SOURCE_ID,
                source_url=f"{session.client.server_base}/c.xml",
                retrieved_at=now_utc_iso(),
                freshness="live",
            ),
            warnings=[],
        )


@tool(mcp, read_only=True)
def sum_records(
    evidence: Annotated[str, _D_EVIDENCE],
    filters: Annotated[list[FilterCondition] | None, _D_FILTERS] = None,
) -> RecordEnvelope:
    """Souhrn (`$sum`) evidence, volitelně nad filtrem.

    Vhodné na kontrolní součty bez stahování záznamů — např. součet vydaných
    faktur za období. Smysl dává hlavně u dokladových evidencí; u číselníků
    může upstream vrátit prázdný výsledek.
    """
    checked = _require_evidence(evidence)
    with _Session() as session:
        record = _normalize_numbers(session.client.get_sum(checked, _conditions(filters)))
        return _record_envelope(session, checked, record)


@tool(mcp, read_only=True)
def get_evidence_properties(
    evidence: Annotated[str, _D_EVIDENCE],
) -> RecordEnvelope:
    """Samodokumentace evidence: pole, typy, povinnost, editovatelnost.

    Autorita pro skutečný kontrakt dané instance (závisí na verzi, licenci
    a právech uživatele) — použij před prací s méně známou evidencí.
    """
    checked = _require_evidence(evidence)
    with _Session() as session:
        payload = session.client.get_parsed(session.client.properties_path(checked))
        return _record_envelope(session, checked, payload)


# =============================================================================
# Zápis
# =============================================================================
#
# ZÁMĚRNĚ NEVYSTAVENÉ operace — ať je vidět, že to není opomenutí:
#
#   DELETE (cokoliv) ....... mazání dokladů zůstává výhradně ve Flexi UI
#   zápisy do `adresar` .... změny kmenových dat firem/kontaktů = jiná třída rizika
#   generický zápis ........ čtení je generické (registry výše), zápis NE —
#                            „zapiš do libovolné evidence" = neohraničený blast radius
#   storno / action= ....... mění právní stav dokladu
#   dávkové filter= ........ hromadná změna všech shodných záznamů jedním requestem
#   přílohy / webhooky ..... jiná třída rizika (binární obsah, callback URL)
#
# Payload se NIKDY nesestavuje průchodem argumentů — každý nástroj má
# explicitní allowlist polí (`build_payload`). Zbytek zápisové vrstvy
# (politika → strop → diff → potvrzení → audit) je `openmcp_sdk.write`.
#
# Invarianty chování Flexi (MCP_PODKLAD §5.2), které tu vynucujeme:
#   * položka se opravuje JEDNÍM agregovaným PUT přes hlavní doklad a vždy
#     s `kopTypUcOp=false` — jinak Flexi pole přepočítá z předpisu dokladu,
#   * `clenDph` se při změně `typDokl` nepřepočítá — posílá se explicitně,
#   * úspěch zápisu se čte z `winstrom.success`, ne z HTTP stavu.

_WRITE_LIMIT = 10
_WRITE_WINDOW_S = 300
# Vlastní instance (ne DEFAULT_BUDGET), aby jméno zůstalo stabilní API pro testy.
_write_budget = WriteBudget(limit=_WRITE_LIMIT, window_s=_WRITE_WINDOW_S)


#: ASCII číslice — `str.isdigit()` propouští i unicode číslice (`"١٢٣"`),
#: které Flexi jako ID nezná. Délka je omezená na 19 číslic (int64 Flexi):
#: neomezené `[0-9]+` pustilo dál řetězec, na kterém `int()` v Pythonu 3.11+
#: hodí `ValueError: Exceeds the limit (4300 digits)` — neošetřenou výjimku
#: z argumentu, který skládá model (`get_invoice_journal`).
_RECORD_ID_RE = re.compile(r"[0-9]{1,19}")


def _require_record_id(value: str, label: str) -> str:
    ident = str(value).strip()
    if not _RECORD_ID_RE.fullmatch(ident):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT, f"{label} musí být číselné ID záznamu"
        )
    return ident


def _number(value: float) -> str:
    """Částky a množství jdou do Flexi jako řetězce s desetinnou tečkou.

    Přes ``Decimal``, ne ``{:g}`` — `g` má 6 platných cifer a nad ně přepíná
    na exponenciální tvar: cena ``1234567.89`` by odešla jako ``1.23457e+06``,
    tedy poškozená data v cizím účetnictví.

    Formátuje se VŽDY přes ``format(…, "f")``, i celá čísla. ``Decimal``
    exponent nese s sebou a ``to_integral_value()`` ho zachovává, takže
    ``str(Decimal("1e16").to_integral_value())`` je ``"1E+16"`` — přesně ten
    exponenciální tvar, kterému se tahle funkce vyhýbá.

    Nekonečno a NaN se odmítají TADY, i když je schémata (`allow_inf_nan=False`)
    nepustí dál — tohle je poslední místo před drátem a ``format(Decimal("inf"),
    "f")`` vyrobí řetězec ``Infinity``, tedy poškozený zápis do cizího
    účetnictví. Dvě vrstvy proto, že sem vede i cesta z filtrů (`_literal`).
    """
    if not math.isfinite(value):
        raise ConnectorError(
            ErrorCode.INVALID_INPUT, "číselná hodnota musí být konečná"
        )
    decimal = Decimal(str(value))
    integral = decimal.to_integral_value()
    return format(integral if decimal == integral else decimal, "f")


def _result_ids(parsed: dict[str, Any]) -> list[str]:
    """ID záznamů z výsledku zápisu (`winstrom.results.result[].id`).

    Flexi vrací ID jako element ``<id>`` i jako atribut ``<result id="…">``
    (po zploštění klíč ``@id``) — tolerují se oba tvary.
    """
    winstrom = parsed.get("winstrom")
    results = winstrom.get("results") if isinstance(winstrom, dict) else None
    if isinstance(results, dict):
        results = results.get("result")
    if not isinstance(results, list):
        return []
    ids: list[str] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        value = result.get("id") or result.get("@id")
        if value:
            ids.append(str(value))
    return ids


class _MissingTargetError(ConnectorError):
    """Nenalezený cíl zápisu, který se nesmí ignorovat ani bez elicitation."""


def _missing_target(what: str) -> _MissingTargetError:
    """Cíl zápisu neexistuje — diff by byl vymyšlený, tak zápis nepustíme.

    Prázdný výsledek čtení „před" NENÍ totéž co nenalezený záznam: faktura
    bez vyplněného ``popis`` legitimně vrátí prázdný diff. Rozlišuje se proto
    NEEXISTENCE cíle (žádný záznam / položka s tímhle ``id``), ne prázdnota
    hodnot — jinak by šlo potvrzení obejít volbou nevyplněných polí.

    ``execute_write`` od SDK 0.4.3 výjimku z ``fetch_before`` při zapnutém
    potvrzení propustí ven. Při vypnutém potvrzení ji ale kvůli dostupnosti
    diffu ignoruje, proto ``_write`` nese tenhle konkrétní typ až do
    ``apply`` a zastaví zápis i tam. Bez toho by PUT odešel na cizí ``id``.
    """
    return _MissingTargetError(ErrorCode.NOT_FOUND, f"{what} — zápis neproběhl")


def _current_values(
    session: _Session, evidence: str, record_id: str, fields: Any
) -> dict[str, Any]:
    """Současné hodnoty polí, která se chystáme přepsat (diff pro potvrzení)."""
    payload = session.client.get_parsed(
        session.client.evidence_path(evidence, record=record_id), {"detail": "full"}
    )
    rows = session.client.unwrap(payload, evidence)
    if not rows:
        raise _missing_target(f"záznam {record_id} v evidenci {evidence} neexistuje")
    return {k: rows[0].get(k) for k in fields if k in rows[0]}


async def _write(
    tool_name: str,
    evidence: str,
    record_id: str | None,
    payload: dict[str, Any],
    *,
    wrap: Any = None,
    fetch_current: Any = None,
) -> Any:
    """Společná cesta všech zápisů — tenká obálka nad `execute_write`.

    Fail-closed vrstvy řeší `execute_write` samo: politika workspace, strop
    zápisů v okně, potvrzení člověkem s diffem, audit. Tady zůstává jen
    doménová část: stavba `winstrom` těla (`wrap` zanoří payload např. do
    `polozkyFaktury`) a `changed` stopa po přepsaných hodnotách — Flexi
    historii změn nedrží, tohle je jediná stopa po původní hodnotě.
    """
    with _Session() as session:
        captured_before: dict[str, Any] = {}
        missing_target: _MissingTargetError | None = None

        def fetch_before(target: WriteTarget, fields: Any) -> dict[str, Any]:
            nonlocal missing_target
            try:
                if fetch_current is not None:
                    captured_before.update(fetch_current(session, fields))
                else:
                    captured_before.update(
                        _current_values(session, evidence, str(record_id), fields)
                    )
            except _MissingTargetError as exc:
                # Bez potvrzení SDK běžnou chybu načtení diffu záměrně
                # ignoruje a pokračuje do `apply`. Neexistující cíl ale není
                # jen chybějící diff: zápis na cizí ID se nesmí vykonat v
                # žádném režimu. Stav si proto neseme až do apply.
                missing_target = exc
                raise
            return captured_before

        def apply(body: Any) -> dict[str, Any]:
            if missing_target is not None:
                raise missing_target
            flexi_body: dict[str, Any] = wrap(dict(body)) if wrap else dict(body)
            if record_id is not None:
                flexi_body.setdefault("id", record_id)
            parsed = session.client.write_evidence(evidence, flexi_body, record=record_id)
            result: dict[str, Any] = {
                "success": True,
                "changed": {
                    k: {"before": captured_before.get(k), "after": v}
                    for k, v in body.items()
                },
            }
            ids = _result_ids(parsed)
            if ids:
                result["ids"] = ids
            return result

        return await execute_write(
            tool_name,
            WriteTarget(evidence, record_id),
            payload,
            apply=apply,
            product="ABRA Flexi",
            fetch_before=fetch_before,
            budget=_write_budget,
            sanitize=session.sanitize,
        )


def _payload_or_fail(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        raise ConnectorError(
            ErrorCode.INVALID_INPUT, "není co zapsat — zadej aspoň jedno měněné pole"
        )
    return payload


@tool(mcp, read_only=False, destructive=True)
async def update_invoice_header(
    invoice_id: Annotated[str, Field(description="Číselné ID vydané faktury.")],
    document_type: Annotated[
        str | None, Field(description="Kód typu dokladu (typDokl, bez prefixu code:).")
    ] = None,
    accounting_template: Annotated[
        str | None,
        Field(description="Kód předpisu zaúčtování (typUcOp, bez prefixu code:)."),
    ] = None,
    revenue_account: Annotated[
        str | None,
        Field(description="Výnosový účet DAL hlavičky (protiUcet, např. 604001)."),
    ] = None,
    vat_classification: Annotated[
        str | None, Field(description="Členění DPH (clenDph, bez prefixu code:).")
    ] = None,
    description: Annotated[str | None, Field(description="Popis dokladu (popis).")] = None,
) -> Any:
    """Opraví zaúčtování hlavičky vydané faktury. Neuvedená pole se nemění.

    Pravidla Flexi, se kterými počítej: uhrazená faktura má `typDokl` zamčený
    (vázaný na úhradu) — u ní nastav hlavičková pole přímo, deník se přepočítá
    hned. `clenDph` se při změně `typDokl` NEpřepočítá — pošli ho explicitně.
    Účetní deník se generuje z předpisu (`typUcOp`) hlavičky; oprava jen
    `protiUcet` bez předpisu nestačí. Pořadí oprav: typDokl → hlavička →
    položky.
    """
    record = _require_record_id(invoice_id, "invoice_id")
    payload = _payload_or_fail(
        build_payload(
            typDokl=code_ref(require_code(document_type, "document_type"))
            if document_type
            else None,
            typUcOp=code_ref(require_code(accounting_template, "accounting_template"))
            if accounting_template
            else None,
            protiUcet=code_ref(require_code(revenue_account, "revenue_account"))
            if revenue_account
            else None,
            clenDph=code_ref(require_code(vat_classification, "vat_classification"))
            if vat_classification
            else None,
            popis=description,
        )
    )
    return await _write("update_invoice_header", "faktura-vydana", record, payload)


@tool(mcp, read_only=False, destructive=True)
async def update_invoice_item(
    invoice_id: Annotated[str, Field(description="Číselné ID vydané faktury.")],
    item_id: Annotated[
        str, Field(description="Číselné ID položky faktury (z detailu, polozkyFaktury).")
    ],
    revenue_account: Annotated[
        str | None,
        Field(description="Výnosový účet DAL položky (zklDalUcet, např. 604005)."),
    ] = None,
    vat_classification: Annotated[
        str | None, Field(description="Členění DPH položky (clenDph, bez prefixu code:).")
    ] = None,
    accounting_template: Annotated[
        str | None,
        Field(description="Předpis zaúčtování položky (typUcOp, bez prefixu code:)."),
    ] = None,
) -> Any:
    """Opraví zaúčtování jedné položky faktury JEDNÍM agregovaným zápisem.

    Související pole položky se posílají najednou a vždy s `kopTypUcOp=false`
    (vynucuje server, není to parametr) — položka poslaná po jednotlivých
    polích nebo s `kopTypUcOp=true` by se přepočítala z předpisu dokladu
    a vrátila na jiné hodnoty. Položky nemají vlastní endpoint: zapisuje se
    PUT přes hlavní doklad. Pozor: u dokladů v OSS režimu Flexi `clenDph`
    položek tiše ignoruje.
    """
    record = _require_record_id(invoice_id, "invoice_id")
    item = _require_record_id(item_id, "item_id")
    payload = _payload_or_fail(
        build_payload(
            zklDalUcet=code_ref(require_code(revenue_account, "revenue_account"))
            if revenue_account
            else None,
            clenDph=code_ref(require_code(vat_classification, "vat_classification"))
            if vat_classification
            else None,
            typUcOp=code_ref(require_code(accounting_template, "accounting_template"))
            if accounting_template
            else None,
        )
    )

    def wrap(body: dict[str, Any]) -> dict[str, Any]:
        # XML tvar kolekce: <polozkyFaktury><faktura-vydana-polozka>…
        return {
            "polozkyFaktury": {
                "faktura-vydana-polozka": [{"id": item, **body, "kopTypUcOp": "false"}]
            }
        }

    def fetch_item(session: _Session, fields: Any) -> dict[str, Any]:
        payload_before = session.client.get_parsed(
            session.client.evidence_path("faktura-vydana", record=record),
            {"detail": "full", "relations": "polozky"},
        )
        rows = session.client.unwrap(payload_before, "faktura-vydana")
        entries = rows[0].get("polozkyFaktury") if rows else None
        for entry in entries if isinstance(entries, list) else []:
            if isinstance(entry, dict) and str(entry.get("id")) == item:
                return {k: entry.get(k) for k in fields if k in entry}
        raise _missing_target(f"položka {item} na faktuře {record} není")

    return await _write(
        "update_invoice_item",
        "faktura-vydana",
        record,
        payload,
        wrap=wrap,
        fetch_current=fetch_item,
    )


@tool(mcp, read_only=False, destructive=False, idempotent=False)
async def create_stock_movement(
    document_type: Annotated[
        str, Field(description="Kód typu skladového dokladu (typDokl, bez prefixu code:).")
    ],
    movement_subtype: Annotated[
        Literal["prijemHoly", "prijemNaFak", "prijemDoVyr"],
        Field(description="Podtyp příjmu (typPohybuSkladK)."),
    ],
    warehouse: Annotated[str, Field(description="Kód skladu (bez prefixu code:).")],
    date: Annotated[str, Field(description="Datum vystavení (YYYY-MM-DD).")],
    items: Annotated[
        list[StockItemInput], Field(description="Položky pohybu (aspoň jedna.)")
    ],
) -> Any:
    """Založí skladový pohyb (příjemku) s položkami.

    Položky se při vytváření posílají jako `polozkyDokladu` (při čtení jsou
    pak ve `skladovePolozky` — asymetrie Flexi). Omezení Flexi: produkty typu
    sada do pohybů nesmí a produkt musí mít pro daný rok skladovou kartu.
    """
    if not items:
        raise ConnectorError(ErrorCode.INVALID_INPUT, "pohyb musí mít aspoň jednu položku")
    payload = build_payload(
        typDokl=code_ref(require_code(document_type, "document_type")),
        typPohybuSkladK=f"typPohybuSklad.{movement_subtype}",
        sklad=code_ref(require_code(warehouse, "warehouse")),
        datVyst=require_date(date, "date"),
        polozkyDokladu={
            "skladovy-pohyb-polozka": [
                {
                    "cenik": code_ref(require_code(entry.product_code, "product_code")),
                    "mnozMj": _number(entry.quantity),
                    "cenaMj": _number(entry.unit_price),
                }
                for entry in items
            ]
        },
    )
    return await _write("create_stock_movement", "skladovy-pohyb", None, payload)


@tool(mcp, read_only=False, destructive=True)
async def update_stock_movement_items(
    movement_id: Annotated[str, Field(description="Číselné ID skladového pohybu.")],
    items: Annotated[
        list[StockItemPriceInput],
        Field(description="Položky k úpravě — jen cena a množství."),
    ],
) -> Any:
    """Upraví ceny nebo množství položek existujícího skladového pohybu.

    Položky nemají vlastní endpoint — zapisuje se PUT přes hlavní doklad
    s `polozkyDokladu` a `id` konkrétních položek.
    """
    record = _require_record_id(movement_id, "movement_id")
    if not items:
        raise ConnectorError(ErrorCode.INVALID_INPUT, "zadej aspoň jednu položku k úpravě")
    rows: list[dict[str, Any]] = []
    for entry in items:
        row: dict[str, Any] = {"id": _require_record_id(entry.item_id, "item_id")}
        if entry.unit_price is not None:
            row["cenaMj"] = _number(entry.unit_price)
        if entry.quantity is not None:
            row["mnozMj"] = _number(entry.quantity)
        rows.append(row)
    payload = build_payload(polozkyDokladu={"skladovy-pohyb-polozka": rows})
    wanted_ids = {row["id"] for row in rows}

    def fetch_current(session: _Session, fields: Any) -> dict[str, Any]:
        # Diff pro potvrzení: při ČTENÍ jsou položky ve `skladovePolozky`
        # (asymetrie Flexi vůči zápisovému `polozkyDokladu`).
        detail = session.client.get_parsed(
            session.client.evidence_path("skladovy-pohyb", record=record),
            {"detail": "full"},
        )
        recs = session.client.unwrap(detail, "skladovy-pohyb")
        entries = recs[0].get("skladovePolozky") if recs else None
        before = [
            {key: item.get(key) for key in ("id", "cenaMj", "mnozMj") if key in item}
            for item in (entries if isinstance(entries, list) else [])
            if isinstance(item, dict) and str(item.get("id")) in wanted_ids
        ]
        if missing := sorted(wanted_ids - {str(row.get("id")) for row in before}):
            raise _missing_target(
                f"na pohybu {record} nejsou položky {', '.join(missing)}"
            )
        return {"polozkyDokladu": before}

    return await _write(
        "update_stock_movement_items",
        "skladovy-pohyb",
        record,
        payload,
        fetch_current=fetch_current,
    )


# -- test spojení --------------------------------------------------------------

#: Rozpočet hosted ``/internal/credential-test`` je ~12 s. Výchozí klient
#: (timeout 30 s, ``READ_RETRY`` se čtyřmi pokusy) ho umí přetáhnout
#: několikanásobně — control plane mezitím request utne a uživatel místo
#: „server je nedostupný" uvidí `outcome_unknown`. Safe test proto dostává
#: vlastní krátký rozpočet a JEDEN pokus. Běžné čtecí nástroje si retry
#: ponechávají: tam je latence levnější než zbytečné selhání.
_TEST_TIMEOUT_S = 6.0
_TEST_CONNECT_TIMEOUT_S = 3.0


def test_connection() -> str:
    """Ověří přesně tu verzi credentials, kterou SDK vložilo do kontextu.

    Hosted ``/internal/credential-test`` nepřenáší tajemství v těle requestu.
    SDK načte konkrétní staged verzi z Vaultu, vytvoří ``current_context`` a
    callback volá bez argumentů. Stejný kontrakt používají i ostatní hosted
    konektory; starý podpis ``(secrets, config)`` by skončil jako interní chyba.

    Klasifikace používá ``ConnectorError.status``, ne text odpovědi upstreamu.
    Syrové vendor tělo se nikdy nevrací do API ani logu.
    """
    try:
        session = _Session(
            timeout=_TEST_TIMEOUT_S,
            connect_timeout=_TEST_CONNECT_TIMEOUT_S,
            retry=NO_RETRY,
        )
    except (ConnectorError, KeyError) as exc:
        # Sem spadne chybějící heslo i neplatná `api_url`/`company` — tedy
        # něco, co opraví uživatel v aktivaci, ne provoz. `INVALID_INPUT` se
        # od API PR #34 skládá na `runtime_unavailable` („platforma je
        # rozbitá"), což je špatná rada; `credential_invalid` vede na akci
        # `set_access`.
        raise ConnectorError(
            ErrorCode.CREDENTIAL_INVALID,
            "Chybí nebo jsou neplatné údaje připojení k ABRA Flexi.",
        ) from exc

    try:
        companies = session.client.company_info()
    except ConnectorError as exc:
        # 401 a 403 NEJSOU totéž. 401 = Flexi neuznala jméno/heslo. 403 =
        # přihlášení prošlo, ale uživatel na firmu nebo evidenci nemá právo —
        # měnit heslo je tam špatná rada, správná je upravit roli ve Flexi.
        # Control plane obojí rozlišuje (`credential_invalid` vs
        # `provider_permission_denied`, viz `credentialversion/tester.go`).
        if exc.status == 401:
            raise ConnectorError(
                ErrorCode.CREDENTIAL_INVALID,
                "Flexi odmítla přihlášení — zkontroluj uživatele a heslo.",
            ) from exc
        if exc.status == 403:
            raise ConnectorError(
                ErrorCode.PROVIDER_PERMISSION_DENIED,
                "Uživatel se přihlásil, ale nemá ve Flexi právo na tuto firmu "
                "— zkontroluj jeho role a přístup k firmě.",
            ) from exc
        if exc.status == 404:
            # 404 NENÍ odmítnuté tajemství: heslo projde, nedosáhneme na
            # firmu. Příčiny jsou podle dokumentace dvě a zvenčí je nerozlišíme
            # — zdroj neexistuje, NEBO je skrytý z licenčních důvodů; navíc
            # „402 (neaktivní REST licence) u čtení může působit jako 404"
            # (§3.3). Rada proto míří na obojí, ne jen na překlep v kódu firmy.
            #
            # Control plane `instance_unknown` zná od API PR #34
            # (`normalizeTestResponseCode`, migrace 00074) a webapp ho vede na
            # akci `set_access` stejně jako `credential_invalid`.
            # `INVALID_INPUT` by tu bylo horší než dřív: od stejného PR se
            # skládá na `runtime_unavailable`, tedy „platforma je rozbitá".
            raise ConnectorError(
                ErrorCode.INSTANCE_UNKNOWN,
                "K firmě s tímto kódem se nedá přistoupit — zkontroluj kód "
                "firmy a také to, že má instance aktivovaný přístup přes REST "
                "API (licenci).",
            ) from exc
        if exc.status == 429:
            # Rate limit není výpadek. `provider_rate_limited` říká „zkus to
            # znovu", kdežto `provider_unavailable` vede diagnostiku k serveru.
            raise ConnectorError(
                ErrorCode.RATE_LIMITED,
                "ABRA Flexi teď odmítá požadavky kvůli limitu — zkus to za chvíli.",
            ) from exc
        if exc.code is ErrorCode.INTERNAL:
            # Odpověď, která není platné XML, nebo chybějící `winstrom` obálka.
            # To je porušení protokolu na naší straně kontraktu, ne odmítnuté
            # tajemství — `runtime_unavailable`, nikdy `credential_invalid`.
            raise ConnectorError(
                ErrorCode.INTERNAL,
                "Odpověď ABRA Flexi se nepodařilo zpracovat.",
            ) from exc
        # ZDE BÝVALA větev `status is None and code is INVALID_INPUT`, která
        # měla propustit chybu formátu/konfigurace. Byla mrtvá: všechny takové
        # chyby (`_validated_api_url`, kontroly `base_url` v `UpstreamClient`,
        # `seg()` nad `company`) vznikají při STAVBĚ klienta, tedy uvnitř
        # `_Session()` — a ty chytá `except` výše. Z `company_info()` přijde
        # `INVALID_INPUT` už jen se `status` (400/409/422); 404/410 mapuje
        # SDK na `NOT_FOUND`. Connection test se rozhoduje podle zachovaného
        # HTTP statusu, takže 404 firmy zůstává `INSTANCE_UNKNOWN`.
        raise ConnectorError(
            ErrorCode.UPSTREAM_UNAVAILABLE,
            "Server ABRA Flexi je nedostupný, zkus to prosím později.",
        ) from exc
    finally:
        session.client.close()

    expected_company = session.company.casefold()
    if not companies or not any(
        str(company.get("dbNazev") or "").casefold() == expected_company
        for company in companies
    ):
        # Fail-closed: HTTP 200 sám o sobě není důkaz spojení s Flexi.
        # `/c/{firma}.xml` vrací podle dokumentace obálku `<companies>` se
        # záznamem `<company>` a jeho `dbNazev` je identifikátor firmy
        # (§16.1). Aktivace míří na konkrétní firmu, takže prázdný seznam ani
        # platný záznam jiné databáze nejsou legitimní odpověď.
        #
        # Bez téhle kontroly potvrdil test spojení i captive portál, který na
        # 200 vrátí dobře formované XHTML: `company_info()` v něm obálku
        # nenajde, `ConnectorError` z fallbacku si sám odchytí a vrátí `[]`.
        raise ConnectorError(
            ErrorCode.INTERNAL,
            "Odpověď ABRA Flexi neobsahuje údaje o aktivované firmě — "
            "zkontroluj adresu serveru a kód firmy.",
        )
    return "Spojení s ABRA Flexi funguje."
