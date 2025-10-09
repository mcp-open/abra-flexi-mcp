/**
 * Tool handlers for Flexi MCP Server
 */

import { FlexiClient } from '../client/index.js';
import { FakturaVydanaQueryParams, ObjednavkaPrijataQueryParams, FlexiResponse } from '../types.js';
import {
  validateDateFormat,
  validateDetailLevel,
  validatePaymentStatus,
  validateOrderDirection,
  validatePagination,
  validateNumericRange,
  validateResponseSize,
} from '../validators/index.js';
import { ValidationError } from '../errors/index.js';
import { filterOrderItemsForStornoAudit, filterOrderHeaderForStornoAudit } from '../config/detail-modes.js';

export interface ToolResult {
  content: Array<{
    type: 'text';
    text: string;
  }>;
  isError?: boolean;
  [key: string]: any; // Allow additional properties for MCP compatibility
}

/**
 * Handles the company tool
 */
export async function handleCompanyTool(
  client: FlexiClient,
  args: any
): Promise<ToolResult> {
  const detail = args?.detail || 'full';

  // Validate detail level - always validate, not just when truthy
  if (!['id', 'summary', 'full'].includes(detail)) {
    throw new ValidationError(`Invalid detail level for company: ${detail}`, 'detail');
  }

  const result = await client.getCompanyInfo(detail);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result, null, 2),
      },
    ],
  };
}

/**
 * Validates faktura-vydana parameters
 */
function validateFakturaVydanaParams(args: any): FakturaVydanaQueryParams {
  const params: FakturaVydanaQueryParams = {};

  // Basic parameters
  if (args?.id !== undefined) {
    params.id = String(args.id);
  }

  if (args?.detail !== undefined) {
    validateDetailLevel(args.detail);
    params.detail = args.detail;
  }

  // Boolean parameters
  if (args?.includeItems !== undefined) {
    params.includeItems = Boolean(args.includeItems);
  }

  if (args?.includeCenik !== undefined) {
    params.includeCenik = Boolean(args.includeCenik);
  }

  if (args?.useRelations !== undefined) {
    params.useRelations = Boolean(args.useRelations);
  }

  // Pagination
  if (args?.limit !== undefined) {
    params.limit = Number(args.limit);
  }

  if (args?.offset !== undefined) {
    params.offset = Number(args.offset);
  }

  validatePagination(params.limit, params.offset);

  // Date filtering
  if (args?.datVystOd !== undefined) {
    validateDateFormat(args.datVystOd, 'datVystOd');
    params.datVystOd = args.datVystOd;
  }

  if (args?.datVystDo !== undefined) {
    validateDateFormat(args.datVystDo, 'datVystDo');
    params.datVystDo = args.datVystDo;
  }

  if (args?.datSplatOd !== undefined) {
    validateDateFormat(args.datSplatOd, 'datSplatOd');
    params.datSplatOd = args.datSplatOd;
  }

  if (args?.datSplatDo !== undefined) {
    validateDateFormat(args.datSplatDo, 'datSplatDo');
    params.datSplatDo = args.datSplatDo;
  }

  // Status and customer
  if (args?.stavUhrK !== undefined) {
    validatePaymentStatus(args.stavUhrK);
    params.stavUhrK = args.stavUhrK;
  }

  if (args?.firma !== undefined) {
    params.firma = String(args.firma);
  }

  // Amount filtering
  if (args?.sumCelkemOd !== undefined) {
    params.sumCelkemOd = Number(args.sumCelkemOd);
    validateNumericRange(params.sumCelkemOd, 0, undefined, 'sumCelkemOd');
  }

  if (args?.sumCelkemDo !== undefined) {
    params.sumCelkemDo = Number(args.sumCelkemDo);
    validateNumericRange(params.sumCelkemDo, 0, undefined, 'sumCelkemDo');
  }

  // Validate amount range
  if (params.sumCelkemOd !== undefined && params.sumCelkemDo !== undefined) {
    if (params.sumCelkemOd > params.sumCelkemDo) {
      throw new ValidationError(
        `sumCelkemOd (${params.sumCelkemOd}) cannot be greater than sumCelkemDo (${params.sumCelkemDo})`
      );
    }
  }

  // Tags
  if (args?.stitky !== undefined) {
    params.stitky = String(args.stitky);
  }

  // Raw filter
  if (args?.filter !== undefined) {
    params.filter = String(args.filter);
  }

  // Ordering
  if (args?.order !== undefined) {
    params.order = args.order;
  }

  if (args?.orderDirection !== undefined) {
    validateOrderDirection(args.orderDirection);
    params.orderDirection = args.orderDirection;
  }

  // Extended information flags
  if (args?.addRowCount !== undefined) {
    params.addRowCount = Boolean(args.addRowCount);
  }

  if (args?.noExtIds !== undefined) {
    params.noExtIds = Boolean(args.noExtIds);
  }

  if (args?.noIds !== undefined) {
    params.noIds = Boolean(args.noIds);
  }

  if (args?.codeAsId !== undefined) {
    params.codeAsId = Boolean(args.codeAsId);
  }

  return params;
}

