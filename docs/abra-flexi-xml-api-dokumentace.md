# ABRA Flexi — Kompletní dokumentace XML (REST) API

> Souhrnná referenční příručka k REST API systému ABRA Flexi (dříve FlexiBee) se zaměřením na nativní XML formát. Sestaveno z oficiální referenční dokumentace (demo.flexibee.eu/devdoc, flexibee.eu/api, podpora.flexibee.eu) a doplněno o praktické poznámky. Stav k červenci 2026.

---

## Obsah

1. [Úvod a základní principy](#1-úvod-a-základní-principy)
2. [Struktura URL](#2-struktura-url)
3. [Autentizace](#3-autentizace)
4. [Podporované HTTP operace](#4-podporované-http-operace)
5. [Podporované formáty](#5-podporované-formáty)
6. [Formát FlexiBee XML (winstrom)](#6-formát-flexibee-xml-winstrom)
7. [Identifikátory záznamů](#7-identifikátory-záznamů)
8. [Identifikátor firmy](#8-identifikátor-firmy)
9. [Čtení dat (export)](#9-čtení-dat-export)
10. [Zápis dat (import)](#10-zápis-dat-import)
11. [Datové typy](#11-datové-typy)
12. [Povinné atributy a vnitřní vazby](#12-povinné-atributy-a-vnitřní-vazby)
13. [Výpočet DPH](#13-výpočet-dph)
14. [Cizí měny a kurzy](#14-cizí-měny-a-kurzy)
15. [Štítky](#15-štítky)
16. [Přílohy](#16-přílohy)
17. [Tiskové reporty, PDF a odesílání e-mailem](#17-tiskové-reporty-pdf-a-odesílání-e-mailem)
18. [Párování plateb](#18-párování-plateb)
19. [Changes API (sledování změn)](#19-changes-api-sledování-změn)
20. [WebHooks](#20-webhooks)
21. [XSD schémata](#21-xsd-schémata)
22. [Obsluha chyb](#22-obsluha-chyb)
23. [Výkonnostní doporučení](#23-výkonnostní-doporučení)
24. [Přehled evidencí](#24-přehled-evidencí)
25. [Užitečné servisní endpointy](#25-užitečné-servisní-endpointy)
26. [Zdroje](#26-zdroje)

---

## 1. Úvod a základní principy

ABRA Flexi poskytuje **REST API**, které je primárním integračním rozhraním systému. Platí tyto základní principy:

- **Vše je zdroj (resource)** — každá firma, evidence i jednotlivý záznam má vlastní URL.
- **XML je základ komunikace** — nativní formát „FlexiBee XML" umožňuje číst i zapisovat veškerá dostupná data. JSON je automatickou konverzí téhož formátu, pro faktury je navíc k dispozici standard ISDOC.
- **Inkrementální aktualizace** — při změně záznamu stačí poslat pouze měněné položky; ostatní hodnoty zůstávají zachovány nebo se dopočítají.
- **Velikost písmen v názvech tagů a atributů se ignoruje** — `<nazev>`, `<NAZEV>` i `<Nazev>` jsou rovnocenné.
- Stejné XML, které API vyexportuje, lze (po odstranění read-only polí) použít jako vstup pro import.
- Server standardně běží na portu **5434** (HTTPS), cloudové instance na `https://<firma>.flexibee.eu`.

Veřejný demo server pro testování: `https://demo.flexibee.eu` (uživatel `winstrom`, heslo `winstrom`).

```bash
curl -u winstrom:winstrom 'https://demo.flexibee.eu/c/demo/adresar.xml'
```

---

## 2. Struktura URL

### Základní vzor

```
/c/<identifikátor-firmy>/<evidence>/<identifikátor-záznamu>.<formát>
```

| Složka | Význam |
|---|---|
| `/c/` | Konstantní prefix (company) |
| `<identifikátor-firmy>` | Určuje firmu/databázi (viz kap. 8) |
| `<evidence>` | Typ záznamů — např. `adresar`, `faktura-vydana`, `cenik` (viz kap. 24) |
| `<identifikátor-záznamu>` | ID konkrétního záznamu (viz kap. 7); bez něj jde o výpis |
| `.<formát>` | Výstupní formát (`xml`, `json`, `pdf`, …); bez přípony se vrací HTML |

### Přehled variant URL

| URL | Význam |
|---|---|
| `/c/firma/adresar` | Výpis záznamů evidence |
| `/c/firma/adresar/123.xml` | Detail záznamu (interní ID) |
| `/c/firma/adresar/code:ABC.xml` | Detail záznamu podle kódu |
| `/c/firma/adresar/(nazev like 'Novák')` | Filtrovaný výpis (filtr v kulatých závorkách) |
| `/c/firma/faktura-vydana/$sum` | Sumace záznamů (jen doklady) |
| `/c/firma/faktura-vydana/(filtr)/$sum` | Sumace přes filtr |
| `/c/firma/adresar/properties` | Přehled atributů (metadata) evidence |
| `/c/firma/faktura-vydana/reports` | Seznam tiskových reportů evidence |
| `/c/firma/adresar/12/prilohy` | Podřízená evidence (vazba) konkrétního záznamu |
| `/c/firma/adresar/schema-export.xsd` | XSD schéma exportu |
| `/c.xml` | Seznam firem na serveru |

### Nejdůležitější URL parametry

| Parametr | Význam |
|---|---|
| `limit`, `start` | Stránkování (kap. 9.4) |
| `order`, `sort`, `dir` | Řazení (kap. 9.5) |
| `detail` | Úroveň detailu: `id`, `summary`, `full`, `custom:...` (kap. 9.3) |
| `relations` | Přibalení vazeb (`polozky`, `prilohy`, `vazby`, …) |
| `includes` | Vložení celých navázaných objektů místo ID |
| `add-row-count=true` | Přidá celkový počet záznamů |
| `add-global-version=true` | Přidá globální verzi databáze (Changes API) |
| `dry-run=true` | Testovací uložení bez zápisu (kap. 10.7) |
| `filtrovat-platnost=false` | Vypne implicitní filtr platnosti (`platiOd`/`platiDo`) |
| `no-ext-ids=true` | Nevypisovat externí identifikátory (rychlejší export) |
| `report-name`, `report-lang`, `report-sign` | Volba tiskového reportu pro PDF (kap. 17) |
| `encoding` | Kódování pro CSV/DBF (např. `iso-8859-2`) |
| `authSessionId` | Přenos autentizačního tokenu v URL |
| `otp` | Jednorázový kód při dvoufázovém ověření |
| `skupina-stitku` | Rozpad štítků dle skupin (kap. 15) |
| `evidence` | U Changes API omezení na konkrétní evidence |

Celkem API podporuje přes 30 parametrů; kompletní výčet je v referenční příručce (`/devdoc/urls`).

---

## 3. Autentizace

### 3.1 HTTP Basic Authentication

Původní a nejjednodušší metoda — jméno a heslo se posílají v hlavičce `Authorization` (Base64) s každým požadavkem:

```bash
curl -u winstrom:winstrom 'https://demo.flexibee.eu:5434/c/demo/adresar.xml'
```

Bez hlavičky vrací server přesměrování na přihlašovací formulář, resp. `401 Authorization Required`. Při zapnutém dvoufázovém ověření se aktuální jednorázový kód předává parametrem `?otp=`.

### 3.2 Přihlášení přes JSON (session token)

Endpoint `POST /login-logout/login.json` s formulářovými daty `username`, `password` (volitelně `otp`) vrátí token:

```json
{
  "success": true,
  "authSessionId": "00112233445566778899aabbccddeeff..."
}
```

Token lze následně předávat třemi způsoby:

- cookie `authSessionId=<token>`
- HTTP hlavička `X-authSessionId: <token>`
- URL parametr `?authSessionId=<token>` (pozor — token se objeví v logu serveru)

### 3.3 Údržba a ukončení session

- Udržování platnosti: `GET /login-logout/session-keep-alive.js` cca každých 60 s (nejméně jednou za 30 minut).
- Odhlášení: `/login-logout/logout`.
- Reset hesla: `/password-reset/send-email` → ověření tokenu → `/password-reset/set-password`.

### 3.4 Přístupová práva

API respektuje uživatelská oprávnění a role nastavené ve Flexi — uživatel přes API nevidí a nezmění nic, co nemůže dělat v aplikaci. Zápis přes REST API navíc vyžaduje aktivní licenci REST API pro zápis (jinak `402 Payment Required`).

---

## 4. Podporované HTTP operace

| Metoda | Použití |
|---|---|
| `GET` | Čtení záznamů (výpis i detail) v požadovaném formátu |
| `POST` / `PUT` | Vytvoření nebo změna záznamů — Flexi je zpracovává **shodně** |
| `DELETE` | Smazání jednoho záznamu přes jeho detailové URL |

### Pravidla pro POST/PUT

- Na **výpisovém URL** (`/c/firma/faktura-vydana.xml`) se záznamy zakládají, nebo aktualizují podle identifikátoru uvedeného v těle.
- Na **detailovém URL** (`/c/firma/faktura-vydana/123.xml`) se identifikátor bere z URL a záznam musí existovat.
- V jednom požadavku lze poslat **více záznamů i více evidencí** najednou.
- Tělo musí být XML nebo JSON — **ne** `multipart/form-data`.
- Vstupní a výstupní formát musí odpovídat (podle přípony URL nebo hlavičky `Content-Type`).
- Identifikátor nově založeného záznamu vrací server v hlavičce `Location` a v těle odpovědi (`<id>` v sekci `result`; při úspěchu `201 Created`).

### Pravidla pro DELETE

- Lze mazat jen jednotlivé záznamy přes detailové URL; hromadné mazání se řeší akcí `action="delete"` při importu (kap. 10.5).
- `200` = smazáno, `404` = záznam neexistuje.

---

## 5. Podporované formáty

Formát určuje **přípona v URL** (má přednost), případně hlavičky `Accept` / `Content-Type`.

| Formát | Přípona | Content-Type | Import |
|---|---|---|---|
| HTML | `.html` (výchozí) | `text/html` | ne |
| **XML** | `.xml` | `application/xml` | **ano** |
| JSON | `.json`, `.js` | `application/json`, `text/javascript` | ano |
| CSV | `.csv` | `text/csv` | ano |
| DBF | `.dbf` | `application/dbf` | ano |
| XLS | `.xls` | `application/ms-excel` | ano |
| XLSX | `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | ano |
| ISDOC | `.isdoc`, `.isdocx` | `application/x-isdoc(x)` | ano |
| EDI Inhouse | `.edi` | `application/x-edi-inhouse` | ano |
| PDF | `.pdf` | `application/pdf` | ne (výjimka: ISDOC vložený v PDF) |
| vCard | `.vcf` | `text/vcard` | ne |
| iCalendar | `.ical` | `text/calendar` | ne |

Poznámky:

- CSV a DBF podporují parametr `?encoding=` (např. `iso-8859-2`).
- Import ISDOC má parametry `typDokl` (typ dokladu, povinný), `typUcOp` (účetní předpis) a `odpocetZaloh` (automatický odpočet záloh/ZDD, výchozí `true`).
- PDF export odpovídá tiskovým reportům aplikace (kap. 17).

---

## 6. Formát FlexiBee XML (winstrom)

### 6.1 Základní struktura

Kořenovým elementem každého XML dokumentu (exportu i importu) je `<winstrom>` s atributem `version="1.0"` (historický název systému; v JSON je to klíč `"winstrom"` a atributy se zapisují s prefixem `@`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<winstrom version="1.0">
  <adresar>
    <id>123</id>
    <kod>NOVAK</kod>
    <nazev>Jan Novák s.r.o.</nazev>
    <ic>12345678</ic>
    <dic>CZ12345678</dic>
    <ulice>Dlouhá 1</ulice>
    <mesto>Praha</mesto>
    <psc>11000</psc>
    <stat>code:CZ</stat>
  </adresar>
</winstrom>
```

Uvnitř `<winstrom>` je libovolný počet elementů pojmenovaných podle **evidence** (`<adresar>`, `<faktura-vydana>`, `<cenik>`, …) — každý reprezentuje jeden záznam. V jednom dokumentu lze kombinovat více evidencí; pořadí je významné (např. nejdřív adresář, pak faktura, která se na něj odkazuje).

### 6.2 Záznam s položkami (doklad)

Položkové doklady mají kolekce položek ve vnořeném elementu:

```xml
<winstrom version="1.0">
  <faktura-vydana>
    <typDokl>code:FAKTURA</typDokl>
    <firma>code:NOVAK</firma>
    <datVyst>2026-07-01</datVyst>
    <polozkyFaktury>
      <faktura-vydana-polozka>
        <nazev>Konzultace</nazev>
        <mnozMj>10</mnozMj>
        <cenaMj>1500</cenaMj>
        <typSzbDphK>typSzbDph.dphZakl</typSzbDphK>
      </faktura-vydana-polozka>
    </polozkyFaktury>
  </faktura-vydana>
</winstrom>
```

### 6.3 Ekvivalent v JSON

```json
{
  "winstrom": {
    "@version": "1.0",
    "faktura-vydana": [{
      "typDokl": "code:FAKTURA",
      "firma": "code:NOVAK",
      "datVyst": "2026-07-01"
    }]
  }
}
```

XML atributy (`action`, `filter`, `removeAll`, `sourceId`, …) se v JSON zapisují jako klíče s `@` (`"@action": "delete"`, `"polozkyFaktury@removeAll": "true"`).

### 6.4 Pomocné atributy v exportu

Export doplňuje k vazbám atributy `ref` (relativní URL navázaného objektu) a `showAs` (lidsky čitelná reprezentace). Při importu se tyto atributy **ignorují** — rozhoduje pouze hodnota tagu.

### 6.5 Odpověď serveru na import

```xml
<?xml version="1.0" encoding="UTF-8"?>
<winstrom version="1.0" success="true">
  <stats>
    <created>1</created>
    <updated>0</updated>
    <deleted>0</deleted>
    <skipped>0</skipped>
    <failed>0</failed>
  </stats>
  <results>
    <result>
      <request-id>ext:SHOP:123</request-id>
      <ref>/c/firma/faktura-vydana/456.xml</ref>
      <id>456</id>
    </result>
  </results>
</winstrom>
```

Při chybě obsahuje `result` element `<error>` s popisem (kap. 22).

---

## 7. Identifikátory záznamů

Na místě identifikátoru (v URL i v XML vazbách) lze použít více typů:

| Typ | Syntaxe | Popis | Příklad |
|---|---|---|---|
| Interní ID | `123` | Číselné ID přidělené aplikací; nelze měnit | `123` |
| Kód (zkratka) | `code:...` | Uživatelský kód záznamu (pole `kod`), lze měnit v aplikaci; zapisuje se velkými písmeny | `code:CZK` |
| Klíč | `key:...` | Unikátní náhodný UUID atribut, neměnný | `key:550e8400e29b41d4a716` |
| PLU | `plu:...` | PLU kód ceníkové položky (4–5 číslic) | `plu:4020` |
| EAN | `ean:...` | Čárový kód | `ean:4710937332698` |
| **Externí ID** | `ext:SYSTEM:id` | Identifikátor z externí aplikace — dvojice „systém : ID v něm" | `ext:SHOP:123` |
| Hybridní | `ws:uuid:id` | UUID firmy + interní ID | `ws:a931bdf0-…-08e6800b0234:1` |
| DIČ | `vatid:...` | Daňové identifikační číslo (adresář) | `vatid:CZ28019920` |
| IČO | `in:...` | Identifikační číslo osoby (adresář) | `in:28019920` |
| IBAN | `iban:...` | Číslo bankovního účtu | `iban:CZ1201000002801992` |

### Externí identifikátory

Klíčový mechanismus pro integrace: záznam může nést libovolný počet externích ID. Při importu s `ext:SHOP:123` platí — pokud záznam s tímto externím ID existuje, aktualizuje se; pokud ne, **založí se** a externí ID se mu přiřadí. Tím je import idempotentní.

Odebrání externích ID: atribut `removeExternalIds` (lze s prefixem, např. `removeExternalIds="ext:SYSTEM"` odebere všechna ID daného systému).

### Více identifikátorů najednou

V exportu má záznam všechny identifikátory v opakovaném elementu `<id>`:

```xml
<adresar>
  <id>123</id>
  <id>ext:SHOP:55</id>
  <kod>NOVAK</kod>
</adresar>
```

V URL lze spojit více identifikátorů hranatými závorkami: `/c/firma/adresar/[123][code:ABC][ext:SHOP:55]`. Speciální znaky `[`, `]`, `\` se escapují jako `\[`, `\]`, `\\` (plus URL encoding).

---

## 8. Identifikátor firmy

- Povinná součást každého datového URL (`/c/<firma>/…`).
- Smí obsahovat jen **malá písmena, číslice a podtržítka**; musí být unikátní v rámci serveru.
- Obvykle se odvozuje z názvu firmy (při kolizi se přidá číslo).
- **Přejmenování firmy identifikátor nemění.** Smazání a nové založení (i obnova ze zálohy) vede k **novému** identifikátoru.
- Seznam firem na serveru: `GET /c.xml` (resp. `/c.json`).
- Založení firmy: `PUT /admin/zalozeni-firmy?name=…`; obnovení ze zálohy: `PUT /c/<firma>/restore-backup`.

---

## 9. Čtení dat (export)

### 9.1 Výpis vs. detail

- **Výpis** (`/c/firma/faktura-vydana.xml`) — více záznamů, výchozí úroveň detailu `summary`, stránkuje se.
- **Detail** (`/c/firma/faktura-vydana/123.xml`) — jeden záznam, výchozí úroveň `full`.

Hromadné čtení konkrétních záznamů bez omezení délky URL: `POST`/`PUT` na výpisové URL se seznamem ID v těle —

```xml
<winstrom>
  <id>1</id>
  <id>code:VF1-0001/2026</id>
  <id>ext:SYS:3</id>
</winstrom>
```

Neexistující identifikátory se tiše ignorují; duplicitní vrátí záznam vícekrát.

### 9.2 Podmíněné čtení

Hlavička `If-Modified-Since` → při nezměněném záznamu vrací `304 Not Modified`. Datum poslední změny nese atribut `lastUpdate`.

### 9.3 Úrovně detailu (`detail`)

| Úroveň | Obsah |
|---|---|
| `id` | Jen primární klíč a externí ID |
| `summary` | Základní přehled (`id`, `lastUpdate`, `kod`, `nazev`, …) — výchozí pro výpisy |
| `full` | Všechna pole záznamu — výchozí pro detail |
| `custom:pole1,pole2` | Jen vyjmenovaná pole (ID je vždy) |

Vnořené kolekce v custom detailu: `?detail=custom:kod,sady-a-komplety(cenik,cenikSada)`.

Doplnění vazeb: `?relations=polozky,prilohy,vazby,sklad-karty` (čárkami oddělený seznam). Parametr `?includes=/faktura-vydana/firma/` vloží místo ID celý navázaný objekt. Takto řízené exporty jsou **jen pro čtení**.

### 9.4 Stránkování

| Parametr | Význam | Výchozí |
|---|---|---|
| `limit` | Max. počet záznamů na stránku; `0` = bez omezení | 20 |
| `start` | Kolik záznamů přeskočit (offset) | 0 |
| `add-row-count=true` | Přidá do výstupu celkový počet záznamů (respektuje filtr) | — |

```
/c/firma/adresar.xml?limit=100&start=200&add-row-count=true
```

### 9.5 Řazení

- `?order=nazev` — vzestupně (výchozí `@A`), `?order=nazev@D` — sestupně.
- Víceúrovňové řazení = parametr `order` vícekrát.
- Relační vlastnosti 1. úrovně tečkovou notací: `?order=stat.kod`.
- Zpětně kompatibilní: `?sort=nazev&dir=DESC`.

### 9.6 Filtrování

Filtr se zapisuje **v kulatých závorkách** za evidenci: `/c/firma/adresar/(nazev like 'Novák' and mesto = 'Praha').xml` (nutné URL kódování).

**Porovnávací operátory**

| Operátor | Význam | Příklad |
|---|---|---|
| `=`, `==`, `eq` | rovnost | `kod = 'ABC'` |
| `<>`, `!=`, `ne` | nerovnost | `id != 1` |
| `<`, `<=`, `>`, `>=` (`lt`, `lte`, `gt`, `gte`) | porovnání | `datVyst >= '2026-01-01'` |
| `like` | obsahuje text | `nazev like 'nov'` |
| `like similar` | obsahuje text bez diakritiky | `nazev like similar 'novak'` |
| `begins` / `ends` | začíná / končí na | `kod begins 'VF'` |
| `between` | interval | `castka between 100 1000` |
| `in` | výčet hodnot | `id in (1,2,3)` |
| `in subtree` | podstrom stromové evidence | `stredisko in subtree 3` |
| `is null` / `is not null` | (ne)vyplněno | `datSplat is null` |
| `is empty` / `is not empty` | prázdné / neprázdné | `poznam is empty` |
| `is true` / `is false` | booleovské hodnoty | `storno is false` |

**Logické operátory:** `and`, `or`, `not` + závorky. Priorita: porovnání → `not` → `and` → `or`.

**Speciální funkce:** `now()` (aktuální datum/čas), `currentYear()` (aktuální rok), `me()` (přihlášený uživatel).

**Zápis hodnot:** čísla `10`, `-1`, `5.8`; řetězce v `'` nebo `"`; `true`/`false`; datum `YYYY-MM-DD`; datum s časem `YYYY-MM-DD'T'HH:MM:SS` (ve filtrech bez časové zóny). Na místě hodnoty vazby lze použít libovolný identifikátor (`firma = 'code:NOVAK'`).

**Pokročilé možnosti:**

- vazby tečkovou notací: `(firma.skupFir = 'code:VELKOOBCHOD')`
- filtr podle štítků: `(stitky = 'code:VIP')`
- evidence s poli `platiOd`/`platiDo` se implicitně filtrují na platnost dle účetního období — vypnutí `?filtrovat-platnost=false`.

### 9.7 Sumace

`/c/firma/faktura-vydana/(filtr)/$sum.xml` vrátí základní součty (částky apod.) — **jen pro doklady** (faktury, objednávky, nabídky, pokladní a skladové pohyby, …).

### 9.8 Metadata evidence

- `/c/firma/<evidence>/properties.xml` — kompletní popis atributů evidence: název, typ, povinnost, zapisovatelnost, seznam hodnot výčtů atd.
- `/c/firma/evidence-list.xml` — seznam všech evidencí systému (identifikátor, název, cesta).

---

## 10. Zápis dat (import)

### 10.1 Založení a změna záznamu

- Záznam **bez identifikátoru** → vždy se založí nový.
- Záznam **s interním ID / `code:`** → musí existovat, aktualizuje se.
- Záznam s **`ext:`** → existuje-li, aktualizuje se; jinak se založí (upsert).

### 10.2 Inkrementální aktualizace

Posílají se jen měněná pole; **prázdný element hodnotu maže**:

```xml
<winstrom version="1.0">
  <cenik id="123">
    <nazevA>Nový název</nazevA>
    <ean></ean>   <!-- smaže EAN -->
  </cenik>
</winstrom>
```

Kolekce položek: položka bez identifikátoru se **přidá** (rozhoduje pořadí — riskantní); s identifikátorem se aktualizuje. Pro položky se důrazně doporučují externí ID.

Atribut `removeAll="true"` na kolekci smaže všechny položky, které v importu nejsou uvedeny (nahrazení celého seznamu):

```xml
<faktura-vydana id="123">
  <polozkyFaktury removeAll="true">
    <faktura-vydana-polozka><id>14</id></faktura-vydana-polozka>
  </polozkyFaktury>
</faktura-vydana>
```

JSON: `"polozkyFaktury@removeAll": "true"`. Jednotlivou položku smaže `action="delete"` na elementu položky.

### 10.3 Režim pro založení/změnu (`create` / `update`)

Atributy na elementu záznamu řídí chování při ne/existenci záznamu:

| Atribut | Hodnota | Chování |
|---|---|---|
| `create` | `ok` (výchozí) | neexistuje-li, založí se |
| | `ignore` | neexistuje-li, požadavek se přeskočí |
| | `fail` | neexistuje-li, chyba |
| `update` | `ok` (výchozí) | existuje-li, změní se |
| | `ignore` | existuje-li, požadavek se přeskočí |
| | `fail` | existuje-li, chyba |

```xml
<faktura-vydana update="ignore">…</faktura-vydana>  <!-- jen založit, nikdy nepřepsat -->
```

Vazby mají atribut `if-not-found` pro případ, že odkazovaný záznam neexistuje: `null` (nechat prázdné), `create` (založit), `nearest-invalid` (navázat na nejbližší zneplatněný záznam — pro historické doklady).

### 10.4 Kopie záznamu (`sourceId`)

```xml
<winstrom version="1.0">
  <ucet sourceId="code:132001">
    <id>code:132002</id>
    <nazev>Zboží na hlavním skladě</nazev>
  </ucet>
</winstrom>
```

Založí nový záznam jako kopii zdrojového a aplikuje uvedené změny. S uvedeným cílovým identifikátorem je operace idempotentní. U číselníků je nutné zajistit unikátnost polí (kód apod.); kopie dokladů to řeší automaticky (nové číslo dokladu).

### 10.5 Provádění akcí (`action`)

Atribut `action` na elementu záznamu spustí akci; záznam musí existovat a kromě `id` se nic dalšího neuvádí:

```xml
<winstrom version="1.0">
  <faktura-vydana action="delete">
    <id>123</id>
  </faktura-vydana>
</winstrom>
```

Obecné akce: `delete` (smazání), `storno` (stornování — jen doklady), `lock` / `lock-for-ucetni` / `unlock` (zamykání, kap. dále), `copy`. Evidence mohou mít i specifické akce (realizace objednávky, přepočet skladu, fakturace smluv, …) — jejich seznam vrací `/c/firma/<evidence>/actions.xml`.

Akce na položce dokladu: `<faktura-vydana-polozka id="456" action="delete"/>` uvnitř kolekce; JSON `"@action": "delete"`.

### 10.6 Dávkové operace (`filter`)

Atribut `filter` na elementu záznamu aplikuje změnu/akci na **všechny záznamy vyhovující filtru** (jazyk filtru shodný s REST API; elementy `id` se ignorují):

```xml
<winstrom version="1.0">
  <cenik filter="dodavatel = 'code:FIRMA'">
    <stitky>VIP</stitky>
  </cenik>
</winstrom>
```

```json
{ "winstrom": { "@version": "1.0",
  "faktura-vydana": { "@filter": "stitky='code:OVERENO'", "@action": "lock" } } }
```

### 10.7 Testovací uložení (dry-run)

`?dry-run=true` na URL importu: provedou se **všechny validace a dopočty závislých hodnot** (ceny, DPH, vliv typu dokladu…), ale nic se neuloží. Odpověď obsahuje výsledný záznam v sekci `<content/>` — ideální pro náhledy výpočtů a kontrolu před ostrým uložením. Číslo dokladu přidělené při dry-run se ihned uvolní (ostré uložení může dostat jiné).

### 10.8 Transakční zpracování (`atomic`)

- Výchozí chování: **celý import = jedna databázová transakce** (vše, nebo nic).
- `<winstrom version="1.0" atomic="false">` → každý záznam ve vlastní transakci; položky zůstávají v transakci svého dokladu. Výhody: nižší paměťová náročnost, rychlejší velké importy, částečný úspěch. Riziko: nekonzistence při chybách.

### 10.9 Zamykání a odemykání

```xml
<faktura-vydana action="lock"><id>1</id></faktura-vydana>
<faktura-vydana action="lock-for-ucetni"><id>1</id></faktura-vydana>
<faktura-vydana action="unlock"><id>1</id></faktura-vydana>
```

Zamčený záznam nelze měnit. Lze kombinovat s `filter` pro dávkové zamykání.

### 10.10 Validace

Při každém uložení probíhají stejné validace jako v aplikaci; výsledkem mohou být chyby (uložení selže), varování a informační zprávy — vše se vrací ve strukturované odpovědi.

---

## 11. Datové typy

| Typ | Popis | Formát / příklad |
|---|---|---|
| `string` | Unicode řetězec, libovolné znaky | `šílený koníček` |
| `integer` | Znaménkový 4bajtový celočíselný typ, bez mezer | `12` |
| `numeric` | Desetinné číslo, **oddělovač tečka**, 8bajtový double | `12.5` |
| `date` | Datum `YYYY-MM-DD`, volitelná časová zóna se ignoruje; podporuje substituci `${currentYear}` | `1980-05-06`, `2015-01-30Z` |
| `datetime` | `YYYY-MM-DD'T'HH:MM:SS(.SSS)` s volitelnou zónou (W3C) | `2008-09-01T17:18:14.075+02:00` |
| `logic` | Booleovská hodnota | `true` / `false` |
| `select` | Výběr jedné hodnoty z výčtu (konstanty) | `typVztahu.odberDodav` |
| `relation` | Vazba na záznam jiné evidence — libovolný identifikátor | `123`, `code:CZK`, `ext:SHOP:5` |

Hodnoty výčtů (`select`) jsou tzv. **konstanty** — mají tvar `skupina.hodnota` (např. `typSzbDph.dphZakl`, `stavUhr.uhrazeno`, `typPohybu.prijem`). Kompletní přehled je v referenční dokumentaci (`/devdoc/constants`) a v `properties` každé evidence.

---

## 12. Povinné atributy a vnitřní vazby

- Povinná jsou zpravidla jen pole, která je nutné vyplnit i při ručním zadání v aplikaci; u dokladů je téměř vždy povinný **typ dokladu** `<typDokl>`.
- Povinnost může být **kontextová** — závisí na typu dokladu, modulu apod. Přesné informace poskytuje `/c/firma/<evidence>/properties.xml` (atributy `mandatory`, `writable`, …).
- Pole označená v exportu jako *read-only* nelze importovat.
- **Vnitřní vazby:** při ukládání systém staví strom závislostí — hodnota, která ovlivňuje jinou (typ dokladu → řada, účty, sazby DPH; stát → měna…), se aplikuje první, nezávisle na pořadí v XML. Výchozí hodnoty se doplní automaticky, proto stačí posílat jen to, co se má lišit. Vedlejší efekt: inkrementální změna jednoho pole může přepočítat i pole jiná.
- Pořadí **záznamů** v dokumentu ale významné je (nejdřív číselníky/adresář, pak doklady).

---

## 13. Výpočet DPH

Souhrnná pole dokladů (za sazby):

| Pole | Význam |
|---|---|
| `sumZklZakl` / `sumDphZakl` / `sumCelkZakl` | základ / DPH / celkem — základní sazba |
| `sumZklSniz` / `sumDphSniz` / `sumCelkSniz` | základ / DPH / celkem — snížená sazba |
| `sumZklSniz2` / `sumDphSniz2` | druhá snížená sazba (historicky) |
| `sumOsv` | osvobozená plnění |
| `sumCelkem` | celková částka dokladu |

Principy:

- U položkových dokladů je DPH **součtem DPH položek** (se zaokrouhlením výsledku).
- Směr výpočtu („shora" z celkové částky vs. „zdola" ze základu) se řídí tím, **která pole pošlete** — obvykle se posílá základ a Flexi dopočítá zbytek; pošlete-li vše, systém zkontroluje matematické vztahy a při nesouladu vrátí chybu.
- Sazba na položce: `typSzbDphK` s konstantami `typSzbDph.dphZakl` (základní), `typSzbDph.dphSniz` (snížená), `typSzbDph.dphSniz2`, `typSzbDph.dphOsv` (osvobozeno).
- Bezpoložkové doklady lze zapsat přímo přes souhrnná pole.

---

## 14. Cizí měny a kurzy

- Měna dokladu: `<mena>code:EUR</mena>`; kurz: `kurz`, množství kurzu: `kurzMnozstvi` (např. 100 pro HUF).
- Částky v cizí měně mají pole se sufixem `Men` (`sumCelkemMen`, `cenaMjMen`…), domácí měna bez sufixu.
- Neuvedete-li kurz, Flexi jej **automaticky stáhne** (ČNB, ECB).
- Částka v měně, částka v domácí měně a kurz musí být **v rovnováze**; protože se částky zaokrouhlují na 2 desetinná místa, systém dorovnává kurz (ukládán na 6 desetinných míst) tak, aby vztahy seděly — kurz na dokladu se tedy může nepatrně lišit od kurzu lístku.

---

## 15. Štítky

- Štítky (`stitky`) jsou volné nálepky na záznamech (doklady, adresář, ceník…); samostatná evidence `stitek`.
- V exportu/importu vystupují jako čárkami oddělený seznam kódů v elementu `<stitky>`.
- Bez `removeAll` se štítky pouze **přidávají**; nahrazení celé sady:

```xml
<adresar>
  <id>14</id>
  <stitky removeAll="true">STITEK1,NOVY_STITEK</stitky>
</adresar>
```

(JSON: `"stitky@removeAll": "true", "stitky": "STITEK1,NOVY_STITEK"`.) Smazání všech = `<stitky removeAll="true"></stitky>`.

- Štítky lze členit do **skupin**; skupina s omezením „jeden štítek" simuluje stavy záznamu (nastavení nového štítku odebere ostatní ze skupiny). Export po skupinách: `?skupina-stitku=SKUPINA1,SKUPINA2` → `<stitky SKUPINA1="STITEK1" …>`.
- Filtrování: `(stitky = 'code:VIP')`.

---

## 16. Přílohy

| Operace | URL |
|---|---|
| Seznam příloh záznamu | `GET /c/firma/adresar/12/prilohy` |
| Metadata přílohy | `GET /c/firma/adresar/12/prilohy/75` |
| Binární obsah | `GET /c/firma/adresar/12/prilohy/75/content` (správný Content-Type) |
| Náhled obrázku | `GET /c/firma/adresar/12/prilohy/75/thumbnail` (`?w=`, `?h=`; 404 pokud není) |
| Hlavní obrázek objektu | `GET /c/firma/cenik/12/thumbnail.png` |
| Nahrání přílohy | `PUT /c/firma/adresar/12/prilohy/new/<název-souboru>` + `Content-Type` + binární tělo |

- Existující přílohu nelze změnit — jen smazat (`DELETE`) a nahrát znovu.
- V XML exportu je obsah Base64: `<content encoding="base64">…</content>`; importem lze měnit jen metadata, přílohy musí být vnořené v nadřazeném objektu.
- Podporované obrázky pro náhledy: JPEG, GIF, PNG.
- Speciální přílohy firmy (logo, podpis/razítko) se spravují přes `/c/firma/nastaveni/`.

---

## 17. Tiskové reporty, PDF a odesílání e-mailem

### PDF export

```
GET /c/firma/faktura-vydana/1.pdf?report-name=dodaciList&report-lang=en&report-sign=true
```

| Parametr | Význam |
|---|---|
| `report-name` | Volba tiskové sestavy (seznam: `/c/firma/<evidence>/reports`) |
| `report-lang` | Jazyk sestavy: `cs`, `sk`, `en`, `de` |
| `report-sign` | `true` = elektronicky podepsané PDF (vyžaduje právě jeden certifikát ve Flexi) |

Endpoint `/reports` vrací (i v XML/JSON) identifikátory sestav, výchozí sestavu a podporu sumace.

### Odeslání dokladu e-mailem

```
PUT /c/firma/faktura-vydana/1/odeslani-dokladu.xml?to=email@example.com&subject=Faktura
```

Parametry: `to`, `cc` (vícekrát), `subject`, `sablona` (mailová šablona), `report-lang`. Tělo požadavku = text zprávy (UTF-8). Alespoň jeden příjemce je povinný. Přikládá se PDF (volitelně i ISDOC). Vyžaduje nakonfigurovaný SMTP server.

---

## 18. Párování plateb

Platbu (bankovní pohyb `banka` nebo pokladní `pokladni-pohyb`) lze při importu spárovat s fakturami elementem `<sparovani>`:

```xml
<winstrom version="1.0">
  <banka>
    <id>ext:BANK:2026-001</id>
    <typDokl>code:STANDARD</typDokl>
    <typPohybuK>typPohybu.prijem</typPohybuK>
    <sumCelkem>12100</sumCelkem>
    <sparovani>
      <uhrazovanaFak>code:VF1-0001/2026</uhrazovanaFak>
      <zbytek>castecnaUhrada</zbytek>
    </sparovani>
  </banka>
</winstrom>
```

- V jednom spárování lze uhradit **více faktur** (stejného směru — vydané × přijaté); u faktury lze atributem `castka` omezit uhrazovanou část.
- `<zbytek>` řídí naložení s rozdílem částek: `ne` (nepovolit), `zauctovat` (interní doklad na rozdíl), `ignorovat`, `castecnaUhrada` (částečná úhrada), `castecnaUhradaNeboZauctovat`, `castecnaUhradaNeboIgnorovat`.
- Podporováno je i párování napříč měnami (kurzový přepočet automaticky).
- K dispozici je také **automatické párování** (REST akce s parametry režimu, období a tolerance) a další platební operace: hotovostní úhrada (`hotovostni-uhrada`), úhrada přeplatkem, vzájemné zápočty, příkazy k úhradě (`prikaz-k-uhrade`).

---

## 19. Changes API (sledování změn)

Mechanismus pro **inkrementální synchronizaci**: Flexi zaznamenává všechny změny v databázi firmy do changelogu s rostoucím číslem verze (globální verze).

### Zapnutí

| Operace | URL |
|---|---|
| Stav | `GET /c/firma/changes/status.xml` → `true`/`false` |
| Zapnutí | `PUT /c/firma/changes/enable.xml` (`Content-Length: 0`) |
| Vypnutí | `PUT /c/firma/changes/disable.xml` |
| Ovládání z prohlížeče | `/c/firma/changes/control` |

Vyžaduje licenci REST API. Zapnutí zamyká celou databázi — při chybě `could not obtain lock on relation` je nutné se všude odhlásit.

### Čtení změn

`GET /c/firma/changes.xml?start=<verze>`:

```xml
<winstrom version="1.0" globalVersion="6">
  <faktura-vydana in-version="3" operation="create" timestamp="2019-01-01 00:00:00.0">
    <id>1</id>
  </faktura-vydana>
  <faktura-vydana in-version="5" operation="update" timestamp="2019-06-07 12:34:56.7">
    <id>1</id>
    <id>code:VF1-0001/2012</id>
  </faktura-vydana>
  <next>6</next>
</winstrom>
```

| Parametr | Význam |
|---|---|
| `start` | Od které verze číst (včetně) |
| `limit` | Počet záznamů (výchozí 100, max 1000) |
| `evidence` | Omezení na evidence (lze vícekrát) |

Každá změna nese `in-version`, `operation` (`create` / `update` / `delete`), `timestamp` a identifikátory záznamu; `<next>` je verze pro další dotaz.

### Synchronizační postup

1. Prvotní načtení dat s `?add-global-version=true` → zapamatovat `globalVersion`.
2. Periodicky číst `/changes.xml?start=<zapamatovaná verze>`; změněné záznamy dotáhnout, smazané odstranit.
3. Uložit hodnotu `<next>` a opakovat.

---

## 20. WebHooks

Aktivní notifikace o změnách (nadstavba Changes API):

```
PUT /c/firma/hooks.xml?url=http://muj.server.cz/hook.php&format=XML&lastVersion=123&secKey=TajnyToken
```

| Parametr | Povinný | Význam |
|---|---|---|
| `url` | ano | Cílové URL notifikací |
| `format` | ano | `XML` nebo `JSON` |
| `lastVersion` | ne | Počáteční verze (výchozí = aktuální globalVersion) |
| `secKey` | ne | Token zasílaný v hlavičce `X-FB-Hook-SecKey` |
| `skipUrlTest` | ne | Přeskočí test funkčnosti URL při registraci |

Chování:

- Obsah notifikace = seznam změn od posledního volání, formát shodný s Changes API.
- Úspěch = odpověď `2xx` do **30 sekund** (ideálně do 15 s); při selhání opakování s rostoucími rozestupy (penalizace).
- Zatím nelze omezit na konkrétní evidence — chodí všechny změny databáze.
- Best effort: možné duplicity i zpoždění — hook berte jako impuls, data čtěte přes Changes API.
- Registrované hooky: `GET /c/firma/hooks.xml`, zrušení `DELETE /c/firma/hooks/<id>`.

---

## 21. XSD schémata

- Struktura XML je variabilní (závisí na evidenci a úrovni detailu); schémata se generují pro každou evidenci:
  - export: `/c/<firma>/<evidence>/schema-export.xsd`
  - import: `/c/<firma>/<evidence>/schema-import.xsd` (bez read-only polí)
- Příklad: `https://demo.flexibee.eu/c/demo/adresar/schema-export.xsd`.
- Upozornění z dokumentace: XSD plně neodráží všechny možnosti API — systém může vracet validní XML, které schématu neodpovídá; berte XSD jako vodítko, ne jako kontrakt.

---

## 22. Obsluha chyb

### HTTP stavové kódy

| Kód | Význam |
|---|---|
| `200 OK` | Operace úspěšná |
| `201 Created` | Záznam založen; `Location` obsahuje URL, tělo identifikátor |
| `304 Not Modified` | Beze změny (při `If-Modified-Since`) |
| `400 Bad Request` | Neplatný požadavek (typicky odkaz na neexistující objekt při PUT) |
| `401 Unauthorized` | Chybí/špatná autentizace |
| `402 Payment Required` | REST API pro zápis není licenčně aktivováno |
| `403 Forbidden` | Nedostatečná oprávnění (i licenční omezení) |
| `404 Not Found` | Záznam/evidence neexistuje (možná smazán) |
| `406 Not Acceptable` | Cílový formát není pro zdroj podporován |
| `409 Conflict` | Konfliktní souběžná operace na serveru — vyčkejte |
| `500 Internal Server Error` | Neočekávaná chyba serveru |
| `503 Maintenance` | Probíhá údržba |

### Struktura chybové odpovědi

Kromě chyb 500 vrací server strojově čitelný popis:

```xml
<winstrom version="1.0">
  <success>false</success>
  <result>
    <id>105</id>
    <error>Při ukládání došlo k neznámé chybě.</error>
  </result>
</winstrom>
```

U hromadného importu obsahuje odpověď výsledek pro každý záznam (`request-id` odpovídá zaslanému identifikátoru); u validací se rozlišují chyby, varování a informace, chyba nese i informaci o poli, kterého se týká.

---

## 23. Výkonnostní doporučení

- **Autentizaci posílejte rovnou** s každým požadavkem (nečekejte na 401), případně používejte `authSessionId`.
- **Omezujte pole**: `?detail=custom:...` je nejrychlejší; nevyžadujte `relations=all`, ale jen potřebné vazby.
- **`?no-ext-ids=true`** u velkých exportů, pokud externí ID nepotřebujete.
- Počet záznamů zjišťujte přes `?add-row-count=true` + `limit=1`, ne stažením všeho.
- **Seskupujte požadavky**: hromadné čtení přes POST se seznamem ID, hromadný import více záznamů v jednom dokumentu; u velkých importů zvažte `atomic="false"`.
- Neopakujte stejná volání v rámci jednoho zpracování; využívejte `If-Modified-Since`/`lastUpdate` a Changes API místo plných exportů.
- Hardware: společné umístění DB a serveru, dostatek RAM, ladění PostgreSQL, rychlé disky.

---

## 24. Přehled evidencí

Kompletní a autoritativní seznam pro konkrétní instalaci vrací `GET /c/<firma>/evidence-list.xml`. Nejpoužívanější evidence:

### Obchodní doklady

| Evidence | Význam |
|---|---|
| `faktura-vydana` / `faktura-prijata` | Vydané / přijaté faktury (vč. záloh, ZDD, dobropisů — dle typu dokladu) |
| `objednavka-vydana` / `objednavka-prijata` | Vydané / přijaté objednávky |
| `nabidka-vydana` / `nabidka-prijata` | Nabídky |
| `poptavka-vydana` / `poptavka-prijata` | Poptávky |
| `smlouva` | Smlouvy (pravidelná fakturace) |

### Peníze

| Evidence | Význam |
|---|---|
| `banka` | Bankovní doklady (pohyby) |
| `bankovni-ucet` | Bankovní účty |
| `pokladni-pohyb` | Pokladní doklady |
| `pokladna` | Pokladny |
| `prikaz-k-uhrade` / `prikaz-k-inkasu` | Příkazy k úhradě / inkasu |
| `vzajemny-zapocet` | Vzájemné zápočty |
| `interni-doklad` | Interní doklady |
| `zavazek` / `pohledavka` | Ostatní závazky / pohledávky |

### Zboží a sklad

| Evidence | Význam |
|---|---|
| `cenik` | Ceník (položky zboží a služeb) |
| `skupina-zbozi` | Skupiny zboží |
| `sklad` | Sklady |
| `skladovy-pohyb` | Skladové doklady (příjemky/výdejky) |
| `skladova-karta` | Skladové karty |
| `inventura` | Inventury |
| `vyrobni-cislo` | Výrobní čísla |
| `cenova-uroven` / `cenik-individualni` | Cenové úrovně / individuální ceny |
| `kusovnik` | Kusovníky (sady a komplety) |

### Číselníky a nastavení

| Evidence | Význam |
|---|---|
| `adresar` | Adresář firem |
| `kontakt` | Kontaktní osoby |
| `stitek` | Štítky |
| `mena` | Měny |
| `stat` | Státy |
| `stredisko` | Střediska |
| `zakazka` | Zakázky |
| `cinnost` | Činnosti |
| `typ-faktury-vydane`, `typ-faktury-prijate`, `typ-banka`, `typ-pokladni-pohyb`, `typ-objednavky-vydane`, … | Typy dokladů jednotlivých modulů |
| `rada-faktury-vydane`, `rada-banka`, … | Dokladové řady |
| `ucet` | Účtový rozvrh |
| `ucetni-obdobi` | Účetní období |
| `ucetni-predpis` | Účetní předpisy (předkontace) |
| `sazba-dph` | Sazby DPH |
| `uzivatel` | Uživatelé |
| `sablona-mail` | Mailové šablony |
| `custom-button` | Uživatelská tlačítka |

### Majetek a mzdy

| Evidence | Význam |
|---|---|
| `majetek` | Dlouhodobý majetek |
| `drobny-majetek` | Drobný majetek |
| `zamestnanec` | Zaměstnanci |
| `pracovni-pomer` | Pracovní poměry |
| `mzda` / `mzdova-slozka` | Mzdy |

### Účetní výstupy (jen čtení)

`analyza-prodeje`, `analyza-nakupu`, `stav-uctu`, `obraty-uctu`, `hlavni-kniha`, `rozvaha`, `vysledovka`, `pokladni-kniha`, `kniha-faktur`, saldo, přehledy DPH (přiznání, kontrolní hlášení, souhrnné hlášení) aj.

> Názvy evidencí v URL jsou vždy malými písmeny s pomlčkami. Strukturu polí konkrétní evidence zjistíte na `/c/<firma>/<evidence>/properties.xml`, vzorová anotovaná XML jsou v dokumentaci („samodokumentující příklady").

---

## 25. Užitečné servisní endpointy

| URL | Význam |
|---|---|
| `/c.xml` | Seznam firem na serveru |
| `/status.xml` | Stav serveru |
| `/login-logout/login.json` | Přihlášení (session token) |
| `/login-logout/logout` | Odhlášení |
| `/login-logout/session-keep-alive.js` | Udržení session |
| `/password-reset/…` | Reset hesla |
| `/admin/zalozeni-firmy` | Založení nové firmy |
| `/c/<firma>/restore-backup` | Obnova firmy ze zálohy |
| `/c/<firma>/backup` | Stažení zálohy firmy |
| `/c/<firma>/evidence-list.xml` | Seznam evidencí |
| `/c/<firma>/<evidence>/properties.xml` | Metadata atributů evidence |
| `/c/<firma>/<evidence>/actions.xml` | Seznam akcí evidence |
| `/c/<firma>/<evidence>/reports.xml` | Seznam tiskových sestav |
| `/c/<firma>/<evidence>/schema-(export\|import).xsd` | XSD schémata |
| `/c/<firma>/changes.xml` | Changes API |
| `/c/<firma>/hooks.xml` | WebHooks |
| `/c/<firma>/nastaveni` | Nastavení firmy (vč. loga, razítka) |
| `/devdoc/` | Referenční příručka REST API přímo na serveru |

---

## 26. Zdroje

Oficiální dokumentace, z níž tato příručka vychází:

- [Referenční příručka REST API (devdoc)](https://demo.flexibee.eu/devdoc/) — a její kapitoly: [autentizace](https://demo.flexibee.eu/devdoc/login), [URL](https://demo.flexibee.eu/devdoc/urls), [formáty](https://demo.flexibee.eu/devdoc/format-types), [HTTP operace](https://demo.flexibee.eu/devdoc/http-operations), [identifikátory](https://demo.flexibee.eu/devdoc/identifiers), [filtry](https://demo.flexibee.eu/devdoc/filters), [typy proměnných](https://demo.flexibee.eu/devdoc/variable-types), [úrovně detailu](https://demo.flexibee.eu/devdoc/detail-levels), [stránkování](https://demo.flexibee.eu/devdoc/paging), [řazení](https://demo.flexibee.eu/devdoc/ordering), [sumace](https://demo.flexibee.eu/devdoc/sumace), [přílohy](https://demo.flexibee.eu/devdoc/attachments), [inkrementální aktualizace](https://demo.flexibee.eu/devdoc/partial-updates), [režim založení/změny](https://demo.flexibee.eu/devdoc/create-update-mode), [kopie záznamu](https://demo.flexibee.eu/devdoc/copy), [akce](https://demo.flexibee.eu/devdoc/actions), [dávkové operace](https://demo.flexibee.eu/devdoc/batch-operations), [transakce](https://demo.flexibee.eu/devdoc/tx), [dry-run](https://demo.flexibee.eu/devdoc/dry-run), [chyby](https://demo.flexibee.eu/devdoc/errors), [výkon](https://demo.flexibee.eu/devdoc/performance), [DPH](https://demo.flexibee.eu/devdoc/dph), [kurzy](https://demo.flexibee.eu/devdoc/kurz), [štítky](https://demo.flexibee.eu/devdoc/stitky), [zamykání](https://demo.flexibee.eu/devdoc/zamykani-odemykani), [párování plateb](https://demo.flexibee.eu/devdoc/parovani-plateb), [odesílání mailem](https://demo.flexibee.eu/devdoc/odesilani-mailem), [XSD](https://demo.flexibee.eu/devdoc/xsd), [PDF](https://demo.flexibee.eu/devdoc/pdf), [identifikátor firmy](https://demo.flexibee.eu/devdoc/company-identifier), [povinnost atributů](https://demo.flexibee.eu/devdoc/required-fields), [vnitřní vazby](https://demo.flexibee.eu/devdoc/internal-dependencies), [výpis záznamů](https://demo.flexibee.eu/devdoc/list)
- [Dokumentace API — rozcestník](https://www.flexibee.eu/api/dokumentace)
- [FlexiBee XML — popis formátu](https://www.flexibee.eu/api/dokumentace/xml-2/)
- [Referenční dokumentace evidencí](https://www.flexibee.eu/api/dokumentace/ref/)
- [Changes API (podpora.flexibee.eu)](https://podpora.flexibee.eu/cs/articles/4744362-changes-api)
- [WebHooks (podpora.flexibee.eu)](https://podpora.flexibee.eu/cs/articles/4744379-web-hooks)
- [Dokumentace REST API — kolekce článků podpory](https://podpora.flexibee.eu/en/collections/2592813-rest-api-documentation)

> **Poznámka:** Konkrétní pole evidencí se mohou mezi verzemi Flexi mírně lišit — před nasazením integrace si vždy ověřte strukturu přes `properties.xml` a chování přes `dry-run=true` na testovací firmě (`https://demo.flexibee.eu/c/demo`).
