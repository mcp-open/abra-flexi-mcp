# ABRA Flexi API — podklad pro vlastní MCP server

Syntéza znalostí o fungování **ABRA Flexi** (dříve FlexiBee) REST API,
ověřených prací v tomto projektu. Čistě obecné chování API — bez vazby na
konkrétní firmu; vše firemně specifické (URL, credentials, účtová osnova)
patří do konfigurace, ne do tohoto dokumentu.

---

## 1. Základy API

### 1.1 Schéma URL

```
https://{server}:{port}/c/{company}/{evidence}.json
https://{server}:{port}/c/{company}/{evidence}/{id}.json
```

- Cloudové instance běží typicky na portu **5434**.
- `{company}` je identifikátor firmy (databáze) ve Flexi.
- `{evidence}` je název evidence (agendy), např. `faktura-vydana`,
  `skladovy-pohyb`, `cenik`.
- Přípona určuje formát (`.json`, `.xml`, `.csv`, `.pdf` u dokladů).

### 1.2 Autentizace

HTTP **Basic Auth**. Osvědčený vzor: dva oddělené uživatele —
jeden **read-only** pro dotazy a jeden **write** pro zápisy. Oprávnění se
řídí rolí uživatele ve Flexi.

Pozor na SSL: některé instance mají certifikát, který neprojde validací —
klient musí umět konfigurovatelné `verify_ssl`.

### 1.3 Obálka `winstrom`

Všechny requesty i odpovědi jsou zabalené v kořenovém objektu `winstrom`
(historický název produktu):

```json
// Odpověď GET
{ "winstrom": { "faktura-vydana": [ { "id": "2416", ... } ] } }

// Tělo PUT/POST
{ "winstrom": { "faktura-vydana": [ { "id": "16792", "protiUcet": "code:604005" } ] } }

// Výsledek zápisu
{ "winstrom": { "success": "true", "results": [ { "errors": [ { "message": "..." } ] } ] } }
```

Úspěch zápisu se pozná z `winstrom.success == "true"` (pozor — **string**,
ne boolean). Chybové zprávy jsou v `winstrom.results[].errors[].message`.
HTTP 200/201 samo o sobě úspěch nezaručuje.

### 1.4 Datové konvence

- **Reference na číselníky** mají prefix `code:` — např.
  `"mena": "code:CZK"`, `"sklad": "code:SKLAD"`, `"protiUcet": "code:604001"`.
  Při čtení je nutné prefix odstraňovat; při zápisu naopak přidávat.
  Kódy mohou obsahovat mezery (např. kódy typů dokladů) — `code:` prefix
  s mezerami funguje.
- **Referenční pole mohou přijít jako dict** s klíči `@ref`, `@showAs`,
  `value` — parser musí bezpečně převádět na string (viz helpery `_as_str`,
  `_strip_code` v `auditflow/app/audit_invoices.py`).
- **Doplňkové atributy** k poli chodí jako samostatné klíče:
  `cenik@showAs`, `idDokl@evidencePath` apod.
- **Data** jsou ISO formát s časovou zónou: `"2025-01-01+01:00"` — pro
  porovnávání ořezat na `[:10]`.
- **Částky** jsou stringy s desetinnou tečkou: `"1355.0"`.
- **Booleany** jsou stringy `"true"`/`"false"`.

---

## 2. Čtení dat (GET)

### 2.1 Parametry dotazu

| Parametr | Význam |
|----------|--------|
| `detail=full` | plný detail včetně vnořených položek; bez něj jen souhrnná pole |
| `start`, `limit` | stránkování (offset + velikost dávky) |
| `add-row-count=true` | přidá `@rowCount` s celkovým počtem záznamů |
| `includes=/{evidence}/{pole}` | přibalí podřízené záznamy (např. `includes=/skladovy-pohyb/polozkyDokladu`) |

Osvědčené stránkování: smyčka po dávkách (`limit=100`), konec když dávka
je menší než limit.

### 2.2 Filtry

