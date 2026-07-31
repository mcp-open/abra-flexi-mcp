"""Testy generických čtecích nástrojů — allowlist evidencí a skládání filtru."""

from __future__ import annotations

import pytest
from openmcp_sdk.envelope import ConnectorError, ErrorCode
from tests.conftest import ctx, winstrom_xml, xml_response

from connector.registry import EVIDENCES
from connector.schemas import FilterCondition
from connector.server import (
    get_evidence_properties,
    get_record,
    list_companies,
    list_evidences,
    list_records,
    sum_records,
)

# -- katalog -------------------------------------------------------------------


def test_catalog_lists_allowlisted_evidences():
    result = list_evidences()
    names = {row["evidence"] for row in result.items}
    assert names == set(EVIDENCES)
    assert result.total == len(EVIDENCES)


def test_catalog_filters_by_area():
    result = list_evidences(area="penize")
    names = {row["evidence"] for row in result.items}
    assert {"banka", "pokladni-pohyb", "prikaz-k-uhrade", "vzajemny-zapocet"} <= names
    assert all(row["area"] == "penize" for row in result.items)


def test_catalog_covers_accounting_reports_and_vat():
    reports = {r["evidence"] for r in list_evidences(area="reporty").items}
    assert {"hlavni-kniha", "obratova-predvaha", "vysledovka-po-uctech", "saldo"} <= reports
    vat = {r["evidence"] for r in list_evidences(area="dph").items}
    assert {"podklady-dph", "kontrolni-hlaseni-dph", "cleneni-dph"} <= vat


def test_catalog_rejects_unknown_area():
    with pytest.raises(ConnectorError) as excinfo:
        list_evidences(area="vesmir")
    assert excinfo.value.code is ErrorCode.INVALID_INPUT


def test_registry_names_look_like_flexi_evidences():
    for name in EVIDENCES:
        assert name == name.lower()
        assert " " not in name


# -- allowlist a skládání filtru -----------------------------------------------


def test_unknown_evidence_is_rejected_before_any_request(upstream):
    seen = upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with ctx(), pytest.raises(ConnectorError) as excinfo:
        list_records("uzivatel")
    assert excinfo.value.code is ErrorCode.INVALID_INPUT
    assert seen == []


def test_filter_conditions_compose_typed_literals(upstream):
    seen = upstream(lambda request: xml_response(winstrom_xml("faktura-vydana", [])))
    with ctx():
        list_records(
            "faktura-vydana",
            filters=[
                FilterCondition(field="datVyst", op="gte", value="2026-01-01"),
                FilterCondition(field="storno", op="is_false"),
                FilterCondition(field="firma", op="eq", value="code:ACME"),
                FilterCondition(field="sumCelkem", op="gt", value=1000),
            ],
        )
    path = str(seen[0].url)
    # Datum a číslo bez uvozovek, reference jako řetězcový literál.
    assert "datVyst%20%3E%3D%202026-01-01" in path
    assert "storno%20is%20false" in path
    assert "firma%20%3D%20%27code%3AACME%27" in path
    assert "sumCelkem%20%3E%201000" in path
    assert "%20and%20" in path


def test_filter_value_cannot_escape_the_literal(upstream):
    seen = upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with ctx(), pytest.raises(ConnectorError) as excinfo:
        list_records(
            "adresar",
            filters=[FilterCondition(field="nazev", op="eq", value="x') or (1=1")],
        )
    assert excinfo.value.code is ErrorCode.INVALID_INPUT
    assert seen == []


def test_filter_field_name_is_validated(upstream):
    upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with ctx(), pytest.raises(ConnectorError):
        list_records(
            "adresar",
            filters=[FilterCondition(field="nazev='x' or id", op="eq", value="1")],
        )


def test_unary_operator_refuses_value(upstream):
    upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with ctx(), pytest.raises(ConnectorError):
        list_records(
            "adresar", filters=[FilterCondition(field="storno", op="is_true", value="x")]
        )


def test_binary_operator_requires_value(upstream):
    upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with ctx(), pytest.raises(ConnectorError):
        list_records("adresar", filters=[FilterCondition(field="nazev", op="eq")])


def test_custom_detail_fields_are_validated(upstream):
    seen = upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with ctx():
        list_records("adresar", fields=["kod", "nazev", "ic"])
    assert seen[0].url.params["detail"] == "custom:kod,nazev,ic"
    with ctx(), pytest.raises(ConnectorError):
        list_records("adresar", fields=["kod,nazev"])


