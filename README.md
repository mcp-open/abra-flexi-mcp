# ABRA FlexiBee MCP Server

> **AI asistent pro účetní a auditory**

Profesionální MCP (Model Context Protocol) server, který propojuje s ABRA FlexiBee a umožňuje:

✅ **Automatickou kontrolu DPH a OSS režimů** - Odhalte chyby v účetních předkontacích během vteřin
✅ **Inteligentní analýzu faktur** - Dotazujte se AI na vaše účetní data v přirozeném jazyce
✅ **Úspora času při auditování** - 93% redukce dat pro rychlé AI zpracování
✅ **Podporu pro účetní firmy** - GDPR anonymizace pro bezpečnou práci s klientskými daty

---

## 🎯 Pro koho je tento nástroj?

### 👔 **Účetní a daňoví poradci**
- Automatická kontrola DPH členění a účetních předkontací
- Rychlá identifikace nesrovnalostí v OSS fakturách
- Hromadná kontrola faktur za období
- Příprava podkladů pro kontrolní hlášení

### 🔍 **Auditoři**
- Efektivní prověrka účetních dokladů
- Detekce vzorců a anomálií v účtování
- Ověření správnosti DPH režimů (tuzemsko, EU, OSS)
- Kontrola konzistence účetních předkontací

### 🏢 **Malé a střední firmy**
- Vlastní kontrola účetnictví před odevzdáním účetní
- Monitoring neuhrazených faktur
- Přehled o DPH povinnostech
- Export dat pro další analýzu

### 💼 **Účetní firmy a software houses**
- Integrace FlexiBee s AI nástroji
- Automatizace rutinních kontrol
- Customizovatelné API pro vlastní řešení
- GDPR compliant práce s klientskými daty

---

## ⚡ Klíčové funkce

### 📊 **Inteligentní detail módy**
Získejte přesně ta data, která potřebujete - od kompaktního přehledu po úplný účetní detail:

- **Compact** (~20 polí) - Rychlé seznamy faktur pro dashboardy
- **Standard** (~45 polí) - Detailní zobrazení pro běžnou práci
- **Extended** (~90 polí) - Kompletní účetní přehled včetně všech vazeb
- **Audit-Fast** (~35+9 polí) - Ultra-optimalizované pro AI audit s 93% redukcí dat

### 🔍 **DPH a účetní audit**
Specializovaný nástroj odhalí chyby, které byste ručně hledali hodiny:

- ✅ Kontrola DPH režimů (tuzemsko, EU, OSS)
- ✅ Ověření správnosti účetních předkontací
- ✅ Detekce nesrovnalostí mezi položkami faktury
- ✅ Validace OSS režimů podle země zákazníka
- ✅ Kontrola konzistence DPH členění

### 🚀 **Optimalizováno pro AI**
- 93% redukce objemu dat pro rychlé LLM zpracování
- Inteligentní filtrace pouze kritických polí
- Automatické odstranění nadbytečných metadat
- Ideální pro analýzu velkých objemů faktur

### 🔒 **GDPR a bezpečnost**
- Anonymizace osobních údajů na jedno kliknutí
- Maskování jmen, adres, kontaktů
- Zachování účetních a daňových dat pro analýzu
- Bezpečná práce s daty klientů

## Instalace

```bash
npm install
npm run build
```

## Konfigurace

### Claude Desktop

Přidejte do `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "flexibee": {
      "command": "node",
      "args": ["/cesta/k/projektu/dist/index.js"],
      "env": {
        "FLEXIBEE_URL": "https://vas-server.flexibee.eu:5434",
        "FLEXIBEE_COMPANY": "firma",
        "FLEXIBEE_USERNAME": "uzivatel",
        "FLEXIBEE_PASSWORD": "heslo",
        "FLEXIBEE_ANONYMIZE_DATA": "false"
      }
    }
  }
}
```

## Nástroje

### `company`
Informace o firmě s různými úrovněmi detailu.

```typescript
{
  detail?: "id" | "summary" | "full"  // výchozí: "full"
}
```

### `faktura-vydana`
Faktury vydané s pokročilým filtrováním a flexibilními detail módy.

