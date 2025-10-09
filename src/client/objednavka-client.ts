/**
 * Objednavka Client
 * Handles received orders operations
 */

import { BaseFlexiClient } from './base-client.js';
import { FlexiResponse, ObjednavkaPrijataQueryParams } from '../types.js';

export class ObjednavkaClient extends BaseFlexiClient {
  /**
   * Query received orders (objednávky prijaté)
   */
  async getPrijate(params: ObjednavkaPrijataQueryParams): Promise<FlexiResponse> {
    const queryParams = new URLSearchParams();

    // Get specific order by ID
    if (params.id) {
      const url = `/objednavka-prijata/${params.id}.json`;

      // Add detail level
      queryParams.append('detail', params.detail || 'full');

      // Build relations for items (objednavka-prijata uses relations, not includes)
      if (params.includeItems) {
        queryParams.append('relations', 'polozkyObchDokladu');
      }

      // Extended information flags
      this.addExtendedFlags(queryParams, params);

      const finalUrl = `${url}?${queryParams.toString()}`;
      const response = await this.get<FlexiResponse>(finalUrl);

      return this.anonymizeOrderResponse(response);
    }

    // List orders with filtering, sorting, and pagination

    // Build and add filter
    const filterString = this.buildFilterString(params);
    if (filterString) {
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
    queryParams.append('detail', params.detail || 'summary');

    // Build relations for items (objednavka-prijata uses relations, not includes)
    if (params.includeItems) {
      queryParams.append('relations', 'polozkyObchDokladu');
    }

    // Extended information flags
    this.addExtendedFlags(queryParams, params);

    const url = `/objednavka-prijata.json?${queryParams.toString()}`;
    const response = await this.get<FlexiResponse>(url);

    return this.anonymizeOrderResponse(response);
  }

  /**
   * Build filter string from individual filter parameters
   */
  private buildFilterString(params: ObjednavkaPrijataQueryParams): string | undefined {
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

    // Order number filter
    if (params.cisObj) {
      filters.push(`cisObj = '${params.cisObj}'`);
    }

    // Customer filter
    if (params.firma) {
      if (/^\d+$/.test(params.firma)) {
        filters.push(`firma = ${params.firma}`);
      } else {
        filters.push(`firma = 'code:${params.firma}'`);
      }
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
  private buildOrderParam(params: ObjednavkaPrijataQueryParams): string | undefined {
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
    params: ObjednavkaPrijataQueryParams
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
   * Anonymize personal data in a single order record
   */
  private anonymizeOrder(order: any): any {
    if (!order) return order;

    const anonymized = { ...order };

    // Customer name
    if (anonymized.nazFirmy) {
      anonymized.nazFirmy = '*** ANONYMIZOVANÉ ***';
    }

    // Customer address
    if (anonymized.ulice) anonymized.ulice = '***';
    if (anonymized.mesto) anonymized.mesto = '***';
    if (anonymized.psc) anonymized.psc = '***';

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

    // Notes
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
  private anonymizeOrderResponse(response: FlexiResponse): FlexiResponse {
    if (!this.shouldAnonymize()) {
      return response;
    }

    const anonymized = { ...response };

    if (anonymized.winstrom && anonymized.winstrom['objednavka-prijata']) {
      const orders = anonymized.winstrom['objednavka-prijata'];

      if (Array.isArray(orders)) {
        anonymized.winstrom['objednavka-prijata'] = orders.map(order =>
          this.anonymizeOrder(order)
        );
      }
    }

    return anonymized;
  }
}
