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


# -- rozsah = vlastník credentials, ne přihlášený uživatel ---------------------
#
# Hosted aktivace může patřit týmu. Se `sub` v klíči by každý člen dostal na
# tatáž data jiný token — tokeny by přestaly být sdílitelné a člověk by
# nepoznal, že `<EMAIL_a…>` a `<EMAIL_b…>` je stejný e-mail.

#: Platné UUID; `Principal` na `credential_owner_id` trvá v kanonickém tvaru.
TEAM_ID = "6f1c9d2e-3a4b-4c5d-8e9f-0a1b2c3d4e5f"
USER_ID = "11111111-2222-4333-8444-555555555555"
OTHER_TEAM_ID = "9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b"


def test_team_members_share_one_token_scope():
    """Dva členové téhož týmu → identický rozsah, tedy identické tokeny."""
    from tests.conftest import hosted_ctx

    from connector.pii_fields import scope_by_sub_and_instance

    with hosted_ctx(sub="clen-a", owner_kind="team", owner_id=TEAM_ID) as first:
        scope_a = scope_by_sub_and_instance(first)
    with hosted_ctx(sub="clen-b", owner_kind="team", owner_id=TEAM_ID) as second:
        scope_b = scope_by_sub_and_instance(second)
    assert scope_a == scope_b
    value = {"email": "ucetni@firma.cz"}
    assert Pseudonymizer(derive_key(*scope_a), POLICY).sanitize(dict(value)) == (
        Pseudonymizer(derive_key(*scope_b), POLICY).sanitize(dict(value))
    )


def test_different_owners_stay_isolated():
    """Jiný tým = jiný rozsah. Sdílení uvnitř týmu nesmí znamenat sdílení mezi nimi."""
    from tests.conftest import hosted_ctx

    from connector.pii_fields import scope_by_sub_and_instance

    with hosted_ctx(sub="clen-a", owner_kind="team", owner_id=TEAM_ID) as first:
        scope_a = scope_by_sub_and_instance(first)
    with hosted_ctx(sub="clen-a", owner_kind="team", owner_id=OTHER_TEAM_ID) as second:
        scope_b = scope_by_sub_and_instance(second)
    assert scope_a != scope_b
    value = {"email": "ucetni@firma.cz"}
    assert Pseudonymizer(derive_key(*scope_a), POLICY).sanitize(dict(value)) != (
        Pseudonymizer(derive_key(*scope_b), POLICY).sanitize(dict(value))
    )


def test_user_owned_credentials_keep_the_existing_tokens():
    """Zpětná kompatibilita: pro `owner_kind="user"` je `owner_id == sub`.

    SDK to vynucuje v `Principal.__post_init__`, takže se klíč nemění a
    tokeny vydané před touhle změnou zůstávají bitově platné. Proto se do
    klíče dává jen ID, ne dvojice kind+ID.
    """
    from openmcp_sdk.testing import with_context
    from tests.conftest import CONFIG, hosted_ctx

    from connector.pii_fields import scope_by_sub_and_instance

    with hosted_ctx(sub=USER_ID, owner_kind="user", owner_id=USER_ID) as hosted:
        hosted_scope = scope_by_sub_and_instance(hosted)
    # Rozsah, jaký dávala implementace před touhle změnou (klíč ze `sub`).
    with with_context(config=CONFIG, sub=USER_ID) as legacy:
        legacy_scope = scope_by_sub_and_instance(legacy)
    assert hosted_scope == legacy_scope

    value = {"email": "ucetni@firma.cz"}
    assert Pseudonymizer(derive_key(*hosted_scope), POLICY).sanitize(dict(value)) == (
        Pseudonymizer(derive_key(*legacy_scope), POLICY).sanitize(dict(value))
    )


def test_local_run_falls_back_to_sub():
    """Bez hosted identity je vlastník `None` — rozsah zůstává `sub`."""
    from openmcp_sdk.testing import with_context

    from connector.pii_fields import scope_by_sub_and_instance

    with with_context(
        config={"api_url": "https://demo.flexibee.eu:5434", "company": "demo"},
        sub="lokalni-uzivatel",
    ) as ctx:
        assert ctx.principal.credential_owner_id is None
        assert scope_by_sub_and_instance(ctx)[0] == "lokalni-uzivatel"
