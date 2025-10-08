/**
 * Faktura Client
 * Handles invoice-related operations (issued and received invoices)
 */

import { BaseFlexiClient } from './base-client.js';
import { FlexiResponse, FakturaVydanaQueryParams } from '../types.js';
import {
  getFakturaVydanaDetailMode,
  buildCustomDetailParam,
  isBuiltInDetailMode,
  filterInvoiceItemsForAudit,
  filterFields,
  FAKTURA_VYDANA_DETAIL_MODES,
} from '../config/detail-modes.js';

export class FakturaClient extends BaseFlexiClient {
  /**
   * Build detail parameter for Flexibee API
   * Converts custom modes (compact, standard, extended, audit) to Flexibee format
   *
   * Special handling for audit mode:
   * - When detail=audit and includeItems=true, we fetch detail=full
   * - Then filter the response on the server side to keep only audit fields
   */
  private buildDetailParam(detail?: string, includeItems?: boolean): string {
    if (!detail) {
      return 'summary';
    }

    // Handle built-in Flexibee modes
    if (detail === 'id' || detail === 'summary' || detail === 'full') {
      return detail;
    }

    // Special handling for audit modes with items
    // We need full detail to get all item fields, then filter on server side
    if ((detail === 'audit' || detail === 'audit-fast') && includeItems) {
      return 'full';
    }

    // Handle custom detail modes (compact, standard, extended, audit)
    const fields = getFakturaVydanaDetailMode(detail);
    if (fields) {
      return buildCustomDetailParam(fields);
    }

    // Pass through custom detail strings (e.g., 'custom:kod,nazFirmy')
    return detail;
  }

  /**
   * Filter response for audit mode
   * Keeps only audit fields from invoice and items
   * @param fast - if true, uses audit-fast field set and excludes @ref/@showAs metadata
   */
  private filterAuditResponse(response: FlexiResponse, includeItems?: boolean, fast: boolean = false): FlexiResponse {
    if (!response.winstrom || !response.winstrom['faktura-vydana']) {
      return response;
    }

    const filtered = { ...response };
    const invoices = response.winstrom['faktura-vydana'];

    // Select field set based on mode
    const invoiceFields = fast
      ? FAKTURA_VYDANA_DETAIL_MODES['audit-fast']
      : FAKTURA_VYDANA_DETAIL_MODES.audit;

    if (filtered.winstrom && Array.isArray(invoices)) {
      filtered.winstrom['faktura-vydana'] = invoices.map(invoice => {
        // Filter invoice fields
        const filteredInvoice = filterFields(invoice, invoiceFields, fast);

        // Filter items if present
        if (includeItems && invoice.polozkyFaktury && Array.isArray(invoice.polozkyFaktury)) {
          filteredInvoice.polozkyFaktury = filterInvoiceItemsForAudit(invoice.polozkyFaktury, fast);
        }

        return filteredInvoice;
      });
    }

    return filtered;
  }

  /**
   * Query issued invoices (faktúry vydané)
   */
  async getVydane(params: FakturaVydanaQueryParams): Promise<FlexiResponse> {
    const queryParams = new URLSearchParams();

    // Get specific invoice by ID
    if (params.id) {
      const url = `/faktura-vydana/${params.id}.json`;

      // Add detail level
      const detailParam = this.buildDetailParam(params.detail || 'full', params.includeItems || params.includeCenik);
      queryParams.append('detail', detailParam);

      // Build includes/relations for items
      if (params.includeItems || params.includeCenik) {
        if (params.useRelations) {
          queryParams.append('relations', 'polozkyFaktury');
        }

        if (params.includeCenik) {
          queryParams.append('includes', '/faktura-vydana/polozkyFaktury/faktura-vydana-polozka/cenik/');
        } else if (params.includeItems) {
          queryParams.append('includes', '/faktura-vydana/polozkyFaktury');
        }
      }

      // Extended information flags
      this.addExtendedFlags(queryParams, params);

      const finalUrl = `${url}?${queryParams.toString()}`;
      let response = await this.get<FlexiResponse>(finalUrl);

      // Apply audit filtering if needed
      if (params.detail === 'audit') {
        response = this.filterAuditResponse(response, params.includeItems, false);
      } else if (params.detail === 'audit-fast') {
        response = this.filterAuditResponse(response, params.includeItems, true);
      }

      return this.anonymizeInvoiceResponse(response);
    }

    // List invoices with filtering, sorting, and pagination

    // Build and add filter
    const filterString = this.buildFilterString(params);
    if (filterString) {
      // URLSearchParams will handle encoding automatically
      queryParams.append('q', filterString);
    }

    // Add ordering
    const orderParam = this.buildOrderParam(params);
    if (orderParam) {
      queryParams.append('order', orderParam);
    }

    // Pagination
    if (params.limit !== undefined) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params.offset !== undefined) {
      queryParams.append('start', params.offset.toString());
    }

    // Add detail level
    const detailParam = this.buildDetailParam(params.detail || 'summary', params.includeItems || params.includeCenik);
    queryParams.append('detail', detailParam);

    // Build includes/relations for items
    if (params.includeItems || params.includeCenik) {
      if (params.useRelations) {
        queryParams.append('relations', 'polozkyFaktury');
      }

      if (params.includeCenik) {
        queryParams.append('includes', '/faktura-vydana/polozkyFaktury/faktura-vydana-polozka/cenik/');
      } else if (params.includeItems) {
        queryParams.append('includes', '/faktura-vydana/polozkyFaktury');
      }
    }

