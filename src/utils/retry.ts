/**
 * Retry utility for handling transient errors
 */

import { NetworkError } from '../errors/index.js';

export interface RetryOptions {
  /**
   * Maximum number of retry attempts
   * @default 3
   */
  maxAttempts?: number;

  /**
   * Initial delay in milliseconds before first retry
   * @default 1000
   */
  initialDelay?: number;

  /**
   * Maximum delay in milliseconds between retries
   * @default 10000
   */
  maxDelay?: number;

  /**
   * Multiplier for exponential backoff
   * @default 2
   */
  backoffMultiplier?: number;

  /**
   * Function to determine if an error should trigger a retry
   * @default Retries on NetworkError with 5xx status codes
   */
  shouldRetry?: (error: any, attempt: number) => boolean;

  /**
   * Callback called before each retry attempt
   */
  onRetry?: (error: any, attempt: number, delay: number) => void;
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
  shouldRetry: (error: any) => {
    // Retry on network errors and 5xx server errors
    if (error instanceof NetworkError) {
      const status = error.statusCode;
      return !status || status >= 500;
    }
    return false;
  },
  onRetry: () => {},
};

/**
 * Execute a function with retry logic
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: any;
  let delay = opts.initialDelay;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Check if we should retry
      const isLastAttempt = attempt === opts.maxAttempts;
      if (isLastAttempt || !opts.shouldRetry(error, attempt)) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const currentDelay = Math.min(delay, opts.maxDelay);

      // Call retry callback
      opts.onRetry(error, attempt, currentDelay);

      // Wait before retrying
      await sleep(currentDelay);

      // Increase delay for next attempt
      delay *= opts.backoffMultiplier;
    }
  }

  // This should never be reached, but TypeScript needs it
  throw lastError;
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry decorator for class methods
 */
export function Retry(options: RetryOptions = {}) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      return withRetry(
        () => originalMethod.apply(this, args),
        options
      );
    };

    return descriptor;
  };
}

/**
 * Create a retry-enabled version of a function
 */
export function retryable<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: RetryOptions = {}
): T {
  return ((...args: any[]) => {
    return withRetry(() => fn(...args), options);
  }) as T;
}
