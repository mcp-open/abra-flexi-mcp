"""Přesměrování při adresování externím ID (`ext:`).

Jediné místo, kde konektor vůbec nějaké přesměrování následuje, je
`_fetch_detail` s `ext:` identifikátorem — Flexi na něj odpovídá 301 na
kanonickou URL záznamu. Politika je „same origin, nebo nic".

Kontroly na neplatný port a userinfo v `Location` **jsou v SDK** — v `main`
od PR #8 (`0d36cf1`, `UpstreamClient._same_origin_location`). Dřív žily jen
ve větvi `codex/abraflexi-safe-redirect-20260726`, na které konektor do
31. 7. 2026 visel pinem, a mezi `b843432` a `0d36cf1` v `main` chyběly.

Konektor si je proto nedrží sám. Tyhle testy jsou tu jako **regrese přes
skutečnou volací cestu konektoru**: kdyby je budoucí bump SDK zase ztratil,
padnou tady, ne až v provozu.
"""

from __future__ import annotations

import httpx
import pytest
from openmcp_sdk.envelope import ConnectorError
from tests.conftest import ctx, winstrom_xml, xml_response

from connector.server import get_record

CANONICAL = "https://demo.flexibee.eu:5434/c/demo/objednavka-prijata/2736.xml"


def _redirecting(location: str):
    """Na `ext:` URL odpoví 301, na cokoli dalšího záznamem."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "ext%3A" in str(request.url):
            return httpx.Response(301, headers={"Location": location})
        return xml_response(
            winstrom_xml("objednavka-prijata", [{"id": "2736", "kod": "OBP1"}])
        )

    return handler


def test_same_origin_redirect_is_followed(upstream):
    seen = upstream(_redirecting(CANONICAL))
    with ctx():
        result = get_record("objednavka-prijata", "ext:SHOP:order-99")
    assert result.record["id"] == "2736"
    assert [str(request.url) for request in seen][-1] == CANONICAL


def test_relative_redirect_stays_on_the_validated_origin(upstream):
    """Relativní `Location` nemůže opustit ověřený origin.

    Tvrdí se tu jen origin, ne výsledná cesta: SDK relativní `Location`
    nepředává přes RFC 3986 resolution, ale jako cestu httpx klientu, který
    ji připojí k `base_url` (ta u Flexi končí `/c`). Živá Flexi odpovídá
    absolutní URL, takže se to v provozu neprojeví — a bezpečnostní záruka
    (nikam mimo host) platí tak jako tak.
    """
    seen = upstream(_redirecting("/c/demo/objednavka-prijata/2736.xml"))
    with ctx():
        get_record("objednavka-prijata", "ext:SHOP:order-99")
    assert len(seen) == 2
    assert str(seen[-1].url).startswith("https://demo.flexibee.eu:5434/")


def test_cross_origin_redirect_is_not_followed(upstream):
    """Basic credentials nesmí odejít na cizí host — 301 zůstane chybou."""
    seen = upstream(_redirecting("https://evil.example.com/c/demo/x.xml"))
    with ctx(), pytest.raises(ConnectorError):
        get_record("objednavka-prijata", "ext:SHOP:order-99")
    assert len(seen) == 1


def test_redirect_with_invalid_port_is_a_connector_error(upstream):
    """`urlsplit(...).port` hodí ValueError pro port mimo rozsah.

    Nechycený by z nástroje odešel jako neošetřená výjimka — upstream by tím
    řídil typ chyby, kterou konektor vyhodí. Musí to být `ConnectorError`
    z nenásledovaného 301, ne `ValueError`.
    """
    seen = upstream(_redirecting("https://demo.flexibee.eu:99999/c/demo/x.xml"))
    with ctx(), pytest.raises(ConnectorError):
        get_record("objednavka-prijata", "ext:SHOP:order-99")
    assert len(seen) == 1


def test_redirect_carrying_userinfo_is_not_followed(upstream):
    """Stejný host, ale `Location` nese cizí přihlašovací údaje.

    Auth klienta má přednost, takže se credentials nepodvrhnou — ale URL
    s cizím userinfo nemá důvod se dostat do requestu ani do telemetrie.
    """
    seen = upstream(
        _redirecting("https://kdokoli:tajne@demo.flexibee.eu:5434/c/demo/x.xml")
    )
    with ctx(), pytest.raises(ConnectorError):
        get_record("objednavka-prijata", "ext:SHOP:order-99")
    assert len(seen) == 1


def test_plain_reads_never_follow_redirects(upstream):
    """Bez `ext:` se `same_origin_redirects` nezapíná — 301 je rovnou chyba."""
    seen = upstream(lambda request: httpx.Response(301, headers={"Location": CANONICAL}))
    with ctx(), pytest.raises(ConnectorError):
        get_record("objednavka-prijata", "2736")
    assert len(seen) == 1
