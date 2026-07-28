"""Allowlist evidencí ABRA Flexi pro generické čtecí nástroje.

Katalog vychází z `docs/abra-flexi-xml-api-kompletni-dokumentace.md` §16.3 a
z živého ``/evidence-list`` reálné instance (23. 7. 2026, 249 evidencí).
Úplný živý seznam dané instance je na ``/c/{firma}/evidence-list`` a skutečný
kontrakt polí dá ``get_evidence_properties`` — tenhle katalog je **allowlist**:
generické nástroje odmítnou evidenci, která tu není, takže „všechna data"
znamená „všechna vyjmenovaná", ne neohraničený přístup.

Položkové evidence (``*-polozka``) jsou čitelné napřímo; zápis položek jde
vždy přes rodičovský doklad (``NOT_DIRECT``).

ZÁMĚRNĚ MIMO allowlist (ať je vidět, že to není opomenutí):
- technické/konfigurační evidence instance (``dashboard-*``, ``sestava``,
  ``sablona-*``, ``*-store``, ``xslt``, ``custom-button``, ``filtr``,
  ``uzivatelsky-dotaz*``, ``integrace``, ``doplnek``, ``autotisk``,
  ``strom*``, ``atribut*``, ``format-elektronickeho-*``…) — konfigurace
  aplikace, ne účetní data;
- bezpečnostní evidence (``certifikat*``, ``pristupove-pravo``,
  ``pravo-viditelnosti``) — nepatří do kontextu modelu;
- mzdové evidence (``mzda*`` a příbuzné) — zvláštní kategorie osobních
  údajů, vyžadovala by samostatné posouzení (COMPLIANCE.md §7);
- ``intrastat-*`` číselníky — niche výkaznictví, snadno doplnitelné.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """Jedna evidence: oblast + krátký popis pro katalogový nástroj."""

    area: str
    description: str


EVIDENCES: dict[str, Evidence] = {
    # -- partneři --------------------------------------------------------------
    "adresar": Evidence("partneri", "Firmy a kontakty (odběratelé, dodavatelé)"),
    "kontakt": Evidence("partneri", "Kontaktní osoby firem"),
    "misto-urceni": Evidence("partneri", "Místa určení / dodací adresy"),
    "adresar-bankovni-ucet": Evidence("partneri", "Bankovní účty firem v adresáři"),
    "skupina-firem": Evidence("partneri", "Skupiny firem"),
    # -- CRM -------------------------------------------------------------------
    "udalost": Evidence("crm", "Události a aktivity CRM"),
    "typ-aktivity": Evidence("crm", "Číselník typů aktivit"),
    "naklad": Evidence("crm", "Náklady na aktivity"),
    "typ-nakladu": Evidence("crm", "Číselník typů nákladů"),
    # -- prodej ----------------------------------------------------------------
    "faktura-vydana": Evidence("prodej", "Vydané faktury"),
    "faktura-vydana-polozka": Evidence("prodej", "Položky vydaných faktur"),
    "objednavka-prijata": Evidence("prodej", "Přijaté objednávky"),
    "objednavka-prijata-polozka": Evidence("prodej", "Položky přijatých objednávek"),
    "nabidka-vydana": Evidence("prodej", "Vydané nabídky"),
    "poptavka-prijata": Evidence("prodej", "Přijaté poptávky"),
    "prodejka": Evidence("prodej", "Prodejky (prodejní kasa)"),
    # -- nákup -----------------------------------------------------------------
    "faktura-prijata": Evidence("nakup", "Přijaté faktury"),
    "faktura-prijata-polozka": Evidence("nakup", "Položky přijatých faktur"),
    "objednavka-vydana": Evidence("nakup", "Vydané objednávky"),
    "objednavka-vydana-polozka": Evidence("nakup", "Položky vydaných objednávek"),
    "nabidka-prijata": Evidence("nakup", "Přijaté nabídky"),
    "poptavka-vydana": Evidence("nakup", "Vydané poptávky"),
    # -- zboží a sklad ---------------------------------------------------------
    "cenik": Evidence("sklad", "Ceník — produkty a služby"),
    "skladova-karta": Evidence("sklad", "Skladové karty produktů"),
    "skladovy-pohyb": Evidence("sklad", "Skladové pohyby (příjemky, výdejky)"),
    "skladovy-pohyb-polozka": Evidence("sklad", "Položky skladových pohybů"),
    "sklad": Evidence("sklad", "Číselník skladů"),
    "vyrobni-cislo": Evidence("sklad", "Výrobní čísla"),
    "rezervace": Evidence("sklad", "Rezervace zboží"),
    "sady-a-komplety": Evidence("sklad", "Sady a komplety"),
    "kusovnik": Evidence("sklad", "Kusovníky"),
    "stav-skladu-k-datu": Evidence("sklad", "Stav zásob k datu"),
    # -- ceny ------------------------------------------------------------------
    "dodavatel": Evidence("ceny", "Dodavatelské ceny"),
    "odberatel": Evidence("ceny", "Odběratelské ceny"),
    "cenova-uroven": Evidence("ceny", "Cenové úrovně"),
    "cenikova-skupina": Evidence("ceny", "Ceníkové skupiny"),
    "poplatek": Evidence("ceny", "Poplatky (recyklační, autorské…)"),
    # -- peníze ----------------------------------------------------------------
    "banka": Evidence("penize", "Bankovní doklady"),
    "banka-polozka": Evidence("penize", "Položky bankovních dokladů"),
    "pokladni-pohyb": Evidence("penize", "Pokladní doklady"),
    "pokladni-pohyb-polozka": Evidence("penize", "Položky pokladních dokladů"),
    "prikaz-k-uhrade": Evidence("penize", "Příkazy k úhradě"),
    "prikaz-k-uhrade-polozka": Evidence("penize", "Položky příkazů k úhradě"),
    # -- účetnictví ------------------------------------------------------------
    "interni-doklad": Evidence("ucetnictvi", "Interní doklady"),
    "interni-doklad-polozka": Evidence("ucetnictvi", "Položky interních dokladů"),
    "pohledavka": Evidence("ucetnictvi", "Ostatní pohledávky"),
    "zavazek": Evidence("ucetnictvi", "Ostatní závazky"),
    "ucet": Evidence("ucetnictvi", "Účtový rozvrh"),
    "ucetni-denik": Evidence("ucetnictvi", "Účetní deník (zápisy MD/DAL)"),
    "predpis-zauctovani": Evidence("ucetnictvi", "Předpisy zaúčtování"),
    "stredisko": Evidence("ucetnictvi", "Střediska"),
    "zakazka": Evidence("ucetnictvi", "Zakázky"),
    "cinnost": Evidence("ucetnictvi", "Činnosti"),
    "ucetni-obdobi": Evidence("ucetnictvi", "Účetní období"),
    # -- číselníky -------------------------------------------------------------
    "mena": Evidence("ciselniky", "Měny"),
    "stat": Evidence("ciselniky", "Státy"),
    "sazba-dph": Evidence("ciselniky", "Sazby DPH"),
    "merna-jednotka": Evidence("ciselniky", "Měrné jednotky"),
    "forma-uhrady": Evidence("ciselniky", "Formy úhrady"),
    "konst-symbol": Evidence("ciselniky", "Konstantní symboly"),
    "penezni-ustav": Evidence("ciselniky", "Peněžní ústavy"),
    # -- typy dokladů ----------------------------------------------------------
    "typ-faktury-vydane": Evidence("typy", "Typy vydaných faktur"),
    "typ-faktury-prijate": Evidence("typy", "Typy přijatých faktur"),
    "typ-objednavky-prijate": Evidence("typy", "Typy přijatých objednávek"),
    "typ-objednavky-vydane": Evidence("typy", "Typy vydaných objednávek"),
    "typ-skladovy-pohyb": Evidence("typy", "Typy skladových pohybů"),
    "typ-pokladni-pohyb": Evidence("typy", "Typy pokladních pohybů"),
    "typ-banka": Evidence("typy", "Typy bankovních dokladů"),
    # -- dokladové řady --------------------------------------------------------
    "rada-faktury-vydane": Evidence("rady", "Řady vydaných faktur"),
    "rada-faktury-prijate": Evidence("rady", "Řady přijatých faktur"),
    "rada-objednavky-prijate": Evidence("rady", "Řady přijatých objednávek"),
    "rada-skladovy-pohyb": Evidence("rady", "Řady skladových pohybů"),
    "rada-pokladni-pohyb": Evidence("rady", "Řady pokladních dokladů"),
    # -- štítky a vazby --------------------------------------------------------
    "stitek": Evidence("stitky", "Štítky"),
    "skupina-stitku": Evidence("stitky", "Skupiny štítků"),
    "uzivatelska-vazba": Evidence("stitky", "Uživatelské vazby mezi záznamy"),
    "typ-uzivatelske-vazby": Evidence("stitky", "Typy uživatelských vazeb"),
    "vazba": Evidence("stitky", "Systémové vazby dokladů"),
    # -- majetek ---------------------------------------------------------------
    "majetek": Evidence("majetek", "Dlouhodobý majetek"),
    "majetek-udalost": Evidence("majetek", "Události majetku (odpisy…)"),
    "leasing": Evidence("majetek", "Leasingy"),
    "umisteni": Evidence("majetek", "Umístění majetku"),
    "typ-majetku": Evidence("majetek", "Typy majetku"),
    "danovy-odpis": Evidence("majetek", "Daňové odpisy"),
    "ucetni-odpis": Evidence("majetek", "Účetní odpisy"),
    "odpisova-skupina": Evidence("majetek", "Odpisové skupiny"),
    "danovy-naklad": Evidence("majetek", "Daňové náklady majetku"),
    # -- účetní reporty (ověřeno na živé instanci — obyčejný GET funguje) ------
    "hlavni-kniha": Evidence("reporty", "Hlavní kniha — obraty a zůstatky po účtech"),
    "obratova-predvaha": Evidence("reporty", "Obratová předvaha"),
    "vysledovka-po-uctech": Evidence("reporty", "Výsledovka po účtech"),
    "rozvaha-po-uctech": Evidence("reporty", "Rozvaha po účtech"),
    "vykaz-hospodareni": Evidence("reporty", "Výkaz hospodaření"),
    "obrat": Evidence("reporty", "Obraty"),
    "saldo": Evidence("reporty", "Saldo — párování dokladů a úhrad"),
    "saldo-k-datu": Evidence("reporty", "Saldo k datu"),
    "stav-uctu": Evidence("reporty", "Stavy účtů"),
    "pohyb-na-uctech": Evidence("reporty", "Pohyby na účtech"),
    "neuhrazene-po-splatnosti": Evidence("reporty", "Neuhrazené doklady po splatnosti"),
    "neuhrazene-po-splatnosti-2": Evidence("reporty", "Neuhrazené po splatnosti (var. 2)"),
    "po-splatnosti": Evidence("reporty", "Doklady po splatnosti"),
    "doklad-k-uhrade": Evidence("reporty", "Doklady k úhradě"),
    # -- DPH -------------------------------------------------------------------
    "podklady-dph": Evidence("dph", "Podklady přiznání DPH po dokladech"),
    "kontrolni-hlaseni-dph": Evidence("dph", "Kontrolní hlášení DPH"),
    "souhrnne-hlaseni-dph": Evidence("dph", "Souhrnné hlášení DPH"),
    "radek-priznani-dph": Evidence("dph", "Řádky přiznání DPH"),
    "ulozene-priznani-dph": Evidence("dph", "Uložená přiznání DPH"),
    "ulozene-priznani-kon-vyk-dph": Evidence("dph", "Uložená kontrolní hlášení"),
    "cleneni-dph": Evidence("dph", "Členění DPH"),
    "cleneni-kontrolni-hlaseni": Evidence("dph", "Členění kontrolního hlášení"),
    "stat-dph": Evidence("dph", "Státy pro DPH (OSS)"),
    "preneseni-dph": Evidence("dph", "Přenesená daňová povinnost"),
    "castky-k-odpoctu": Evidence("dph", "Částky k odpočtu"),
    "zaloha-k-odpoctu": Evidence("dph", "Zálohy k odpočtu"),
    "skupina-plneni": Evidence("dph", "Skupiny plnění DPH"),
    "uplatneni-dane-zavazku": Evidence("dph", "Uplatnění daně u závazků"),
    "uplatneni-dane-zavazku-polozka": Evidence("dph", "Položky uplatnění daně"),
    # -- smlouvy ---------------------------------------------------------------
    "smlouva": Evidence("smlouvy", "Odběratelské smlouvy"),
    "smlouva-polozka": Evidence("smlouvy", "Položky smluv"),
    "smlouva-zurnal": Evidence("smlouvy", "Žurnál změn smluv"),
    "typ-smlouvy": Evidence("smlouvy", "Typy smluv"),
    "stav-smlouvy": Evidence("smlouvy", "Stavy smluv"),
    "dodavatelska-smlouva": Evidence("smlouvy", "Dodavatelské smlouvy"),
    "dodavatelsky-typ-smlouvy": Evidence("smlouvy", "Typy dodavatelských smluv"),
    "splatkovy-kalendar": Evidence("smlouvy", "Splátkové kalendáře"),
    "zapujcka": Evidence("smlouvy", "Zápůjčky"),
    # -- peníze (doplnění) -----------------------------------------------------
    "prikaz-k-inkasu": Evidence("penize", "Příkazy k inkasu"),
    "prikaz-k-inkasu-polozka": Evidence("penize", "Položky příkazů k inkasu"),
    "vzajemny-zapocet": Evidence("penize", "Vzájemné zápočty"),
    "typ-vzajemnych-zapoctu": Evidence("penize", "Typy vzájemných zápočtů"),
    "pokladna": Evidence("penize", "Číselník pokladen"),
    "bankovni-ucet": Evidence("penize", "Vlastní bankovní účty"),
    "prodejka-platba": Evidence("penize", "Platby prodejek"),
    # -- účetnictví (doplnění) -------------------------------------------------
    "ucetni-osnova": Evidence("ucetnictvi", "Účetní osnova"),
    "standardni-predpis": Evidence("ucetnictvi", "Standardní předpisy zaúčtování"),
    "doklad": Evidence("ucetnictvi", "Souhrnný pohled přes všechny doklady"),
    "vazebni-doklad": Evidence("ucetnictvi", "Vazby mezi doklady"),
    "zurnal": Evidence("ucetnictvi", "Žurnál změn záznamů (audit)"),
    "pohledavka-polozka": Evidence("ucetnictvi", "Položky ostatních pohledávek"),
    "zavazek-polozka": Evidence("ucetnictvi", "Položky ostatních závazků"),
    # -- sklad (doplnění) ------------------------------------------------------
    "inventura": Evidence("sklad", "Inventury"),
    "inventura-polozka": Evidence("sklad", "Položky inventur"),
    "sarze-expirace": Evidence("sklad", "Šarže a expirace"),
    "cislo-baliku": Evidence("sklad", "Čísla balíků"),
    "umisteni-ve-skladu": Evidence("sklad", "Umístění ve skladu"),
    # -- prodej/nákup (položky dalších dokladů) --------------------------------
    "nabidka-vydana-polozka": Evidence("prodej", "Položky vydaných nabídek"),
    "poptavka-prijata-polozka": Evidence("prodej", "Položky přijatých poptávek"),
    "nabidka-prijata-polozka": Evidence("nakup", "Položky přijatých nabídek"),
    "poptavka-vydana-polozka": Evidence("nakup", "Položky vydaných poptávek"),
    # -- číselníky (doplnění) --------------------------------------------------
    "kurz": Evidence("ciselniky", "Kurzy měn"),
    "psc": Evidence("ciselniky", "Číselník PSČ"),
    "region": Evidence("ciselniky", "Regiony"),
    "forma-dopravy": Evidence("ciselniky", "Formy dopravy"),
    "skupina-zbozi": Evidence("ciselniky", "Skupiny zboží"),
    "stav-obchodniho-dokladu": Evidence("ciselniky", "Stavy obchodních dokladů"),
    "stav-zakazky": Evidence("ciselniky", "Stavy zakázek"),
    "typ-zakazky": Evidence("ciselniky", "Typy zakázek"),
    "typ-organizace": Evidence("ciselniky", "Typy organizací"),
    # -- typy dokladů (doplnění) -----------------------------------------------
    "typ-dokladu": Evidence("typy", "Souhrnný číselník typů dokladů"),
    "typ-interniho-dokladu": Evidence("typy", "Typy interních dokladů"),
    "typ-pohledavky": Evidence("typy", "Typy pohledávek"),
    "typ-zavazku": Evidence("typy", "Typy závazků"),
    "typ-prodejky": Evidence("typy", "Typy prodejek"),
    "typ-nabidky-vydane": Evidence("typy", "Typy vydaných nabídek"),
    "typ-nabidky-prijate": Evidence("typy", "Typy přijatých nabídek"),
    "typ-poptavky-prijate": Evidence("typy", "Typy přijatých poptávek"),
    "typ-poptavky-vydane": Evidence("typy", "Typy vydaných poptávek"),
    "typ-uplatneni-dane-zavazku": Evidence("typy", "Typy uplatnění daně u závazků"),
    # -- dokladové řady (doplnění) ---------------------------------------------
    "rada": Evidence("rady", "Souhrnný číselník dokladových řad"),
    "rocni-rada": Evidence("rady", "Roční stavy dokladových řad"),
    "rada-banka": Evidence("rady", "Řady bankovních dokladů"),
    "rada-interniho-dokladu": Evidence("rady", "Řady interních dokladů"),
    "rada-pohledavky": Evidence("rady", "Řady pohledávek"),
    "rada-zavazku": Evidence("rady", "Řady závazků"),
    "rada-objednavky-vydane": Evidence("rady", "Řady vydaných objednávek"),
    "rada-nabidky-vydane": Evidence("rady", "Řady vydaných nabídek"),
    "rada-nabidky-prijate": Evidence("rady", "Řady přijatých nabídek"),
    "rada-poptavky-prijate": Evidence("rady", "Řady přijatých poptávek"),
    "rada-poptavky-vydane": Evidence("rady", "Řady vydaných poptávek"),
    "rada-uplatneni-dane-zavazku": Evidence("rady", "Řady uplatnění daně"),
}
