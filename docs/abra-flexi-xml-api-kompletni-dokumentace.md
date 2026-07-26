# ABRA Flexi XML API — kompletní praktická dokumentace

> Česká referenční příručka pro návrh, implementaci a provoz integrací. Stav zdrojů ověřen k 22. 7. 2026.

## Obsah

1. [Co přesně je ABRA Flexi XML API](#1-co-přesně-je-abra-flexi-xml-api)
2. [Adresy, zdroje a samodokumentace](#2-adresy-zdroje-a-samodokumentace)
3. [Autentizace, oprávnění a bezpečnost](#3-autentizace-oprávnění-a-bezpečnost)
4. [Základní XML kontrakt](#4-základní-xml-kontrakt)
5. [Datové typy](#5-datové-typy)
6. [Identifikátory a idempotence](#6-identifikátory-a-idempotence)
7. [Čtení dat](#7-čtení-dat)
8. [Filtrační jazyk](#8-filtrační-jazyk)
9. [Zápis, změna a mazání](#9-zápis-změna-a-mazání)
10. [Vnořené kolekce a položky dokladů](#10-vnořené-kolekce-a-položky-dokladů)
11. [Validace, odpovědi a chyby](#11-validace-odpovědi-a-chyby)
12. [Transakce a dávkové operace](#12-transakce-a-dávkové-operace)
13. [Přílohy a binární data](#13-přílohy-a-binární-data)
14. [Synchronizace: Changes API a webhooky](#14-synchronizace-changes-api-a-webhooky)
15. [XSD, XPath a XSLT](#15-xsd-xpath-a-xslt)
16. [Firmy, evidence a nejčastější strojové názvy](#16-firmy-evidence-a-nejčastější-strojové-názvy)
17. [Praktické XML a cURL vzory](#17-praktické-xml-a-curl-vzory)
18. [Výkon, robustnost a bezpečný provoz](#18-výkon-robustnost-a-bezpečný-provoz)
19. [Implementační checklist](#19-implementační-checklist)
20. [Autoritativní zdroje](#20-autoritativní-zdroje)

---

## 1. Co přesně je ABRA Flexi XML API

ABRA Flexi zpřístupňuje účetní data přes HTTP rozhraní, které se běžně označuje jako REST API. Nativním datovým modelem přenosu je **ABRA Flexi XML**. Stejný logický model lze serializovat také jako JSON; XML atribut se v JSON zpravidla zapisuje klíčem se zavináčem, například XML `rowCount="10"` odpovídá JSON `"@rowCount":"10"`.

Nejdůležitější vlastnost: **neexistuje jeden neměnný univerzální kontrakt všech evidencí**. Dostupná pole a operace závisí na:

- verzi ABRA Flexi;
- licenci a variantě produktu;
- české/slovenské legislativě a typu organizace;
- daňové evidenci versus podvojném účetnictví;
- přihlášeném uživateli a jeho právech;
- konkrétní evidenci a někdy typu dokladu.

Proto musí produkční integrace kombinovat tuto obecnou příručku se **samodokumentací konkrétní cílové instance**. Oficiální dokumentace výslovně upozorňuje, že XSD je vývojové a server může vytvořit XML, které mu zcela neodpovídá. Autoritou pro konkrétní nasazení jsou endpointy `evidence-list`, `properties`, `relations` a schémata generovaná daným serverem.

### 1.1 Základní principy

- Kořen dokumentu je obvykle `<winstrom version="1.0">`.
- Strojové názvy evidencí jsou malými písmeny a slova odděluje pomlčka: `faktura-vydana`.
- Pole záznamu používají camelCase: `typDokl`, `datVyst`, `sumCelkem`.
- Názvy jsou case-sensitive.
- Čtení používá `GET`; zápis `PUT` nebo `POST`; smazání detailu `DELETE`.
- Flexi mezi `PUT` a `POST` u běžného importu významově zásadně nerozlišuje. Rozhoduje cílová URL, obsah a identifikátor.
- Zápis je inkrementální: nepřítomné pole se nemění, prázdný element zpravidla stávající hodnotu vymaže.
- Záznam může být adresován interním ID, kódem, UUID/klíčem, externím ID nebo doménovým identifikátorem.
- Vazby se obvykle zapisují textovým identifikátorem, například `<mena>code:CZK</mena>`.
- Výchozí import je jedna databázová transakce: buď se uloží vše, nebo nic.

---

## 2. Adresy, zdroje a samodokumentace

### 2.1 Základ URL

```text
https://{server}:{port}/c/{firma}/{evidence}/{identifikator}.{format}
```

Příklad:

```text
https://demo.flexibee.eu/c/demo/faktura-vydana/15.xml
```

`{firma}` je databázový identifikátor společnosti, nikoli její zobrazovaný název. Na vlastním serveru bývá výchozí HTTPS port `5434`, ale port je konfigurovatelný. V cloudu může být port skrytý za standardním HTTPS.

Koncovka je volitelná. Pokud chybí, server zohlední hlavičku `Accept`; při běžném otevření v prohlížeči může vrátit HTML. Pro integrační klient je nejméně dvojznačné uvádět `.xml` i hlavičky.

### 2.2 Mapa obecných cest

| Účel | Metoda | Cesta |
|---|---:|---|
| Seznam firem serveru | GET | `/c.xml?limit=0` |
| Web firmy | GET | `/c/{firma}` |
| Seznam všech evidencí | GET | `/c/{firma}/evidence-list` |
| Výpis evidence | GET | `/c/{firma}/{evidence}.xml` |
| Filtrovaný výpis | GET | `/c/{firma}/{evidence}/({filtr}).xml` |
| Detail záznamu | GET | `/c/{firma}/{evidence}/{id}.xml` |
| Popis polí evidence | GET | `/c/{firma}/{evidence}/properties` |
| Popis relací evidence | GET | `/c/{firma}/{evidence}/relations` |
| Exportní XSD evidence | GET | `/c/{firma}/{evidence}/schema-export.xsd` |
| Importní XSD evidence | GET | `/c/{firma}/{evidence}/schema-import.xsd` |
| Součet evidence | GET | `/c/{firma}/{evidence}/$sum.xml` |
| Složitý čtecí dotaz v body | POST | `/c/{firma}/{evidence}/query.xml` |
| Import více záznamů | PUT/POST | `/c/{firma}/{evidence}.xml` nebo firemní importní URL dle verze |
| Změna konkrétního záznamu | PUT/POST | `/c/{firma}/{evidence}/{id}.xml` |
| Smazání záznamu | DELETE | `/c/{firma}/{evidence}/{id}.xml` |
| Metadata příloh | GET | `/c/{firma}/{evidence}/{id}/prilohy` |
| Binární obsah přílohy | GET | `/c/{firma}/{evidence}/{id}/prilohy/{pid}/content` |
| Vložení binární přílohy | PUT | `/c/{firma}/{evidence}/{id}/prilohy/new/{nazev}` |
| Změnový žurnál | GET | `/c/{firma}/changes.xml` |
| Stav Changes API | GET | `/c/{firma}/changes/status.xml` |
| Zapnutí/vypnutí Changes API | PUT/POST | `/c/{firma}/changes/enable.xml`, `/disable.xml` |
| Správa webhooků | GET/PUT/POST | `/c/{firma}/hooks` |
| Smazání webhooku | DELETE | `/c/{firma}/hooks/{id}` |
| Opakování webhooku | PUT | `/c/{firma}/hooks/{id}/retry` |

U některých serverových verzí lze pro samodokumentaci použít také `/devdoc`. Konkrétní obchodní služby mají vlastní podcesty, například akce nad dokladem; jejich úplný aktuální seznam je v referenční dokumentaci dané instance a v oficiální kolekci API.

### 2.3 Jak získat skutečný kontrakt konkrétní evidence

1. Otevřít `/c/{firma}/evidence-list` a najít **strojový název** evidence.
2. Na `/c/{firma}/{evidence}/properties` získat pole, typy, editovatelnost, povinnost, omezení a vazby dostupné danému uživateli.
3. Na `/c/{firma}/{evidence}/relations` zjistit exportovatelné podevidence/relace.
4. Stáhnout `schema-import.xsd` a `schema-export.xsd` zvlášť.
5. Vyexportovat jeden reprezentativní záznam s `detail=full`; první záznam bývá doplněn vysvětlujícími XML komentáři.
6. Kontrakt archivovat spolu s verzí Flexi, legislativou, identifikátorem firmy a identitou/rolí uživatele, pod kterým byl získán.
7. Po upgradu Flexi kontrakt znovu stáhnout a porovnat.

Tento postup je spolehlivější než ručně udržovaný globální seznam stovek polí.

### 2.4 Formáty a content negotiation

| Formát | Přípona | Content-Type | Import | Poznámka |
|---|---|---|---:|---|
| XML | `.xml` | `application/xml` | ano | Nativní hierarchický formát této příručky. |
| JSON | `.json`, `.js` | `application/json`, `text/javascript` | ano | Stejný logický model; XML atributy mají zpravidla prefix `@`. |
| CSV | `.csv` | `text/csv` | ano | Plochý formát; neumí v jednom výstupu vnořené kolekce. |
| DBF | `.dbf` | `application/dbf` | ano | Starší tabulková výměna. |
| XLS | `.xls` | `application/ms-excel` | ano | Tabulkový import/export. |
| ISDOC/ISDOCX | `.isdoc`, `.isdocx` | `application/x-isdoc`, `application/x-isdocx` | ano | Faktury; import vyžaduje parametry jako `typDokl`, případně `typUcOp`. |
| EDI INHOUSE | `.edi` | `application/x-edi-inhouse` | ano | Elektronická výměna dokladů. |
| PDF | `.pdf` | `application/pdf` | ne | Tisková sestava, ne datový kontrakt. |
| vCard | `.vcf` | `text/vcard` | ne | Export kontaktů/adresáře. |
| iCalendar | `.ical` | `text/calendar` | ne | Události a termíny splatnosti. |
| HTML | `.html` | `text/html` | ne | Webové zobrazení, ne integrační formát. |

Přípona výstupu má přednost před `Accept`. Vstupní formát primárně určuje `Content-Type`. CSV/DBF podporují volbu kódování, například `encoding=iso-8859-2`; u XML používat UTF-8. Při XML importu přílohy může server vynutit XML komunikaci bez ohledu na původně očekávanou JSON odpověď.

### 2.5 Přehled společných URL parametrů

| Parametr | Účinek |
|---|---|
| `detail=id|summary|full|custom:...` | Rozsah polí. |
| `limit`, `start` | Stránkování. |
| `order=field[@D]` | Řazení; parametr lze opakovat. |
| `add-row-count=true` | Celkový počet záznamů po filtraci. |
| `relations=...` | Export vybraných podevidencí/relací. |
| `includes=...` | Vložení odkazovaných objektů. |
| `no-ext-ids=true` | Bez externích ID; výkonová optimalizace. |
| `only-ext-ids=true` | Exportovat pouze externí identifikátory. |
| `no-ids=true` | Potlačit primární/interní identifikátory; přesný dosah ověřit na verzi serveru. |
| `code-as-id=true` | Doplnit unikátní kód jako `<id>code:…</id>`. |
| `use-ext-id=A,B` | Preferovat externí ID z vyjmenovaných systémů jako vazební. |
| `use-internal-id=true` | Doplnit `internalId` k exportované vazbě. |
| `no-comments=true` | Potlačit vysvětlující XML komentáře. |
| `mode=simple` | Minimalistický výstup bez prezentačních atributů a XML komentářů. |
| `mode=xml_import_export` | Přenosový režim s hybridními ID. |
| `access-attribs=true` | Doplnit editovatelnost/mazatelnost/vložitelnost. |
| `dry-run=true` | Validovat a vypočítat bez uložení. |
| `fail-on-warning=true` | Neuložit při varování. |
| `code-in-response=true` | Ve výsledku zápisu vrátit také kód. |
| `add-global-version=true` | Přidat verzi Changes API snapshotu. |
| `no-http-errors=true` | Převést některé 4xx na 200; kompatibilní, ale rizikové. |
| `filtrovat-platnost=false` | Vypnout implicitní filtr platnosti účetního období. |
| `xpath=...` | Oříznout výsledné XML výrazem XPath. |
| `format=...` | Aplikovat vestavěnou nebo uživatelskou XSLT. |
| `report-name`, `report-lang`, `report-sign` | Volby PDF/tiskového výstupu. |
| `auth=http|html` | Vynutit způsob přihlášení. |

Booleovský parametr lze u řady verzí zkrátit pouhou přítomností, například `?no-comments`; pro čitelnost integrační konfigurace je vhodnější explicitní `=true`.

---

## 3. Autentizace, oprávnění a bezpečnost

### 3.1 HTTP Basic

Nejběžnější integrační mechanismus je HTTP Basic Authentication:

```bash
curl --user "$FLEXI_USER:$FLEXI_PASSWORD" \
  -H 'Accept: application/xml' \
  'https://server.example/c/firma/adresar.xml?limit=1'
```

Pokud autodetekce REST volání selže, lze přidat `?auth=http`. Přihlašovací údaje vkládané přímo do URL jsou nevhodné: mohou skončit v logu, historii shellu, proxy nebo monitoringu.

### 3.2 Autentizační relace

Přihlášení relace probíhá přes JSON-only endpoint:

```text
POST /login-logout/login.json
Content-Type: application/json

{"username":"novak","password":"heslo","otp":"volitelne"}
```

Úspěch vrátí `success` a `authSessionId`. Token lze předávat:

- v cookie `authSessionId`;
- v hlavičce `X-authSessionId` — doporučená varianta;
- v query parametru `authSessionId` — nedoporučeno, protože se zapisuje do logů.

Relaci lze udržovat voláním `GET /login-logout/session-keep-alive.js`. Oficiální dokumentace uvádí, že volání jednou za 30 minut by mělo stačit. SAMLv2/OpenID jsou závislé na licenci a lokální instalaci.

### 3.3 Práva a licence

Schéma i dostupná data jsou omezená právy přihlášeného uživatele. Typické stavové kódy:

- `401` — uživatel není přihlášen;
- `402` — není aktivní licence REST zápisu; u čtení může stejný stav působit jako `404`;
- `403` — uživatel nebo licence operaci nepovoluje;
- `404` — zdroj či záznam neexistuje, byl smazán, nebo je z licenčních důvodů skryt.

### 3.4 Bezpečnostní minimum

- Vždy HTTPS; nevypínat kontrolu certifikátu mimo jednorázový lokální test.
- Samostatný technický účet s minimální rolí.
- Tajemství mimo zdrojový kód, URL a aplikační logy.
- Maskovat `Authorization`, `X-authSessionId`, `authSessionId` a `X-FB-Hook-SecKey`.
- Pro webhook ověřovat tajný klíč, omezit zdrojovou síť, chránit se proti opakovanému doručení a rychle vracet `2xx`.
- Nepoužívat `no-http-errors=true`, pokud klient současně spolehlivě nekontroluje `<success>` a chybové struktury.

---

## 4. Základní XML kontrakt

### 4.1 Obálka

```xml
<?xml version="1.0" encoding="UTF-8"?>
<winstrom version="1.0">
  <!-- jeden nebo více záznamů -->
</winstrom>
```

Element evidence je přímým potomkem `winstrom`:

```xml
<winstrom version="1.0">
  <adresar>
    <id>ext:CRM:customer-42</id>
    <kod>ACME</kod>
    <nazev>ACME s.r.o.</nazev>
  </adresar>
</winstrom>
```

Pro více záznamů se element evidence opakuje. XML nemá povinný globální namespace. Pořadí polí uvnitř záznamu není důležité: server kvůli vnitřním závislostem skládá pořadí aplikace hodnot sám. **Pořadí jednotlivých záznamů ale důležité být může** — například nejprve založit firmu a až potom doklad, který na ni odkazuje.

### 4.2 Atributy kořenového elementu

| Atribut | Význam |
|---|---|
| `version="1.0"` | Verze formátu obálky. |
| `atomic="true|false"` | Jedna transakce pro celý import, nebo transakce po kořenovém záznamu. Výchozí `true`. |
| `globalVersion="…"` | Na exportu při `add-global-version=true`; verze změnového žurnálu. |
| `rowCount="…"` | Na seznamu při `add-row-count=true`; celkový počet po filtraci. |

### 4.3 Běžné atributy záznamu a kolekce

| Atribut | Umístění | Význam |
|---|---|---|
| `id="123"` | záznam | Zkrácená identifikace; ekvivalent `<id>123</id>`. |
| `action="delete"` | záznam | Smazání existujícího záznamu. |
| `action="storno"` | doklad | Storno dokladu. |
| `create="ok|ignore|fail"` | záznam | Co dělat, pokud záznam neexistuje. |
| `update="ok|ignore|fail"` | záznam | Co dělat, pokud záznam existuje. |
| `filter="…"` | záznam | Dávková operace nad všemi shodnými záznamy; `id` se ignoruje. |
| `removeExternalIds="prefix"` | záznam/kolekce | Odebrání externích ID daného prefixu. |
| `removeAll="true"` | kolekce | Odstraní existující členy neuvedené v importu. |
| `if-not-found="null|nearest-invalid|create"` | relační pole | Chování, pokud cílový záznam vazby nebyl nalezen. |
| `encoding="base64"` | obsah přílohy | Tělo elementu je Base64. |

Na exportu se mohou objevit prezentační atributy `ref` a `showAs`. Pro import je nepovažujte za autoritativní; zapisuje se hodnota elementu. `mode=simple` je odstraňuje. Parametr `access-attribs=true` může doplnit `editable`, `deletable` a `insertable`.

### 4.4 Kontrakt čtecí odpovědi

```xml
<winstrom version="1.0" rowCount="2">
  <adresar>
    <id>1</id>
    <kod>ACME</kod>
    <nazev>ACME s.r.o.</nazev>
    <stat ref="/c/firma/stat/1" showAs="Česká republika">code:CZ</stat>
  </adresar>
  <adresar>
    <id>2</id>
    <kod>EXAMPLE</kod>
    <nazev>Example a.s.</nazev>
  </adresar>
</winstrom>
```

### 4.5 Kontrakt zápisové odpovědi

Moderní odpověď může obsahovat souhrn a výsledky:

```xml
<winstrom version="1.0">
  <success>true</success>
  <stats>
    <created>1</created>
    <updated>0</updated>
    <deleted>0</deleted>
    <skipped>0</skipped>
    <failed>0</failed>
  </stats>
  <results>
    <result>
      <id>804</id>
      <ref>/c/firma/adresar/804.xml</ref>
    </result>
  </results>
</winstrom>
```

Starší či jiný kontext může vrátit jednotlivé `<result>` přímo bez obalového `<results>`. Klient by měl tolerovat obě podoby, kontrolovat HTTP status i hodnotu `success` a nespoléhat pouze na jedno pole.

---

## 5. Datové typy

Flexi v samodokumentaci používá tyto základní strojové typy:

| Typ | XML reprezentace | Pravidla a příklad |
|---|---|---|
| `string` | text elementu | Unicode; `<nazev>Žluťoučký kůň</nazev>`. XML znaky musí být escapované. |
| `integer` | desítkové celé číslo | Podepsané 4 bajty, bez mezer; konkrétní pole může rozsah dále omezit. `<mnozMj>12</mnozMj>`. |
| `numeric` | desítkové číslo | Tečka jako oddělovač, bez mezer; interně 8bajtové `double`, takže pro peněžní mezivýpočty na straně klienta používat decimal. `<cenaMj>12.50</cenaMj>`. |
| `date` | `YYYY-MM-DD[ZZZ]` | `<datVyst>2026-07-22</datVyst>`; zóna `Z`/`±HH:MM` se přijme, ale ignoruje. Filtr používá datum bez zóny. |
| `datetime` | ISO-like | `YYYY-MM-DD'T'HH:MM:SS[.SSS][ZZZ]`; zóna se přijme, ale ignoruje. Filtr podporuje jen dokumentované varianty bez zóny. |
| `logic` / boolean | `true` nebo `false` | Malými písmeny; `<storno>false</storno>`. |
| `select` | řetězec z číselníku | `<typVztahuK>typVztahu.odberDodav</typVztahuK>`. Povolené hodnoty zjistit z `properties`. |
| `relation` | identifikátor jiného záznamu | `<mena>code:CZK</mena>` nebo `<firma>123</firma>`. |

### 5.1 Null, prázdná hodnota a nepřítomnost

Tyto tři stavy se zásadně liší:

- element chybí: při update se pole nemění;
- element je prázdný, například `<ean/>`: hodnota se odstraní/nastaví na prázdnou, dovoluje-li to pole;
- element obsahuje hodnotu: hodnota se nastaví.

U povinného pole prázdná hodnota vyvolá validaci. U kolekcí neznamená prázdná kolekce automaticky „smaž vše“; k nahrazení celé kolekce slouží `removeAll="true"`.

### 5.2 Číselníkové hodnoty

Hodnoty typu `select` jsou obvykle kvalifikované řetězce, například `typPrilohy.ostatni`. Nehádat je podle českého popisku. Vždy použít strojovou hodnotu ze samodokumentace, exportu nebo odpovídajícího číselníku.

### 5.3 Peníze, sazby a výpočty

Doklady obsahují mnoho odvozených částek. Jejich zapisovatelnost a priorita se liší podle typu dokladu a nastavení výpočtu DPH. Obecné pravidlo:

- posílat vstupní údaje, které by uživatel zadal v aplikaci;
- neimportovat slepě všechny exportované součty;
- před ostrým uložením použít `dry-run=true` a zkontrolovat serverem dopočtený obsah;
- importní pole vždy ověřit v `schema-import.xsd`/`properties`.

---

## 6. Identifikátory a idempotence

### 6.1 Podporované formy

| Druh | Syntaxe | Poznámka |
|---|---|---|
| Interní ID | `123` | Neměnné, přiděluje Flexi. Odkaz na neexistující ID je chyba. |
| Kód/zkratka | `code:CZK` | Uživatelsky měnitelný; musí být unikátní tam, kde jej evidence podporuje. |
| Klíč/UUID | `key:550e…` | Náhodný neměnný klíč přidělený Flexi. Některé starší příklady používají i označení UUID. |
| PLU | `plu:4020` | Typicky ceník/prodejní kasa. |
| EAN | `ean:4710937332698` | Ceník; může hledat i EAN balení. |
| Externí ID | `ext:SHOP:123` | Doporučené pro integrace; unikátní v rámci evidence. |
| Hybridní ID | `ws:{uuid-firmy}:{interni-id}` | V původní firmě se chová jako interní ID, jinde jako externí. |
| DIČ | `vatid:CZ28019920` | Doménový identifikátor firmy. |
| IČO | `in:28019920` | Doménový identifikátor firmy. |
| IBAN | `iban:CZ…` | Doménový identifikátor bankovního účtu. |

Poznámka: přesný rozsah identifikátorů závisí na evidenci.

### 6.2 Create-or-update

Na URL seznamu platí:

- interní ID musí existovat, jinak chyba;
- jiný identifikátor (`code:`, `ext:`…) aktualizuje nalezený záznam;
- není-li podle neinterního identifikátoru nic nalezeno, záznam se obvykle založí.

Tím lze dosáhnout idempotentního importu:

```xml
<winstrom version="1.0">
  <adresar>
    <id>ext:CRM:customer-42</id>
    <nazev>ACME s.r.o.</nazev>
  </adresar>
</winstrom>
```

Opakované odeslání aktualizuje stejný záznam, nevytvoří duplikát.

### 6.3 Více identifikátorů

V importním XML lze uvést více `<id>`:

```xml
<cenik>
  <id>123</id>
  <id>code:KRABICE</id>
  <id>ext:SHOP:sku-99</id>
</cenik>
```

Všechny existující identifikátory musí ukazovat na tentýž záznam. Neexistující se ignorují a mohou se připojit. Mimo opakované XML elementy se používá složená syntaxe `[123][code:KRABICE][ext:SHOP:sku-99]`; hranaté závorky a zpětné lomítko uvnitř hodnoty je nutné escapovat a v URL navíc percent-enkódovat.

### 6.4 Odebrání externích ID

```xml
<cenik removeExternalIds="ext:OLD-SYSTEM">
  <id>123</id>
  <id>ext:SHOP:sku-99</id>
</cenik>
```

Hodnota je prefix. Prázdný řetězec odebere všechna externí ID. Operaci používat opatrně: externí ID může být synchronizační klíč jiné integrace.

### 6.5 Doporučení

- Pro každý zdrojový systém vyhradit stabilní namespace, například `ext:ESHOP:{id}`.
- Externí ID přidělit i položkám dokladů, ne jen hlavičce.
- Interní ID ukládat jako technickou cache, ne jako jediný integrační klíč při migraci mezi firmami.
- Nevytvářet externí ID z měnitelného údaje, například e-mailu.
- Při konfliktu více ID import zastavit; nesnažit se automaticky „uhodnout“ správný záznam.

---

## 7. Čtení dat

### 7.1 Detail

Parametr `detail` ovlivňuje XML, JSON, XLS a CSV:

| Hodnota | Obsah |
|---|---|
| `id` | primární a externí identifikátory |
| `summary` | základní přehled, typicky `id`, `lastUpdate`, `kod`, `nazev` |
| `full` | pole základního záznamu |
| `custom:a,b,c` | `id` plus vyjmenovaná pole |

Výchozí detail seznamu je `summary`, detailu jednoho záznamu `full`.

```text
/c/firma/adresar.xml?detail=custom:kod,nazev,ic,email
```

Vnořené kolekce lze omezit závorkami:

```text
?detail=custom:kod,sady-a-komplety(cenik,cenikSada)
```

Neznámá vlastnost v `custom` se ignoruje, což může maskovat překlep. Proto je vhodné testovat proti `properties`.

### 7.2 Relace a includes

`relations` přidává zvláštní kolekce:

```text
?relations=vazby,prilohy,polozky
```

Časté hodnoty jsou `vazby`, `prilohy`, `polozky`, `sklad-karty`; dostupnost zjistí `/relations`. Tyto exportní relace nejsou automaticky importním kontraktem.

`includes` vloží celý odkazovaný objekt namísto pouhé reference:

```text
?includes=/adresar/stat/,/adresar/stredisko/
```

Lze kombinovat s vnořeným `custom` detailem. Používat střídmě: každý include rozšiřuje dotaz a payload.

### 7.3 Stránkování

| Parametr | Význam |
|---|---|
| `limit` | Počet záznamů; výchozí `20`, hodnota `0` znamená bez limitu. |
| `start` | Počet přeskočených záznamů; výchozí `0`. |
| `add-row-count=true` | Přidá `rowCount`; vyžaduje další databázový dotaz. |

```text
/c/firma/adresar.xml?limit=100&start=200&add-row-count=true
```

V produkci vždy explicitně řadit. Bez stabilního řazení se při souběžných změnách mohou offsetové stránky překrýt nebo něco přeskočit. Pro velké synchronizace preferovat Changes API.

### 7.4 Řazení

```text
?order=datVyst@D&order=id
```

Opakované `order` určuje priority. Bez přípony je řazení vzestupné, `@D` znamená sestupně. Alternativní kompatibilní forma je `sort=nazev&dir=ASC|DESC`. Lze řadit i podle relační vlastnosti první úrovně, například `order=stredisko.nazev`.

### 7.5 Součty

```text
/c/firma/faktura-vydana/$sum.xml
/c/firma/faktura-vydana/(storno=false)/$sum.xml
```

Sumace se používá u dokladových evidencí. Některé účetní výstupy vyžadují parametry `period`, `fields` a `group-by`:

```text
$sum.xml?period=(rokMesic,2026-01-01,2026-12-31)&fields=obrDal,obrMd&group-by=rokMesic
```

### 7.6 `/query`

Když je URL s filtrem příliš dlouhá nebo se obtížně escapuje, lze parametry předat tělem POST:

```text
POST /c/firma/faktura-vydana/query.xml
Content-Type: application/xml
Accept: application/xml
```

XML varianta logicky používá položky obálky analogické JSON dokumentaci serveru; dostupnost a přesný XML tvar ověřit na cílové verzi. U široce používané JSON varianty jsou v `winstrom` klíče `detail`, `includes`, `filter`, `limit`, `start` a `order`. `/query` je čtecí operace, přestože používá POST.

### 7.7 Podmíněné čtení

Server podporuje `If-Modified-Since`; při nezměněném zdroji může vrátit `304 Not Modified`. Každý běžný záznam obsahuje `lastUpdate`, ale pro bezchybnou delta synchronizaci je vhodnější Changes API, protože samotné filtrování podle času hůře zachycuje smazání a souběh.

---

## 8. Filtrační jazyk

Filtr je v cestě uzavřený v závorkách:

```text
/c/firma/faktura-vydana/(datVyst>=2026-01-01 and storno=false).xml
```

Celý výraz musí být správně URL-enkódován.

### 8.1 Operátory

| Skupina | Operátory |
|---|---|
| Rovnost | `=`, `==`, `eq` |
| Nerovnost | `<>`, `!=`, `ne`, `neq` |
| Porovnání | `<`, `lt`, `<=`, `lte`, `>`, `gt`, `>=`, `gte` |
| Text | `like`, `like similar`, `begins`, `begins similar`, `ends` |
| Rozsah/seznam | `between`, `in` |
| Strom | `in subtree`, volitelně `nonrecursive` |
| Boolean | `is true`, `is false` |
| Null | `is null`, `is not null` |
| Prázdnost | `is empty`, `is not empty` |
| Logika | `not`, `and`, `or`, závorky |

`similar` ignoruje diakritiku na podporované verzi PostgreSQL. `is empty` je širší než `is null`: zahrnuje také nulu, `false` či prázdný řetězec.

Priorita je: porovnávací operátory, `not`, `and`, `or`. Pro čitelnost používat závorky.

### 8.2 Literály a funkce

- číslo: `10`, `-5.8`;
- text: `'ABC'` nebo `"ABC"`;
- boolean: `true`, `false`;
- datum: `2026-07-22`;
- datum a čas: `2026-07-22T14:30:00` nebo s milisekundami;
- `now()` — aktuální datum/čas;
- `currentYear()` — aktuální rok;
- `me()` — přihlášený uživatel.

Příklad:

```text
(datSplat < now() and storno is false)
```

### 8.3 Vazby a vnořené vlastnosti

```text
firma = 'code:ACME'
firma.skupFir = 'code:VIP'
udalost.zakazka.mistUrc.mesto = 'Praha'
```

Kladné filtry přes jednoznačné vazby 1:1 lze řetězit hluboko. Negativní operátory nad relačním poddotazem mohou skončit chybou `OR logical subselect filter not supported`; bezpečnější je negovat celou podmínku:

```text
not(typDokl.typDoklK eq 'typDokladu.dobropis')
```

Kolekci 1:N, například položky faktury, filtrujte přímo v evidenci položek:

```text
/c/firma/faktura-vydana-polozka/(doklFak=123 and cenik='code:AUTO').xml
```

### 8.4 Štítky, strom a implicitní platnost

```text
stitky='code:VIP' or stitky='code:DULEZITE'
cenik in subtree 3
in subtree 7 nonrecursive
```

Evidence s `platiOd`/`platiDo` mohou být implicitně filtrovány aktuálním účetním obdobím. Potlačení:

```text
?filtrovat-platnost=false
```

### 8.5 Bezpečné sestavování filtru

Filtr není SQL, ale i tak jej neskládejte prostou konkatenací nedůvěryhodného vstupu. Omezte povolená pole a operátory, escapujte uvozovky podle filtračního jazyka a následně percent-enkódujte celý path segment. Dlouhé dotazy posílejte přes `/query`.

---

## 9. Zápis, změna a mazání

### 9.1 HTTP metody a URL

- `PUT` a `POST` na URL seznamu: vytvoření nebo změna podle identifikátoru; lze poslat více záznamů.
- `PUT` a `POST` na detailu: změna konkrétního existujícího záznamu; identifikátor v body není nutný.
- `DELETE` na detailu: smazání jednoho záznamu.
- `POST` není formulářový submit; body má být XML/JSON, ne `multipart/form-data`.

Hlavičky:

```http
Content-Type: application/xml; charset=UTF-8
Accept: application/xml
```

Vstupní formát primárně určuje `Content-Type`; koncovka/`Accept` určují výstup. U běžného uložení je vstupní a výstupní formát stejný.

### 9.2 Inkrementální update

```xml
<winstrom version="1.0">
  <cenik>
    <id>ext:SHOP:sku-99</id>
    <nazev>Nový název</nazev>
    <ean/>
  </cenik>
</winstrom>
```

Změní `nazev`, vymaže `ean`, ostatní pole ponechá. Interní závislosti však mohou přepočítat i neposlaná pole — typ dokladu, stát DPH či firma mohou změnit odvozené hodnoty.

### 9.3 Režim create/update

| Atribut | Hodnota | Chování |
|---|---|---|
| `create` | `ok` | neexistující záznam vytvořit; výchozí |
| `create` | `ignore` | neexistující záznam přeskočit |
| `create` | `fail` | při neexistenci selhat |
| `update` | `ok` | existující záznam změnit; výchozí |
| `update` | `ignore` | existující záznam přeskočit |
| `update` | `fail` | při existenci selhat |

Příklad „vytvoř jen jednou, změny uživatele nepřepisuj“:

```xml
<adresar update="ignore">
  <id>ext:CRM:customer-42</id>
  <nazev>ACME s.r.o.</nazev>
</adresar>
```

### 9.4 Nenalezená vazba

```xml
<firma if-not-found="null">code:ACME</firma>
```

| Režim | Chování |
|---|---|
| `null` | vazbu nenastaví |
| `nearest-invalid` | použije nejbližší historicky neplatný záznam k datu dokladu |
| `create` | pokusí se založit číselníkový záznam; nelze, pokud chybí další povinná pole |

Automatické `create` je pohodlné, ale může vytvářet nekvalitní číselníky. V účetní integraci je bezpečnější explicitní master-data fáze.

### 9.5 Akce

```xml
<faktura-vydana action="delete">
  <id>123</id>
</faktura-vydana>
```

Obecné akce:

- `delete` — smazání;
- `storno` — storno dokumentu.

Další akce jsou specifické pro evidence a verze, například zamykání nebo obchodní workflow. Získat je z referenční dokumentace konkrétní služby. U akce se záznam jinak nemění; posílat pouze identifikaci a případné parametry akce.

### 9.6 DELETE versus `action="delete"`

- HTTP `DELETE` cílí jeden detail v URL.
- `action="delete"` je součást importního XML, funguje v dávce a také u vnořených položek.
- Obě operace vyžadují existující záznam; obchodní/účetní omezení mohou fyzické smazání zakázat.

---

## 10. Vnořené kolekce a položky dokladů

### 10.1 Základní vzor

```xml
<winstrom version="1.0">
  <faktura-vydana>
    <id>ext:SHOP:invoice-1001</id>
    <typDokl>code:FAKTURA</typDokl>
    <firma>ext:CRM:customer-42</firma>
    <polozkyFaktury>
      <faktura-vydana-polozka>
        <id>ext:SHOP:invoice-1001:1</id>
        <nazev>Servisní práce</nazev>
        <mnozMj>2</mnozMj>
        <cenaMj>1250.00</cenaMj>
      </faktura-vydana-polozka>
    </polozkyFaktury>
  </faktura-vydana>
</winstrom>
```

Názvy kolekce i položkové evidence jsou specifické; u vydané faktury se běžně používá `polozkyFaktury` a `faktura-vydana-polozka`. Ověřit v `properties` a vzorovém exportu.

### 10.2 Přidávání a aktualizace položek

- položka s existujícím ID se aktualizuje;
- položka s neinterním ID se vytvoří nebo aktualizuje;
- položka bez ID se při aktualizaci zpravidla přidá;
- identifikace pouhou pozicí je křehká a může ponechat vazby u nesprávné původní položky.

### 10.3 Nahrazení celé kolekce

```xml
<polozkyFaktury removeAll="true">
  <faktura-vydana-polozka>
    <id>ext:SHOP:invoice-1001:1</id>
    <nazev>Jediná ponechaná položka</nazev>
  </faktura-vydana-polozka>
</polozkyFaktury>
```

Všechny existující položky neuvedené v importu se odstraní. Používat jen tehdy, když je zdrojový systém autoritou celé kolekce.

### 10.4 Smazání jedné položky

```xml
<faktura-vydana>
  <id>123</id>
  <polozkyFaktury>
    <faktura-vydana-polozka id="456" action="delete"/>
  </polozkyFaktury>
</faktura-vydana>
```

Položku nelze vždy mazat přes samostatný root endpoint; dokumentace ji často označuje `NOT_DIRECT`. Pak musí být změna provedena přes rodičovský dokument.

---

## 11. Validace, odpovědi a chyby

### 11.1 Tři úrovně validace

- `error`: záznam nelze uložit; operace končí neúspěchem;
- `warning`: problém, ale záznam se běžně uloží;
- `info`: doplňující informace, záznam se uloží.

`?fail-on-warning=true` změní varování na důvod k neuložení.

### 11.2 Dry run

```text
?dry-run=true
```

Server provede výpočty a validace, ale transakci neuloží. Odpověď může v `<result><content>` obsahovat podobu výsledného záznamu. Číslo dokumentu přidělené v dry-run se u ostrého zápisu může změnit.

Dry run je vhodný pro:

- kontrolu povinných polí a vazeb;
- náhled DPH a dopočtených částek;
- zobrazení varování uživateli;
- ověření kontraktu po upgradu.

Není náhradou ostrého testu souběhu: mezi dry-run a zápisem se mohou data změnit.

### 11.3 Chybová odpověď

```xml
<winstrom version="1.0">
  <success>false</success>
  <stats>
    <created>0</created>
    <updated>0</updated>
    <deleted>0</deleted>
    <skipped>0</skipped>
    <failed>1</failed>
  </stats>
  <results>
    <result>
      <errors>
        <error for="kod" code="INVALID">Zkratku již používá jiný záznam.</error>
      </errors>
    </result>
  </results>
</winstrom>
```

Parser musí počítat s jedním i více `result`, `error`, `warning` a `info`. Text je lokalizovaný; automatiku řídit HTTP statusem, `success`, `stats`, atributem `code` a `for`, ne přes přesné znění zprávy.

### 11.4 HTTP stavové kódy

| Kód | Význam v API |
|---:|---|
| `200 OK` | Operace dokončena; přesto zkontrolovat XML `success`. |
| `201 Created` | Záznam vytvořen; `Location` obsahuje URL nového záznamu. |
| `304 Not Modified` | Podmíněný GET a zdroj se nezměnil. |
| `400 Bad Request` | Neplatný vstup, reference, filtr nebo validace zápisu. |
| `401 Unauthorized` | Nutné přihlášení. |
| `402 Payment Required` | Není aktivní REST zápis v licenci. |
| `403 Forbidden` | Chybí uživatelské/licenční oprávnění. |
| `404 Not Found` | Evidence/záznam neexistuje, byl smazán nebo je skryt. |
| `405 Method Not Allowed` | Zdroj nepovoluje metodu. |
| `406 Not Acceptable` | Zdroj nepodporuje požadovaný formát. |
| `500 Internal Server Error` | Interní chyba serveru; nereinterpretovat jako validační chybu. |

Parametr `no-http-errors=true` může změnit 4xx na `200`; používat jen kvůli starým klientům a vždy zpracovat tělo.

### 11.5 Retry politika

- `400`, `401`, `402`, `403`, `404`, `405`, `406`: bez změny požadavku obvykle neopakovat.
- timeout/transportní chyba: opakovat pouze idempotentní čtení nebo zápis se stabilním externím ID.
- `500`: omezený exponenciální retry s jitterem; po opakování incident zaznamenat.
- při nejistém výsledku zápisu nejprve dohledat záznam externím ID; neposílat slepě create bez ID.

---

## 12. Transakce a dávkové operace

### 12.1 Atomický import

Výchozí chování:

```xml
<winstrom version="1.0" atomic="true">
  ...
</winstrom>
```

Celý import je jedna transakce. Chyba znamená rollback všeho. To je nejbezpečnější volba pro vzájemně závislé záznamy.

### 12.2 Transakce po záznamu

```xml
<winstrom version="1.0" atomic="false">
  <adresar>...</adresar>
  <adresar>...</adresar>
</winstrom>
```

Každý kořenový záznam má vlastní transakci; jeho vnořené položky zůstávají ve stejné transakci s rodičem. Výhoda: menší paměť a lepší výkon velkých nezávislých importů. Riziko: částečný úspěch a potenciální nekonzistence. Klient musí zpracovat výsledek každého záznamu a umět bezpečný replay.

### 12.3 Dávková změna podle filtru

```xml
<winstrom version="1.0">
  <cenik filter="dodavatel = 'code:FIRMA'">
    <stitky>VIP</stitky>
  </cenik>
</winstrom>
```

Operace se chová, jako by klient poslal jeden element pro každý nalezený záznam. Elementy `<id>` se v dávkové operaci ignorují. Lze kombinovat s akcí, například zamknout všechny odpovídající záznamy, pokud evidence akci podporuje.

Bezpečný postup:

1. stejný filtr nejprve spustit přes GET s `detail=custom:id,kod`;
2. uložit počet a vzorek cílových ID;
3. provést `dry-run=true`, pokud to operace podporuje;
4. až poté ostrý zápis;
5. výsledek auditovat.

---

## 13. Přílohy a binární data

### 13.1 Čtení

```text
GET /c/firma/adresar/12/prilohy
GET /c/firma/adresar/12/prilohy/75
GET /c/firma/adresar/12/prilohy/75/content
GET /c/firma/adresar/12/prilohy/75/thumbnail
```

`content` vrací binární data se správným `Content-Type`. `thumbnail` může vrátit `404`. Primární obrázek objektu lze u podporovaných evidencí získat například `/c/firma/cenik/12/thumbnail.png?w=200&h=200`.

### 13.2 Přímý binární upload

```http
PUT /c/firma/adresar/12/prilohy/new/foto.jpg
Content-Type: image/jpeg

<binární data>
```

Existující obsah přílohy nelze běžně přepsat; přílohu je nutné smazat a znovu vytvořit.

### 13.3 Příloha uvnitř XML

```xml
<winstrom version="1.0">
  <faktura-vydana>
    <id>11925</id>
    <prilohy>
      <priloha update="ignore">
        <id>ext:DMS:faktura-vydana:11925</id>
        <contentType>application/pdf</contentType>
        <nazSoub>faktura.pdf</nazSoub>
        <typK>typPrilohy.ostatni</typK>
        <content encoding="base64">JVBERi0xLjQK...</content>
      </priloha>
    </prilohy>
  </faktura-vydana>
</winstrom>
```

Omezení:

- nová příloha musí být vnořená do rodičovského objektu, ne kořenový záznam;
- obsah je Base64;
- metadata lze změnit, binární obsah existující přílohy ne;
- pro velké soubory je přímý binární endpoint úspornější než Base64 (Base64 zvětšuje data přibližně o třetinu).

JPEG, GIF a PNG podporují generování náhledů.

---

## 14. Synchronizace: Changes API a webhooky

### 14.1 Proč nepoužívat pouze `lastUpdate`

`lastUpdate` je užitečné pole a lze podle něj filtrovat, ale samotné časové okno obtížně řeší smazání, souběžné změny, časové hranice a konzistentní počáteční snapshot. Changes API poskytuje monotonicky rostoucí globální verzi a explicitní `create`, `update`, `delete`.

### 14.2 Aktivace a stav

```text
GET      /c/{firma}/changes/status.xml
PUT/POST /c/{firma}/changes/enable.xml
PUT/POST /c/{firma}/changes/disable.xml
```

Webová kontrola je na `/c/{firma}/changes/control`. Funkce vyžaduje odpovídající licenci.

### 14.3 Čtení změn

```text
GET /c/firma/changes.xml?start=123&limit=500&evidence=faktura-vydana
```

Parametry:

- `start` — verze včetně, od které číst;
- `limit` — výchozí `100`, maximum `1000`;
- `evidence` — lze opakovat pro více evidencí.

Tvar:

```xml
<winstrom version="1.0" globalVersion="106">
  <faktura-vydana in-version="104" operation="update"
                   timestamp="2026-07-22 10:11:12.3">
    <id>1</id>
    <id>code:VF-0001/2026</id>
    <id>ext:SHOP:invoice-1001</id>
  </faktura-vydana>
  <next>105</next>
</winstrom>
```

`operation` je `create`, `update` nebo `delete`. Verze jsou unikátní a rostou, ale nemusí být souvislé. `next` je pokračovací pozice nebo `none`.

### 14.4 Konzistentní iniciační synchronizace

1. Stáhnout počáteční data s `add-global-version=true`.
2. Data uložit atomicky ve vlastním systému.
3. Uložit `globalVersion` snapshotu.
4. Číst `/changes.xml?start={ulozena_verze}` po stránkách.
5. Pro create/update stáhnout aktuální detail; pro delete lokální záznam odstranit/označit.
6. Až po úspěšném zpracování celé dávky uložit checkpoint `next`.
7. Opakovat; zpracování musí být idempotentní.

Samotná změnová zpráva je oznámení, ne plný historický obraz záznamu. Mezi oznámením a detailním GET mohl záznam projít další změnou nebo být smazán; synchronizace má konvergovat k aktuálnímu stavu.

### 14.5 Webhooky

Registrace:

```text
PUT /c/{firma}/hooks?url=https://integrace.example/flexi-hook
    &format=XML
    &lastVersion=123
    &secKey=nahodne-dlouhe-tajemstvi
```

Volitelné `skipUrlTest=true` vypne registrační test cílové URL. Tajemství přichází v hlavičce `X-FB-Hook-SecKey`. Seznam je na `/hooks`, smazání `/hooks/{id}`, okamžitý retry `/hooks/{id}/retry`.

Provozní vlastnosti:

- Flexi posílá POST se souhrnem změn ve formátu Changes API.
- Hook je pro všechny evidence; serverový filtr při registraci není k dispozici.
- Registrace standardně proběhne jen při úspěšném testu s `2xx`.
- Při chybě se volání opakuje s rostoucí prodlevou/penalty.
- Mohou vzniknout zpoždění a duplicity; deduplikovat přes `globalVersion`/verzi změny.
- Handler má ideálně pouze ověřit, trvale uložit zprávu a rychle vrátit `2xx`; doporučeno pod 15 s, limit je 30 s.
- `301`/`308` může trvale aktualizovat URL; `410 Gone` hook zruší.

Nejspolehlivější architektura je webhook jako budíček a Changes API jako zdroj pravdy: po notifikaci načíst změny od posledního potvrzeného checkpointu.

---

## 15. XSD, XPath a XSLT

### 15.1 XSD

Pro jednu evidenci:

```text
/c/{firma}/{evidence}/schema-export.xsd
/c/{firma}/{evidence}/schema-import.xsd
```

Importní schéma vynechává needitovatelná pole, exportní popisuje výstup. XSD je pomocné, ne absolutní garance. Generovaný klient musí být tolerantní k doplnění nových elementů a atributů.

### 15.2 XPath na exportu

Pouze XML:

```text
/c/demo/adresar.xml?detail=full&xpath=//winstrom/adresar/email/text()
```

Pořadí zpracování je: filtr → stránkování → detail → XPath. XPath tedy nezvyšuje počet záznamů a nenahrazuje databázový filtr; pouze ořízne už vytvořené XML.

### 15.3 XSLT

Pouze XML. Parametr `format` vybere vestavěnou nebo uživatelskou transformaci:

```text
/c/demo/faktura-vydana.xml?format=awis-items
/c/demo/faktura-vydana.xml?format=code:moje-transformace
```

- při importu se nejprve aplikuje XSLT, výsledné Flexi XML se importuje;
- při exportu se nejprve aplikuje filtr, stránkování a detail, potom XSLT.

Transformaci verzovat stejně jako integrační kód. Chyba XSLT může změnit význam dat ještě před validací Flexi.

---

## 16. Firmy, evidence a nejčastější strojové názvy

### 16.1 Seznam firem

```text
GET /c.xml?limit=0
```

Odpověď používá obálku `<companies>` a záznam `<company>`. Důležitá pole:

- `dbNazev` — identifikátor do URL;
- `nazev` — zobrazovaný název;
- `createDt` — vytvoření;
- `show` — dostupnost;
- `stavEnum` — například `ESTABLISHING`, `ESTABLISHED`, `MAINTENANCE`;
- `watchingChanges` — stav Changes API.

Identifikátor firmy používá malá písmena, číslice a podtržítka; přejmenování firmy jej nemění. Obnova zálohy na stejném serveru může vytvořit jiný identifikátor.

### 16.2 Význam stavů importu v `evidence-list`

Server zobrazuje vedle strojového názvu také podporu importu. Praktická interpretace:

- `SUPPORTED` — přímý import podporován;
- `NOT_DIRECT` — typicky se zapisuje jako vnořená podevidence přes rodiče;
- `NOT_DOCUMENTED` — přímé chování není veřejně dokumentováno; ověřit na cílové instanci;
- `DISALLOWED` — přímý import není povolen.

Tyto hodnoty nejsou náhradou licenčních a uživatelských práv.

### 16.3 Orientační katalog často používaných evidencí

Úplný seznam je dynamický na `/c/{firma}/evidence-list`. Následující tabulka je navigační, nikoli náhrada živého seznamu.

| Oblast | Evidence / strojový název |
|---|---|
| Partneři | `adresar`, `kontakt`, `misto-urceni`, `adresar-bankovni-ucet`, `skupina-firem` |
| CRM | `udalost`, `typ-aktivity`, `naklad`, `typ-nakladu` |
| Prodej | `faktura-vydana`, `faktura-vydana-polozka`, `objednavka-prijata`, `objednavka-prijata-polozka`, `nabidka-vydana`, `poptavka-prijata`, `prodejka` |
| Nákup | `faktura-prijata`, `faktura-prijata-polozka`, `objednavka-vydana`, `objednavka-vydana-polozka`, `nabidka-prijata`, `poptavka-vydana` |
| Zboží/sklad | `cenik`, `skladova-karta`, `skladovy-pohyb`, `skladovy-pohyb-polozka`, `sklad`, `vyrobni-cislo`, `rezervace`, `sady-a-komplety`, `kusovnik` |
| Ceny | `dodavatel`, `odberatel`, `cenova-uroven`, `cenikova-skupina`, `poplatek` |
| Peníze | `banka`, `banka-polozka`, `pokladni-pohyb`, `pokladni-pohyb-polozka`, `prikaz-k-uhrade`, `prikaz-k-uhrade-polozka` |
| Účetnictví | `interni-doklad`, `interni-doklad-polozka`, `pohledavka`, `zavazek`, `ucet`, `stredisko`, `zakazka`, `cinnost`, `ucetni-obdobi` |
| Číselníky | `mena`, `stat`, `sazba-dph`, `merna-jednotka`, `forma-uhrady`, `konst-symbol`, `penezni-ustav` |
| Typy dokladů | `typ-faktury-vydane`, `typ-faktury-prijate`, `typ-objednavky-prijate`, `typ-objednavky-vydane`, `typ-skladovy-pohyb`, `typ-pokladni-pohyb`, `typ-banka` |
| Řady | `rada-faktury-vydane`, `rada-faktury-prijate`, `rada-objednavky-prijate`, `rada-skladovy-pohyb`, `rada-pokladni-pohyb` |
| Štítky/vazby | `stitek`, `skupina-stitku`, `uzivatelska-vazba`, `typ-uzivatelske-vazby`, `vazba` |
| Majetek | `majetek`, `majetek-udalost`, `leasing`, `umisteni`, `typ-majetku` |

Položkové evidence bývají `NOT_DIRECT`; zapisují se přes kolekci na rodičovském dokladu. Některé číselníky mají obecný strojový název v exportu, ale pro zápis dokumentu se používá modulově specifická evidence — vždy rozhoduje živá samodokumentace.

---

## 17. Praktické XML a cURL vzory

Všechny ukázky jsou šablony. Povinná pole a číselníky ověřit v cílové firmě.

### 17.1 Čtení adresáře

```bash
curl --fail-with-body --silent --show-error \
  --user "$FLEXI_USER:$FLEXI_PASSWORD" \
  -H 'Accept: application/xml' \
  'https://server.example/c/firma/adresar.xml?detail=custom:id,kod,nazev,ic,email&limit=100&order=id'
```

### 17.2 Bezpečně enkódovaný filtr s cURL

```bash
curl --get --fail-with-body \
  --user "$FLEXI_USER:$FLEXI_PASSWORD" \
  -H 'Accept: application/xml' \
  --data-urlencode 'detail=custom:id,kod,datVyst,sumCelkem' \
  --data-urlencode 'limit=100' \
  'https://server.example/c/firma/faktura-vydana/(datVyst>=2026-01-01%20and%20storno=false).xml'
```

Pozor: filtr je součást cesty, nikoli query parametr. Knihovna musí správně enkódovat path segment; výše je jen shellová ilustrace.

### 17.3 Vytvoření/aktualizace partnera

`adresar.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<winstrom version="1.0">
  <adresar>
    <id>ext:CRM:customer-42</id>
    <kod>ACME</kod>
    <nazev>ACME s.r.o.</nazev>
    <ic>12345678</ic>
    <dic>CZ12345678</dic>
    <email>uctarna@example.com</email>
    <stat>code:CZ</stat>
  </adresar>
</winstrom>
```

```bash
curl --fail-with-body \
  --user "$FLEXI_USER:$FLEXI_PASSWORD" \
  -X PUT \
  -H 'Content-Type: application/xml; charset=UTF-8' \
  -H 'Accept: application/xml' \
  --data-binary @adresar.xml \
  'https://server.example/c/firma/adresar.xml?fail-on-warning=true'
```

### 17.4 Testovací uložení faktury

```bash
curl --fail-with-body \
  --user "$FLEXI_USER:$FLEXI_PASSWORD" \
  -X PUT \
  -H 'Content-Type: application/xml; charset=UTF-8' \
  -H 'Accept: application/xml' \
  --data-binary @faktura.xml \
  'https://server.example/c/firma/faktura-vydana.xml?dry-run=true&fail-on-warning=true'
```

### 17.5 Aktualizace detailu bez ID v body

```xml
<winstrom version="1.0">
  <adresar>
    <email>nove@example.com</email>
  </adresar>
</winstrom>
```

```text
PUT /c/firma/adresar/123.xml
```

Detail musí existovat.

### 17.6 Dávka s různými evidencemi

```xml
<winstrom version="1.0">
  <adresar update="ignore">
    <id>ext:CRM:customer-42</id>
    <nazev>ACME s.r.o.</nazev>
  </adresar>
  <faktura-vydana>
    <id>ext:SHOP:invoice-1001</id>
    <typDokl>code:FAKTURA</typDokl>
    <firma>ext:CRM:customer-42</firma>
    <polozkyFaktury>
      <faktura-vydana-polozka>
        <id>ext:SHOP:invoice-1001:1</id>
        <nazev>Implementace</nazev>
        <mnozMj>1</mnozMj>
        <cenaMj>10000</cenaMj>
      </faktura-vydana-polozka>
    </polozkyFaktury>
  </faktura-vydana>
</winstrom>
```

Pořadí kořenových elementů zajistí, že partner vznikne před fakturou. Přesná importní URL pro smíšené evidence se může lišit podle verze; ověřit v samodokumentaci serveru. Nejspolehlivější je posílat související evidence odděleně, není-li smíšený import na cíli výslovně otestován.

### 17.7 Čtení Changes API

```bash
curl --fail-with-body \
  --user "$FLEXI_USER:$FLEXI_PASSWORD" \
  -H 'Accept: application/xml' \
  'https://server.example/c/firma/changes.xml?start=123&limit=1000&evidence=faktura-vydana'
```

### 17.8 Export připravený pro přenos mezi firmami

```text
/c/firma_a/adresar.xml?limit=0&mode=xml_import_export
```

Alternativní starší vzor je `code-as-id=true&no-ids=true`. Režim `xml_import_export` používá hybridní identifikátory a řeší i složitější reference; před importem do jiné firmy vždy provést dry run.

---

## 18. Výkon, robustnost a bezpečný provoz

### 18.1 Výkon

- První požadavek po startu může kvůli inicializaci jádra trvat až desítky sekund.
- Posílat autentizaci preemptivně, nečekat na první `401`.
- Používat `detail=custom:...` a jen nezbytné `includes`/`relations`.
- Pokud externí ID nejsou potřeba, `no-ext-ids=true` výrazně pomáhá.
- Nevypisovat `relations=all`.
- Stránkovat; `limit=0` jen u prokazatelně malé evidence nebo řízeného exportu.
- `add-row-count=true` nepřidávat na každou stránku.
- Více podobných detailů načíst jedním filtrovaným požadavkem.
- Velké nezávislé importy lze po pečlivém návrhu poslat s `atomic=false`.
- Base64 přílohy jsou objemnější; pro velká data používat binární endpoint.

### 18.2 Tolerantní parser

XML klient by měl:

- bezpečně zakázat externí entity a DTD (ochrana proti XXE);
- přijmout neznámé elementy/atributy a zalogovat je jako změnu schématu;
- zachovat pořadí opakovaných elementů;
- rozlišovat chybějící a prázdný element;
- neparsovat peníze přes binární float;
- neodvozovat logiku z lokalizovaných `showAs` nebo chybových textů;
- počítat s XML komentáři, nebo použít `no-comments`/`mode=simple`;
- omezit maximální velikost odpovědi a hloubku XML.

### 18.3 Pozorovatelnost

Pro každý request logovat bez citlivých dat:

- korelační ID na straně integrace;
- metodu, normalizovanou cestu a firmu;
- HTTP status, dobu, velikost requestu/response;
- `success`, `stats` a strojové validační kódy;
- externí integrační ID cílového záznamu;
- Changes API start/next/globalVersion;
- počet retry a výsledek dohledání po nejistém zápisu.

Do běžného logu neukládat celé účetní dokumenty, osobní údaje, hesla, session tokeny ani obsah příloh.

### 18.4 Kompatibilita a verzování

- Formát obálky `1.0` neznamená, že se nemění evidence a jejich pole.
- Aktualizace Flexi může přidat pole, číselníkové hodnoty, služby a validace.
- Kontrakt je kombinace: verze serveru × firma × licence × legislativa × role.
- Před upgradem a po něm porovnat `evidence-list`, `properties`, `relations` a XSD kritických evidencí.
- Udržovat integrační smoke testy: čtení, dry-run vytvoření, dry-run update, chyba validace, stránkování a Changes API.

---

## 19. Implementační checklist

### Před vývojem

- [ ] Znám přesnou URL serveru, port a `dbNazev` firmy.
- [ ] Technický účet má jen nutná práva a licenci.
- [ ] Stáhl jsem živý `evidence-list`, `properties`, `relations` a importní/exportní XSD.
- [ ] Znám povinná pole pro konkrétní typy dokladů.
- [ ] Zvolil jsem stabilní namespace externích ID.
- [ ] Rozhodl jsem, kdo je autoritou jednotlivých polí a kolekcí.

### Čtení

- [ ] Vždy používám explicitní `detail`, `limit`, `start` a stabilní `order`.
- [ ] Filtr je bezpečně sestavený a URL-enkódovaný.
- [ ] Nepotřebné externí ID, relace a komentáře jsou vypnuté.
- [ ] Parser toleruje přidaná pole a opakované elementy.

### Zápis

- [ ] Posílám `Content-Type` i `Accept`.
- [ ] Každý kořenový i položkový záznam má idempotentní ID.
- [ ] Rozlišuji nepřítomné pole od prázdného elementu.
- [ ] `removeAll`, `removeExternalIds`, `filter` a `action` používám jen po explicitní kontrole rozsahu.
- [ ] Kritické zápisy nejprve procházejí `dry-run=true`.
- [ ] Kontroluji HTTP status, `success`, `stats` i všechny výsledky.
- [ ] Retry nemůže vytvořit duplikát.

### Synchronizace

- [ ] Changes API je aktivní a checkpoint ukládám až po úspěšném zpracování.
- [ ] Umím zpracovat create/update/delete, mezery ve verzích a duplicity.
- [ ] Webhook pouze budí synchronizaci; změny dohledávám od checkpointu.
- [ ] Handler ověřuje `X-FB-Hook-SecKey` a odpovídá rychle.
- [ ] Existuje pravidelný reconciliation/full audit pro případ provozní chyby.

### Provoz

- [ ] TLS certifikát se ověřuje.
- [ ] Tajemství nejsou v URL ani logu.
- [ ] Jsou nastavené timeouty, omezené retry a circuit breaker.
- [ ] Monitoruji chyby podle evidence, latenci a backlog Changes API.
- [ ] Po upgradu automaticky porovnávám kontrakty.

---

## 20. Autoritativní zdroje

Tato příručka syntetizuje obecné mechanismy; u konfliktu má přednost živá samodokumentace cílové instance a aktuální oficiální dokumentace.

### Oficiální dokumentace ABRA Flexi

- [Kolekce dokumentace REST API](https://podpora.flexibee.eu/en/collections/2592813-rest-api-documentation)
- [ABRA Flexi XML](https://podpora.flexibee.eu/cs/articles/4722242-abra-flexi-xml)
- [Sestavování URL a kompletní seznam parametrů](https://podpora.flexibee.eu/cs/articles/4713911-sestavovani-url)
- [Autentizace](https://podpora.flexibee.eu/en/articles/4713880-authentication)
- [Podporované formáty](https://podpora.flexibee.eu/en/articles/4719998-supported-formats)
- [Podporované HTTP operace](https://podpora.flexibee.eu/en/articles/4720093-supported-http-operations)
- [Datové typy](https://podpora.flexibee.eu/en/articles/4722246-supported-variable-types)
- [Identifikátory záznamů](https://podpora.flexibee.eu/en/articles/4725798-record-identifiers)
- [Inkrementální aktualizace](https://podpora.flexibee.eu/en/articles/4725908-incremental-updates)
- [Povinná importní pole](https://podpora.flexibee.eu/en/articles/4725919-required-import-fields)
- [Režimy založení/změny](https://podpora.flexibee.eu/en/articles/4725944-founding-amendment-mode)
- [Akce](https://podpora.flexibee.eu/en/articles/4725960-performing-actions)
- [Vnitřní vazby při ukládání](https://podpora.flexibee.eu/en/articles/4725928-internal-links-when-saving)
- [Úrovně detailu](https://podpora.flexibee.eu/en/articles/4722190-levels-of-detail)
- [Stránkování](https://podpora.flexibee.eu/en/articles/4722193-pagination)
- [Řazení](https://podpora.flexibee.eu/en/articles/4722194-records-sorting)
- [Filtrování](https://podpora.flexibee.eu/en/articles/4722195-filtering-records)
- [Sumace](https://podpora.flexibee.eu/en/articles/4722199-summary)
- [Použití `/query`](https://podpora.flexibee.eu/en/articles/5264924-using-query-in-the-rest-api)
- [Validace dat](https://podpora.flexibee.eu/en/articles/4720108-data-validation)
- [Dry run](https://podpora.flexibee.eu/en/articles/4720123-test-save-dry-run)
- [Návratové hodnoty](https://podpora.flexibee.eu/en/articles/4719646-return-values)
- [Chybové stavy](https://podpora.flexibee.eu/en/articles/4720060-error-handling)
- [Transakční zpracování](https://podpora.flexibee.eu/en/articles/4726125-transaction-processing)
- [Dávkové operace](https://podpora.flexibee.eu/en/articles/4726115-batch-operations)
- [Přílohy](https://podpora.flexibee.eu/en/articles/4722200-attachments)
- [Changes API](https://podpora.flexibee.eu/en/articles/4744362-changes-api)
- [Webhooky](https://podpora.flexibee.eu/en/articles/4744379-web-hooks)
- [Datum poslední změny](https://podpora.flexibee.eu/en/articles/4725975-last-modified-date)
- [XSD](https://www.flexibee.eu/api/dokumentace/xsd/)
- [XPath](https://www.flexibee.eu/api/dokumentace/ref/xpath/)
- [XSLT](https://www.flexibee.eu/api/dokumentace/ref/xslt/)
- [Optimalizace výkonu](https://podpora.flexibee.eu/en/articles/4720082-performance-optimization)
- [Identifikátor a seznam firem](https://podpora.flexibee.eu/en/articles/4425606-company-identifier-company-id-and-a-list-of-companies-created-via-api)

### Živá ukázková samodokumentace

- [Seznam evidencí demo firmy](https://demo.flexibee.eu/c/demo/evidence-list)
- `https://{server}/c/{firma}/{evidence}/properties`
- `https://{server}/c/{firma}/{evidence}/relations`
- `https://{server}/c/{firma}/{evidence}/schema-import.xsd`
- `https://{server}/c/{firma}/{evidence}/schema-export.xsd`

### Důležité omezení rozsahu

ABRA Flexi má stovky doménových služeb: úhrady, párování, dobropisy, zápočty, skladové přepočty, DPH výstupy, účetní sestavy, workflow, e-mailing, bankovní importy a další. Jejich parametry nejsou jednotným XML kontraktem a mění se podle verze/modulu. Tato příručka kompletně popisuje **obecný XML/HTTP mechanismus**, cestovní vzory, kontrakty, typy a synchronizaci; přesný katalog doménových akcí je nutné vždy získat z [aktuální oficiální referenční kolekce](https://podpora.flexibee.eu/en/collections/2592813-rest-api-documentation) a ze samodokumentace cílového serveru.

---

## Krátký tahák

```text
Seznam firem:       GET /c.xml?limit=0
Seznam evidencí:    GET /c/{firma}/evidence-list
Pole evidence:      GET /c/{firma}/{evidence}/properties
Importní XSD:       GET /c/{firma}/{evidence}/schema-import.xsd
Výpis:              GET /c/{firma}/{evidence}.xml?detail=custom:...&limit=100
Filtr:              GET /c/{firma}/{evidence}/({filter}).xml
Detail:             GET /c/{firma}/{evidence}/{id}.xml
Upsert:             PUT /c/{firma}/{evidence}.xml
Update detailu:     PUT /c/{firma}/{evidence}/{id}.xml
Delete:             DELETE /c/{firma}/{evidence}/{id}.xml
Dry run:            ?dry-run=true&fail-on-warning=true
Změny:              GET /c/{firma}/changes.xml?start={verze}&limit=1000
Webhooky:           PUT /c/{firma}/hooks?url=...&format=XML&secKey=...
```

Nejdůležitější pravidlo: **žádný produkční zápis bez stabilního externího ID, validace odpovědi a kontraktu staženého z cílové instance.**