- **Filtr patří do URL cesty v závorce** (URL-encoded), ne do query stringu:
  ```
  GET /c/{company}/faktura-vydana/(datVyst>='2025-11-01' and datVyst<='2025-11-30').json?detail=full
  ```
  Datumové filtry tímto způsobem **fungují spolehlivě**.
- Stejný mechanismus funguje i s odkazem na doklad:
  `ucetni-denik/(idDokl=<ID>).json`.
- ⚠️ Ad-hoc query filtry (`?cond=...`) se v praxi ukázaly **nespolehlivé**
  (ověřeno na `skladovy-pohyb`) — robustní vzor je stáhnout evidenci
  stránkovaně celou a filtrovat na straně klienta (podle `kod`,
  `typPohybuK` apod.).

---

## 3. Zápis dat (POST/PUT)

- **POST** na `/{evidence}.json` vytváří záznam, **PUT** na
  `/{evidence}/{id}.json` aktualizuje; tělo vždy ve `winstrom` obálce.
- **Částečný update funguje**: pošle se jen `id` + měněná pole, ostatní
  zůstávají zachována.
- **Položky dokladu nelze měnit samostatným endpointem** — vždy PUT přes
  hlavní doklad s vnořeným polem položek a `id` konkrétní položky:
  ```json
  { "winstrom": { "faktura-vydana": [{
      "id": "16792",
      "polozkyFaktury": [{ "id": "128072", "zklDalUcet": "code:604005" }]
  }]}}
  ```
- Pozor na asymetrii názvů polí u skladových pohybů: při **čtení** jsou
  položky v poli `skladovePolozky`, při **vytváření** se posílají jako
  `polozkyDokladu`.

---

## 4. Klíčové evidence

| Evidence | Obsah |
|----------|-------|
| `faktura-vydana` | vydané faktury; položky v `polozkyFaktury` |
| `faktura-prijata` | přijaté faktury (analogická struktura) |
| `skladovy-pohyb` | příjemky (S+) a výdejky (S-) |
| `skladovy-pohyb-polozka` | položky pohybů samostatně (čtení) |
| `cenik` | produkty: `kod`, `nazev`, `skupZboz`, `nakupCena`, `eanKod`, `mj1` |
| `sklad` | číselník skladů |
| `stav-skladu-k-datu` | stav zásob k datu: `?sklad=code:...&datum=YYYY-MM-DD`, pole `stavMJ`, `cenik` (ref) |
| `ucetni-denik` | účetní zápisy; k dokladu přes `(idDokl=<ID>)`, filtrovat `idDokl@evidencePath`, sledovat `madatiUcet`/`dalUcet` |
| `adresar` | firmy/kontakty (odběratelé, dodavatelé) |
| `predpis-zauctovani` | předpisy zaúčtování (šablony účtů + daňového režimu) |
| `typ-dokladu` (dle evidence, např. `typ-faktury-vydane`) | typy dokladů; nesou vazbu na předpis přes `typUcOpPrijem` |

### 4.1 Faktura vydaná — důležitá pole

Podrobná struktura v `faktura_vydana_struktura.md`. Shrnutí:

- **Identifikace**: `id`, `kod` (např. `FV1-000002/2025`), `varSym`,
  `specSym`, `konSym`, `cisObj`
- **Data**: `datVyst`, `datSplat`, `datUhr`, `datUcto`, `duzpPuv`, `duzpUcto`
- **Částky**: `sumCelkem`, `sumZklCelkem`, `sumDphCelkem` + rozpad podle
  sazeb (`sumZklZakl`, `sumDphZakl`, `sumZklSniz`, …)
- **Odběratel**: `nazFirmy`, `ic`, `dic`, `stat`, `firma` (ref na adresář).
  Pozor: DIČ i stát mohou být jen na hlavičce, nebo jen ve vnořeném
  `firma` — číst s fallbackem (`stat` → `dorucStat` → `statOdber` →
  `firma.stat`; `dic` → `firma.dic`).
