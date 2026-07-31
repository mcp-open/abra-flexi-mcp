"""Kontroly, které odhalí rozjezd mezi manifestem, kódem a build kontextem.

Tento soubor se kopíruje do konektorů **1:1** — nic v něm není specifické
pro šablonu.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = yaml.safe_load((ROOT / "connector.yaml").read_text(encoding="utf-8"))
SLUG = MANIFEST["slug"]


def test_version_matches_pyproject():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == MANIFEST["version"]


def test_dockerfile_references_only_sdk_and_slug():
    """Build kontext přejmenovává adresář repozitáře na slug.

    Zděděný odkaz na `template/` tedy v konektoru `zasilkovna` shodí build —
    a projeví se to až v CI, ne při psaní kódu.

    Kontrolují se **všechna** místa, ne vyjmenovaná dvě: kromě `COPY`
    a `WORKDIR` je slug i v `RUN pip install ./sdk ./<slug>`. Právě na tu
    třetí se při scaffoldu zapomíná, protože checklist i komentář v Dockerfile
    mluvily o „dvou řádcích".
    """
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    referenced: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for token in re.findall(r"\./([A-Za-z0-9._-]+)", stripped):
            referenced.add(token)
        for token in re.findall(r"WORKDIR\s+/app/([A-Za-z0-9._-]+)", stripped):
            referenced.add(token)

    unexpected = referenced - {"sdk", SLUG}
    assert not unexpected, (
        f"Dockerfile odkazuje na {sorted(unexpected)}, ale slug je {SLUG!r} — "
        "build kontext přejmenovává adresář na slug, takže build selže"
    )
    assert f"WORKDIR /app/{SLUG}" in text
    assert f"COPY {SLUG} ./{SLUG}" in text


def test_dockerfile_runs_as_expected_uid():
    """UID musí sedět s `runAsUser: 10001` v podSecurityContext."""
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER 10001" in text
    assert "--uid 10001" in text


def test_dockerignore_exists_in_repo_root():
    """V podadresáři by se neuplatnil — build kontext je nadřazená složka."""
    assert (ROOT / ".dockerignore").is_file()


def test_sdk_ref_is_a_commit_sha():
    """CI checkoutuje SDK na tento ref; bump je jednořádkový diff v PR."""
    ref = (ROOT / ".sdk-ref").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"[0-9a-f]{40}", ref), f"nevypadá jako commit SHA: {ref!r}"


def test_scaffold_checklist_is_removed_before_release():
    """SCAFFOLD.md smí existovat jen v samotné šabloně.

    Když zůstane ve scaffoldnutém konektoru, znamená to nedokončený scaffold —
    a s ním typicky i nezměněné TODO(scaffold) placeholdery.
    """
    if SLUG == "template":
        pytest.skip("toto JE šablona")
    assert not (ROOT / "SCAFFOLD.md").exists(), (
        "SCAFFOLD.md zůstal v repozitáři — scaffold není dokončen"
    )


#: Rozdělené, aby tento soubor nenašel sám sebe — hledaný řetězec by jinak
#: byl v něm a test by hlásil falešný nález.
_PLACEHOLDER = "TODO" + "(scaffold)"

#: Recepty popisují varianty, které si konektor nemusí vybrat, takže v nich
#: placeholder zůstává legitimně.
_PLACEHOLDER_ALLOWED = {"tests/test_packaging.py", "docs/recipes"}


def test_no_scaffold_placeholders_left():
    if SLUG == "template":
        pytest.skip("toto JE šablona")
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(
            part in {".git", ".venv", "node_modules", "__pycache__"}
            for part in path.parts
        ):
            continue
        # Whitelist přípon by minul `Dockerfile` (bez přípony) i
        # `.env.example` — tedy přesně soubory, kde placeholder nejvíc bolí.
        if path.suffix not in {".py", ".yaml", ".yml", ".toml", ".md"} and path.name not in {
            "Dockerfile",
            ".env.example",
            ".sdk-ref",
        }:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(rel.startswith(allowed) for allowed in _PLACEHOLDER_ALLOWED):
            continue
        if _PLACEHOLDER in path.read_text(encoding="utf-8", errors="ignore"):
            offenders.append(rel)
    assert not offenders, f"nevyplněné placeholdery ze šablony: {offenders}"


def test_egress_host_is_not_placeholder():
    """Placeholder, který tiše projde, je horší než žádný."""
    if SLUG == "template":
        pytest.skip("toto JE šablona")
    assert MANIFEST["egress"]["host"] != "api.example.com", (
        "egress.host je stále placeholder ze šablony"
    )


def test_pii_connector_has_compliance_doc():
    """`runtime.pii_salt` ⇒ vyplněná COMPLIANCE.md.

    GDPR záznam podle čl. 30 nemá kdo připomenout. Manifest ale ví, že
    konektor zpracovává osobní údaje (žádá si salt), tak si o dokument řekne sám.
    """
    if not MANIFEST.get("runtime", {}).get("pii_salt"):
        pytest.skip("konektor nezpracovává osobní údaje")
    doc = ROOT / "docs" / "COMPLIANCE.md"
    assert doc.is_file(), "chybí docs/COMPLIANCE.md"
    text = doc.read_text(encoding="utf-8")
    assert "čl. 30" in text, "chybí záznam o činnostech zpracování (čl. 30)"
    if SLUG != "template":
        assert "TODO" not in text, "COMPLIANCE.md není vyplněná"


def test_runtime_dependencies_match_the_dockerfile():
    """Dockerfile instaluje závislosti ručně — nesmí se rozejít s pyproject.

    Konektor se v image instaluje s `--no-deps`, takže seznam v `RUN pip
    install` je jediné místo, které runtime závislosti opravdu vybírá.
    Duplicita se rozchází tiše: po bumpu SDK na FastMCP 3 tu zůstalo
    `fastmcp>=2.11,<3`, které fastmcp po instalaci `./sdk` zase srazilo zpět
    na 2.x. Zachytil by to až `pip check` v CI, ne psaní kódu.
    """
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = {
        spec for spec in data["project"]["dependencies"] if not spec.startswith("openmcp-sdk")
    }
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    installed = set(re.findall(r'"([a-zA-Z0-9_.-]+(?:[<>=!]=?[^"]*)?)"', text))
    missing = declared - installed
    assert not missing, (
        f"Dockerfile neinstaluje {sorted(missing)} v tom tvaru, jak je má "
        "pyproject.toml — image poběží na jiných verzích než testy"
    )


def test_localized_fields_keep_every_hint():
    """API lokalizací hint bezpodmínečně přepíše, i prázdným.

    `catalog/localization.go` dělá `c.Fields[i].Hint = translated.Hint`, takže
    pole bez `hint` v `display.locales.<lang>.fields` zůstane v aktivačním UI
    úplně bez nápovědy — i když ho `credentials` v kořeni manifestu má.
    """
    display = MANIFEST.get("display") or {}
    if display.get("schema_version") != 1:
        pytest.skip("display schema_version 1 tuhle záruku nedává")
    documented = {
        field["key"]
        for field in MANIFEST.get("credentials", []) + MANIFEST.get("user_config", [])
        if field.get("hint")
    }
    for locale, content in (display.get("locales") or {}).items():
        localized = {field["key"] for field in content.get("fields", []) if field.get("hint")}
        missing = sorted(documented - localized)
        assert not missing, (
            f"display.locales.{locale}.fields nemá hint u {missing} — "
            "lokalizace hint přepíše prázdným a v UI nápověda zmizí"
        )
