# DPH a účetní audit (faktura-vydana-audit)

Specializovaný nástroj pro DPH a účetní auditory. Automaticky kontroluje DPH režimy a účetní předkontace.

## Parametry

```typescript
{
  id?: string                 // ID faktury k auditu
  datVystOd?: string         // datum od (YYYY-MM-DD)
  datVystDo?: string         // datum do
  firma?: string             // zákazník
  filter?: string            // např. "(typDokl like 'OSS')"
  limit?: number             // max 50, výchozí 10
  stitky?: string            // štítky
}
```

## Co audit kontroluje?

**Automaticky kontroluje:**
- ✅ DPH režimy (CZ, SK, OSS, reverse charge)
- ✅ Účetní předkontace (MD/DAL účty)
- ✅ Konzistenci DPH členění mezi položkami
- ✅ Správnost OSS režimu podle země
- ✅ Kontrolní hlášení klasifikaci

**Vrací ultra-kompaktní data:**
- 93% redukce dat
- Pouze kritická pole pro audit
- Bez nadbytečných metadat
- Položky automaticky zahrnuty

## Příklady použití

### Audit jedné faktury
```javascript
// "Zkontroluj fakturu 10045 na DPH chyby"
{
  "id": "10045"
}
```

### Hromadný audit OSS faktur
```javascript
// "Zkontroluj všechny OSS faktury za říjen 2025"
{
  "datVystOd": "2025-10-01",
  "datVystDo": "2025-10-31",
  "filter": "(typDokl like 'OSS')",
  "limit": 20
}
```

### Audit konkrétního zákazníka
```javascript
// "Jsou správně zaúčtované faktury pro zákazníka ZUZANA46?"
{
  "firma": "ZUZANA46",
  "limit": 10
}
```

## Praktický příklad

```
Faktura OSS SK má 3 položky:
- Položka 1: clenDph="code:24", zklDalUcet="code:604001" ❌
- Položka 2: clenDph="code:000U", zklDalUcet="code:604004" ✅
- Položka 3: clenDph="code:000U", zklDalUcet="code:604004" ✅

→ AI okamžitě detekuje: Položka 1 má chybné členění DPH a účet tržeb!
```

## Co AI automaticky dělá

- Analyzuje DPH režimy všech faktur
- Porovná účetní předkontace mezi položkami
- Identifikuje nesrovnalosti a chyby
- Doporučí správné hodnoty
- Vysvětlí dopady chyb na účetnictví
