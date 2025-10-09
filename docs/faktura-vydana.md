# Faktury vydané (faktura-vydana)

Nástroj pro práci s vydanými fakturami v ABRA FlexiBee.

## Parametry

```typescript
{
  // Základní
  id?: string                 // ID konkrétní faktury
  detail?: string             // Detail mód
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

## Detail módy

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

## Příklady použití

### Získat posledních 10 neuhrazených faktur
```javascript
{
  "stavUhrK": "stavUhr.neuhrazeno",
  "limit": 10,
  "detail": "compact",
  "order": "datVyst",
  "orderDirection": "desc"
}
```

### Faktury za období
```javascript
{
  "datVystOd": "2025-01-01",
  "datVystDo": "2025-01-31",
  "detail": "standard"
}
```

### Konkrétní faktura s položkami
```javascript
{
  "id": "12345",
  "detail": "extended",
  "includeItems": true
}
```

## Stavy úhrad

- `stavUhr.uhrazeno` - uhrazeno
- `stavUhr.neuhrazeno` - neuhrazeno
- `stavUhr.castUhr` - částečně uhrazeno
- `stavUhr.preplaceno` - přeplaceno
