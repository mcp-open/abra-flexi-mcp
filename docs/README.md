# Dokumentácia ABRA FlexiBee MCP Server

Detailná technická dokumentácia všetkých nástrojov a funkcií.

## 📑 Obsah

### Faktury
- **[faktura-vydana.md](faktura-vydana.md)** - Vydané faktury s pokročilým filtrovaním
  - Parametry, detail módy, stavy úhrad
  - Příklady použití

- **[faktura-vydana-audit.md](faktura-vydana-audit.md)** - DPH a účetní audit
  - Co audit kontroluje
  - Praktické příklady
  - AI analýza

### Objednávky (Dativery / Upgates)
- **[objednavka-prijata.md](objednavka-prijata.md)** - Přijaté objednávky
  - Parametry, filtrovanie
  - Dativery integrace
  - Příklady

- **[objednavka-prijata-storno-audit.md](objednavka-prijata-storno-audit.md)** - Storno audit
  - 4 indikátory storna
  - Inteligentní stránkování
  - Kompaktní detail mód
  - Typické problémy Dativery

## 🔧 Další zdroje

- **[CHANGELOG.md](../CHANGELOG.md)** - Historie změn a novinky
- **[README.md](../README.md)** - Rychlý start a přehled
- **[GitHub Issues](https://github.com/LukasOrcik/abra-flexi-mcp/issues)** - Bug reports a feature requests

## 💡 Tipy

### Pro vývojáře
```bash
# TypeScript watch mode (auto-compile)
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch
```

### Pro účetní
- Používejte `detail: "compact"` pro rychlé seznamy
- Používejte `detail: "audit-fast"` pro DPH kontroly
- Zapněte anonymizaci pro práci s klientskými daty

### Pro auditora
- `faktura-vydana-audit` - Kontrola DPH a OSS
- `objednavka-prijata-storno-audit` - Kontrola stornovaných objednávek
- Inteligentní stránkovanie načte jen relevantní data
