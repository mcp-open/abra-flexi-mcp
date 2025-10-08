# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Detail modes system** for optimized data retrieval
  - `compact` mode (~20 fields) - optimized for invoice lists and dashboards
  - `standard` mode (~45 fields) - detailed view for invoice display and printing
  - `extended` mode (~90 fields) - complete accounting overview
  - `audit` mode (~55 header + ~35 item fields) - VAT and accounting control with metadata
  - `audit-fast` mode (~35 header + ~9 item fields) - ultra-compact audit for LLM processing
- **`faktura-vydana-audit` tool** - specialized VAT and accounting audit tool
  - Automatically uses `audit-fast` mode with items included
  - 93% data reduction compared to full mode
  - Perfect for detecting accounting errors and OSS regime issues
  - Default limit: 10 invoices, max limit: 50
- **Server-side response filtering** for audit modes
  - Fetches full detail from FlexiBee API
  - Filters response to keep only critical fields
  - Removes @showAs/@ref metadata in audit-fast mode
  - Filters both invoice header and line items
- **Configuration module** (`src/config/detail-modes.ts`)
  - Centralized field definitions for all detail modes
  - Separate field sets for invoice headers and items
  - Utility functions for filtering and field selection
  - Type-safe field definitions with readonly arrays
- **Enhanced FlexiBee client**
  - Smart detail parameter building
  - Automatic detail mode conversion to FlexiBee format
  - Audit response filtering with configurable metadata inclusion
- **Comprehensive test suite**
  - Unit tests for detail mode configurations
  - Tests for field filtering functions
  - Validation of field counts and presence

### Changed
- Extended `faktura-vydana` tool with new detail modes
- Updated validators to support all new detail modes
- Enhanced tool descriptions with detailed mode explanations
- Improved type definitions with `DetailMode` type

### Technical
- Added `filterFields()` utility for selective field extraction
- Added `filterInvoiceItemsForAudit()` for item filtering
- Enhanced `FakturaClient.buildDetailParam()` with audit mode handling
- Enhanced `FakturaClient.filterAuditResponse()` with fast mode support

## [0.1.0] - 2025-10-08

### Added
- Initial release of ABRA Flexi MCP Server
- `company` tool - Get company information with configurable detail levels
- `faktura-vydana` tool - Query issued invoices with advanced filtering
  - Date range filtering (datVystOd, datVystDo, datSplatOd, datSplatDo)
  - Payment status filtering (stavUhrK)
  - Customer filtering (firma)
  - Amount range filtering (sumCelkemOd, sumCelkemDo)
  - Pagination support (limit, offset)
  - Sorting capabilities (order, orderDirection)
  - Detail level control (id, summary, full, custom)
  - Include nested data (includeItems, includeCenik)
- Resource endpoints:
  - `flexibee://evidences` - List available Flexi evidences
  - `flexibee://company-info` - Get company configuration
- Input validation for all parameters
- Response size validation (25,000 token limit)
- Automatic suggestions when response size exceeds limit
- Data anonymization support (GDPR compliance)
- Custom error hierarchy for better error handling
- Clean architecture with separated concerns:
  - Configuration management
  - Error handling
  - Input validation
  - Tool handlers
  - Resource handlers

### Features
- TypeScript with strict typing
- Environment-based configuration through MCP client
- Support for custom detail levels with field selection
- Token-based response size estimation
- Helpful error messages with actionable suggestions

### Technical
- Node.js 18+ required
- MCP SDK 1.19.1
- Axios 1.12.2
- TypeScript 5.7.2

### Documentation
- Czech/Slovak README (README.md)

### License
- CC-BY-NC-4.0 (Creative Commons Attribution-NonCommercial 4.0 International)

[0.1.0]: https://github.com/LukasOrcik/abra-flexi-mcp/releases/tag/v0.1.0
