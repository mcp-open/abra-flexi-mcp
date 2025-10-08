/**
 * Flexi API types and interfaces
 */

export interface FlexiConfig {
  url: string;
  company: string;
  username: string;
  password: string;
  anonymizeData?: boolean;
}

export interface FlexiResponse<T = any> {
  success: string;
  'winstrom'?: {
    '@version': string;
    [key: string]: any;
  };
  results?: T[];
  message?: string;
}

export interface FlexiRecord {
  id?: string;
  [key: string]: any;
}

export interface Evidence {
  name: string;
  description?: string;
  url: string;
}

export interface QueryOptions {
  limit?: number;
  offset?: number;
  detail?: 'id' | 'summary' | 'full';
  order?: string;
  includes?: string;
}

export interface CreateRecordParams {
  evidence: string;
  data: FlexiRecord;
}

export interface UpdateRecordParams {
  evidence: string;
  id: string;
  data: Partial<FlexiRecord>;
}

export interface GetRecordParams {
  evidence: string;
  id: string;
  detail?: 'id' | 'summary' | 'full';
}

export interface QueryEvidenceParams {
  evidence: string;
  query?: string;
  options?: QueryOptions;
}

/**
 * Faktura Vydana (Issued Invoice) types
 */

export interface PolozkaFaktury {
  id?: string;
  kod?: string;
  eanKod?: string;
  nazev?: string;
  cisRad?: string;
  mnozMj?: string;
  cenaMj?: string;
  sumZkl?: string;
  sumDph?: string;
  sumCelkem?: string;
  szbDph?: string;
  typPolozkyK?: string;
  typSzbDphK?: string;
  sklad?: string;
  cenik?: string;
  mj?: string;
  poznam?: string;
  [key: string]: any;
}

export interface FakturaVydana {
  id?: string;
  kod?: string;
  varSym?: string;
  cisObj?: string;

  // Dates
  datVyst?: string;
  datSplat?: string;
  datUhr?: string;
  datReal?: string;
  duzpPuv?: string;

  // Customer info
  firma?: string;
  nazFirmy?: string;
  ulice?: string;
  mesto?: string;
  psc?: string;
  ic?: string;
  dic?: string;

  // Billing address
  faNazev?: string;
  faUlice?: string;
  faMesto?: string;
  faPsc?: string;

  // Amounts
  sumCelkem?: string;
  sumZklCelkem?: string;
  sumDphCelkem?: string;
  sumZklSniz?: string;
  sumDphSniz?: string;
  sumZklZakl?: string;
  sumDphZakl?: string;
  zbyvaUhradit?: string;

  // Payment
  stavUhrK?: string;
  formaUhradyCis?: string;
  bankovniUcet?: string;

  // Accounting
  typDokl?: string;
  rada?: string;
  stredisko?: string;
  typUcOp?: string;
  mena?: string;

  // Notes
  popis?: string;
  poznam?: string;

  // Status
  zamekK?: string;
  storno?: string;
  stavUzivK?: string;

  // Items
  polozkyFaktury?: PolozkaFaktury[];

  [key: string]: any;
}

/**
 * Detail mode for evidence queries
 * Built-in modes: id, summary, full, compact, standard, extended
 * Custom modes: 'custom:field1,field2,...'
 */
export type DetailMode =
  | 'id'           // Minimal: only ID
  | 'summary'      // Basic fields (Flexibee default)
  | 'full'         // All fields
  | 'compact'      // Custom: ~25 fields for lists
  | 'standard'     // Custom: ~40 fields for detail views
  | 'extended'     // Custom: ~70 fields for accounting
  | string;        // Custom detail like 'custom:kod,nazFirmy'

export interface FakturaVydanaQueryParams {
  id?: string;
  detail?: DetailMode;
  includeItems?: boolean;
  includeCenik?: boolean;
  useRelations?: boolean;
  limit?: number;
  offset?: number;

  // Filtering parameters
  filter?: string; // Raw filter string like "(datVyst > '2024-01-01')"
  datVystOd?: string; // Date from (YYYY-MM-DD)
  datVystDo?: string; // Date to (YYYY-MM-DD)
  datSplatOd?: string; // Due date from
  datSplatDo?: string; // Due date to
  stavUhrK?: string; // Payment status
  firma?: string; // Customer ID or code
  sumCelkemOd?: number; // Total amount from
  sumCelkemDo?: number; // Total amount to
  stitky?: string; // Tags filter

  // Ordering parameters
  order?: string | string[]; // Single or multiple order fields
  orderDirection?: 'asc' | 'desc' | 'A' | 'D'; // Direction for simple ordering

  // Extended information
  addRowCount?: boolean; // Add total count of records
  noExtIds?: boolean; // Exclude external IDs for performance
  noIds?: boolean; // Exclude internal IDs
  codeAsId?: boolean; // Use code as identifier instead of ID
}
