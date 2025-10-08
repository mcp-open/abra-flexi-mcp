/**
 * Tests for validation functions
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  validateDateFormat,
  validateDetailLevel,
  validatePaymentStatus,
  validateOrderDirection,
  validateNumericRange,
  validatePagination,
  estimateTokenCount,
  validateResponseSize,
} from './index.js';
import { ValidationError } from '../errors/index.js';

describe('Validators', () => {
  describe('validateDateFormat', () => {
    it('should accept valid date format', () => {
      assert.doesNotThrow(() => validateDateFormat('2024-01-15', 'testDate'));
    });

    it('should reject invalid date format', () => {
      assert.throws(
        () => validateDateFormat('15-01-2024', 'testDate'),
        ValidationError
      );
    });

    it('should reject invalid date values', () => {
      assert.throws(
        () => validateDateFormat('2024-13-01', 'testDate'),
        ValidationError
      );
    });

    it('should reject malformed date', () => {
      assert.throws(
        () => validateDateFormat('not-a-date', 'testDate'),
        ValidationError
      );
    });
  });

  describe('validateDetailLevel', () => {
    it('should accept valid detail levels', () => {
      assert.doesNotThrow(() => validateDetailLevel('id'));
      assert.doesNotThrow(() => validateDetailLevel('summary'));
      assert.doesNotThrow(() => validateDetailLevel('full'));
    });

    it('should accept custom detail format', () => {
      assert.doesNotThrow(() => validateDetailLevel('custom:kod,nazev'));
    });

    it('should reject invalid detail level', () => {
      assert.throws(
        () => validateDetailLevel('invalid'),
        ValidationError
      );
    });
  });

  describe('validatePaymentStatus', () => {
    it('should accept valid payment statuses', () => {
      assert.doesNotThrow(() => validatePaymentStatus('stavUhr.uhrazeno'));
      assert.doesNotThrow(() => validatePaymentStatus('stavUhr.neuhrazeno'));
      assert.doesNotThrow(() => validatePaymentStatus('stavUhr.castUhr'));
      assert.doesNotThrow(() => validatePaymentStatus('stavUhr.preplaceno'));
    });

    it('should reject invalid payment status', () => {
      assert.throws(
        () => validatePaymentStatus('invalid'),
        ValidationError
      );
    });
  });

  describe('validateOrderDirection', () => {
    it('should accept valid order directions', () => {
      assert.doesNotThrow(() => validateOrderDirection('asc'));
      assert.doesNotThrow(() => validateOrderDirection('desc'));
      assert.doesNotThrow(() => validateOrderDirection('A'));
      assert.doesNotThrow(() => validateOrderDirection('D'));
    });

    it('should reject invalid order direction', () => {
      assert.throws(
        () => validateOrderDirection('invalid'),
        ValidationError
      );
    });
  });

  describe('validateNumericRange', () => {
    it('should accept value within range', () => {
      assert.doesNotThrow(() => validateNumericRange(50, 0, 100));
    });

    it('should accept value at minimum', () => {
      assert.doesNotThrow(() => validateNumericRange(0, 0, 100));
    });

    it('should accept value at maximum', () => {
      assert.doesNotThrow(() => validateNumericRange(100, 0, 100));
    });

    it('should reject value below minimum', () => {
      assert.throws(
        () => validateNumericRange(-1, 0, 100, 'testField'),
        ValidationError
      );
    });

    it('should reject value above maximum', () => {
      assert.throws(
        () => validateNumericRange(101, 0, 100, 'testField'),
        ValidationError
      );
    });

    it('should work with only minimum', () => {
      assert.doesNotThrow(() => validateNumericRange(100, 0, undefined));
      assert.throws(
        () => validateNumericRange(-1, 0, undefined),
        ValidationError
      );
    });

    it('should work with only maximum', () => {
      assert.doesNotThrow(() => validateNumericRange(-100, undefined, 100));
      assert.throws(
        () => validateNumericRange(101, undefined, 100),
        ValidationError
      );
    });
  });

  describe('validatePagination', () => {
    it('should accept valid pagination', () => {
      assert.doesNotThrow(() => validatePagination(10, 0));
    });

    it('should accept large limits', () => {
      assert.doesNotThrow(() => validatePagination(1000, 500));
    });

    it('should reject negative limit', () => {
      assert.throws(
        () => validatePagination(0, 0),
        ValidationError
      );
    });

    it('should reject limit exceeding maximum', () => {
      assert.throws(
        () => validatePagination(10001, 0),
        ValidationError
      );
    });

    it('should reject negative offset', () => {
      assert.throws(
        () => validatePagination(10, -1),
        ValidationError
      );
    });

    it('should work with undefined values', () => {
      assert.doesNotThrow(() => validatePagination(undefined, undefined));
      assert.doesNotThrow(() => validatePagination(10, undefined));
      assert.doesNotThrow(() => validatePagination(undefined, 0));
    });
  });

  describe('estimateTokenCount', () => {
    it('should estimate tokens correctly', () => {
      const text = 'a'.repeat(400); // 400 characters
      const tokens = estimateTokenCount(text);
      assert.strictEqual(tokens, 100); // 400 / 4 = 100
    });

    it('should round up fractional tokens', () => {
      const text = 'a'.repeat(401); // 401 characters
      const tokens = estimateTokenCount(text);
      assert.strictEqual(tokens, 101); // ceil(401 / 4) = 101
    });

    it('should handle empty string', () => {
      const tokens = estimateTokenCount('');
      assert.strictEqual(tokens, 0);
    });
  });

  describe('validateResponseSize', () => {
    it('should accept response within size limit', () => {
      const data = { small: 'data' };
      const result = validateResponseSize(data, 1000);
      assert.strictEqual(result.valid, true);
      assert.ok(result.estimatedTokens > 0);
    });

    it('should reject response exceeding size limit', () => {
      const largeData = { data: 'x'.repeat(100000) };
      const result = validateResponseSize(largeData, 1000);
      assert.strictEqual(result.valid, false);
      assert.ok(result.message);
      assert.ok(result.estimatedTokens > 1000);
    });

    it('should use default max tokens', () => {
      const data = { test: 'data' };
      const result = validateResponseSize(data);
      assert.strictEqual(result.valid, true);
    });

    it('should return estimated tokens even when valid', () => {
      const data = { test: 'data' };
      const result = validateResponseSize(data, 10000);
      assert.ok(result.estimatedTokens !== undefined);
      assert.ok(result.estimatedTokens > 0);
    });
  });
});
