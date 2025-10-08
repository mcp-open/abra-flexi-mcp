/**
 * Custom error classes for Flexi MCP Server
 */

export class FlexiError extends Error {
  constructor(message: string, public readonly code?: string) {
    super(message);
    this.name = 'FlexiError';
  }
}

export class ConfigurationError extends FlexiError {
  constructor(message: string) {
    super(message, 'CONFIG_ERROR');
    this.name = 'ConfigurationError';
  }
}

export class AuthenticationError extends FlexiError {
  constructor(message: string) {
    super(message, 'AUTH_ERROR');
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends FlexiError {
  constructor(message: string, public readonly field?: string) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends FlexiError {
  constructor(message: string, public readonly resource?: string) {
    super(message, 'NOT_FOUND');
    this.name = 'NotFoundError';
  }
}

export class NetworkError extends FlexiError {
  constructor(message: string, public readonly statusCode?: number) {
    super(message, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}