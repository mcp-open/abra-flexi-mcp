/**
 * Tests for FlexiFilterBuilder
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { FlexiFilterBuilder } from './filter-builder.js';

describe('FlexiFilterBuilder', () => {
  it('should build empty filter when no filters added', () => {
    const builder = new FlexiFilterBuilder();
    assert.strictEqual(builder.build(), undefined);
    assert.strictEqual(builder.hasFilters(), false);
  });

  it('should build simple equals filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addEquals('field', 'value');
    assert.strictEqual(builder.build(), "(field = 'value')");
  });

  it('should build numeric equals filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addEquals('amount', 100);
    assert.strictEqual(builder.build(), '(amount = 100)');
  });

  it('should build date range filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addDateRange('datVyst', '2024-01-01', '2024-12-31');
    assert.strictEqual(
      builder.build(),
      "(datVyst >= '2024-01-01' and datVyst <= '2024-12-31')"
    );
  });

  it('should build numeric range filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addNumericRange('sumCelkem', 1000, 5000);
    assert.strictEqual(
      builder.build(),
      '(sumCelkem >= 1000 and sumCelkem <= 5000)'
    );
  });

  it('should build like filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addLike('nazev', 'test');
    assert.strictEqual(builder.build(), "(nazev like 'test')");
  });

  it('should build like similar filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addLike('nazev', 'test', true);
    assert.strictEqual(builder.build(), "(nazev like similar 'test')");
  });

  it('should build IN filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addIn('status', ['new', 'pending', 'done']);
    assert.strictEqual(
      builder.build(),
      "(status in ('new', 'pending', 'done'))"
    );
  });

  it('should build IN filter with numbers', () => {
    const builder = new FlexiFilterBuilder();
    builder.addIn('id', [1, 2, 3]);
    assert.strictEqual(builder.build(), '(id in (1, 2, 3))');
  });

  it('should build is null filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addIsNull('deletedAt');
    assert.strictEqual(builder.build(), '(deletedAt is null)');
  });

  it('should build is not null filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addIsNotNull('email');
    assert.strictEqual(builder.build(), '(email is not null)');
  });

  it('should build boolean filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addBoolean('active', true);
    assert.strictEqual(builder.build(), '(active is true)');
  });

  it('should build relation filter with code', () => {
    const builder = new FlexiFilterBuilder();
    builder.addRelation('mena', 'CZK');
    assert.strictEqual(builder.build(), "(mena = 'code:CZK')");
  });

  it('should build relation filter with numeric ID', () => {
    const builder = new FlexiFilterBuilder();
    builder.addRelation('firma', 123);
    assert.strictEqual(builder.build(), '(firma = 123)');
  });

  it('should build tag filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addTag('VIP');
    assert.strictEqual(builder.build(), "(stitky = 'code:VIP')");
  });

  it('should combine multiple filters with AND', () => {
    const builder = new FlexiFilterBuilder();
    builder
      .addDateRange('datVyst', '2024-01-01', '2024-12-31')
      .addEquals('stavUhrK', 'stavUhr.neuhrazeno')
      .addNumericRange('sumCelkem', 1000, undefined);

    assert.strictEqual(
      builder.build(),
      "(datVyst >= '2024-01-01' and datVyst <= '2024-12-31' and stavUhrK = 'stavUhr.neuhrazeno' and sumCelkem >= 1000)"
    );
  });

  it('should build OR filter', () => {
    const builder = new FlexiFilterBuilder();
    builder
      .addEquals('status', 'new')
      .addEquals('status', 'pending');

    assert.strictEqual(
      builder.buildOr(),
      "(status = 'new' or status = 'pending')"
    );
  });

  it('should support custom filter expressions', () => {
    const builder = new FlexiFilterBuilder();
    builder.addCustom("firma.skupFir = 'code:VIP'");
    assert.strictEqual(builder.build(), "(firma.skupFir = 'code:VIP')");
  });

  it('should support begins with filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addBeginsWith('kod', '2024');
    assert.strictEqual(builder.build(), "(kod begins '2024')");
  });

  it('should support ends with filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addEndsWith('kod', '-001');
    assert.strictEqual(builder.build(), "(kod ends '-001')");
  });

  it('should support between filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addBetween('vek', 18, 65);
    assert.strictEqual(builder.build(), '(vek between 18 65)');
  });

  it('should support greater than filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addGreaterThan('amount', 1000);
    assert.strictEqual(builder.build(), '(amount > 1000)');
  });

  it('should support less than or equal filter', () => {
    const builder = new FlexiFilterBuilder();
    builder.addLessThanOrEqual('amount', 5000);
    assert.strictEqual(builder.build(), '(amount <= 5000)');
  });

  it('should count filters correctly', () => {
    const builder = new FlexiFilterBuilder();
    assert.strictEqual(builder.count(), 0);

    builder.addEquals('field1', 'value1');
    assert.strictEqual(builder.count(), 1);

    builder.addEquals('field2', 'value2');
    assert.strictEqual(builder.count(), 2);
  });

  it('should reset filters', () => {
    const builder = new FlexiFilterBuilder();
    builder.addEquals('field', 'value');
    assert.strictEqual(builder.hasFilters(), true);

    builder.reset();
    assert.strictEqual(builder.hasFilters(), false);
    assert.strictEqual(builder.build(), undefined);
  });
});
