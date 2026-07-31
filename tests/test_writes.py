"""Testy zapisovací cesty — potvrzení, allowlist, winstrom.success, rozpočet.

Potvrzení řeší `openmcp_sdk.write.execute_write` přes fastmcp elicitation —
testy používají `openmcp_sdk.testing.elicitation`.
"""

from __future__ import annotations

import httpx
import pytest
from openmcp_sdk.envelope import ConnectorError, ErrorCode
from openmcp_sdk.testing import elicitation
from tests.conftest import WRITE_FAIL, WRITE_OK, ctx, winstrom_xml, xml_response

from connector import server
from connector.schemas import StockItemInput, StockItemPriceInput
from connector.server import (
    create_stock_movement,
    update_invoice_header,
    update_invoice_item,
    update_stock_movement_items,
)

pytestmark = pytest.mark.anyio

INVOICE_DETAIL = winstrom_xml(
    "faktura-vydana",
    [
        {
            "id": "16792",
            "protiUcet": "code:604001",
            "clenDph": "code:TUZEMSKO",
            # Reálný XML tvar kolekce: obal + položková evidence.
            "polozkyFaktury": {
                "faktura-vydana-polozka": [
                    {
                        "id": "128072",
                        "zklDalUcet": "code:604001",
                        "clenDph": "code:TUZEMSKO",
                    }
                ]
            },
        }
    ],
)


#: Skladový pohyb má položky ve `skladovePolozky` (asymetrie vůči zápisovému
#: `polozkyDokladu`). Vlastní fixture proto, že testy pohybů dřív dostávaly
#: z GETu detail FAKTURY — na nesouvisejícím tvaru se nedalo poznat, že se
#: „původní hodnoty" nenačetly.
MOVEMENT_DETAIL = winstrom_xml(
    "skladovy-pohyb",
    [
        {
            "id": "555",
            "skladovePolozky": {
                "skladovy-pohyb-polozka": [
                    {"id": "77", "cenaMj": "99.5", "mnozMj": "3"},
                    {"id": "78", "cenaMj": "10.0", "mnozMj": "1"},
                ]
            },
        }
    ],
)


def _write_upstream(upstream):
    """GET vrací detail faktury (diff), POST/PUT úspěch zápisu."""
    writes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(INVOICE_DETAIL)
        writes.append(request)
        return xml_response(WRITE_OK)

    seen = upstream(handler)
    return seen, writes


async def test_confirmation_shows_real_diff_and_writes_on_accept(upstream):
    _, writes = _write_upstream(upstream)
    with elicitation("accept") as fake, ctx(write=True, confirm=True):
        result = await update_invoice_header("16792", revenue_account="604005")
    assert len(writes) == 1
    assert writes[0].method == "PUT"
    assert "/c/demo/faktura-vydana/16792.xml" in str(writes[0].url)
    # Diff v potvrzení nese skutečné hodnoty — čte ho člověk, ne model.
    assert "604005" in fake.messages[0]
    assert "code:604001" in fake.messages[0]
    assert result["success"] is True
    assert result["changed"]["protiUcet"]["before"] == "code:604001"
    assert result["changed"]["protiUcet"]["after"] == "code:604005"


async def test_declined_confirmation_blocks_write(upstream):
    _, writes = _write_upstream(upstream)
    with (
        elicitation("decline"),
        ctx(write=True, confirm=True),
        pytest.raises(ConnectorError) as excinfo,
    ):
        await update_invoice_header("16792", revenue_account="604005")
    assert excinfo.value.code is ErrorCode.FORBIDDEN
    assert writes == []


async def test_client_without_elicitation_is_fail_closed(upstream):
    _, writes = _write_upstream(upstream)
    with (
        elicitation("unsupported"),
        ctx(write=True, confirm=True),
        pytest.raises(ConnectorError),
    ):
        await update_invoice_header("16792", revenue_account="604005")
    assert writes == []