def test_generic_rows_are_pseudonymized(upstream):
    upstream(
        lambda request: xml_response(
            winstrom_xml(
                "adresar",
                [{"kod": "ACME", "nazev": "ACME s.r.o.", "email": "info@acme.cz"}],
            )
        )
    )
    with ctx():
        result = list_records("adresar")
    assert result.items[0]["email"].startswith("<EMAIL_")
    assert result.items[0]["nazev"] == "ACME s.r.o."


# -- detail, sumace, properties ------------------------------------------------


def test_generic_get_record_by_id(upstream):
    seen = upstream(
        lambda request: xml_response(winstrom_xml("banka", [{"id": "7", "kod": "B7"}]))
    )
    with ctx():
        result = get_record("banka", "7")
    assert "/c/demo/banka/7.xml" in str(seen[0].url)
    assert result.record["kod"] == "B7"


def test_sum_records_uses_sum_endpoint(upstream):
    seen = upstream(
        lambda request: xml_response(
            winstrom_xml(raw="<sumCelkem>12345.6</sumCelkem>")
        )
    )
    with ctx():
        result = sum_records(
            "faktura-vydana",
            filters=[FilterCondition(field="datVyst", op="gte", value="2026-01-01")],
        )
    path = str(seen[0].url)
    assert path.endswith("/$sum.xml")
    assert "datVyst" in path
    assert result.record["sumCelkem"] == "12345.6"


def test_sum_records_normalizes_scientific_notation(upstream):
    """`2.18E7` je pro model past na řády — souhrny se převádí na běžný zápis."""
    upstream(
        lambda request: xml_response(
            winstrom_xml(raw="<sumCelkem>2.183981677E7</sumCelkem><sumMale>-1.5E-2</sumMale>")
        )
    )
    with ctx():
        result = sum_records("faktura-vydana")
    assert result.record["sumCelkem"] == "21839816.77"
    assert result.record["sumMale"] == "-0.015"


def test_get_record_relations_param(upstream):
    seen = upstream(
        lambda request: xml_response(
            winstrom_xml("faktura-vydana", [{"id": "5", "kod": "FV5"}])
        )
    )
    with ctx():
        get_record("faktura-vydana", "5", relations=["vazby", "prilohy"])
    assert seen[0].url.params["relations"] == "vazby,prilohy"


def test_list_companies(upstream):
    seen = upstream(
        lambda request: xml_response(
            '<?xml version="1.0"?><companies>'
            "<company><dbNazev>demo</dbNazev><nazev>Demo</nazev></company>"
            "<company><dbNazev>ostra</dbNazev><nazev>Ostrá</nazev></company>"
            "</companies>"
        )
    )
    with ctx():
        result = list_companies()
    assert str(seen[0].url).startswith("https://demo.flexibee.eu:5434/c.xml")
    assert [row["dbNazev"] for row in result.items] == ["demo", "ostra"]
    assert result.total == 2


def test_properties_returns_self_documentation(upstream):
    seen = upstream(
        lambda request: xml_response(
            '<?xml version="1.0"?><properties><evidenceName>adresar</evidenceName>'
            "<property><propertyName>email</propertyName><type>string</type></property>"
            "</properties>"
        )
    )
    with ctx():
        result = get_evidence_properties("adresar")
    assert "/c/demo/adresar/properties.xml" in str(seen[0].url)
    assert result.record["properties"]["evidenceName"] == "adresar"


# -- opravy z bugscanu ---------------------------------------------------------


def test_scan_total_is_honest_when_stopped_early(upstream):
    """Předčasné zastavení scanu nesmí vydávat len(matched) za total."""
    rows = [
        {"id": str(i), "typPohybuK": "typPohybu.prijem", "sklad": "code:S",
         "datVyst": "2026-01-02"}
        for i in range(100)  # plná stránka — scan neví, kolik je dál
    ]
    upstream(lambda request: xml_response(winstrom_xml("skladovy-pohyb", rows)))
    from connector.server import list_stock_movements
    with ctx():
        result = list_stock_movements(
            date_from="2026-01-01", date_to="2026-01-31", direction="prijem", limit=5
        )
    assert len(result.items) == 5
    assert result.total is None  # nedočteno → total nesmí lhát
    assert result.truncated is True


def test_scan_last_page_has_no_leftover_warning(upstream):
    """truncated=False nesmí doprovázet varování „pokračuje dále"."""
    rows = [
        {"id": str(i), "typPohybuK": "typPohybu.prijem", "sklad": "code:S"}
        for i in range(25)
    ]
    upstream(lambda request: xml_response(winstrom_xml("skladovy-pohyb", rows)))
    from connector.server import list_stock_movements
    with ctx():
        result = list_stock_movements(
            date_from="2026-01-01", date_to="2026-01-31", direction="prijem",
            limit=10, offset=20,
        )
    assert len(result.items) == 5
    assert result.total == 25
    assert result.truncated is False
    assert result.warnings == []