/**
 * Handles the faktura-vydana tool
 */
export async function handleFakturaVydanaTool(
  client: FlexiClient,
  args: any
): Promise<ToolResult> {
  const params = validateFakturaVydanaParams(args);
  const result = await client.getFakturyVydane(params);

  // Validate response size
  const sizeCheck = validateResponseSize(result);

  if (!sizeCheck.valid) {
    // Build helpful suggestions based on current parameters
    const suggestions: string[] = [];

    if (!params.limit || params.limit > 10) {
      suggestions.push('- Reduce limit parameter (currently: ' + (params.limit || 'default 20') + ')');
    }

    if (params.includeItems || params.includeCenik) {
      suggestions.push('- Remove includeItems or includeCenik to exclude nested data');
    }

    if (params.detail === 'full' || !params.detail) {
      suggestions.push('- Use detail=summary or detail=id for less data');
    }

    if (!params.datVystOd && !params.datVystDo && !params.filter) {
      suggestions.push('- Add date filtering (datVystOd, datVystDo)');
    }

    const suggestionText = suggestions.length > 0
      ? '\n\nSuggestions to reduce response size:\n' + suggestions.join('\n')
      : '';

    throw new ValidationError(
      sizeCheck.message + suggestionText,
      'response_size'
    );
  }

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result, null, 2),
      },
    ],
  };
}

/**
 * Handles the faktura-vydana-audit tool
 * Automatically uses audit-fast mode with items included
 */
export async function handleFakturaVydanaAuditTool(
  client: FlexiClient,
  args: any
): Promise<ToolResult> {
  const params = validateFakturaVydanaParams(args);

  // Force audit-fast mode and include items
  params.detail = 'audit-fast';
  params.includeItems = true;

  // Set default limit for audit to prevent overwhelming responses
  if (!params.limit) {
    params.limit = 10;
  }

  // Enforce max limit for audit
  if (params.limit > 50) {
    throw new ValidationError('Audit tool maximum limit is 50 invoices');
  }

  const result = await client.getFakturyVydane(params);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result, null, 2),
      },
    ],
  };
}

/**
 * Validates objednavka-prijata parameters
 */
