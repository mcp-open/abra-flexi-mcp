# Changelog

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