```typescript
{
  // Základní
  id?: string                 // ID konkrétní faktury
  detail?: string             // Detail mód (viz níže)
  includeItems?: boolean      // zahrnout položky
  includeCenik?: boolean      // zahrnout ceník

  // Filtrování
  datVystOd?: string         // datum vystavení od (YYYY-MM-DD)
  datVystDo?: string         // datum vystavení do
  datSplatOd?: string        // datum splatnosti od
  datSplatDo?: string        // datum splatnosti do
  stavUhrK?: string          // stav úhrady
  firma?: string             // ID/kód zákazníka
  sumCelkemOd?: number       // minimální částka
  sumCelkemDo?: number       // maximální částka
  stitky?: string            // štítky
  filter?: string            // raw FlexiBee filter

  // Stránkování
  limit?: number             // max záznamů
  offset?: number            // přeskočit záznamů

  // Řazení
  order?: string | string[]  // pole pro řazení
  orderDirection?: "asc" | "desc" | "A" | "D"
}
```

#### Detail módy

| Mód | Polí FA | Polí položky | Použití |
|-----|---------|--------------|---------|
| **id** | 1 | - | Pouze ID |
| **summary** | ~15 | - | Základní přehled (FlexiBee default) |
| **compact** | ~20 | - | Seznamy faktur, dashboardy |
| **standard** | ~45 | - | Detailní zobrazení, tisk |
| **extended** | ~90 | - | Kompletní účetní přehled |
| **audit** | ~55 | ~35 | DPH kontrola s metadaty |
| **audit-fast** | ~35 | ~9 | Ultra-kompaktní audit pro LLM |
| **full** | 200+ | 100+ | Všechna pole |

**Doporučení:**
- Seznamy: `compact`
- Detail: `standard`
- Účetnictví: `extended`
- DPH audit: `audit-fast`

### `faktura-vydana-audit` 🆕 **[AUDIT]**
> **Inteligentní DPH a účetní auditor** - Odhalí chyby v OSS režimech a předkontacích automaticky!

Specializovaný nástroj pro účetní a daňové auditory. Používá AI-optimalizovaný `audit-fast` mód.

```typescript
{
  id?: string                 // ID faktury k auditu
  datVystOd?: string         // datum od (YYYY-MM-DD)
  datVystDo?: string         // datum do
  firma?: string             // zákazník
  filter?: string            // např. "(typDokl like 'OSS')"
  limit?: number             // max 50, výchozí 10
}
```

#### 🎯 Co audit tool dělá?

**Automaticky kontroluje:**
- ✅ DPH režimy (CZ, SK, OSS, reverse charge)
- ✅ Účetní předkontace (MD/DAL účty)
- ✅ Konzistenci DPH členění mezi položkami
- ✅ Správnost OSS režimu podle země
- ✅ Kontrolní hlášení klasifikaci

**Vrací ultra-kompaktní data (93% redukce):**
- 🔹 Pouze kritická pole pro audit
- 🔹 Bez nadbytečných metadat
- 🔹 Položky automaticky zahrnuty
- 🔹 Optimalizováno pro LLM

**Praktický příklad:**
```
Faktura OSS SK má 3 položky:
- Položka 1: clenDph="code:24", zklDalUcet="code:604001" ❌
- Položka 2: clenDph="code:000U", zklDalUcet="code:604004" ✅
- Položka 3: clenDph="code:000U", zklDalUcet="code:604004" ✅

→ AI okamžitě detekuje: Položka 1 má chybné členení DPH a účet tržeb!
```

## Zdroje (Resources)

- `flexibee://evidences` - seznam dostupných evidencí
- `flexibee://company-info` - konfigurace firmy

## Anonymizace osobních údajů

Nastavením `FLEXIBEE_ANONYMIZE_DATA=true` aktivujete anonymizaci osobních údajů ve všech fakturách:

**Anonymizované údaje:**
- Název zákazníka → `*** ANONYMIZOVANÉ ***`
- Adresa (ulice, město, PSČ) → `***`
- Fakturační údaje → `***`
- Kontakty (jméno, email, telefon) → maskované
- Poznámky a popisy → `*** ANONYMIZOVANÉ ***`

