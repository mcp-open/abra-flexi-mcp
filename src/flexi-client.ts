/**
 * Flexi API Client
 * Handles communication with Flexi REST API
 */

import axios, { AxiosInstance } from 'axios';
import {
  FlexiConfig,
  FlexiResponse,
  FlexiRecord,
  Evidence,
  QueryOptions,
  QueryEvidenceParams,
  CreateRecordParams,
  UpdateRecordParams,
  GetRecordParams,
  FakturaVydanaQueryParams,
  FakturaVydana,
} from './types.js';

export class FlexiClient {
  private client: AxiosInstance;
  private config: FlexiConfig;

  constructor(config: FlexiConfig) {
    this.config = config;

    this.client = axios.create({
      baseURL: `${config.url}/c/${config.company}`,
      auth: {
        username: config.username,
        password: config.password,
      },
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });
  }

  /**
   * Get list of available evidences
   */
  async listEvidences(): Promise<Evidence[]> {
    try {
      const response = await this.client.get('/evidence-list.json');
      const data = response.data;

      if (data.winstrom && data.winstrom.evidence) {
        return data.winstrom.evidence.map((ev: any) => ({
          name: ev.evidenceType || ev['@evidenceType'] || '',
          description: ev.evidenceName || ev['@evidenceName'] || '',
          url: `${this.config.url}/c/${this.config.company}/${ev.evidenceType || ev['@evidenceType']}`,
        }));
      }

      return [];
    } catch (error: any) {
      throw new Error(`Failed to list evidences: ${error.message}`);
    }
  }

  /**
   * Query records from an evidence
   */
  async queryEvidence(params: QueryEvidenceParams): Promise<FlexiResponse> {
    const { evidence, query, options = {} } = params;

    try {
      const queryParams = new URLSearchParams();

      if (query) {
        queryParams.append('q', query);
      }

      if (options.limit) {
        queryParams.append('limit', options.limit.toString());
      }

      if (options.offset) {
        queryParams.append('start', options.offset.toString());
      }

      if (options.detail) {
        queryParams.append('detail', options.detail);
      }

      if (options.order) {
        queryParams.append('order', options.order);
      }

      if (options.includes) {
        queryParams.append('includes', options.includes);
      }

      const url = `/${evidence}.json${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await this.client.get(url);

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to query evidence ${evidence}: ${error.message}`);
    }
  }

  /**
   * Get a specific record by ID
   */
  async getRecord(params: GetRecordParams): Promise<FlexiResponse> {
    const { evidence, id, detail = 'full' } = params;

    try {
      const url = `/${evidence}/${id}.json?detail=${detail}`;
      const response = await this.client.get(url);

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to get record ${id} from ${evidence}: ${error.message}`);
    }
  }

  /**
   * Create a new record
   */
  async createRecord(params: CreateRecordParams): Promise<FlexiResponse> {
    const { evidence, data } = params;

    try {
      const url = `/${evidence}.json`;
      const payload = {
        winstrom: {
          [evidence]: [data],
        },
      };

      const response = await this.client.put(url, payload);

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to create record in ${evidence}: ${error.message}`);
    }
  }

  /**
   * Update an existing record
   */
  async updateRecord(params: UpdateRecordParams): Promise<FlexiResponse> {
    const { evidence, id, data } = params;

    try {
      const url = `/${evidence}/${id}.json`;
      const payload = {
        winstrom: {
          [evidence]: [{
            ...data,
            id,
          }],
        },
      };

      const response = await this.client.put(url, payload);

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to update record ${id} in ${evidence}: ${error.message}`);
    }
  }

  /**
   * Delete a record
   */
  async deleteRecord(evidence: string, id: string): Promise<FlexiResponse> {
    try {
      const url = `/${evidence}/${id}.json`;
      const response = await this.client.delete(url);

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to delete record ${id} from ${evidence}: ${error.message}`);
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
      // Keep country code, mask rest
      anonymized.kontaktTel = anonymized.kontaktTel.substring(0, 4) + '*********';
    }

    // Notes (may contain personal info)
    if (anonymized.poznam) {
      anonymized.poznam = '*** ANONYMIZOVANÉ ***';
    }
    if (anonymized.popis) {
      anonymized.popis = '*** ANONYMIZOVANÉ ***';
    }

    // Keep IC/DIC as they are public business identifiers
    // Keep amounts, dates, and other non-personal data

    return anonymized;
  }

  /**
   * Anonymize response data
   */
  private anonymizeResponse(response: FlexiResponse): FlexiResponse {
    if (!this.config.anonymizeData) {
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
      // Check if it's an ID or code
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
      // Multiple order fields
      return params.order.join(',');
    } else {
      // Single order field with optional direction
      if (params.orderDirection && params.orderDirection.toLowerCase() === 'desc') {
        return `${params.order}@D`;
      }
      return params.order;
    }
  }

  /**
   * Get company information
   */
  async getCompanyInfo(detail: 'id' | 'summary' | 'full' = 'full'): Promise<FlexiResponse> {
    try {
      const url = `/${this.config.company}.json?detail=${detail}`;
      const response = await this.client.get(url, {
        baseURL: `${this.config.url}/c`
      });

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to get company info: ${error.message}`);
    }
  }

  /**
   * Query issued invoices (faktury vydané)
   */
  async getFakturyVydane(params: FakturaVydanaQueryParams): Promise<FlexiResponse> {
    try {
      const queryParams = new URLSearchParams();

      // Get specific invoice by ID
      if (params.id) {
        const url = `/faktura-vydana/${params.id}.json`;

        // Add detail level
        queryParams.append('detail', params.detail || 'full');

        // Build includes/relations for items
        if (params.includeItems || params.includeCenik) {
          if (params.useRelations) {
            queryParams.append('relations', 'polozkyFaktury');
          }

          if (params.includeCenik) {
            // Include items with product catalog (cenik) data
            queryParams.append('includes', '/faktura-vydana/polozkyFaktury/faktura-vydana-polozka/cenik/');
          } else if (params.includeItems) {
            // Include just items without cenik
            queryParams.append('includes', '/faktura-vydana/polozkyFaktury');
          }
        }

        // Extended information flags
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

        const finalUrl = `${url}?${queryParams.toString()}`;
        const response = await this.client.get(finalUrl);
        return this.anonymizeResponse(response.data);
      }

      // List invoices with filtering, sorting, and pagination

      // Build and add filter
      const filterString = this.buildFilterString(params);
      if (filterString) {
        // URL encode the filter but preserve the parentheses structure
        const encodedFilter = filterString.replace(/'/g, '%27');
        queryParams.append('q', encodedFilter);
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
      const detail = params.detail || 'summary';
      queryParams.append('detail', detail);

      // Build includes/relations for items
      if (params.includeItems || params.includeCenik) {
        if (params.useRelations) {
          queryParams.append('relations', 'polozkyFaktury');
        }

        if (params.includeCenik) {
          // Include items with product catalog (cenik) data
          queryParams.append('includes', '/faktura-vydana/polozkyFaktury/faktura-vydana-polozka/cenik/');
        } else if (params.includeItems) {
          // Include just items without cenik
          queryParams.append('includes', '/faktura-vydana/polozkyFaktury');
        }
      }

      // Extended information flags
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

      const url = `/faktura-vydana.json?${queryParams.toString()}`;
      const response = await this.client.get(url);

      return this.anonymizeResponse(response.data);
    } catch (error: any) {
      throw new Error(`Failed to query faktury vydané: ${error.message}`);
    }
  }
}
