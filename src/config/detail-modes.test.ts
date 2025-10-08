/**
 * Tests for detail mode configuration
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  getFakturaVydanaDetailMode,
  buildCustomDetailParam,
  isBuiltInDetailMode,
  FAKTURA_VYDANA_DETAIL_MODES,
} from './detail-modes.js';

describe('Detail Modes', () => {
  describe('getFakturaVydanaDetailMode', () => {
    it('should return compact mode fields', () => {
      const fields = getFakturaVydanaDetailMode('compact');
      assert.ok(fields);
      assert.deepStrictEqual(fields, FAKTURA_VYDANA_DETAIL_MODES.compact);
      assert.ok(fields.length > 0);
      assert.ok(fields.includes('id'));
      assert.ok(fields.includes('kod'));
      assert.ok(fields.includes('sumCelkem'));
    });

    it('should return standard mode fields', () => {
      const fields = getFakturaVydanaDetailMode('standard');
      assert.ok(fields);
      assert.deepStrictEqual(fields, FAKTURA_VYDANA_DETAIL_MODES.standard);
      assert.ok(fields.length > FAKTURA_VYDANA_DETAIL_MODES.compact.length);
    });

    it('should return extended mode fields', () => {
      const fields = getFakturaVydanaDetailMode('extended');
      assert.ok(fields);
      assert.deepStrictEqual(fields, FAKTURA_VYDANA_DETAIL_MODES.extended);
      assert.ok(fields.length > FAKTURA_VYDANA_DETAIL_MODES.standard.length);
    });

    it('should return audit mode fields', () => {
      const fields = getFakturaVydanaDetailMode('audit');
      assert.ok(fields);
      assert.deepStrictEqual(fields, FAKTURA_VYDANA_DETAIL_MODES.audit);
      assert.ok(fields.length > 0);
    });

    it('should return null for unknown mode', () => {
      const fields = getFakturaVydanaDetailMode('unknown');
      assert.strictEqual(fields, null);
    });

    it('should return null for built-in Flexibee modes', () => {
      assert.strictEqual(getFakturaVydanaDetailMode('id'), null);
      assert.strictEqual(getFakturaVydanaDetailMode('summary'), null);
      assert.strictEqual(getFakturaVydanaDetailMode('full'), null);
    });
  });

  describe('buildCustomDetailParam', () => {
    it('should build custom detail parameter', () => {
      const fields = ['id', 'kod', 'sumCelkem'];
      const result = buildCustomDetailParam(fields);
      assert.strictEqual(result, 'custom:id,kod,sumCelkem');
    });

    it('should handle single field', () => {
      const result = buildCustomDetailParam(['id']);
      assert.strictEqual(result, 'custom:id');
    });

    it('should handle empty array', () => {
      const result = buildCustomDetailParam([]);
      assert.strictEqual(result, 'custom:');
    });

    it('should handle fields with @showAs', () => {
      const fields = ['firma@showAs', 'mena@showAs'];
      const result = buildCustomDetailParam(fields);
      assert.strictEqual(result, 'custom:firma@showAs,mena@showAs');
    });
  });

  describe('isBuiltInDetailMode', () => {
    it('should recognize Flexibee built-in modes', () => {
      assert.strictEqual(isBuiltInDetailMode('id'), true);
      assert.strictEqual(isBuiltInDetailMode('summary'), true);
      assert.strictEqual(isBuiltInDetailMode('full'), true);
    });

    it('should recognize custom modes', () => {
      assert.strictEqual(isBuiltInDetailMode('compact'), true);
      assert.strictEqual(isBuiltInDetailMode('standard'), true);
      assert.strictEqual(isBuiltInDetailMode('extended'), true);
      assert.strictEqual(isBuiltInDetailMode('audit'), true);
    });

    it('should return false for unknown modes', () => {
      assert.strictEqual(isBuiltInDetailMode('unknown'), false);
      assert.strictEqual(isBuiltInDetailMode('custom:id,kod'), false);
      assert.strictEqual(isBuiltInDetailMode(''), false);
    });
  });

  describe('FAKTURA_VYDANA_DETAIL_MODES', () => {
    it('compact should have expected key fields', () => {
      const { compact } = FAKTURA_VYDANA_DETAIL_MODES;

      // Identification
      assert.ok(compact.includes('id'));
      assert.ok(compact.includes('kod'));
      assert.ok(compact.includes('varSym'));

      // Dates
      assert.ok(compact.includes('datVyst'));
      assert.ok(compact.includes('datSplat'));

      // Customer
      assert.ok(compact.includes('firma'));
      assert.ok(compact.includes('nazFirmy'));

      // Finance
      assert.ok(compact.includes('sumCelkem'));
      assert.ok(compact.includes('zbyvaUhradit'));

      // Status
      assert.ok(compact.includes('stavUhrK'));
    });

    it('standard should include all compact fields plus extras', () => {
      const { compact, standard } = FAKTURA_VYDANA_DETAIL_MODES;

      // All compact fields should be in standard
      compact.forEach(field => {
        assert.ok(standard.includes(field));
      });

      // Standard should have additional fields
      assert.ok(standard.includes('ulice'));
      assert.ok(standard.includes('mesto'));
      assert.ok(standard.includes('kontaktEmail'));
      assert.ok(standard.includes('bankovniUcet'));
    });

    it('extended should include all standard fields plus extras', () => {
      const { standard, extended } = FAKTURA_VYDANA_DETAIL_MODES;

      // All standard fields should be in extended
      standard.forEach(field => {
        assert.ok(extended.includes(field));
      });

      // Extended should have additional accounting fields
      assert.ok(extended.includes('primUcet'));
      assert.ok(extended.includes('protiUcet'));
      assert.ok(extended.includes('szbDphSniz'));
      assert.ok(extended.includes('lastUpdate'));
    });

    it('should have reasonable field counts', () => {
      const { compact, standard, extended, audit } = FAKTURA_VYDANA_DETAIL_MODES;

      assert.ok(compact.length >= 15);
      assert.ok(compact.length < 25);

      assert.ok(standard.length >= 35);
      assert.ok(standard.length < 55);

      assert.ok(extended.length >= 60);
      assert.ok(extended.length < 100);

      assert.ok(audit.length >= 35);
      assert.ok(audit.length < 60);
    });

    it('audit should have VAT and accounting fields', () => {
      const { audit } = FAKTURA_VYDANA_DETAIL_MODES;

      // VAT fields
      assert.ok(audit.includes('statDph'));
      assert.ok(audit.includes('clenDph'));
      assert.ok(audit.includes('clenKonVykDph'));
      assert.ok(audit.includes('szbDphSniz'));
      assert.ok(audit.includes('uzpTuzemsko'));

      // Accounting fields
      assert.ok(audit.includes('primUcet'));
      assert.ok(audit.includes('protiUcet'));
      assert.ok(audit.includes('dphZaklUcet'));
      assert.ok(audit.includes('dphSnizUcet'));
      assert.ok(audit.includes('typUcOp'));

      // OSS fields
      assert.ok(audit.includes('stat'));
      assert.ok(audit.includes('faStat'));
      assert.ok(audit.includes('typDokl'));

      // Currency
      assert.ok(audit.includes('mena'));
      assert.ok(audit.includes('kurz'));
    });
  });
});
