/**
 * Company Client
 * Handles company information and settings
 */

import { BaseFlexiClient } from './base-client.js';
import { FlexiResponse } from '../types.js';
import { ResponseCache, createCacheKey } from '../cache/index.js';

export class CompanyClient extends BaseFlexiClient {
  private cache: ResponseCache;

  constructor(config: any, retryOptions?: any) {
    super(config, retryOptions);
    this.cache = new ResponseCache({
      maxSize: 50,
      defaultTtl: 600000, // 10 minutes for company info
    });
  }

  /**
   * Get company information
   * @param detail Level of detail: 'id', 'summary', or 'full'
   */
  async getInfo(detail: 'id' | 'summary' | 'full' = 'full'): Promise<FlexiResponse> {
    const cacheKey = createCacheKey('company', detail);

    return this.cache.getOrSet(cacheKey, async () => {
      const url = `/${this.config.company}.json?detail=${detail}`;
      return await this.get(url, {
        baseURL: `${this.config.url}/c`
      });
    });
  }

  /**
   * Get list of available evidences
   */
  async listEvidences(): Promise<Array<{
    name: string;
    description: string;
    url: string;
  }>> {
    const cacheKey = createCacheKey('evidences');

    return this.cache.getOrSet(cacheKey, async () => {
      const response = await this.get<any>('/evidence-list.json');
      const data = response;

      if (data.winstrom && data.winstrom.evidence) {
        return data.winstrom.evidence.map((ev: any) => ({
          name: ev.evidenceType || ev['@evidenceType'] || '',
          description: ev.evidenceName || ev['@evidenceName'] || '',
          url: `${this.config.url}/c/${this.config.company}/${ev.evidenceType || ev['@evidenceType']}`,
        }));
      }

      return [];
    });
  }
}