    // Extended information flags
    this.addExtendedFlags(queryParams, params);

    const url = `/faktura-vydana.json?${queryParams.toString()}`;
    let response = await this.get<FlexiResponse>(url);

    // Apply audit filtering if needed
    if (params.detail === 'audit') {
      response = this.filterAuditResponse(response, params.includeItems, false);
    } else if (params.detail === 'audit-fast') {
      response = this.filterAuditResponse(response, params.includeItems, true);
    }

    return this.anonymizeInvoiceResponse(response);
  }

  /**
   * Build filter string from individual filter parameters
   */
  private buildFilterString(params: FakturaVydanaQueryParams): string | undefined {
    if (params.filter) {
      return params.filter;
    }

    const filters: string[] = [];

    // Date filters
    if (params.datVystOd) {
      filters.push(`datVyst >= '${params.datVystOd}'`);
    }
    if (params.datVystDo) {
      filters.push(`datVyst <= '${params.datVystDo}'`);
    }
    if (params.datSplatOd) {
      filters.push(`datSplat >= '${params.datSplatOd}'`);
    }
    if (params.datSplatDo) {
      filters.push(`datSplat <= '${params.datSplatDo}'`);
    }

    // Status filters
    if (params.stavUhrK) {
      filters.push(`stavUhrK = '${params.stavUhrK}'`);
    }

    // Customer filter
    if (params.firma) {
      if (/^\d+$/.test(params.firma)) {
        filters.push(`firma = ${params.firma}`);
      } else {
        filters.push(`firma = 'code:${params.firma}'`);
      }
    }

    // Amount filters
    if (params.sumCelkemOd !== undefined) {
      filters.push(`sumCelkem >= ${params.sumCelkemOd}`);
    }
    if (params.sumCelkemDo !== undefined) {
      filters.push(`sumCelkem <= ${params.sumCelkemDo}`);
    }

    // Tags filter
    if (params.stitky) {
      filters.push(`stitky = '${params.stitky}'`);
    }

    return filters.length > 0 ? `(${filters.join(' and ')})` : undefined;
  }

  /**
   * Build order parameter from order options
   */
  private buildOrderParam(params: FakturaVydanaQueryParams): string | undefined {
    if (!params.order) {
      return undefined;
    }

    if (Array.isArray(params.order)) {
      return params.order.join(',');
    } else {
      if (params.orderDirection && params.orderDirection.toLowerCase() === 'desc') {
        return `${params.order}@D`;
      }
      return params.order;
    }
  }

  /**
   * Add extended information flags to query params
   */
  private addExtendedFlags(
    queryParams: URLSearchParams,
    params: FakturaVydanaQueryParams
  ): void {
    if (params.addRowCount) {
      queryParams.append('add-row-count', 'true');
    }
    if (params.noExtIds) {
      queryParams.append('no-ext-ids', 'true');
    }
    if (params.noIds) {
      queryParams.append('no-ids', 'true');
    }
    if (params.codeAsId) {
      queryParams.append('code-as-id', 'true');
    }
  }

  /**
   * Anonymize personal data in a single invoice record
   */
  private anonymizeInvoice(invoice: any): any {
    if (!invoice) return invoice;

    const anonymized = { ...invoice };

    // Customer name
    if (anonymized.nazFirmy) {
      anonymized.nazFirmy = '*** ANONYMIZOVANÉ ***';
    }

    // Customer address
    if (anonymized.ulice) anonymized.ulice = '***';
    if (anonymized.mesto) anonymized.mesto = '***';
    if (anonymized.psc) anonymized.psc = '***';

    // Billing address
    if (anonymized.faNazev) anonymized.faNazev = '*** ANONYMIZOVANÉ ***';
    if (anonymized.faUlice) anonymized.faUlice = '***';
    if (anonymized.faMesto) anonymized.faMesto = '***';
    if (anonymized.faPsc) anonymized.faPsc = '***';

    // Contact information
    if (anonymized.kontaktJmeno) {
      anonymized.kontaktJmeno = '*** ANONYMIZOVANÉ ***';
    }
    if (anonymized.kontaktEmail) {
      anonymized.kontaktEmail = '***@***.***';
    }
    if (anonymized.kontaktTel) {
      anonymized.kontaktTel = anonymized.kontaktTel.substring(0, 4) + '*********';
    }

    // Notes (may contain personal info)
    if (anonymized.poznam) {
      anonymized.poznam = '*** ANONYMIZOVANÉ ***';
    }
    if (anonymized.popis) {
      anonymized.popis = '*** ANONYMIZOVANÉ ***';
    }

    return anonymized;
  }

  /**
   * Anonymize response data if enabled
   */
  private anonymizeInvoiceResponse(response: FlexiResponse): FlexiResponse {
    if (!this.shouldAnonymize()) {
      return response;
    }

    const anonymized = { ...response };

    if (anonymized.winstrom && anonymized.winstrom['faktura-vydana']) {
      const invoices = anonymized.winstrom['faktura-vydana'];

      if (Array.isArray(invoices)) {
        anonymized.winstrom['faktura-vydana'] = invoices.map(invoice =>
          this.anonymizeInvoice(invoice)
        );
      }
    }

    return anonymized;
  }
}
