/**
 * Logging system for Flexi MCP Server
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4,
}

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: Date;
  meta?: Record<string, any>;
}

export interface LoggerOptions {
  level?: LogLevel;
  prefix?: string;
  enableColors?: boolean;
}

export class Logger {
  private level: LogLevel;
  private prefix: string;
  private enableColors: boolean;

  constructor(options: LoggerOptions = {}) {
    this.level = options.level !== undefined ? options.level : LogLevel.INFO;
    this.prefix = options.prefix || '';
    this.enableColors = options.enableColors !== false;
  }

  /**
   * Log a debug message
   */
  debug(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, meta);
  }

  /**
   * Log an info message
   */
  info(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, meta);
  }

  /**
   * Log a warning message
   */
  warn(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, meta);
  }

  /**
   * Log an error message
   */
  error(message: string, error?: Error | Record<string, any>): void {
    const meta = error instanceof Error
      ? { error: error.message, stack: error.stack }
      : error;
    this.log(LogLevel.ERROR, message, meta);
  }

  /**
   * Set the log level
   */
  setLevel(level: LogLevel): void {
    this.level = level;
  }

  /**
   * Get the current log level
   */
  getLevel(): LogLevel {
    return this.level;
  }

  /**
   * Check if a level is enabled
   */
  isLevelEnabled(level: LogLevel): boolean {
    return level >= this.level;
  }

  /**
   * Core logging method
   */
  private log(level: LogLevel, message: string, meta?: Record<string, any>): void {
    if (!this.isLevelEnabled(level)) {
      return;
    }

    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date(),
      meta,
    };

    this.write(entry);
  }

  /**
   * Write log entry to output
   */
  private write(entry: LogEntry): void {
    const levelName = this.getLevelName(entry.level);
    const levelColor = this.getLevelColor(entry.level);
    const timestamp = entry.timestamp.toISOString();

    let output = '';

    // Add timestamp
    output += this.colorize(`[${timestamp}]`, '\x1b[90m') + ' ';

    // Add level
    output += this.colorize(`[${levelName}]`, levelColor) + ' ';

    // Add prefix if set
    if (this.prefix) {
      output += this.colorize(`[${this.prefix}]`, '\x1b[36m') + ' ';
    }

    // Add message
    output += entry.message;

    // Add metadata if present
    if (entry.meta && Object.keys(entry.meta).length > 0) {
      output += ' ' + JSON.stringify(entry.meta);
    }

    // Write to stderr (MCP servers should use stderr for logging)
    console.error(output);
  }

  /**
   * Get level name string
   */
  private getLevelName(level: LogLevel): string {
    switch (level) {
      case LogLevel.DEBUG: return 'DEBUG';
      case LogLevel.INFO: return 'INFO ';
      case LogLevel.WARN: return 'WARN ';
      case LogLevel.ERROR: return 'ERROR';
      default: return 'UNKNOWN';
    }
  }

  /**
   * Get ANSI color code for level
   */
  private getLevelColor(level: LogLevel): string {
    switch (level) {
      case LogLevel.DEBUG: return '\x1b[37m'; // White
      case LogLevel.INFO: return '\x1b[32m';  // Green
      case LogLevel.WARN: return '\x1b[33m';  // Yellow
      case LogLevel.ERROR: return '\x1b[31m'; // Red
      default: return '\x1b[0m';
    }
  }

  /**
   * Colorize text if colors are enabled
   */
  private colorize(text: string, color: string): string {
    if (!this.enableColors) {
      return text;
    }
    return `${color}${text}\x1b[0m`;
  }
}

/**
 * Default logger instance
 */
export const defaultLogger = new Logger({
  level: process.env.LOG_LEVEL
    ? parseInt(process.env.LOG_LEVEL)
    : LogLevel.INFO,
  prefix: 'Flexi',
  enableColors: true,
});

/**
 * Create a child logger with a specific prefix
 */
export function createLogger(prefix: string, options: Omit<LoggerOptions, 'prefix'> = {}): Logger {
  return new Logger({
    ...options,
    prefix,
  });
}
