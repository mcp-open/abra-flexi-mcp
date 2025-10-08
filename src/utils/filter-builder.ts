/**
 * Filter Builder utility for constructing Flexibee filter strings
 */

export type FilterOperator =
  | '=' | '==' | 'eq'
  | '<>' | '!=' | 'ne' | 'neq'
  | '<' | 'lt'
  | '<=' | 'lte'
  | '>' | 'gt'
  | '>=' | 'gte'
  | 'like' | 'like similar'
  | 'begins' | 'begins similar'
  | 'ends'
  | 'between'
  | 'in'
  | 'is null' | 'is not null'
  | 'is empty' | 'is not empty'
  | 'is true' | 'is false';

export class FlexiFilterBuilder {
  private filters: string[] = [];

  /**
   * Add a date range filter
   */
  addDateRange(field: string, from?: string, to?: string): this {
    if (from) {
      this.filters.push(`${field} >= '${from}'`);
    }
    if (to) {
      this.filters.push(`${field} <= '${to}'`);
    }
    return this;
  }

  /**
   * Add an equals filter
   */
  addEquals(field: string, value: string | number | boolean): this {
    if (typeof value === 'string') {
      this.filters.push(`${field} = '${value}'`);
    } else {
      this.filters.push(`${field} = ${value}`);
    }
    return this;
  }

  /**
   * Add a not equals filter
   */
  addNotEquals(field: string, value: string | number | boolean): this {
    if (typeof value === 'string') {
      this.filters.push(`${field} <> '${value}'`);
    } else {
      this.filters.push(`${field} <> ${value}`);
    }
    return this;
  }

  /**
   * Add a greater than filter
   */
  addGreaterThan(field: string, value: number): this {
    this.filters.push(`${field} > ${value}`);
    return this;
  }

  /**
   * Add a greater than or equal filter
   */
  addGreaterThanOrEqual(field: string, value: number): this {
    this.filters.push(`${field} >= ${value}`);
    return this;
  }

  /**
   * Add a less than filter
   */
  addLessThan(field: string, value: number): this {
    this.filters.push(`${field} < ${value}`);
    return this;
  }

  /**
   * Add a less than or equal filter
   */
  addLessThanOrEqual(field: string, value: number): this {
    this.filters.push(`${field} <= ${value}`);
    return this;
  }

  /**
   * Add a numeric range filter
   */
  addNumericRange(field: string, min?: number, max?: number): this {
    if (min !== undefined) {
      this.filters.push(`${field} >= ${min}`);
    }
    if (max !== undefined) {
      this.filters.push(`${field} <= ${max}`);
    }
    return this;
  }

  /**
   * Add a like (contains) filter
   */
  addLike(field: string, value: string, similar: boolean = false): this {
    const operator = similar ? 'like similar' : 'like';
    this.filters.push(`${field} ${operator} '${value}'`);
    return this;
  }

  /**
   * Add a begins with filter
   */
  addBeginsWith(field: string, value: string, similar: boolean = false): this {
    const operator = similar ? 'begins similar' : 'begins';
    this.filters.push(`${field} ${operator} '${value}'`);
    return this;
  }

  /**
   * Add an ends with filter
   */
  addEndsWith(field: string, value: string): this {
    this.filters.push(`${field} ends '${value}'`);
    return this;
  }

  /**
   * Add an IN filter (value is one of the list)
   */
  addIn(field: string, values: Array<string | number>): this {
    const formattedValues = values.map(v =>
      typeof v === 'string' ? `'${v}'` : v
    ).join(', ');
    this.filters.push(`${field} in (${formattedValues})`);
    return this;
  }

  /**
   * Add a between filter
   */
  addBetween(field: string, min: number, max: number): this {
    this.filters.push(`${field} between ${min} ${max}`);
    return this;
  }

  /**
   * Add an is null filter
   */
  addIsNull(field: string): this {
    this.filters.push(`${field} is null`);
    return this;
  }

  /**
   * Add an is not null filter
   */
  addIsNotNull(field: string): this {
    this.filters.push(`${field} is not null`);
    return this;
  }

  /**
   * Add an is empty filter
   */
  addIsEmpty(field: string): this {
    this.filters.push(`${field} is empty`);
    return this;
  }

  /**
   * Add an is not empty filter
   */
  addIsNotEmpty(field: string): this {
    this.filters.push(`${field} is not empty`);
    return this;
  }

  /**
   * Add a boolean filter
   */
  addBoolean(field: string, value: boolean): this {
    this.filters.push(`${field} is ${value ? 'true' : 'false'}`);
    return this;
  }

  /**
   * Add a custom filter expression
   */
  addCustom(expression: string): this {
    this.filters.push(expression);
    return this;
  }

  /**
   * Add a filter for relation (uses code: prefix automatically)
   */
  addRelation(field: string, codeOrId: string | number): this {
    if (typeof codeOrId === 'string' && !/^\d+$/.test(codeOrId)) {
      // It's a code, add code: prefix
      this.filters.push(`${field} = 'code:${codeOrId}'`);
    } else {
      // It's a numeric ID
      this.filters.push(`${field} = ${codeOrId}`);
    }
    return this;
  }

  /**
   * Add a tag filter (štítky)
   */
  addTag(tag: string): this {
    return this.addRelation('stitky', tag);
  }

  /**
   * Add OR group - combines multiple filters with OR
   */
  addOrGroup(builderFn: (builder: FlexiFilterBuilder) => void): this {
    const orBuilder = new FlexiFilterBuilder();
    builderFn(orBuilder);
    const orExpression = orBuilder.buildWithoutParens();
    if (orExpression) {
      this.filters.push(`(${orExpression.split(' and ').join(' or ')})`);
    }
    return this;
  }

  /**
   * Build the filter string with parentheses
   */
  build(): string | undefined {
    if (this.filters.length === 0) {
      return undefined;
    }
    return `(${this.filters.join(' and ')})`;
  }

  /**
   * Build without outer parentheses (for internal use)
   */
  private buildWithoutParens(): string {
    return this.filters.join(' and ');
  }

  /**
   * Build with OR logic instead of AND
   */
  buildOr(): string | undefined {
    if (this.filters.length === 0) {
      return undefined;
    }
    return `(${this.filters.join(' or ')})`;
  }

  /**
   * Get the raw filters array
   */
  getFilters(): string[] {
    return [...this.filters];
  }

  /**
   * Reset all filters
   */
  reset(): this {
    this.filters = [];
    return this;
  }

  /**
   * Check if builder has any filters
   */
  hasFilters(): boolean {
    return this.filters.length > 0;
  }

  /**
   * Get count of filters
   */
  count(): number {
    return this.filters.length;
  }
}