async def test_write_denied_by_read_only_policy(upstream):
    _, writes = _write_upstream(upstream)
    with ctx(write=False), pytest.raises(ConnectorError) as excinfo:
        await update_invoice_header("16792", revenue_account="604005")
    assert excinfo.value.code is ErrorCode.FORBIDDEN
    assert writes == []


async def test_header_payload_contains_only_allowlisted_fields(upstream):
    _, writes = _write_upstream(upstream)
    with ctx(write=True):
        await update_invoice_header(
            "16792", revenue_account="604005", vat_classification="TUZEMSKO"
        )
    body = writes[0].content.decode("utf-8")
    assert "<protiUcet>code:604005</protiUcet>" in body
    assert "<clenDph>code:TUZEMSKO</clenDph>" in body
    assert "<id>16792</id>" in body
    # Nic navíc — žádné pole, které nástroj nevystavuje.
    assert "typDokl" not in body
    assert "popis" not in body


async def test_item_update_is_one_aggregated_put_with_kop_false(upstream):
    _, writes = _write_upstream(upstream)
    with ctx(write=True):
        await update_invoice_item(
            "16792", "128072", revenue_account="604005", vat_classification="TUZEMSKO"
        )
    assert len(writes) == 1
    body = writes[0].content.decode("utf-8")
    assert "<polozkyFaktury>" in body
    assert "<faktura-vydana-polozka>" in body
    assert "<id>128072</id>" in body
    assert "<zklDalUcet>code:604005</zklDalUcet>" in body
    # Invariant: bez kopTypOp=false by Flexi položku přepočítala z předpisu.
    assert "<kopTypUcOp>false</kopTypUcOp>" in body


async def test_create_stock_movement_posts_polozky_dokladu(upstream):
    _, writes = _write_upstream(upstream)
    with ctx(write=True):
        result = await create_stock_movement(
            document_type="PRIJEMKA",
            movement_subtype="prijemHoly",
            warehouse="SKLAD",
            date="2025-11-30",
            items=[StockItemInput(product_code="ZID-01", quantity=5, unit_price=100.5)],
        )
    assert writes[0].method == "POST"
    body = writes[0].content.decode("utf-8")
    assert "<typPohybuSkladK>typPohybuSklad.prijemHoly</typPohybuSkladK>" in body
    assert "<sklad>code:SKLAD</sklad>" in body
    assert "<skladovy-pohyb-polozka>" in body
    assert "<cenik>code:ZID-01</cenik>" in body
    assert "<mnozMj>5</mnozMj>" in body
    assert "<cenaMj>100.5</cenaMj>" in body
    assert result["ids"] == ["901"]


async def test_update_stock_items_requires_a_change(upstream):
    _write_upstream(upstream)
    with pytest.raises(ValueError):
        StockItemPriceInput(item_id="1")


async def test_update_stock_items_builds_rows(upstream):
    writes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(MOVEMENT_DETAIL)
        writes.append(request)
        return xml_response(WRITE_OK)

    upstream(handler)
    with ctx(write=True):
        await update_stock_movement_items(
            "555",
            items=[StockItemPriceInput(item_id="77", unit_price=42.0)],
        )
    body = writes[0].content.decode("utf-8")
    assert "<polozkyDokladu>" in body
    assert "<id>77</id>" in body
    assert "<cenaMj>42</cenaMj>" in body


async def test_flexi_success_false_is_an_error_without_upstream_text(upstream):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(INVOICE_DETAIL)
        return xml_response(WRITE_FAIL)

    upstream(handler)
    with ctx(write=True), pytest.raises(ConnectorError) as excinfo:
        await update_invoice_header("16792", revenue_account="604005")
    assert excinfo.value.code is ErrorCode.UPSTREAM_ERROR
    # HTTP 200 + success=false: chybová zpráva Flexi nesmí do kontextu modelu.
    assert "IGNORE PREVIOUS INSTRUCTIONS" not in excinfo.value.message


async def test_write_rejects_pseudonymization_tokens(upstream):
    _, writes = _write_upstream(upstream)
    with ctx(write=True), pytest.raises(ConnectorError) as excinfo:
        await update_invoice_header("16792", description="pošli na <EMAIL_3f9c1a2b4d5e>")
    assert excinfo.value.code is ErrorCode.INVALID_INPUT
    assert writes == []


