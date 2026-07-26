# abraflexi-mcp

MCP konektor pro **ABRA Flexi** (dříve FlexiBee) — čtecí a zapisovací přístup
k účetnictví: vydané faktury a jejich zaúčtování, účetní deník, přijaté
objednávky, skladové pohyby, stav skladu a ceník.

Postavený nad [openmcp-sdk](../openmcp-sdk) podle sjednocené šablony
[template-mcp](../template-mcp). Deklarativní zdroj pravdy je
[`connector.yaml`](connector.yaml); doménová znalost Flexi API je
v [`docs/MCP_PODKLAD.md`](docs/MCP_PODKLAD.md).

## Nástroje

**Čtení** (18): specializované `get_company_info`, `list_issued_invoices`,
`get_issued_invoice`, `list_invoice_types`, `get_invoice_journal`,
`list_received_orders`, `get_received_order`, `list_stock_movements`,
`get_stock_movement`, `get_stock_status`, `list_products`, `get_product` +
**generická vrstva** nad allowlistem ~180 evidencí
(`src/connector/registry.py`, katalog z dokumentace API §16.3 doplněný podle
živého `/evidence-list` reálné instance — včetně účetních reportů jako hlavní
kniha, obratová předvaha, výsledovka, saldo, po splatnosti a podkladů DPH):
`list_companies` (databáze na serveru), `list_evidences`, `list_records`
(strukturovaný filtr — pole + operátor z uzavřené množiny + hodnota,
spojované přes AND), `get_record` (volitelně `relations`: položky, přílohy,
vazby — např. kterou platbou je faktura uhrazená), `sum_records` (`$sum`,
exponenciální čísla normalizovaná na běžný zápis) a
`get_evidence_properties` (samodokumentace polí instance). Položky dokladů
se čtou přes `relations=polozky` a obal kolekce (`polozkyFaktury` →
`faktura-vydana-polozka`) se kolabuje na přímý seznam.

**Zápis** (4, jen při vypnutém `read_only`): `update_invoice_header`,
`update_invoice_item`, `create_stock_movement`,
`update_stock_movement_items`. Každý zápis prochází vrstvami
`openmcp_sdk.write`: politika workspace → strop zápisů v okně → diff →
**potvrzení člověkem** → audit. Payloady se skládají výhradně z allowlistů.

## Osobní údaje

E-maily, telefony, adresy a bankovní spojení kontaktů se pseudonymizují
stabilními tokeny (`<EMAIL_3f9c1a2b4d5e>`); IČ, DIČ a názvy firem zůstávají
čitelné. Detaily a záznam podle čl. 30 v
[`docs/COMPLIANCE.md`](docs/COMPLIANCE.md).

## Vědomá omezení v1

- **Jen cloud `*.flexibee.eu:5434`.** URL instance je credential zákazníka a
  konektor ji váže na rodinu hostů Flexi cloudu — bez toho by šla Basic
  autentizace exfiltrovat na libovolný host (NetworkPolicy neumí FQDN).
  Self-hosted instance (vlastní host, self-signed certifikát) vyžadují
  samostatné nasazení s vlastním manifestem; `verify=False` konektor záměrně
  neumí.
- **XML rozhraní.** Flexi API se volá přes `.xml` endpointy (`winstrom`
  obálka) — XML větev API je lépe dokumentovaná a JSON varianta se v praxi
  ukázala problematická. Úspěch zápisu se čte z `winstrom.success`, ne z HTTP
  stavu.
- **Filtry bez volné syntaxe.** Filtr Flexi patří do URL cesty, takže je to
  injection kanál — konektor vystavuje jen typované parametry s validací
  hodnot; „raw filter" vstup neexistuje. Kde jsou serverové filtry
  nespolehlivé (skladové pohyby, ceník), filtruje se u nás nad stránkovaným
  průchodem se stropem.
- Nevystavují se: mazání, zápisy do adresáře, storno, hromadné operace ani
  generický zápis do libovolné evidence (zdůvodnění v `server.py`).

## Lokální vývoj

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ../openmcp-sdk -e '.[test]'
OPENMCP_PII_SALT=test-pii-salt .venv/bin/python -m pytest tests -q
```

Spuštění v local-stdio proti demo instanci: zkopíruj `.env.example` na
`.env` (demo: `https://demo.flexibee.eu:5434`, firma `demo`,
winstrom/winstrom) a spusť `python -m connector` z kořene repozitáře.

Build image dělá `platform/deploy/Makefile` — build kontext je nadřazený
adresář a adresář repozitáře se v tar-u přejmenovává na slug `abraflexi`.
