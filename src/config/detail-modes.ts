/**
 * Detail mode configurations for different evidence types
 * Defines field sets for compact, standard, and extended detail levels
 */

/**
 * Faktura Vydana (Issued Invoice) Detail Modes
 */
export const FAKTURA_VYDANA_DETAIL_MODES = {
  /**
   * COMPACT: Minimal overview for lists and dashboards (~20-25 fields)
   * Use case: Quick overview of invoices, list views
   */
  compact: [
    // Identification
    'id',
    'kod',
    'varSym',
    'cisObj',

    // Dates
    'datVyst',
    'datSplat',
    'datUhr',

    // Customer
    'firma',
    'nazFirmy',

    // Finance
    'sumCelkem',
    'sumZklCelkem',
    'sumDphCelkem',
    'zbyvaUhradit',
    'mena',

    // Status
    'stavUhrK',
    'storno',
    'zamekK',

    // Notes
    'popis',
    'poznam',
  ],

  /**
   * STANDARD: Common use case with essential details (~35-40 fields)
   * Use case: Invoice detail view, printing, basic exports
   */
  standard: [
    // All compact fields
    'id',
    'kod',
    'varSym',
    'cisObj',
    'datVyst',
    'datSplat',
    'datUhr',
    'firma',
    'nazFirmy',
    'sumCelkem',
    'sumZklCelkem',
    'sumDphCelkem',
    'zbyvaUhradit',
    'mena',
    'stavUhrK',
    'storno',
    'zamekK',
    'popis',
    'poznam',

    // Extended dates
    'datUcto',
    'duzpPuv',

    // Customer address
    'ulice',
    'mesto',
    'psc',
    'ic',
    'dic',

    // Billing address
    'faNazev',
    'faUlice',
    'faMesto',
    'faPsc',

    // Contact
    'kontaktJmeno',
    'kontaktEmail',
    'kontaktTel',

    // Extended finance
    'sumZalohy',
    'sumPrepl',
    'kurz',
    'sumCelkemBezZaloh',

    // Payment
    'formaUhradyCis',
    'bankovniUcet',

    // Type and series
    'typDokl',
    'rada',

    // Delivery
    'formaDopravy',
    'doprava',

    // Accounting
    'stredisko',
    'typUcOp',
  ],

  /**
   * EXTENDED: Detailed overview for accounting and integrations (~60-70 fields)
   * Use case: Accounting detail, audits, system integrations
   */
  extended: [
    // All standard fields
    'id',
    'kod',
    'varSym',
    'cisObj',
    'datVyst',
    'datSplat',
    'datUhr',
    'firma',
    'nazFirmy',
    'sumCelkem',
    'sumZklCelkem',
    'sumDphCelkem',
    'zbyvaUhradit',
    'mena',
    'stavUhrK',
    'storno',
    'zamekK',
    'popis',
    'poznam',
    'datUcto',
    'duzpPuv',
    'ulice',
    'mesto',
    'psc',
    'ic',
    'dic',
    'faNazev',
    'faUlice',
    'faMesto',
    'faPsc',
    'kontaktJmeno',
    'kontaktEmail',
    'kontaktTel',
    'sumZalohy',
    'sumPrepl',
    'kurz',
    'sumCelkemBezZaloh',
    'formaUhradyCis',
    'bankovniUcet',
    'typDokl',
    'rada',
    'formaDopravy',
    'doprava',
    'stredisko',
    'typUcOp',

    // All dates
    'datReal',
    'datTermin',
    'datSazbyDph',
    'duzpUcto',

    // Complete sums
    'sumZklSniz',
    'sumDphSniz',
    'sumCelkSniz',
    'sumZklZakl',
    'sumDphZakl',
    'sumCelkZakl',
    'sumOsv',
    'slevaDokl',

    // VAT details
    'szbDphSniz',
    'szbDphZakl',
    'statDph',
    'clenDph',
    'clenKonVykDph',

    // Accounting details
    'primUcet',
    'protiUcet',
    'dphZaklUcet',
    'dphSnizUcet',
    'cinnost',
    'zakazka',
    'zuctovano',
    'ucetni',

    // Payment details
    'iban',
    'bic',
    'specSym',
    'konSym',

    // Status
    'stavMailK',
    'stavOdpocetK',
    'stavUzivK',

    // Users
    'uzivatel',
    'zodpOsoba',
    'createdBy',
    'updatedBy',

    // Texts
    'uvodTxt',
    'zavTxt',

    // Audit
    'lastUpdate',
    'createdDate',

    // UUID
    'uuid',

    // Additional codes
    'cisSml',
    'cisDosle',
    'cisDodak',
  ],

  /**
   * AUDIT: VAT and accounting control mode (~55 fields)
   * Use case: VAT control, accounting verification, OSS regime checks
   * Includes all sums and VAT rates
   */
  audit: [
    // Identification
    'id',
    'kod',
    'varSym',
    'cisObj',

    // Dates
    'datVyst',
    'datSplat',
    'datUcto',
    'duzpPuv',
    'datSazbyDph',

    // Customer and country (OSS)
    'firma',
    'nazFirmy',
    'stat',
    'faStat',
    'ic',
    'dic',

    // Document type and series
    'typDokl',
    'rada',

    // VAT details
    'statDph',
    'clenDph',
    'clenKonVykDph',
    'uzpTuzemsko',
    'szbDphSniz',
    'szbDphSniz2',
    'szbDphZakl',

    // Sums
    'sumCelkem',
    'sumZklCelkem',
    'sumDphCelkem',
    'sumZklSniz',
    'sumDphSniz',
    'sumZklSniz2',
    'sumDphSniz2',
    'sumZklZakl',
    'sumDphZakl',

    // Currency
    'mena',
    'kurz',
    'kurzMnozstvi',
    'sumCelkemMen',
    'sumZklCelkemMen',
    'sumDphCelkemMen',

    // Accounting
    'primUcet',
    'protiUcet',
    'dphZaklUcet',
    'dphSnizUcet',
    'dphSniz2Ucet',
    'typUcOp',
    'stredisko',
    'cinnost',
    'zakazka',
    'zuctovano',
    'ucetni',

    // Status
    'storno',
    'zamekK',
  ],

  /**
   * AUDIT-FAST: Ultra-compact audit mode (~35 fields)
   * Use case: LLM-optimized audit - minimal data for pattern detection
   * Excludes VAT rates and detailed sums, keeps only critical fields
   */
  'audit-fast': [
    // Identification
    'id',
    'kod',
    'varSym',
    'cisObj',

    // Dates (minimal)
    'datVyst',
    'datSplat',
    'datUcto',

    // Customer and country (OSS)
    'firma',
    'nazFirmy',
    'stat',
    'faStat',
    'ic',
    'dic',

    // Document type and series
    'typDokl',
    'rada',

    // VAT details (no rates, only classification)
    'statDph',
    'clenDph',
    'clenKonVykDph',
    'uzpTuzemsko',

    // Currency (minimal)
    'mena',
    'kurz',

    // Accounting (critical)
    'primUcet',
    'protiUcet',
    'dphZaklUcet',
    'dphSnizUcet',
    'dphSniz2Ucet',
    'typUcOp',
    'stredisko',
    'cinnost',
    'zakazka',

    // Status
    'storno',
    'zamekK',
    'ucetni',
    'zuctovano',
  ],
} as const;

