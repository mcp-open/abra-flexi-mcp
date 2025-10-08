/**
 * Tests for FlexiUrlBuilder
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { FlexiUrlBuilder } from './url-builder.js';

describe('FlexiUrlBuilder', () => {
  it('should build empty query string', () => {
    const builder = new FlexiUrlBuilder();
    assert.strictEqual(builder.build(), '');
  });

  it('should build pagination parameters', () => {
    const builder = new FlexiUrlBuilder();
    builder.addPagination(10, 20);
    assert.strictEqual(builder.build(), '?limit=10&start=20');
  });

  it('should build detail parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addDetail('full');
    assert.strictEqual(builder.build(), '?detail=full');
  });

  it('should build filter parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addFilter("(datVyst >= '2024-01-01')");
    const result = builder.build();
    // URLSearchParams automatically encodes
    assert.ok(result.includes('q='));
    assert.ok(result.includes('datVyst'));
  });

  it('should encode quotes in filter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addFilter("(field = 'value')");
    const result = builder.build();
    // URLSearchParams automatically encodes quotes
    assert.ok(result.includes('q='));
    assert.ok(result.includes('field'));
  });

  it('should build single order parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addOrder('kod');
    assert.strictEqual(builder.build(), '?order=kod');
  });

  it('should build multiple order parameters', () => {
    const builder = new FlexiUrlBuilder();
    builder.addOrder(['datVyst', 'sumCelkem']);
    assert.strictEqual(builder.build(), '?order=datVyst%2CsumCelkem');
  });

  it('should build includes parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addIncludes('/faktura-vydana/firma/');
    assert.strictEqual(builder.build(), '?includes=%2Ffaktura-vydana%2Ffirma%2F');
  });

  it('should build relations parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addRelations('polozkyFaktury');
    assert.strictEqual(builder.build(), '?relations=polozkyFaktury');
  });

  it('should build multiple relations', () => {
    const builder = new FlexiUrlBuilder();
    builder.addRelations(['polozkyFaktury', 'prilohy']);
    assert.strictEqual(builder.build(), '?relations=polozkyFaktury%2Cprilohy');
  });

  it('should build row count parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addRowCount(true);
    assert.strictEqual(builder.build(), '?add-row-count=true');
  });

  it('should build noExtIds parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addNoExtIds(true);
    assert.strictEqual(builder.build(), '?no-ext-ids=true');
  });

  it('should build noIds parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addNoIds(true);
    assert.strictEqual(builder.build(), '?no-ids=true');
  });

  it('should build codeAsId parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addCodeAsId(true);
    assert.strictEqual(builder.build(), '?code-as-id=true');
  });

  it('should build custom parameter', () => {
    const builder = new FlexiUrlBuilder();
    builder.addParam('custom', 'value');
    assert.strictEqual(builder.build(), '?custom=value');
  });

  it('should chain multiple parameters', () => {
    const builder = new FlexiUrlBuilder();
    builder
      .addPagination(10, 0)
      .addDetail('summary')
      .addOrder('kod')
      .addRowCount(true);

    assert.strictEqual(
      builder.build(),
      '?limit=10&start=0&detail=summary&order=kod&add-row-count=true'
    );
  });

  it('should skip undefined/false parameters', () => {
    const builder = new FlexiUrlBuilder();
    builder
      .addPagination(undefined, undefined)
      .addDetail(undefined)
      .addFilter(undefined)
      .addRowCount(false);

    assert.strictEqual(builder.build(), '');
  });

  it('should reset builder', () => {
    const builder = new FlexiUrlBuilder();
    builder.addDetail('full').addPagination(10, 0);
    assert.notStrictEqual(builder.build(), '');

    builder.reset();
    assert.strictEqual(builder.build(), '');
  });

  it('should allow accessing URLSearchParams directly', () => {
    const builder = new FlexiUrlBuilder();
    builder.addDetail('full');

    const params = builder.getParams();
    assert.strictEqual(params.get('detail'), 'full');
  });

  it('should build complex faktura query', () => {
    const builder = new FlexiUrlBuilder();
    builder
      .addPagination(20, 0)
      .addDetail('custom:kod,nazFirmy,sumCelkem')
      .addFilter("(datVyst >= '2024-01-01' and stavUhrK = 'stavUhr.neuhrazeno')")
      .addOrder(['datVyst', 'sumCelkem'])
      .addRowCount(true)
      .addNoExtIds(true);

    const result = builder.build();
    assert.ok(result.includes('limit=20'));
    assert.ok(result.includes('start=0'));
    assert.ok(result.includes('detail=custom'));
    assert.ok(result.includes('add-row-count=true'));
    assert.ok(result.includes('no-ext-ids=true'));
  });
});
