/**
 * Input validation utilities for Flexi MCP Server
 */

import { ValidationError } from '../errors/index.js';

/**
 * Validates date format YYYY-MM-DD
 */
export function validateDateFormat(date: string, fieldName: string): void {
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(date)) {
    throw new ValidationError(
      `Invalid date format for ${fieldName}. Expected YYYY-MM-DD, got: ${date}`,
      fieldName
    );
  }

  // Check if date is valid
  const parsed = new Date(date + 'T00:00:00');
  if (isNaN(parsed.getTime())) {
    throw new ValidationError(
      `Invalid date value for ${fieldName}: ${date}`,
      fieldName
    );
  }
}

/**
 * Validates detail level parameter
 */
export function validateDetailLevel(detail: string): void {
  const validLevels = ['id', 'summary', 'full', 'compact', 'standard', 'extended', 'audit', 'audit-fast'];

  // Allow custom detail format
  if (detail.startsWith('custom:')) {
    return;
  }

  if (!validLevels.includes(detail)) {
    throw new ValidationError(
      `Invalid detail level. Expected one of: ${validLevels.join(', ')}, or custom:field1,field2. Got: ${detail}`,
      'detail'
    );
  }
}

/**
 * Validates payment status
 */
export function validatePaymentStatus(status: string): void {
  const validStatuses = [
    'stavUhr.uhrazeno',
    'stavUhr.neuhrazeno',
    'stavUhr.castUhr',
    'stavUhr.preplaceno'
  ];

  if (!validStatuses.includes(status)) {
    throw new ValidationError(
      `Invalid payment status. Expected one of: ${validStatuses.join(', ')}. Got: ${status}`,
      'stavUhrK'
    );
  }
}

/**
 * Validates order direction
 */
export function validateOrderDirection(direction: string): void {
  const validDirections = ['asc', 'desc', 'A', 'D'];

  if (!validDirections.includes(direction)) {
    throw new ValidationError(
      `Invalid order direction. Expected one of: ${validDirections.join(', ')}. Got: ${direction}`,
      'orderDirection'
    );
  }
}

/**
 * Validates numeric range
 */
export function validateNumericRange(
  value: number,
  min?: number,
  max?: number,
  fieldName?: string
): void {
  if (min !== undefined && value < min) {
    throw new ValidationError(
      `Value ${value} is below minimum ${min}${fieldName ? ` for ${fieldName}` : ''}`,
      fieldName
    );
  }

  if (max !== undefined && value > max) {
    throw new ValidationError(
      `Value ${value} exceeds maximum ${max}${fieldName ? ` for ${fieldName}` : ''}`,
      fieldName
    );
  }
}

/**
 * Validates pagination parameters
 */
export function validatePagination(limit?: number, offset?: number): void {
  if (limit !== undefined) {
    validateNumericRange(limit, 1, 10000, 'limit');
  }

  if (offset !== undefined) {
    validateNumericRange(offset, 0, undefined, 'offset');
  }
}

/**
 * Estimates token count for a JSON response
 * Uses approximate calculation: ~4 characters per token
 */
export function estimateTokenCount(text: string): number {
  return Math.ceil(text.length / 4);
}

/**
 * Validates response size against token limit
 */
export function validateResponseSize(
  data: any,
  maxTokens: number = 25000
): { valid: boolean; estimatedTokens: number; message?: string } {
  const jsonString = JSON.stringify(data, null, 2);
  const estimatedTokens = estimateTokenCount(jsonString);

  if (estimatedTokens > maxTokens) {
    return {
      valid: false,
      estimatedTokens,
      message: `Response size (${estimatedTokens} tokens) exceeds maximum allowed (${maxTokens} tokens). Please use pagination, filtering, or limit parameters to reduce the response size.`,
    };
  }

  return {
    valid: true,
    estimatedTokens,
  };
}