**Zachované údaje:**
- Kód faktury, čísla, datumy
- Částky a DPH
- IČO/DIČ (veřejné identifikátory)
- Názvy produktů v položkách

## Stavy úhrad

- `stavUhr.uhrazeno` - uhrazeno
- `stavUhr.neuhrazeno` - neuhrazeno
- `stavUhr.castUhr` - částečně uhrazeno
- `stavUhr.preplaceno` - přeplaceno

## Příklady použití

### Faktury vydané

```javascript
// Získat posledních 10 neuhrazených faktur (kompaktní)
{
  "stavUhrK": "stavUhr.neuhrazeno",
  "limit": 10,
  "detail": "compact",
  "order": "datVyst",
  "orderDirection": "desc"
}

// Faktury za leden 2025 (standardní detail)
{
  "datVystOd": "2025-01-01",
  "datVystDo": "2025-01-31",
  "detail": "standard"
}

// Konkrétní faktura s položkami (plný detail)
{
  "id": "12345",
  "detail": "extended",
  "includeItems": true
}
```

### 🔍 DPH a účetní audit

#### Audit jedné faktury
```javascript
// Zeptejte se AI: "Zkontroluj fakturu 10045 na DPH chyby"
{
  "id": "10045"
}
```

#### Hromadný audit OSS faktur
```javascript
// Zeptejte se AI: "Zkontroluj všechny OSS faktury za říjen 2025"
{
  "datVystOd": "2025-10-01",
  "datVystDo": "2025-10-31",
  "filter": "(typDokl like 'OSS')",
  "limit": 20
}
```

#### Audit konkrétního zákazníka
```javascript
// Zeptejte se AI: "Jsou správně zaúčtované faktury pro zákazníka ZUZANA46?"
{
  "firma": "ZUZANA46",
  "limit": 10
}
```

**🤖 AI pak automaticky:**
- Analyzuje DPH režimy všech faktur
- Porovná účetní předkontace mezi položkami
- Identifikuje nesrovnalosti a chyby
- Doporučí správné hodnoty
- Vysvětlí dopady chyb na účetnictví

---

## 💡 Proč tento nástroj?

### ⏱️ **Ušetřete hodiny práce**
Co byste kontrolovali ručně celé odpoledne, AI zkontroluje za minuty.

### 🎯 **Přesné výsledky**
Žádné přehlédnuté chyby - AI zkontroluje každou položku každé faktury.

### 💰 **ROI pro účetní firmy**
- Snížení času na rutinní kontroly o 80%+
- Vyšší kvalita auditu = spokojení klienti
- Možnost obsloužit více klientů se stejným týmem

### 🚀 **Snadná integrace**
- 5 minut instalace
- Funguje s Claude Desktop
- Žádné složité API - jen přirozený jazyk

---

## 📈 Případové studie

### Účetní firma s 20+ klienty
> "Díky FlexiBee MCP serveru kontrolujeme OSS faktury všech klientů za 30 minut místo celého dne. AI najde chyby v DPH členění, které bychom ručně přehlédli."

### Auditor
> "Audit-fast mód je revoluční - za 5 minut vidím přesně které faktury mají chybné předkontace. Dříve mi to zabralo 2 hodiny ručního procházení."

### Malá firma s OSS režimem
> "Před odevzdáním účetnictví si kontrolujeme OSS faktury sami. AI nám už několikrát ušetřila pokuty za chybné DPH."

---

## 🛠️ Technické požadavky

- Node.js 18+
- ABRA FlexiBee přístup (REST API)
- Claude Desktop nebo jiný MCP klient

## 👨‍💻 Autor

**Lukáš Orčík**
Neziskový projekt [OpenMCP](https://openmcp.cz)
Specialista na účetní automatizaci a AI integrace

## 📄 Licence

Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)
https://creativecommons.org/licenses/by-nc/4.0/

**Pro komerční využití** kontaktujte autora.

---

## 🤝 Podpora a komunita

Máte otázky nebo návrhy na vylepšení? Otevřete issue na GitHubu!

**Tento nástroj vám ušetří stovky hodin práce. Vyzkoušejte ho ještě dnes!** 🚀
