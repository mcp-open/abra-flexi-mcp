# Přijaté objednávky (objednavka-prijata)

Nástroj pro práci s přijatými objednávkami z ABRA FlexiBee. Podporuje objednávky z Dativery integrace (Upgates e-shop).

## Parametry

```typescript
{
  // Základní
  id?: string                 // ID objednávky
  detail?: string             // "id" | "summary" | "full"
  includeItems?: boolean      // zahrnout položky objednávky

  // Filtrování
  datVystOd?: string         // datum od (YYYY-MM-DD)
  datVystDo?: string         // datum do
  cisObj?: string            // číslo objednávky (např. "O23955")
  firma?: string             // ID/kód zákazníka
  stitky?: string            // štítky
  filter?: string            // raw FlexiBee filter

  // Stránkování
  limit?: number             // max záznamů
  offset?: number            // přeskočit záznamů

  // Řazení
  order?: string | string[]  // pole pro řazení
  orderDirection?: "asc" | "desc"
}
```

## Detail módy

- **id** - Pouze ID (minimální)
- **summary** - Základní přehled (~15 polí)
- **full** - Všechna pole (~150 polí)

## Položky objednávky

Při `includeItems: true` se vrací pole `polozkyObchDokladu` s položkami:
- Kód produktu, název
- Množství, cena, sumy
- DPH, sazba
- Ceník, sklad

## Dativery integrace

**External IDs tracking:**
```
"external-ids": ["ext:DATIVERY:com.upgates.orders-0de417:O23955"]
```

**Source field:**
```
"source": "dativery-upgates-flexibee"
```

## Příklady použití

### Získat objednávku podle ID
```javascript
{
  "id": "9260",
  "detail": "full",
  "includeItems": true
}
```

### Seznam objednávek za období
```javascript
{
  "datVystOd": "2025-09-01",
  "datVystDo": "2025-09-30",
  "detail": "summary",
  "limit": 20,
  "order": "datVyst",
  "orderDirection": "desc"
}
```

### Objednávky konkrétního zákazníka
```javascript
{
  "firma": "code:PETR10",
  "detail": "summary",
  "limit": 10
}
```

### Hledání podle čísla objednávky
```javascript
{
  "cisObj": "O23955",
  "includeItems": true
}
```