function validateObjednavkaPrijataParams(args: any): ObjednavkaPrijataQueryParams {
  const params: ObjednavkaPrijataQueryParams = {};

  // Basic parameters
  if (args?.id !== undefined) {
    params.id = String(args.id);
  }

  if (args?.detail !== undefined) {
    if (!['id', 'summary', 'full'].includes(args.detail)) {
      throw new ValidationError(`Invalid detail level for objednavka-prijata: ${args.detail}`, 'detail');
    }
    params.detail = args.detail;
  }

  if (args?.includeItems !== undefined) {
    params.includeItems = Boolean(args.includeItems);
  }

  // Pagination
  if (args?.limit !== undefined) {
    params.limit = Number(args.limit);
  }

  if (args?.offset !== undefined) {
    params.offset = Number(args.offset);
  }

  validatePagination(params.limit, params.offset);

  // Date filtering
  if (args?.datVystOd !== undefined) {
    validateDateFormat(args.datVystOd, 'datVystOd');
    params.datVystOd = args.datVystOd;
  }

  if (args?.datVystDo !== undefined) {
    validateDateFormat(args.datVystDo, 'datVystDo');
    params.datVystDo = args.datVystDo;
  }

  // Order number and customer
  if (args?.cisObj !== undefined) {
    params.cisObj = String(args.cisObj);
  }

  if (args?.firma !== undefined) {
    params.firma = String(args.firma);
  }

  // Tags
  if (args?.stitky !== undefined) {
    params.stitky = String(args.stitky);
  }

  // Raw filter
  if (args?.filter !== undefined) {
    params.filter = String(args.filter);
  }

  // Ordering
  if (args?.order !== undefined) {
    params.order = args.order;
  }

  if (args?.orderDirection !== undefined) {
    validateOrderDirection(args.orderDirection);
    params.orderDirection = args.orderDirection;
  }

  // Extended information flags
  if (args?.addRowCount !== undefined) {
    params.addRowCount = Boolean(args.addRowCount);
  }

  if (args?.noExtIds !== undefined) {
    params.noExtIds = Boolean(args.noExtIds);
  }

  if (args?.noIds !== undefined) {
    params.noIds = Boolean(args.noIds);
  }

  if (args?.codeAsId !== undefined) {
    params.codeAsId = Boolean(args.codeAsId);
  }

  return params;
}

/**
 * Handles the objednavka-prijata tool
 */
export async function handleObjednavkaPrijataTool(
  client: FlexiClient,
  args: any
): Promise<ToolResult> {
  const params = validateObjednavkaPrijataParams(args);
  const result = await client.getObjednavkyPrijate(params);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result, null, 2),
      },
    ],
  };
}

/**
 * Helper function to check if order is storno
 * Note: sumCelkem=0 is NOT used here - it's only for pre-filtering
 * (can be 0 due to rounding, discounts, etc. without being cancelled)
 */
function isStornoOrder(order: any): boolean {
  // Check storno indicators (Dativery integration issue)
  // 1. storno flag
  const stornoFlag = String(order.storno).toLowerCase() === 'true';

  // 2. stavDoklObch contains "STORNO"
  const stavDoklObch = String(order.stavDoklObch || '').toUpperCase();
  const hasStornoStav = stavDoklObch.includes('STORNO');

  // 3. stavUzivK contains "storno"
  const stavUzivK = String(order.stavUzivK || '').toLowerCase();
  const hasStornoUzivStav = stavUzivK.includes('storno');

  // 4. cisSml equals "Storno"
  const cisSml = String(order.cisSml || '');
  const hasStornoSml = cisSml === 'Storno';

  // Order is storno if ANY of these indicators is true
  // Note: sumCelkem=0 is intentionally NOT checked here
  return stornoFlag || hasStornoStav || hasStornoUzivStav || hasStornoSml;
}

/**
 * Handles the objednavka-prijata-storno-audit tool
 * Specialized for storno detection in orders from Dativery integration
 * Uses intelligent pagination with buffer to find requested number of storno orders
 */
