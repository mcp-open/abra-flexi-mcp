#!/usr/bin/env node

/**
 * Abra Flexi MCP Server
 *
 * Provides Model Context Protocol interface to ABRA Flexi ERP API
 * Enables AI assistants to interact with Flexi accounting and business data
 *
 * @version 0.1.0
 * @author MCP Flexi Integration
 */

import { loadConfig } from './config/index.js';
import { MCPServer } from './server.js';
import { ConfigurationError } from './errors/index.js';
import { defaultLogger } from './logging/index.js';

/**
 * Main application entry point
 */
async function main(): Promise<void> {
  try {
    defaultLogger.info('Starting Flexi MCP Server...');

    // Load and validate configuration
    const config = loadConfig();
    defaultLogger.debug('Configuration loaded successfully');

    // Create and start server
    const server = new MCPServer(config);
    await server.start();
  } catch (error) {
    if (error instanceof ConfigurationError) {
      defaultLogger.error('Configuration error', error);
      process.exit(1);
    }

    defaultLogger.error('Failed to start server', error as Error);
    process.exit(1);
  }
}

/**
 * Handle graceful shutdown
 */
function setupShutdownHandlers(): void {
  const shutdown = (signal: string) => {
    defaultLogger.info(`Received ${signal}, shutting down Flexi MCP Server...`);
    process.exit(0);
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  // Handle uncaught errors
  process.on('uncaughtException', (error) => {
    defaultLogger.error('Uncaught exception', error);
    process.exit(1);
  });

  process.on('unhandledRejection', (reason, promise) => {
    defaultLogger.error('Unhandled rejection', {
      reason,
      promise: String(promise),
    });
    process.exit(1);
  });
}

// Setup handlers and start server
setupShutdownHandlers();
main().catch((error) => {
  defaultLogger.error('Fatal server error', error);
  process.exit(1);
});