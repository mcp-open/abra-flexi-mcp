/**
 * Simple in-memory cache for API responses
 */

export interface CacheOptions {
  /**
   * Maximum number of entries in cache
   * @default 100
   */
  maxSize?: number;

  /**
   * Default TTL in milliseconds
   * @default 300000 (5 minutes)
   */
  defaultTtl?: number;

  /**
   * Callback when cache entry expires
   */
  onExpire?: (key: string) => void;
}

interface CacheEntry<T> {
  value: T;
  expiresAt: number;
  createdAt: number;
}

export class ResponseCache {
  private cache: Map<string, CacheEntry<any>>;
  private options: Required<CacheOptions>;
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(options: CacheOptions = {}) {
    this.cache = new Map();
    this.options = {
      maxSize: options.maxSize || 100,
      defaultTtl: options.defaultTtl || 300000, // 5 minutes
      onExpire: options.onExpire || (() => {}),
    };

    // Start cleanup interval (every minute)
    this.startCleanup();
  }

  /**
   * Get value from cache
   * Returns null if not found or expired
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.delete(key);
      return null;
    }

    return entry.value as T;
  }

  /**
   * Set value in cache with optional TTL
   */
  set<T>(key: string, value: T, ttl?: number): void {
    // Enforce max size - remove oldest entry if needed
    if (this.cache.size >= this.options.maxSize && !this.cache.has(key)) {
      this.evictOldest();
    }

    const ttlMs = ttl || this.options.defaultTtl;
    const now = Date.now();

    this.cache.set(key, {
      value,
      expiresAt: now + ttlMs,
      createdAt: now,
    });
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Delete entry from cache
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all entries
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   */
  stats(): {
    size: number;
    maxSize: number;
    keys: string[];
  } {
    return {
      size: this.cache.size,
      maxSize: this.options.maxSize,
      keys: Array.from(this.cache.keys()),
    };
  }

  /**
   * Get or set pattern - fetch if not cached
   */
  async getOrSet<T>(
    key: string,
    fetchFn: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = this.get<T>(key);

    if (cached !== null) {
      return cached;
    }

    const value = await fetchFn();
    this.set(key, value, ttl);
    return value;
  }

  /**
   * Evict oldest entry based on creation time
   */
  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.createdAt < oldestTime) {
        oldestTime = entry.createdAt;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.delete(oldestKey);
    }
  }

  /**
   * Remove expired entries
   */
  private cleanup(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        expiredKeys.push(key);
      }
    }

    for (const key of expiredKeys) {
      this.options.onExpire(key);
      this.delete(key);
    }
  }

  /**
   * Start periodic cleanup
   */
  private startCleanup(): void {
    // Run cleanup every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 60000);

    // Don't prevent process from exiting
    if (this.cleanupInterval.unref) {
      this.cleanupInterval.unref();
    }
  }

  /**
   * Stop cleanup interval
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    this.clear();
  }
}

/**
 * Create cache key from parts
 */
export function createCacheKey(...parts: Array<string | number | boolean | undefined>): string {
  return parts
    .filter(p => p !== undefined && p !== null)
    .map(p => String(p))
    .join(':');
}