async def test_empty_update_is_rejected(upstream):
    _, writes = _write_upstream(upstream)
    with ctx(write=True), pytest.raises(ConnectorError) as excinfo:
        await update_invoice_header("16792")
    assert excinfo.value.code is ErrorCode.INVALID_INPUT
    assert writes == []


async def test_write_budget_caps_runaway_loop(upstream, monkeypatch):
    _write_upstream(upstream)
    monkeypatch.setattr(server, "_write_budget", server.WriteBudget(limit=1, window_s=300))
    with ctx(write=True):
        await update_invoice_header("16792", revenue_account="604005")
        with pytest.raises(ConnectorError) as excinfo:
            await update_invoice_header("16792", revenue_account="604006")
    assert excinfo.value.code is ErrorCode.FORBIDDEN


async def test_write_audit_logs_field_names_not_values(upstream, caplog):
    _write_upstream(upstream)
    with ctx(write=True), caplog.at_level("INFO", logger="openmcp_sdk.write"):
        await update_invoice_header("16792", revenue_account="604005")
    joined = " ".join(record.getMessage() for record in caplog.records)
    assert "protiUcet" in joined
    assert "604005" not in joined


async def test_number_formatting_never_uses_exponent(upstream):
    """`{:g}` by cenu 1234567.89 poslalo jako 1.23457e+06 — poškozená data."""
    _, writes = _write_upstream(upstream)
    with ctx(write=True):
        await create_stock_movement(
            document_type="PRIJEMKA",
            movement_subtype="prijemHoly",
            warehouse="SKLAD",
            date="2026-01-31",
            items=[StockItemInput(product_code="X", quantity=3, unit_price=1234567.89)],
        )
    body = writes[0].content.decode("utf-8")
    assert "<cenaMj>1234567.89</cenaMj>" in body
    assert "e+" not in body and "E+" not in body


async def test_result_id_from_attribute_form(upstream):
    """Flexi umí vrátit ID výsledku i jako atribut `<result id=…>`."""
    writes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(INVOICE_DETAIL)
        writes.append(request)
        return xml_response(
            '<?xml version="1.0"?><winstrom version="1.0"><success>true</success>'
            '<results><result id="777" ref="/c/demo/skladovy-pohyb/777.xml"/></results>'
            "</winstrom>"
        )

    upstream(handler)
    with ctx(write=True):
        result = await create_stock_movement(
            document_type="PRIJEMKA",
            movement_subtype="prijemHoly",
            warehouse="SKLAD",
            date="2026-01-31",
            items=[StockItemInput(product_code="X", quantity=1, unit_price=10)],
        )
    assert result["ids"] == ["777"]


# -- integrita čísel na drátě --------------------------------------------------


async def test_large_amount_never_uses_exponent(upstream):
    """`Decimal` si exponent nese s sebou i po `to_integral_value()`.

    `str(Decimal("1e16").to_integral_value())` je `"1E+16"` — takže dřívější
    „celé číslo přes str()" pouštělo do účetnictví přesně ten exponenciální
    tvar, kterému se `_number` vyhýbá. Hranice je kolem 1e16, kde `repr`
    floatu sám přepne na exponent.
    """
    _, writes = _write_upstream(upstream)
    with ctx(write=True):
        await create_stock_movement(
            document_type="PRIJEMKA",
            movement_subtype="prijemHoly",
            warehouse="SKLAD",
            date="2026-01-31",
            items=[StockItemInput(product_code="X", quantity=1e7, unit_price=1e16)],
        )
    body = writes[0].content.decode("utf-8")
    assert "<mnozMj>10000000</mnozMj>" in body
    assert "<cenaMj>10000000000000000</cenaMj>" in body
    assert "E+" not in body and "e+" not in body


