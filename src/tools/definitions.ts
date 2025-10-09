/**
 * Tool definitions for Flexi MCP Server
 */

export const TOOL_DEFINITIONS = [
  // Company Information Tool
  {
    name: 'company',
    description: 'Get company information including settings, bank accounts, VAT settings, and other company details from Flexibee',
    inputSchema: {
      type: 'object',
      properties: {
        detail: {
          type: 'string',
          enum: ['id', 'summary', 'full'],
          description: 'Level of detail to return. Default: full',
        },
      },
    },
  },

  // Issued Invoices Tool
  {
    name: 'faktura-vydana',
    description: 'Get issued invoices (faktúry vydané) with advanced filtering, sorting, and detail options. Can retrieve specific invoice by ID or list invoices with comprehensive query capabilities.',
    inputSchema: {
      type: 'object',
      properties: {
        // Basic parameters
        id: {
          type: 'string',
          description: 'Specific invoice ID to retrieve (e.g., "8141"). When provided, returns single invoice with full details.',
        },
        detail: {
          type: 'string',
          enum: ['id', 'summary', 'full', 'compact', 'standard', 'extended', 'audit', 'audit-fast'],
          description: `Level of detail to return:
- "id": Minimal (only ID)
- "summary": Basic fields (Flexibee default, ~15 fields)
- "full": All fields (200+ fields, may cause token limit issues)
- "compact": Optimized for lists (~20 key fields: id, kod, dates, customer, totals, status)
- "standard": Detailed view (~45 fields: adds addresses, contact, payment details)
- "extended": Complete accounting view (~90 fields: adds VAT details, accounts, audit trail)
- "audit": VAT and accounting control (~55 fields + ~35 item fields with @showAs metadata: full audit trail)
- "audit-fast": Ultra-compact audit (~55 fields + ~15 item fields, NO @showAs/@ref: optimized for LLM processing)
- Custom: "custom:field1,field2,..." for specific fields

Default: "summary" for lists, "full" for single invoice.
Recommended: Use "compact" for lists, "standard" for detail views, "audit-fast" for VAT/accounting control with LLM.`,
        },
        includeItems: {
          type: 'boolean',
          description: 'Include invoice line items (polozkyFaktury) in response',
        },
        includeCenik: {
          type: 'boolean',
          description: 'Include product catalog (cenik) data for each invoice item. Automatically includes items.',
        },
        useRelations: {
          type: 'boolean',
          description: 'Use relations parameter instead of includes (alternative API method for loading nested data)',
        },

        // Pagination
        limit: {
          type: 'number',
          description: 'Maximum number of invoices to return when listing',
        },
        offset: {
          type: 'number',
          description: 'Number of invoices to skip for pagination',
        },

        // Filtering parameters
        filter: {
          type: 'string',
          description: 'Raw Flexibee filter string, e.g., "(datVyst >= \'2024-01-01\' and stavUhrK = \'stavUhr.uhrazeno\')"',
        },
        datVystOd: {
          type: 'string',
          description: 'Filter by issue date from (YYYY-MM-DD)',
        },
        datVystDo: {
          type: 'string',
          description: 'Filter by issue date to (YYYY-MM-DD)',
        },
        datSplatOd: {
          type: 'string',
          description: 'Filter by due date from (YYYY-MM-DD)',
        },
        datSplatDo: {
          type: 'string',
          description: 'Filter by due date to (YYYY-MM-DD)',
        },
        stavUhrK: {
          type: 'string',
          description: 'Filter by payment status (e.g., "stavUhr.uhrazeno", "stavUhr.neuhrazeno")',
        },
        firma: {
          type: 'string',
          description: 'Filter by customer ID or code',
        },
        sumCelkemOd: {
          type: 'number',
          description: 'Filter by minimum total amount',
        },
        sumCelkemDo: {
          type: 'number',
          description: 'Filter by maximum total amount',
        },
        stitky: {
          type: 'string',
          description: 'Filter by tags (štítky)',
        },

        // Ordering parameters
        order: {
          oneOf: [
            { type: 'string' },
            { type: 'array', items: { type: 'string' } }
          ],
          description: 'Order by field(s). Single field as string or multiple fields as array. Examples: "kod", "datVyst", ["datVyst", "sumCelkem"]',
        },
        orderDirection: {
          type: 'string',
          enum: ['asc', 'desc', 'A', 'D'],
          description: 'Order direction for simple ordering (only used with single order field)',
        },

        // Extended information
        addRowCount: {
          type: 'boolean',
          description: 'Add total count of records to response (useful for pagination)',
        },
        noExtIds: {
          type: 'boolean',
          description: 'Exclude external IDs for better performance',
        },
        noIds: {
          type: 'boolean',
          description: 'Exclude internal IDs from response',
        },
        codeAsId: {
          type: 'boolean',
          description: 'Use code as identifier instead of internal ID',
        },
      },
    },
  },

  // Issued Invoices Audit Tool
  {
    name: 'faktura-vydana-audit',
    description: '[AUDIT] VAT and accounting audit for issued invoices. Ultra-compact mode optimized for LLM analysis. Returns only critical fields: VAT classification, posting accounts, country codes, document types. Automatically includes invoice items with minimal fields (9 per item). Perfect for detecting accounting errors and OSS regime issues.',
    inputSchema: {
      type: 'object',
      properties: {
        // Basic parameters
        id: {
          type: 'string',
          description: 'Specific invoice ID to audit (e.g., "10045"). Required.',
        },

        // Filtering parameters (for listing)
        filter: {
          type: 'string',
          description: 'Raw Flexibee filter string for listing invoices to audit',
        },
        datVystOd: {
          type: 'string',
          description: 'Filter by issue date from (YYYY-MM-DD)',
        },
        datVystDo: {
          type: 'string',
          description: 'Filter by issue date to (YYYY-MM-DD)',
        },
        firma: {
          type: 'string',
          description: 'Filter by customer ID or code',
        },
        stitky: {
          type: 'string',
          description: 'Filter by tags (štítky)',
        },

        // Pagination
        limit: {
          type: 'number',
          description: 'Maximum number of invoices to audit (default: 10, max: 50)',
        },
        offset: {
          type: 'number',
          description: 'Number of invoices to skip for pagination',
        },

        // Ordering
        order: {
          oneOf: [
            { type: 'string' },
            { type: 'array', items: { type: 'string' } }
          ],
          description: 'Order by field(s). Examples: "datVyst", ["datVyst", "kod"]',
        },
        orderDirection: {
          type: 'string',
          enum: ['asc', 'desc', 'A', 'D'],
          description: 'Order direction (default: desc for dates)',
        },
      },
    },
  },

  // Received Orders Tool
  {
    name: 'objednavka-prijata',
    description: 'Get received orders (objednávky prijaté) with advanced filtering, sorting, and detail options. Can retrieve specific order by ID or list orders with comprehensive query capabilities.',
    inputSchema: {
      type: 'object',
      properties: {
        id: {
          type: 'string',
          description: 'Specific order ID to retrieve (e.g., "9120").',
        },
        detail: {
          type: 'string',
          enum: ['id', 'summary', 'full'],
          description: 'Level of detail to return. Default: "summary" for lists, "full" for single order.',
        },
        includeItems: {
          type: 'boolean',
          description: 'Include order line items (polozkyObchDokladu) in response',
        },
        limit: {
          type: 'number',
          description: 'Maximum number of orders to return when listing',
        },
        offset: {
          type: 'number',
          description: 'Number of orders to skip for pagination',
        },
        filter: {
          type: 'string',
          description: 'Raw Flexibee filter string',
        },
        datVystOd: {
          type: 'string',
          description: 'Filter by issue date from (YYYY-MM-DD)',
        },
        datVystDo: {
          type: 'string',
          description: 'Filter by issue date to (YYYY-MM-DD)',
        },
        cisObj: {
          type: 'string',
          description: 'Filter by order number (e.g., "O23286")',
        },
        firma: {
          type: 'string',
          description: 'Filter by customer ID or code',
        },
        stitky: {
          type: 'string',
          description: 'Filter by tags (štítky)',
        },
        order: {
          oneOf: [
            { type: 'string' },
            { type: 'array', items: { type: 'string' } }
          ],
          description: 'Order by field(s)',
        },
        orderDirection: {
          type: 'string',
          enum: ['asc', 'desc', 'A', 'D'],
          description: 'Order direction',
        },
        addRowCount: {
          type: 'boolean',
          description: 'Add total count of records to response',
        },
        noExtIds: {
          type: 'boolean',
          description: 'Exclude external IDs for better performance',
        },
        noIds: {
          type: 'boolean',
          description: 'Exclude internal IDs from response',
        },
        codeAsId: {
          type: 'boolean',
          description: 'Use code as identifier instead of internal ID',
        },
      },
    },
  },

  // Received Orders Storno Audit Tool
  {
    name: 'objednavka-prijata-storno-audit',
    description: '[STORNO AUDIT] Storno detection audit for received orders from Dativery integration. Automatically filters and returns ONLY orders with storno issues: orders marked as storno (storno=true). Includes order items with storno-specific fields. Perfect for checking cancelled orders from e-shop.',
    inputSchema: {
      type: 'object',
      properties: {
        // Basic parameters
        id: {
          type: 'string',
          description: 'Specific order ID to audit (e.g., "9120"). Required for single order check.',
        },

        // Filtering parameters (for listing)
        filter: {
          type: 'string',
          description: 'Raw Flexibee filter string for listing orders to audit',
        },
        datVystOd: {
          type: 'string',
          description: 'Filter by issue date from (YYYY-MM-DD)',
        },
        datVystDo: {
          type: 'string',
          description: 'Filter by issue date to (YYYY-MM-DD)',
        },
        cisObj: {
          type: 'string',
          description: 'Filter by order number (e.g., "O23286")',
        },

        // Pagination
        limit: {
          type: 'number',
          description: 'Maximum number of orders to audit (default: 10, max: 50)',
        },
        offset: {
          type: 'number',
          description: 'Number of orders to skip for pagination',
        },

        // Ordering
        order: {
          oneOf: [
            { type: 'string' },
            { type: 'array', items: { type: 'string' } }
          ],
          description: 'Order by field(s). Examples: "datVyst", ["datVyst", "kod"]',
        },
        orderDirection: {
          type: 'string',
          enum: ['asc', 'desc', 'A', 'D'],
          description: 'Order direction (default: desc for dates)',
        },
      },
    },
  },
];