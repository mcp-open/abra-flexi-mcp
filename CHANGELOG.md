# Changelog

## 0.1.1 — 2026-07-31

Bump SDK na `0d36cf1` (0.4.3, **FastMCP 2 → 3**) a opravy nalezené při auditu
proti němu. Vnější plocha konektoru se nemění: stejných 22 nástrojů, stejná
jména, stejná vstupní schémata.

### Změna tokenů — přečti, pokud používáš týmovou aktivaci

- **Rozsah pseudonymizace je nově vlastník přihlašovacích údajů, ne přihlášený
  uživatel.** U týmové aktivace (`credential_owner_kind: team`) dostávali
  členové téhož týmu na tatáž data různé tokeny, takže se nedaly sdílet ani
  porovnat napříč konverzacemi. Nově je rozsah
  `(credential_owner_id, api_url, company)`.
  **Pro osobní aktivace se nemění nic** — SDK u nich vynucuje
  `credential_owner_id == sub`, takže tokeny zůstávají bitově stejné.

### Opraveno

- **Velké částky odcházely v exponenciálním tvaru.** `Decimal` si exponent
  nese i po `to_integral_value()`, takže cena `1e16` se do Flexi zapsala jako
  `1E+16`. Formátuje se vždy přes `format(…, "f")`.
- **`Infinity` v zápisu i ve filtru.** Pydantic `gt`/`ge` nekonečno propouští
  (`inf > 0` je `True`); položky pohybu i hodnoty filtru mají nově
  `allow_inf_nan=False` a `_number` odmítá nekonečno jako poslední bariéra.
- **Potvrzení zápisu ukazovalo vymyšlený diff.** Zápis na neexistující doklad
  nebo na položku, která k dokladu nepatří, načetl prázdné „původní hodnoty",
  člověku se zobrazilo `'—' → 'nová hodnota'` a PUT odešel. Nově se takový
  zápis odmítne dřív, než se na cokoli zeptá, a zůstane odmítnutý i při
  vědomě vypnutém potvrzení.
- **`get_invoice_journal` padal na neošetřenou `ValueError`** u ID delšího než
  4300 číslic (limit `int()` v Pythonu 3.11+). ID je omezené na 19 číslic.
- **`test_connection` klasifikuje selhání pravdivě.** Dřív byla skoro každá
  příčina `invalid_input` nebo `upstream_unavailable`, takže uživatel dostával
  stejnou radu na různé problémy — a od API PR #34 se `invalid_input` navíc
  skládá na `runtime_unavailable`, tedy „platforma je rozbitá". Nově:
  - chybějící/neplatné údaje aktivace → `credential_invalid`,
  - 401 (Flexi neuznala jméno/heslo) → `credential_invalid`,
  - 403 (přihlášení prošlo, chybí právo) → `provider_permission_denied`,
  - 404 (na firmu se nedá dosáhnout) → `instance_unknown`; rada nově míří
    i na neaktivovaný přístup přes REST API, protože podle dokumentace se
    „402 — není aktivní licence REST" u čtení projeví jako 404 a 404 pokrývá
    i zdroj skrytý z licenčních důvodů (§3.3),
  - 429 → `rate_limited` místo hlášky o výpadku,
  - odpověď, která není platné XML → `internal` (`runtime_unavailable`).
    Nikdy `credential_invalid`: rozbitá proxy by jinak nechala janitora
    označit platné přihlašovací údaje za neplatné.

  Zrušená je větev pro `invalid_input` bez HTTP statusu — byla nedosažitelná.
  Všechny chyby formátu a konfigurace vznikají při stavbě klienta, tedy
  uvnitř `_Session()`, a chytá je dřívější `except`.
- **Úspěšný test spojení nově vyžaduje skutečný záznam firmy.** HTTP 200 samo
  o sobě nestačilo: captive portál nebo proxy, která vrátí dobře formované
  XHTML, prošla jako funkční spojení — `company_info()` v takovém těle
  nenajde dokumentovanou obálku `<companies><company>` (§16.1), chybu si sama
  odchytí a vrátí prázdný seznam. Stejně se odmítne obálka s jinou databází
  než `dbNazev` z aktivace. Prázdná či cizí odpověď je nově `internal`
  (`runtime_unavailable`), nikdy `credential_invalid`.
- **`test_connection` se vejde do rozpočtu hosted credential-testu.** Běžel
  s výchozím klientem (timeout 30 s, 4 pokusy), tedy násobně déle než ~12 s,
  které control plane čeká. Má vlastní krátký timeout a jediný pokus; běžné
  čtecí nástroje si retry ponechávají.
- **Lokalizace mazala nápovědu u tří ze čtyř přihlašovacích polí.** API
  lokalizovaný `hint` přepisuje bezpodmínečně, takže pole bez překladu
  zůstalo v aktivačním UI úplně bez nápovědy. `display.locales.cs|sk.fields`
  mají hint u všech polí.
- **CI netestovala release větev.** Workflow triggeroval jen na `dev`, zatímco
  autoritativní je `main` — PR #3 se tak dostal do `main` bez testů i bez
  image. Trigger je nově `main`, jako u ostatních konektorů; `dev` je legacy
  větev bez release pravomoci.
- **Dockerfile duplikoval seznam závislostí** a po bumpu SDK by srazil FastMCP
  zpět na 2.x. Shodu s `pyproject.toml` nově hlídá test.
- **Testovací pytest 8.4.2 měl otevřený GHSA alert.** Pin je aktualizovaný na
  první opravenou verzi 9.0.3; nejde o runtime závislost výsledného image.

## 0.1.0 — 2026-07-22

První verze podle sjednocené šablony (openmcp-sdk 0.4):

- 12 specializovaných čtecích nástrojů: firma, vydané faktury (+ typy, účetní
  deník), přijaté objednávky, skladové pohyby, stav skladu, ceník.
- Generické čtení všech běžných evidencí (allowlist ~180 evidencí vč.
  účetních reportů — hlavní kniha, předvaha, výsledovka, saldo, po
  splatnosti — a podkladů DPH; ověřeno proti živému `/evidence-list`):
  `list_companies`, `list_evidences`, `list_records` se strukturovaným
  filtrem (AND řetěz, uzavřená množina operátorů, typované literály),
  `get_record` (volitelné `relations`: polozky/prilohy/vazby), `sum_records`
  s normalizací exponenciálních čísel a `get_evidence_properties`
  (samodokumentace instance).
- `display` v manifestu podle platformního schématu v1 (schema_version: 1,
  kompletní locales cs + sk).
- 4 zapisovací nástroje s potvrzením člověkem (diff), allowlisty polí,
  stropem zápisů a auditem: oprava zaúčtování hlavičky a položky faktury,
  založení skladového pohybu, úprava položek pohybu.
- XML transport (`winstrom` obálka) — úspěch zápisu se čte z
  `winstrom.success`, ne z HTTP stavu.
- Pseudonymizace osobních údajů kontaktů (e-maily, telefony, adresy, bankovní
  spojení) s rozsahem tokenů per (uživatel, instance, firma); IČ/DIČ/názvy
  firem čitelné.
- Validace per-zákazník URL na rodinu hostů `*.flexibee.eu:5434`.
- Typované filtry skládané v klientovi (žádný raw filter), klientské
  filtrování skladových pohybů a ceníku se stránkovaným průchodem.
