/**
 * Main FlexiClient - Facade for all client modules
 */

import { FlexiConfig } from '../types.js';
import { CompanyClient } from './company-client.js';
import { FakturaClient } from './faktura-client.js';
import { ObjednavkaClient } from './objednavka-client.js';

export class FlexiClient {
  public company: CompanyClient;
  public faktura: FakturaClient;
  public objednavka: ObjednavkaClient;

  constructor(config: FlexiConfig) {
    this.company = new CompanyClient(config);
    this.faktura = new FakturaClient(config);
    this.objednavka = new ObjednavkaClient(config);
  }

  /**
   * Legacy method for backward compatibility
   * @deprecated Use client.company.getInfo() instead
   */
  async getCompanyInfo(detail: 'id' | 'summary' | 'full' = 'full') {
    return this.company.getInfo(detail);
  }

  /**
   * Legacy method for backward compatibility
   * @deprecated Use client.faktura.getVydane() instead
   */
  async getFakturyVydane(params: any) {
    return this.faktura.getVydane(params);
  }

  /**
   * Legacy method for backward compatibility
   * @deprecated Use client.objednavka.getPrijate() instead
   */
  async getObjednavkyPrijate(params: any) {
    return this.objednavka.getPrijate(params);
  }

  /**
   * Legacy method for backward compatibility
   * @deprecated Use client.company.listEvidences() instead
   */
  async listEvidences() {
    return this.company.listEvidences();
  }
}

// Re-export client classes for direct usage
export { BaseFlexiClient } from './base-client.js';
export { CompanyClient } from './company-client.js';
export { FakturaClient } from './faktura-client.js';
export { ObjednavkaClient } from './objednavka-client.js';
