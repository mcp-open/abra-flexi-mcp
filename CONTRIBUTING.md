# Jak přispět

## Příprava prostředí

SDK se neinstaluje z PyPI — jméno tam patří nesouvisejícímu projektu. Bere se
z gitu podle pinu v `pyproject.toml`:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[test]'
export OPENMCP_PII_SALT="$(openssl rand -hex 32)"
```

Od 31. 7. 2026 je konektor na **SDK 0.4.3 a FastMCP 3**, tedy na stejné verzi
jako zbytek rodiny, a pin míří do `main` SDK.

## Před odesláním změny

```bash
ruff check src tests
mypy src
openmcp-sdk validate connector.yaml
python -m pytest tests -q
```

Všechny čtyři musí projít — přesně totéž běží v CI.

## Konvence

- **Výchozí a release větev je `main`** — stejně jako u ostatních hostovaných
  konektorů (`ares-mcp`, `raynet-mcp`, `dotykacka-mcp`, `upgates-com-mcp`).
  PR do `main` se testuje, ale nebuilduje; teprve push do `main` staví image
  a hlásí kandidátský digest platformě.
- **`dev` je legacy větev bez release pravomoci.** Neběží na ní CI, nestaví se
  z ní image a nehlásí se z ní digest. Zůstává jen kvůli historii; nové PR
  patří do `main`. (Do 31. 7. 2026 byla `dev` GitHub default branch zaseknutá
  na `b0570fd` a CI triggerovalo jen na ni — proto PR #3 do `main` neprošel
  ani testy, ani buildem.)
- Nový nástroj potřebuje: registraci přes `@tool(mcp, read_only=...)`, záznam
  v `display.tools` a test, který ho volá přímo.
- Envelope na každém nástroji — `provenance` říká, odkud data jsou, `warnings`
  o tom, zda nejsou oříznutá.
- Komentáře, docstringy i dokumentace jsou **česky**; `display.locales` musí
  pokrývat `cs` i `sk`.
- Zápisové nástroje jsou opt-in a standardně s potvrzením konkrétního
  rozdílu; firemní politika může potvrzení vynutit. Pokud ho provozovatel
  vědomě vypne, všechny ostatní fail-closed kontroly musí zůstat účinné.
- Filtry se skládají z ověřených hodnot: pole z allowlistu, operátor
  z uzavřené množiny, typovaný literál. Surový filtr od modelu do URL nepatří.
- Do repozitáře nepatří tajemství, `.env`, produkční logy ani cizí API
  specifikace.

## Bump SDK

SDK je připnuté na jeden commit, který musí souhlasit na dvou místech:
`pyproject.toml` a `.sdk-ref`. Shodu hlídá `tests/test_sdk_pin.py`, takže bump
znamená změnit obojí naráz.

## Změny, které potřebují poznámku v CHANGELOG.md

Manifest, autentizace, tvar odpovědi nástroje a cokoliv, co mění
pseudonymizační tokeny. **Tokeny jsou externě viditelný kontrakt** — když se
změní, uživatel uvidí jiné ID pro stejná data.

## Bezpečnostní hranice

Tyto věci nejsou kosmetika a review si na ně dává pozor:

- `readOnlyHint` — při `read_only=true` SDK fail-closed odregistruje vše bez
  ní; chybějící anotace znamená, že nástroj v produkci tiše zmizí
- potvrzení zápisu přes elicitation — jediná vrstva, která zastaví prompt
  injection z obsahu upstreamu
- tělo upstream odpovědi **nikdy** nesmí jít do chybové zprávy pro model
- `egress` v manifestu musí pokrývat vše, na co klient sahá

Zranitelnosti hlaste podle [SECURITY.md](SECURITY.md), nikdy veřejným issue.