export async function handleObjednavkaPrijataStornoAuditTool(
  client: FlexiClient,
  args: any
): Promise<ToolResult> {
  const params = validateObjednavkaPrijataParams(args);

  // Save requested limit (how many storno orders user wants)
  const requestedLimit = params.limit || 10;

  // Enforce max limit
  if (requestedLimit > 50) {
    throw new ValidationError('Audit tool maximum limit is 50 storno orders');
  }

  // Use full detail to get all fields
  params.detail = 'full';
  params.includeItems = true;

  // Default ordering: newest orders first (by last update)
  // Use lastUpdate to catch recently cancelled orders
  if (!params.order) {
    params.order = 'lastUpdate';
    params.orderDirection = 'desc';
  }

  // INTELLIGENT PAGINATION:
  // Fetch orders in batches until we have enough storno orders
  const stornoOrders: any[] = [];
  const BATCH_SIZE = 100; // Fetch 100 orders at a time
  const MAX_FETCH = 1000; // Safety limit: don't fetch more than 1000 total
  let currentOffset = params.offset || 0;
  let totalFetched = 0;

  console.error(`[STORNO-AUDIT] Looking for ${requestedLimit} storno orders...`);

  while (stornoOrders.length < requestedLimit && totalFetched < MAX_FETCH) {
    // Set batch parameters
    params.limit = BATCH_SIZE;
    params.offset = currentOffset;

    console.error(`[STORNO-AUDIT] Fetching batch: offset=${currentOffset}, limit=${BATCH_SIZE}`);

    const result = await client.getObjednavkyPrijate(params);

    if (!result.winstrom || !result.winstrom['objednavka-prijata']) {
      break; // No more data
    }

    const orders = result.winstrom['objednavka-prijata'];

    if (!Array.isArray(orders) || orders.length === 0) {
      console.error(`[STORNO-AUDIT] No more orders found, stopping`);
      break; // No more orders in database
    }

    console.error(`[STORNO-AUDIT] Received ${orders.length} orders in batch`);

    // Filter storno orders from this batch
    const batchStornoOrders = orders.filter(order => {
      const isStorno = isStornoOrder(order);

      if (isStorno) {
        console.error(`  ✅ STORNO: ${order.id} (${order.kod}): stavDoklObch="${order.stavDoklObch}", cisSml="${order.cisSml}", sum="${order.sumCelkem}"`);
      }

      return isStorno;
    });

    console.error(`[STORNO-AUDIT] Found ${batchStornoOrders.length} storno orders in batch`);

    // Add to results
    stornoOrders.push(...batchStornoOrders);

    // Update counters
    totalFetched += orders.length;
    currentOffset += BATCH_SIZE;

    // Stop if we have enough storno orders
    if (stornoOrders.length >= requestedLimit) {
      console.error(`[STORNO-AUDIT] Reached requested limit of ${requestedLimit} storno orders`);
      break;
    }

    // Stop if we got fewer orders than batch size (no more data)
    if (orders.length < BATCH_SIZE) {
      console.error(`[STORNO-AUDIT] Reached end of data (got ${orders.length} < ${BATCH_SIZE})`);
      break;
    }
  }

  console.error(`[STORNO-AUDIT] Total fetched: ${totalFetched} orders, found: ${stornoOrders.length} storno orders`);

  // Limit to requested number and filter to compact fields
  const finalOrders = stornoOrders.slice(0, requestedLimit).map(order => {
    // Filter header to compact fields (no @ref/@showAs)
    const filtered = filterOrderHeaderForStornoAudit(order);

    // Filter items to compact fields
    if (order.polozkyObchDokladu && Array.isArray(order.polozkyObchDokladu)) {
      filtered.polozkyObchDokladu = filterOrderItemsForStornoAudit(order.polozkyObchDokladu);
    }

    return filtered;
  });

  // Build response
  const response: FlexiResponse = {
    success: 'true',
    winstrom: {
      '@version': '1.0',
      'objednavka-prijata': finalOrders
    }
  };

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(response, null, 2),
      },
    ],
  };
}

/**
 * Main tool handler dispatcher
 */
export async function handleToolCall(
  toolName: string,
  args: any,
  client: FlexiClient
): Promise<ToolResult> {
  switch (toolName) {
    case 'company':
      return handleCompanyTool(client, args);

    case 'faktura-vydana':
      return handleFakturaVydanaTool(client, args);

    case 'faktura-vydana-audit':
      return handleFakturaVydanaAuditTool(client, args);

    case 'objednavka-prijata':
      return handleObjednavkaPrijataTool(client, args);

    case 'objednavka-prijata-storno-audit':
      return handleObjednavkaPrijataStornoAuditTool(client, args);

    default:
      throw new ValidationError(`Unknown tool: ${toolName}`);
  }
}