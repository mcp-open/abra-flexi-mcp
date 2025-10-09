# ABRA FlexiBee MCP Server

> **AI asistent pro účetní a auditory**

Propojte Claude AI s ABRA FlexiBee a automatizujte kontrolu účetnictví, DPH a objednávek z e-shopu.

✅ Automatická kontrola DPH a OSS režimů
✅ Audit stornovaných objednávek z Dativery
✅ 93% redukce dat pro rychlé AI zpracování
✅ GDPR anonymizace osobních údajů

---

## 🚀 Rychlý start

### 1. Instalace

```bash
npm install
npm run build
```

### 2. Konfigurace

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

### 3. Použití

Zeptejte se Claude AI:

```
"Zkontroluj fakturu 10045 na DPH chyby"
"Najdi všechny stornované objednávky za září"
"Která faktury jsou neuhrazené a po splatnosti?"
```

---

## 📦 Dostupné nástroje

### 🧾 Faktury

| Nástroj | Popis | Dokumentace |
|---------|-------|-------------|
| `company` | Informace o firmě | - |
| `faktura-vydana` | Vydané faktury s filtrováním | [📖 Detaily](docs/faktura-vydana.md) |
| `faktura-vydana-audit` | DPH a účetní audit faktur | [📖 Detaily](docs/faktura-vydana-audit.md) |

### 🛒 Objednávky (Dativery / Upgates e-shop)

| Nástroj | Popis | Dokumentace |
|---------|-------|-------------|
| `objednavka-prijata` | Přijaté objednávky | [📖 Detaily](docs/objednavka-prijata.md) |
| `objednavka-prijata-storno-audit` | Audit stornovaných objednávek | [📖 Detaily](docs/objednavka-prijata-storno-audit.md) |

---

## 💡 Hlavní výhody

### ⏱️ Ušetřete čas
Co byste kontrolovali ručně celé odpoledne, AI zkontroluje za minuty.

### 🎯 Přesné výsledky
AI zkontroluje každou položku každé faktury - žádné přehlédnuté chyby.

### 🔒 GDPR compliant
Anonymizace osobních údajů na jedno kliknutí (`FLEXIBEE_ANONYMIZE_DATA=true`).

### 🛠️ Snadné použití
Žádné složité API - jen přirozený jazyk v Claude AI.

---

## 📚 Dokumentace

- **[CHANGELOG.md](CHANGELOG.md)** - Historie změn
- **[docs/faktura-vydana.md](docs/faktura-vydana.md)** - Detailní dokumentace faktur
- **[docs/faktura-vydana-audit.md](docs/faktura-vydana-audit.md)** - DPH audit
- **[docs/objednavka-prijata.md](docs/objednavka-prijata.md)** - Přijaté objednávky
- **[docs/objednavka-prijata-storno-audit.md](docs/objednavka-prijata-storno-audit.md)** - Storno audit

---

## 🛠️ Technické požadavky

- Node.js 18+
- ABRA FlexiBee přístup (REST API)
- Claude Desktop nebo jiný MCP klient

---

## 👨‍💻 Autor

**Lukáš Orčík**
Neziskový projekt [OpenMCP](https://openmcp.cz)
Specialista na účetní automatizaci a AI integrace

---

## 📄 Licence

Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)
https://creativecommons.org/licenses/by-nc/4.0/

**Pro komerční využití** kontaktujte autora.

---

## 🤝 Podpora

- 🐛 [Nahlásit chybu](https://github.com/LukasOrcik/abra-flexi-mcp/issues/new?template=bug_report.yml)
- ✨ [Navrhnout funkci](https://github.com/LukasOrcik/abra-flexi-mcp/issues/new?template=feature_request.yml)
- 🚀 [Navrhnout vylepšení](https://github.com/LukasOrcik/abra-flexi-mcp/issues/new?template=improvement.yml)
- 💬 [Diskuze](https://github.com/LukasOrcik/abra-flexi-mcp/discussions)

---

**Ušetřete stovky hodin práce. Vyzkoušejte ho ještě dnes!** 🚀
