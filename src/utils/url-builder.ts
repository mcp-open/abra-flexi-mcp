/**
 * URL Builder utility for constructing Flexibee API URLs
 */

export class FlexiUrlBuilder {
  private params: URLSearchParams;

  constructor() {
    this.params = new URLSearchParams();
  }

  /**
   * Add pagination parameters
   */
  addPagination(limit?: number, offset?: number): this {
    if (limit !== undefined) {
      this.params.append('limit', limit.toString());
    }
    if (offset !== undefined) {
      this.params.append('start', offset.toString());
    }
    return this;
  }

  /**
   * Add detail level parameter
   */
  addDetail(detail?: string): this {
    if (detail) {
      this.params.append('detail', detail);
    }
    return this;
  }

  /**
   * Add filter parameter
   */
  addFilter(filter?: string): this {
    if (filter) {
      // URLSearchParams will handle encoding automatically
      this.params.append('q', filter);
    }
    return this;
  }

  /**
   * Add ordering parameter
   */
  addOrder(order?: string | string[]): this {
    if (!order) return this;

    if (Array.isArray(order)) {
      // Multiple order fields
      this.params.append('order', order.join(','));
    } else {
      // Single order field
      this.params.append('order', order);
    }
    return this;
  }

  /**
   * Add includes parameter for loading nested relations
   */
  addIncludes(includes?: string): this {
    if (includes) {
      this.params.append('includes', includes);
    }
    return this;
  }

  /**
   * Add relations parameter for loading nested data
   */
  addRelations(relations?: string | string[]): this {
    if (!relations) return this;

    if (Array.isArray(relations)) {
      this.params.append('relations', relations.join(','));
    } else {
      this.params.append('relations', relations);
    }
    return this;
  }

  /**
   * Add row count parameter
   */
  addRowCount(addRowCount?: boolean): this {
    if (addRowCount) {
      this.params.append('add-row-count', 'true');
    }
    return this;
  }

  /**
   * Add flag to exclude external IDs
   */
  addNoExtIds(noExtIds?: boolean): this {
    if (noExtIds) {
      this.params.append('no-ext-ids', 'true');
    }
    return this;
  }

  /**
   * Add flag to exclude internal IDs
   */
  addNoIds(noIds?: boolean): this {
    if (noIds) {
      this.params.append('no-ids', 'true');
    }
    return this;
  }

  /**
   * Add flag to use code as ID
   */
  addCodeAsId(codeAsId?: boolean): this {
    if (codeAsId) {
      this.params.append('code-as-id', 'true');
    }
    return this;
  }

  /**
   * Add custom parameter
   */
  addParam(key: string, value: string | number | boolean): this {
    this.params.append(key, value.toString());
    return this;
  }

  /**
   * Build final query string
   */
  build(): string {
    const query = this.params.toString();
    return query ? `?${query}` : '';
  }

  /**
   * Reset all parameters
   */
  reset(): this {
    this.params = new URLSearchParams();
    return this;
  }

  /**
   * Get the URLSearchParams object directly
   */
  getParams(): URLSearchParams {
    return this.params;
  }
}
