# Storno audit objednávek (objednavka-prijata-storno-audit)

Specializovaný audit tool pro detekciu stornovaných objednávek z Dativery integrace (Upgates e-shop).

## Hlavní funkce

- **Inteligentní stránkování**: Automaticky načítá dávky po 100 objednávkách, dokud nenajde požadovaný počet storno objednávek
- **4 indikátory storna**: Řeší problém Dativery integrace, kde `storno` flag není aktualizovaný
- **92% redukce dat**: Kompaktní detail mód (24 polí v hlavičce, 14 v položkách)
- **Automatické filtrování**: Vrací JEN skutečně stornované objednávky

## Parametry

```typescript
{
  id?: string                 // ID objednávky k auditu
  datVystOd?: string         // datum od (YYYY-MM-DD)
  datVystDo?: string         // datum do
  cisObj?: string            // číslo objednávky (např. "O23955")
  filter?: string            // raw FlexiBee filter
  limit?: number             // max 50 storno objednávek, výchozí 10
  order?: string             // řazení (výchozí: "lastUpdate")
  orderDirection?: string    // směr (výchozí: "desc")
}
```

## Jak funguje storno detekce?

Tool kontroluje **4 indikátory storna** a objednávka je vrácena pokud splní **ALESPOŇ 1 podmínku**:

### 1. `storno = true`
Přímý storno flag v ABRA FlexiBee.

**Poznámka:** Dativery tento flag obvykle NENASTAVUJE!

### 2. `stavDoklObch` obsahuje "STORNO"
Stav obchodního dokladu.

**Příklad:** `"stavDoklObch": "code:STORNO"`

### 3. `stavUzivK` obsahuje "storno"
Uživatelský stav objednávky.

**Příklad:** `"stavUzivK": "stavDoklObch.storno"`

### 4. `cisSml` = "Storno"
Dativery storno status (z e-shopu).

**Příklad:** `"cisSml": "Storno"`

### ⚠️ Proč se nepoužívá `sumCelkem = 0`?

`sumCelkem` může být 0 i u normálních objednávek:
- Zaokrouhlovací rozdíly (-0.01 + 0.01 = 0)
- 100% slevové kupóny
- Objednávky s darčekovými produktmi

Proto se `sumCelkem=0` používá pouze pro **pre-filtering** (rychlejší načítání), ale ne pro finální detekci.

## Inteligentní stránkování

### Jak funguje?

```
Uživatel → "Nájdi 10 storno objednávek"
     ↓
1. Načte prvních 100 objednávek (batch 1)
   Filtruje → Najde 2 storno
   Má 2 z 10 požadovaných → pokračuje
     ↓
2. Načte dalších 100 objednávek (batch 2, offset=100)
   Filtruje → Najde 5 storno
   Má 7 z 10 požadovaných → pokračuje
     ↓
3. Načte dalších 100 (batch 3, offset=200)
   Filtruje → Najde 3 storno
   Má 10 z 10 požadovaných → STOP ✅
     ↓
4. Vrátí prvních 10 storno objednávek
```

### Limity

- **Max storno objednávok na vratenie:** 50
- **Max objednávok na prehľadanie:** 1000 (safety limit)
- **Batch size:** 100 objednávok na dávku

### Výhody

✅ **`limit` = počet STORNO objednávok** (nie celkový počet)
✅ Efektívne - zastaví sa hneď ako nájde dostatok
✅ Nenačítava zbytočne všetky objednávky
✅ Funguje aj keď sú storno objednávky roztúsené v databáze

## Kompaktný detail mód

### Header (24 polí)
```
Identifikácia: id, kod, cisDosle, varSym
Dátumy: datVyst, lastUpdate
Zákazník: firma, nazFirmy, stat
Storno: storno, stavDoklObch, stavUzivK, cisSml
Sumy: sumCelkem, sumZklCelkem, sumDphCelkem
Mena: mena, kurz
Typ: typDokl
Tracking: source, external-ids, stitky
```

### Položky (14 polí)
```
Identifikácia: id, kod, nazev, cisRad
Sumy: sumCelkem, sumZkl, sumDph
Množstvo: mnozMj, mnozMjZbyva, cenaMj
DPH: typSzbDphK, szbDph
Produkt: cenik, sklad
```

### Redukce dat

- **Predtým:** ~150 polí + metadata = ~32,000 tokenov (3 objednávky) ❌
- **Teraz:** 24 polí bez metadata = ~2,500 tokenov (3 objednávky) ✅
- **→ Redukcia o 92%!**

## Příklady použití

### Kontrola jedné objednávky
```javascript
// "Zkontroluj objednávku 9260 na storno"
{
  "id": "9260"
}
```

### Hromadná kontrola za období
```javascript
// "Najdi všechny stornované objednávky za září 2025"
{
  "datVystOd": "2025-09-01",
  "datVystDo": "2025-09-30",
  "limit": 20
}
```

### Posledních 10 storno objednávek
```javascript
// "Jaké byly poslední stornované objednávky?"
{
  "limit": 10
}
```

## Praktický příklad

### Vstup
```javascript
{
  "limit": 3
}
```

### Výstup
```json
{
  "objednavka-prijata": [
    {
      "id": "9260",
      "kod": "O23955",
      "cisDosle": "O23955",
      "datVyst": "2025-10-06",
      "storno": "false",           // ❌ Flag není aktualizovaný!
      "stavDoklObch": "code:STORNO", // ✅ Skutečný stav
      "stavUzivK": "stavDoklObch.storno", // ✅
      "cisSml": "Storno",          // ✅ Dativery status
      "sumCelkem": "0.0",
      "firma": "code:JAN194",
      "external-ids": ["ext:DATIVERY:com.upgates.orders-0de417:O23955"],
      "polozkyObchDokladu": []
    }
  ]
}
```

### Co AI detekuje
- ⚠️ **Problém:** Objednávka má `storno=false`, ale je skutečně stornovaná!
- ✅ **Indikátory:** `stavDoklObch=STORNO`, `cisSml=Storno`, `stavUzivK=storno`
- 📊 **Dativery tracking:** External ID pro trasování v e-shopu
- 💡 **Doporučení:** Aktualizovat storno flag nebo opravit Dativery integraci

## Typické problémy Dativery

### Problém 1: Nenastavený storno flag
```
storno: false
stavDoklObch: code:STORNO
cisSml: Storno
```
**→ Tool detekuje:** Objednávka JE stornovaná (podle stavDoklObch a cisSml)

### Problém 2: Prázdné položky
```
polozkyObchDokladu: []
sumCelkem: 0.0
```
**→ Položky vymazané při stornování v e-shopu**

### Problém 3: Nesrovnalosti v synchronizaci
```
E-shop: Objednávka STORNO
ABRA FlexiBee: storno=false, ale stavDoklObch=STORNO
```
**→ Tool odhalí nesrovnalost**