/**
 * Get detail mode field list for faktura-vydana
 */
export function getFakturaVydanaDetailMode(mode: string): readonly string[] | null {
  if (mode === 'compact') {
    return FAKTURA_VYDANA_DETAIL_MODES.compact;
  }
  if (mode === 'standard') {
    return FAKTURA_VYDANA_DETAIL_MODES.standard;
  }
  if (mode === 'extended') {
    return FAKTURA_VYDANA_DETAIL_MODES.extended;
  }
  if (mode === 'audit') {
    return FAKTURA_VYDANA_DETAIL_MODES.audit;
  }
  if (mode === 'audit-fast') {
    return FAKTURA_VYDANA_DETAIL_MODES['audit-fast'];
  }
  return null;
}

/**
 * Build custom detail parameter for Flexibee API
 * Converts array of fields to "custom:field1,field2,..." format
 */
export function buildCustomDetailParam(fields: readonly string[]): string {
  return `custom:${fields.join(',')}`;
}

/**
 * Faktura Vydana Items (polozkyFaktury) - Audit mode fields
 * Fields to keep when filtering invoice items in audit mode
 */
export const FAKTURA_VYDANA_ITEMS_AUDIT_FIELDS = [
  // Identification
  'id',
  'kod',
  'nazev',
  'cisRad',
  'eanKod',

  // Item type
  'typPolozkyK',
  'cenik',
  'ucetni',

  // Quantity and price
  'mnozMj',
  'cenaMj',
  'typCenyDphK',

  // VAT
  'typSzbDphK',
  'szbDph',
  'sazbaDph',
  'clenDph',
  'clenKonVykDph',

  // Sums in CZK
  'sumZkl',
  'sumDph',
  'sumCelkem',

  // Sums in foreign currency
  'sumZklMen',
  'sumDphMen',
  'sumCelkemMen',

  // Accounting
  'zklMdUcet',
  'zklDalUcet',
  'dphMdUcet',
  'dphDalUcet',
  'typUcOp',
  'stredisko',
  'cinnost',
  'zakazka',

  // Currency
  'mena',

  // Storage
  'sklad',

  // Status
  'storno',
  'stornoPol',

  // Notes
  'poznam',
] as const;

