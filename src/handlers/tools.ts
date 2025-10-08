/**
 * Tool handlers for Flexi MCP Server
 */

import { FlexiClient } from '../client/index.js';
import { FakturaVydanaQueryParams } from '../types.js';
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

    default:
      throw new ValidationError(`Unknown tool: ${toolName}`);
  }
}