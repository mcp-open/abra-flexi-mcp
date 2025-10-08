/**
 * Configuration module for Flexi MCP Server
 * Handles environment variables and configuration validation
 */

import { FlexiConfig } from '../types.js';

export interface ServerConfig {
  flexibee: FlexiConfig;
  server: {
    name: string;
    version: string;
  };
}

/**
 * Validates that all required environment variables are present
 * @throws Error if any required variable is missing
 */
function validateEnvironment(): void {
  const required = [
    'FLEXIBEE_URL',
    'FLEXIBEE_COMPANY',
    'FLEXIBEE_USERNAME',
    'FLEXIBEE_PASSWORD'
  ];

  const missing = required.filter(key => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(', ')}\n` +
      'Please configure these in your MCP client settings.'
    );
  }

  // Validate URL format
  const url = process.env.FLEXIBEE_URL!;
  try {
    new URL(url);
  } catch {
    throw new Error(`Invalid FLEXIBEE_URL format: ${url}`);
  }
}

/**
 * Loads and validates server configuration from environment variables
 * @returns Complete server configuration
 */
export function loadConfig(): ServerConfig {
  validateEnvironment();

  return {
    flexibee: {
      url: process.env.FLEXIBEE_URL!,
      company: process.env.FLEXIBEE_COMPANY!,
      username: process.env.FLEXIBEE_USERNAME!,
      password: process.env.FLEXIBEE_PASSWORD!,
      anonymizeData: process.env.FLEXIBEE_ANONYMIZE_DATA === 'true',
    },
    server: {
      name: 'abra-flexi-mcp',
      version: '0.1.0',
    }
  };
}

/**
 * Gets a safe version of config for logging (without sensitive data)
 */
export function getSafeConfig(config: ServerConfig): Record<string, any> {
  return {
    url: config.flexibee.url,
    company: config.flexibee.company,
    username: config.flexibee.username,
    anonymizeData: config.flexibee.anonymizeData,
    serverName: config.server.name,
    serverVersion: config.server.version,
  };
}