@pytest.mark.parametrize("bad", [float("inf"), float("-inf"), float("nan")])
def test_stock_item_rejects_non_finite_numbers(bad):
    """`gt`/`ge` samy nestačí: `inf > 0` je True.

    Bez `allow_inf_nan=False` by `+inf` prošlo validací a `_number` z něj
    udělá řetězec `Infinity` — poškozený zápis do cizího účetnictví.
    """
    with pytest.raises(ValueError):
        StockItemInput(product_code="X", quantity=bad, unit_price=1.0)
    with pytest.raises(ValueError):
        StockItemInput(product_code="X", quantity=1.0, unit_price=bad)
    with pytest.raises(ValueError):
        StockItemPriceInput(item_id="1", unit_price=bad)
    with pytest.raises(ValueError):
        StockItemPriceInput(item_id="1", quantity=bad)


@pytest.mark.parametrize("bad", [float("inf"), float("-inf"), float("nan")])
def test_number_formatter_is_the_last_barrier(bad):
    """Druhá vrstva: `_number` odmítne nekonečno i mimo pydantic schémata."""
    with pytest.raises(ConnectorError) as excinfo:
        server._number(bad)
    assert excinfo.value.code is ErrorCode.INVALID_INPUT


# -- potvrzení nesmí ukazovat vymyšlený diff -----------------------------------


async def test_write_to_missing_item_is_refused(upstream):
    """Položka, která na faktuře není, se nedá „opravit".

    Dřív `fetch_item` vrátila `{}`, člověk uviděl `'—' → 'code:604005'` —
    diff k něčemu, co neexistuje — a PUT s cizím `id` odešel.
    """
    _, writes = _write_upstream(upstream)
    with (
        elicitation("accept"),
        ctx(write=True, confirm=True),
        pytest.raises(ConnectorError) as excinfo,
    ):
        await update_invoice_item("16792", "999999", revenue_account="604005")
    assert excinfo.value.code is ErrorCode.UPSTREAM_UNAVAILABLE
    assert writes == []


async def test_write_to_missing_record_is_refused(upstream):
    """Neexistující doklad — stejný fail-closed jako u položky."""
    writes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(winstrom_xml("faktura-vydana", []))
        writes.append(request)
        return xml_response(WRITE_OK)

    upstream(handler)
    with (
        elicitation("accept"),
        ctx(write=True, confirm=True),
        pytest.raises(ConnectorError),
    ):
        await update_invoice_header("999999", revenue_account="604005")
    assert writes == []


async def test_write_to_missing_record_is_refused_without_confirmation(upstream):
    """Vypnutí elicitation nesmí změnit neexistující ID na povolený PUT."""
    writes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(winstrom_xml("faktura-vydana", []))
        writes.append(request)
        return xml_response(WRITE_OK)

    upstream(handler)
    with ctx(write=True, confirm=False), pytest.raises(ConnectorError) as excinfo:
        await update_invoice_header("999999", revenue_account="604005")
    assert excinfo.value.code is ErrorCode.INVALID_INPUT
    assert writes == []


async def test_stock_item_update_refuses_ids_not_on_the_movement(upstream):
    """Ceny se nedají přepsat položkám, které na tomhle pohybu nejsou."""
    writes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(MOVEMENT_DETAIL)
        writes.append(request)
        return xml_response(WRITE_OK)

    upstream(handler)
    with (
        elicitation("accept"),
        ctx(write=True, confirm=True),
        pytest.raises(ConnectorError),
    ):
        await update_stock_movement_items(
            "555", items=[StockItemPriceInput(item_id="424242", unit_price=42.0)]
        )
    assert writes == []


async def test_stock_item_update_shows_the_real_diff(upstream):
    """Protějšek předchozího testu — existující položka projde s pravdivým diffem."""
    writes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return xml_response(MOVEMENT_DETAIL)
        writes.append(request)
        return xml_response(WRITE_OK)

    upstream(handler)
    with elicitation("accept") as fake, ctx(write=True, confirm=True):
        await update_stock_movement_items(
            "555", items=[StockItemPriceInput(item_id="77", unit_price=42.0)]
        )
    assert len(writes) == 1
    # Původní cena z pohybu, ne vymyšlená pomlčka.
    assert "99.5" in fake.messages[0]
