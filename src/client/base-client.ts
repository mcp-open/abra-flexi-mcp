/**
 * Base Flexi API Client
 * Provides core HTTP communication functionality
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { FlexiConfig, FlexiResponse } from '../types.js';
import { AuthenticationError, NetworkError, NotFoundError } from '../errors/index.js';
import { withRetry, RetryOptions } from '../utils/retry.js';
import { createLogger, Logger } from '../logging/index.js';

export class BaseFlexiClient {
  protected client: AxiosInstance;
  protected config: FlexiConfig;
  protected retryOptions: RetryOptions;
  protected logger: Logger;

  constructor(config: FlexiConfig, retryOptions?: RetryOptions) {
    this.config = config;
    this.logger = createLogger('FlexiClient');

    this.retryOptions = retryOptions || {
      maxAttempts: 3,
      initialDelay: 1000,
      maxDelay: 10000,
      onRetry: (error, attempt, delay) => {
        this.logger.warn(
          `Retry attempt ${attempt} after ${delay}ms`,
          { error: error.message }
        );
      },
    };

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
      timeout: 30000, // 30 second timeout
    });
  }

  /**
   * Execute a GET request with error handling and retry
   */
  protected async get<T = FlexiResponse>(
    url: string,
    options?: { baseURL?: string }
  ): Promise<T> {
    return withRetry(async () => {
      try {
        const response = await this.client.get(url, options);
        return response.data;
      } catch (error) {
        this.handleError(error as AxiosError);
      }
    }, this.retryOptions);
  }

  /**
   * Execute a POST request with error handling and retry
   */
  protected async post<T = FlexiResponse>(
    url: string,
    data: any
  ): Promise<T> {
    return withRetry(async () => {
      try {
        const response = await this.client.post(url, data);
        return response.data;
      } catch (error) {
        this.handleError(error as AxiosError);
      }
    }, this.retryOptions);
  }

  /**
   * Execute a PUT request with error handling and retry
   */
  protected async put<T = FlexiResponse>(
    url: string,
    data: any
  ): Promise<T> {
    return withRetry(async () => {
      try {
        const response = await this.client.put(url, data);
        return response.data;
      } catch (error) {
        this.handleError(error as AxiosError);
      }
    }, this.retryOptions);
  }

  /**
   * Execute a DELETE request with error handling (no retry for safety)
   */
  protected async delete<T = FlexiResponse>(url: string): Promise<T> {
    try {
      const response = await this.client.delete(url);
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Handle Axios errors and convert to custom error types
   */
  protected handleError(error: AxiosError): never {
    if (error.response) {
      const status = error.response.status;
      const message = this.extractErrorMessage(error);

      switch (status) {
        case 401:
        case 403:
          throw new AuthenticationError(
            `Authentication failed: ${message}`
          );
        case 404:
          throw new NotFoundError(
            `Resource not found: ${message}`,
            error.config?.url
          );
        case 400:
          throw new NetworkError(
            `Bad request: ${message}`,
            status
          );
        case 500:
        case 502:
        case 503:
          throw new NetworkError(
            `Server error: ${message}`,
            status
          );
        default:
          throw new NetworkError(
            `HTTP ${status}: ${message}`,
            status
          );
      }
    } else if (error.request) {
      throw new NetworkError(
        'No response received from server. Please check your connection.'
      );
    } else {
      throw new NetworkError(
        `Request failed: ${error.message}`
      );
    }
  }

  /**
   * Extract error message from Axios error response
   */
  private extractErrorMessage(error: AxiosError): string {
    const data = error.response?.data as any;

    if (data?.winstrom?.message) {
      return data.winstrom.message;
    }

    if (data?.message) {
      return data.message;
    }

    if (typeof data === 'string') {
      return data;
    }

    return error.message || 'Unknown error';
  }

  /**
   * Get base URL for the Flexibee instance
   */
  protected getBaseUrl(): string {
    return `${this.config.url}/c/${this.config.company}`;
  }

  /**
   * Check if data anonymization is enabled
   */
  protected shouldAnonymize(): boolean {
    return this.config.anonymizeData === true;
  }
}