def test_like_operator_rejects_wildcard_and_quotes_numbers(upstream):
    """Flexi `like` zástupné znaky nemá — `%` by tiše nenašel nic (ověřeno
    živě), proto se odmítá. Číselně vypadající hodnota se u textových
    operátorů quotuje."""
    seen = upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with ctx(), pytest.raises(ConnectorError):
        list_records(
            "adresar",
            filters=[FilterCondition(field="nazev", op="like", value="kav%")],
        )
    assert seen == []
    with ctx():
        list_records(
            "adresar",
            filters=[FilterCondition(field="kod", op="begins", value="2026")],
        )
    assert "kod%20begins%20%272026%27" in str(seen[0].url)


def test_products_name_filter_accepts_diacritics(upstream):
    rows = [{"id": "1", "kod": "Z", "nazev": "Židle kancelářská"}]
    upstream(lambda request: xml_response(winstrom_xml("cenik", rows)))
    from connector.server import list_products
    with ctx():
        result = list_products(name_contains="Židle")
    assert [row["id"] for row in result.items] == ["1"]


def test_unicode_digits_are_not_record_ids(upstream):
    seen = upstream(lambda request: xml_response(winstrom_xml("cenik", [])))
    with ctx(), pytest.raises(ConnectorError):
        # Unicode číslice nejsou ASCII ID ani platný kód.
        get_record("cenik", "١٢٣")
    assert seen == []


def test_contact_nazev_is_tokenized_with_redact_names(upstream):
    rows = [{"id": "1", "nazev": "Jan Novák", "prijmeni": "Novák"}]
    upstream(lambda request: xml_response(winstrom_xml("kontakt", rows)))
    with ctx(config={"redact_names": True}):
        result = list_records("kontakt")
    assert result.items[0]["nazev"].startswith("<NAME_")
    # Bez redact_names zůstává čitelné (výchozí chování).
    with ctx():
        result = list_records("kontakt")
    assert result.items[0]["nazev"] == "Jan Novák"


def test_adresar_nazev_stays_readable_even_with_redact_names(upstream):
    rows = [{"id": "1", "nazev": "ACME s.r.o."}]
    upstream(lambda request: xml_response(winstrom_xml("adresar", rows)))
    with ctx(config={"redact_names": True}):
        result = list_records("adresar")
    assert result.items[0]["nazev"] == "ACME s.r.o."


def test_multiple_id_elements_are_split_into_id_and_external(upstream):
    """Záznam s externími ID exportuje víc <id> elementů — model potřebuje
    jednoznačné interní ID."""
    upstream(
        lambda request: xml_response(
            '<?xml version="1.0"?><winstrom version="1.0"><objednavka-prijata>'
            "<id>ext:SHOP:order-99</id><id>2736</id><kod>OBP0037/2026</kod>"
            "</objednavka-prijata></winstrom>"
        )
    )
    with ctx():
        row = list_records("objednavka-prijata").items[0]
    assert row["id"] == "2736"
    assert row["externalIds"] == ["ext:SHOP:order-99"]


def test_get_record_accepts_external_id(upstream):
    seen = upstream(
        lambda request: xml_response(
            winstrom_xml("objednavka-prijata", [{"id": "2736", "kod": "OBP0037/2026"}])
        )
    )
    with ctx():
        get_record("objednavka-prijata", "ext:SHOP:order-99")
    # Externí ID adresuje záznam přímo v cestě (percent-encodované dvojtečky).
    assert "/c/demo/objednavka-prijata/ext%3ASHOP%3Aorder-99.xml" in str(seen[0].url)


@pytest.mark.parametrize("bad", [float("inf"), float("-inf"), float("nan")])
def test_filter_value_must_be_a_finite_number(bad, upstream):
    """`Decimal(float("inf"))` dá literál `Infinity` v URL filtru.

    Pydantic `float` nekonečno ve výchozím nastavení propouští, a protože
    `FilterCondition.value` nemá `gt`/`ge`, projde i `-inf` a `NaN`. Flexi
    na takový filtr vrátí prázdný výsledek, ne chybu — tiše špatná odpověď.
    """
    seen = upstream(lambda request: xml_response(winstrom_xml("adresar", [])))
    with pytest.raises(ValueError):
        FilterCondition(field="sumCelkem", op="gt", value=bad)
    assert seen == []