/**
 * Check if a detail mode is a built-in mode
 */
export function isBuiltInDetailMode(mode: string): boolean {
  return ['id', 'summary', 'full', 'compact', 'standard', 'extended', 'audit', 'audit-fast'].includes(mode);
}

/**
 * Filter object to keep only specified fields
 * @param excludeMetadata - if true, excludes @ref and @showAs fields (for audit-fast mode)
 */
export function filterFields<T extends Record<string, any>>(
  obj: T,
  fieldsToKeep: readonly string[],
  excludeMetadata: boolean = false
): Partial<T> {
  const filtered: any = {};

  for (const field of fieldsToKeep) {
    if (field in obj) {
      filtered[field] = obj[field];
    }

    // Include @ref and @showAs variants unless excludeMetadata is true
    if (!excludeMetadata) {
      const refField = `${field}@ref`;
      const showAsField = `${field}@showAs`;
      if (refField in obj) {
        filtered[refField] = obj[refField];
      }
      if (showAsField in obj) {
        filtered[showAsField] = obj[showAsField];
      }
    }
  }

  return filtered;
}

/**
 * Faktura Vydana Items - Audit FAST mode fields (minimal, no metadata)
 * Ultra-compact version for LLM processing - only critical audit fields
 */
export const FAKTURA_VYDANA_ITEMS_AUDIT_FAST_FIELDS = [
  // Identification (minimal)
  'id',
  'kod',
  'cisRad',

  // VAT (critical for audit)
  'typSzbDphK',
  'szbDph',
  'clenDph',

  // Accounting (critical for audit)
  'zklDalUcet',
  'dphDalUcet',
  'typUcOp',
] as const;

/**
 * Objednavka Prijata - Storno Audit header fields
 * Ultra-compact fields for order header in storno audit
 */
export const OBJEDNAVKA_PRIJATA_STORNO_AUDIT_HEADER_FIELDS = [
  // Identification
  'id',
  'kod',
  'cisDosle',
  'varSym',

  // Dates
  'datVyst',
  'lastUpdate',

  // Customer (minimal)
  'firma',
  'nazFirmy',
  'stat',

  // Storno indicators (CRITICAL)
  'storno',
  'stavDoklObch',
  'stavUzivK',
  'cisSml',

  // Sums (CRITICAL for detection)
  'sumCelkem',
  'sumZklCelkem',
  'sumDphCelkem',

  // Currency
  'mena',
  'kurz',

  // Document type
  'typDokl',

  // Dativery tracking
  'source',
  'external-ids',

  // Tags
  'stitky',
] as const;

/**
 * Objednavka Prijata Items - Storno Audit mode fields
 * Ultra-compact version for storno detection in Dativery orders
 * Note: objednavka-prijata items don't have storno/stornoPol fields
 */
export const OBJEDNAVKA_PRIJATA_STORNO_AUDIT_ITEM_FIELDS = [
  // Identification
  'id',
  'kod',
  'nazev',
  'cisRad',

  // Sums (CRITICAL for storno detection)
  'sumCelkem',
  'sumZkl',
  'sumDph',

  // Quantity and price
  'mnozMj',
  'mnozMjZbyva',
  'cenaMj',

  // VAT
  'typSzbDphK',
  'szbDph',

  // Product info
  'cenik',
  'sklad',
] as const;

/**
 * Filter invoice items for audit mode
 */
export function filterInvoiceItemsForAudit(items: any[], fast: boolean = false): any[] {
  if (!Array.isArray(items)) {
    return items;
  }

  if (fast) {
    // Ultra-compact: only essential fields, no @ref/@showAs
    return items.map(item =>
      filterFields(item, FAKTURA_VYDANA_ITEMS_AUDIT_FAST_FIELDS, true)
    );
  }

  // Standard audit: all audit fields with @ref/@showAs
  return items.map(item =>
    filterFields(item, FAKTURA_VYDANA_ITEMS_AUDIT_FIELDS, false)
  );
}

/**
 * Filter order items for storno audit (Dativery)
 */
export function filterOrderItemsForStornoAudit(items: any[]): any[] {
  if (!Array.isArray(items)) {
    return items;
  }

  // Ultra-compact: only storno detection fields, no @ref/@showAs
  return items.map(item =>
    filterFields(item, OBJEDNAVKA_PRIJATA_STORNO_AUDIT_ITEM_FIELDS, true)
  );
}

/**
 * Filter order header for storno audit (Dativery)
 */
export function filterOrderHeaderForStornoAudit(order: any): any {
  if (!order) {
    return order;
  }

  // Ultra-compact: only storno detection fields, no @ref/@showAs
  return filterFields(order, OBJEDNAVKA_PRIJATA_STORNO_AUDIT_HEADER_FIELDS, true);
}