- **Účty**: `primUcet` (MD, pohledávkový), **`protiUcet` (DAL, výnosový) —
  „účet DAL" je právě `protiUcet`; pole jménem `ucetDal` neexistuje**,
  `dphZaklUcet`/`dphSnizUcet`/`dphSniz2Ucet`
- **Daňový režim**: `typDokl`, `typUcOp` (předpis zaúčtování), `clenDph`,
  `statDph`, sazby `szbDph*`
- **Stavy**: `stavUhrK` (`stavUhr.uhrazeno`), `storno`, `zuctovano`,
  `dobropisovano`, `ucetni`
- **Položky** `polozkyFaktury[]`: `id`, `nazev`, `zklDalUcet`, `clenDph`,
  `typUcOp`, `kopTypUcOp`

### 4.2 Skladové pohyby

- Směr: `typPohybuK` = `typPohybu.prijem` / `typPohybu.vydej`.
- Podtyp: `typPohybuSkladK` = `typPohybuSklad.prijemHoly` („holý" příjem),
  `prijemNaFak` (na fakturu), `prijemDoVyr` (do výroby).
- Vytvoření příjemky (POST): `typDokl`, `typPohybuSkladK`, `sklad`,
  `datVyst`, `polozkyDokladu[]` s `cenik: "code:KOD"`, `mnozMj`, `cenaMj`.
- Omezení: produkty typu **sady nesmí do skladových pohybů**; pro pohyb
  v daném roce musí existovat **skladové karty** produktu.

---

## 5. Zaúčtování a předpisy — jak to Flexi dělá interně

Obecné mechanismy Flexi ověřené v produkci (nezávislé na konkrétní účtové
osnově):

### 5.1 Řetězec odvození

**`typDokl` → (pole `typUcOpPrijem`) → předpis zaúčtování (`typUcOp`) →
hlavičkové účty (`protiUcet`, `primUcet`) a daňový režim.**

Předpis (`predpis-zauctovani`) nese mj.:
- `protiUcetPrijem` / `protiUcetVydej` — výnosový a pohledávkový účet
- `dphZaklUcet` / `dphSnizUcet` / `dphSniz2Ucet` — účty DPH podle sazby
- `kodPlneniK` — kód plnění řídící vykázání v přiznání DPH
  (`zbozi` = tuzemské plnění, `zboziOSS` = OSS režim, `prenDanPov` =
  přenesená daňová povinnost / dodání do EU)

Předpis nese **hlavička dokladu i každá položka**
(`polozkyFaktury[].typUcOp`); položka má navíc `kopTypUcOp` — zda předpis
přebírá z dokladu.

### 5.2 Kritická pravidla chování API (naučená bolestí)

1. **Účetní deník (`ucetni-denik`) se generuje dynamicky z `typUcOp`
   HLAVIČKY dokladu.** Oprava jen `protiUcet` (hlavičky i položek)
   nestačí — dokud je hlavičkový `typUcOp` starý, deník účtuje po staru,
   i když pole na dokladu vypadají správně.
2. **Uhrazená faktura má `typDokl` zamčený** (vázaný na úhradu — nejde
   změnit). U neuhrazené se režim mění změnou `typDokl` a Flexi přepočítá
   `protiUcet` i `typUcOp` hlavičky sám. U uhrazené je nutné nastavit
   hlavičková pole přímo — projde to i na zaúčtovaném dokladu a deník se
   ihned přepočítá (žádné „znovu zaúčtovat" není potřeba).
3. **`clenDph` hlavičky se při změně `typDokl` NEpřepočítá** — je nutné ho
   poslat vždy explicitně.
4. **Související pole položky posílat jedním PUT najednou**
   (`zklDalUcet` + `clenDph` + `typUcOp` + `kopTypUcOp=false`). Posílaná
   jednotlivě je Flexi přepočítá z předpisu a přepíše na jiné hodnoty.
5. **`kopTypUcOp=true`** znamená „převezmi předpis z dokladu" — pokud
   doklad nese jiný (starý) předpis, položka se tím vrátí na špatné
   hodnoty. Při explicitní opravě položky vždy `kopTypUcOp=false`.
6. **Pořadí oprav: typDokl → hlavička → položky.**
7. U dokladů v OSS režimu Flexi odvozuje `clenDph` položek z `typDokl` a
   **PUT na toto pole tiše ignoruje** — audit takových polí generuje falešné
   nálezy.
8. Stornované doklady (`storno=true`) a zaokrouhlovací položky (název
   začíná „zaokr", neutrální `clenDph`) z kontrol vynechávat.

---

## 6. Návrh MCP serveru

### 6.1 Architektura

- Python MCP server (`mcp` SDK / FastMCP), stdio transport, sdílený HTTP
  klient s timeouty (osvědčené `(10, 60)` connect/read).
- **Veškerá firemní konfigurace přes env proměnné**: `FLEXI_BASE_URL`,
  `FLEXI_COMPANY`, `FLEXI_READ_USERNAME/PASSWORD`,
  `FLEXI_WRITE_USERNAME/PASSWORD`, `FLEXI_VERIFY_SSL`. Žádné credentials
  ani firemní konstanty v kódu.
- **Oddělený read a write klient** — bez write hesla server běží normálně
  v read-only režimu, write tools vrací srozumitelnou chybu.
- Sdílené utility: `_as_str`, `_strip_code`, `_is_true`, stránkovací
  smyčka, skládání filtru do URL cesty (referenční implementace
  `auditflow/app/audit_invoices.py`).
- Každý write tool s parametrem `dry_run=true` jako default.

### 6.2 Navržené tools — čtení

| Tool | Parametry | Implementace |
|------|-----------|--------------|
| `list_invoices` | year, month, filtry | GET `faktura-vydana/(datVyst…).json`, stránkování |
| `get_invoice` | id nebo kod | GET detail `?detail=full`; hledání podle `kod` klientsky |
| `get_invoice_journal` | invoice_id | GET `ucetni-denik/(idDokl=ID).json` |
| `list_stock_movements` | year?, month?, směr? | GET `skladovy-pohyb.json`, klientský filtr `typPohybuK` |
| `get_stock_movement` | id nebo kod | GET detail se `skladovePolozky` |
| `get_stock_status` | datum, sklad, skupina? | GET `stav-skladu-k-datu` + join s `cenik` |
| `list_products` | skupina? | GET `cenik.json?detail=full`, filtr `skupZboz` klientsky |
| `query_evidence` | evidence, filtr, detail | generický GET pro libovolnou evidenci — únikový ventil |

### 6.3 Navržené tools — zápis (dry-run default)

| Tool | Účel |
|------|------|
| `update_invoice_header` | PUT hlavičky; respektuje pravidla 5.2 (zamčený typDokl, explicitní clenDph) |
| `update_invoice_item` | jeden PUT položky se všemi souvisejícími poli + `kopTypUcOp=false` |
| `create_stock_movement` | POST příjemky/výdejky s `polozkyDokladu` |
| `update_stock_movement_items` | PUT položek přes hlavní doklad (např. ceny `cenaMj`) |

### 6.4 Zásady implementace

1. Invarianty z kap. 5.2 **vynucovat uvnitř serveru** (agregovaný PUT
   položky, pořadí oprav), nenechávat na volajícím.
2. Vracet **strukturovaný JSON**, u seznamů podporovat limit a vracet
   celkový počet (`add-row-count`).
3. Před každým zápisem znovu načíst aktuální stav a ověřit, že změna je
   stále potřeba; všechny zápisy logovat.
4. Vyhodnocovat `winstrom.success` a `results[].errors[].message`, ne jen
   HTTP status.
5. Hesla nikdy nelogovat ani nevracet v odpovědích tools.

---

## 7. Referenční zdroje

- `faktura_vydana_struktura.md` — struktura faktury + předpisy zaúčtování
- `skladove_pohyby.md` — skladové pohyby, curl/Python příklady
- `auditflow/app/audit_invoices.py` — referenční implementace (fetch, filtr v URL, PUT vzory, dry-run)
- Oficiální dokumentace API: https://www.flexibee.eu/api/dokumentace/
