# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Nový tool: `objednavka-prijata`** - Základní nástroj pro načítání přijatých objednávek
- **Nový tool: `objednavka-prijata-storno-audit`** - Audit stornovaných objednávek z Dativery
  - Inteligentné stránkovanie (načítá dávky po 100 až kým nenájde dostatok storno)
  - 4 indikátory storna (storno flag, stavDoklObch, stavUzivK, cisSml)
  - 92% redukcia dát (24 polí v hlavičke, 14 v položkách)
- GitHub Issue Templates (bug report, feature request, improvement)
- ObjednavkaClient pre prácu s prijatými objednávkami

### Changed
- Aktualizované informácie o autorovi (OpenMCP - https://openmcp.cz)

### Fixed
- Storno detekcia v Dativery integrácii (riešený problém kde storno flag nie je nastavený)
- False positives pri sumCelkem=0 (odstránené z finálnej detekcie)

### Removed
- Sekcia "Případové studie" z README

## [0.1.0] - 2025-01-XX

### Added
- Prvotná verzia MCP servera
- Tools: company, faktura-vydana, faktura-vydana-audit
- Detail módy a GDPR anonymizácia
- Test suite (94 testov)
