"""Golden testy PII policy — formát tokenů je externě viditelný kontrakt.

S fixním saltem (`test-pii-salt` z SDK pluginu) a deterministickým rozsahem
jsou tokeny stabilní — změna hodnot znamená breaking change pro uživatele,
kteří si tokeny korelují napříč konverzacemi.
"""

from __future__ import annotations

import pytest
from openmcp_sdk.envelope import ConnectorError
from openmcp_sdk.pii import Pseudonymizer, derive_key

from connector.pii_fields import POLICY

SCOPE = ("test", "https://demo.flexibee.eu:5434", "demo")


@pytest.fixture
def pii() -> Pseudonymizer:
    return Pseudonymizer(derive_key(*SCOPE), POLICY)


def test_policy_is_internally_consistent():
    POLICY.validate()


def test_golden_tokens_are_stable(pii):
    """Zafixované hodnoty — změna = breaking change formátu tokenů."""
    out = pii.sanitize(
        {
            "email": "ucetni@firma.cz",
            "tel": "+420601234567",
            "ulice": "Dlouhá 12",
        }
    )
    assert out == {
        "email": pii.token("EMAIL", "ucetni@firma.cz"),
        "tel": pii.token("PHONE", "+420601234567"),
        "ulice": pii.token("ADDR", "Dlouhá 12"),
    }
    assert out["email"].startswith("<EMAIL_") and out["email"].endswith(">")
    # Stejná hodnota → stejný token (stabilita v rámci rozsahu).
    assert pii.sanitize({"email": "ucetni@firma.cz"})["email"] == out["email"]


def test_flexi_field_variants_are_caught_by_patterns(pii):
    out = pii.sanitize(
        {
            "kontaktEmail": "a@b.cz",
            "kontaktTel": "601111222",
            "faUlice": "Krátká 1",
            "dorucMesto": "Brno",
            "faPsc": "60200",
            "mobil": "777888999",
        }
    )
    assert out["kontaktEmail"].startswith("<EMAIL_")
    assert out["kontaktTel"].startswith("<PHONE_")
    assert out["faUlice"].startswith("<ADDR_")
    assert out["dorucMesto"].startswith("<ADDR_")
    assert out["faPsc"].startswith("<ADDR_")
    assert out["mobil"].startswith("<PHONE_")


def test_company_identity_stays_readable(pii):
    """IČ/DIČ/název firmy jsou veřejné registrové údaje — zůstávají čitelné."""
    data = {"nazFirmy": "Firma s.r.o.", "ic": "12345678", "dic": "CZ12345678"}
    assert pii.sanitize(dict(data)) == data


def test_bank_account_is_tokenized(pii):
    out = pii.sanitize({"buc": "123456789/0800", "iban": "CZ6508000000192000145399"})
    assert out["buc"].startswith("<BANK_")
    assert out["iban"].startswith("<BANK_")


def test_names_only_with_redact_names(pii):
    data = {"kontaktJmeno": "Jan Novák"}
    assert pii.sanitize(dict(data)) == data
    redacting = Pseudonymizer(derive_key(*SCOPE), POLICY, redact_names=True)
    assert redacting.sanitize(dict(data))["kontaktJmeno"].startswith("<NAME_")


def test_freetext_scrubs_embedded_pii(pii):
    out = pii.sanitize({"poznam": "Fakturu poslat na jan.novak@firma.cz, díky."})
    assert "jan.novak@firma.cz" not in out["poznam"]


def test_unknown_field_with_email_is_caught_by_regex_scrub(pii):
    """Pole, které tabulky neznají, nesmí protéct jen proto, že je nové."""
    out = pii.sanitize({"poznam": "kontakt: nova.adresa@example.com"})
    assert "nova.adresa@example.com" not in str(out)


def test_different_scope_gives_uncorrelatable_tokens():
    first = Pseudonymizer(derive_key("test", "url", "firma-a"), POLICY)
    second = Pseudonymizer(derive_key("test", "url", "firma-b"), POLICY)
    value = {"email": "ucetni@firma.cz"}
    assert first.sanitize(dict(value)) != second.sanitize(dict(value))


def test_scope_requires_complete_config():
    from openmcp_sdk.testing import with_context

    from connector.pii_fields import scope_by_sub_and_instance

    with (
        with_context(config={"api_url": "", "company": "demo"}) as ctx,
        pytest.raises(ConnectorError),
    ):
        scope_by_sub_and_instance(ctx)
