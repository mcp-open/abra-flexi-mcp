/**
 * MCP Server instance and lifecycle management
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { FlexiClient } from './client/index.js';
import { ServerConfig, getSafeConfig } from './config/index.js';
import { TOOL_DEFINITIONS } from './tools/definitions.js';
import { handleToolCall } from './handlers/tools.js';
import { handleResourceRead, listResources } from './handlers/resources.js';
import { FlexiError } from './errors/index.js';

export class MCPServer {
  private server: Server;
  private client: FlexiClient;
  private config: ServerConfig;

  constructor(config: ServerConfig) {
    this.config = config;
    this.client = new FlexiClient(config.flexibee);

    this.server = new Server(
      {
        name: config.server.name,
        version: config.server.version,
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    this.setupHandlers();
  }

  /**
   * Sets up all request handlers for the MCP server
   */
  private setupHandlers(): void {
    // Tool listing handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: TOOL_DEFINITIONS,
      };
    });

    // Tool execution handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        return await handleToolCall(name, args, this.client);
      } catch (error: any) {
        console.error(`Error handling tool ${name}:`, error);

        // Provide more specific error messages
        if (error instanceof FlexiError) {
          return {
            content: [
              {
                type: 'text',
                text: `${error.name}: ${error.message}`,
              },
            ],
            isError: true,
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message || 'Unknown error occurred'}`,
            },
          ],
          isError: true,
        };
      }
    });

    // Resource listing handler
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return listResources();
    });

    // Resource reading handler
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      try {
        return await handleResourceRead(uri, this.client);
      } catch (error: any) {
        console.error(`Error reading resource ${uri}:`, error);

        if (error instanceof FlexiError) {
          throw new Error(`${error.name}: ${error.message}`);
        }

        throw new Error(`Failed to read resource: ${error.message}`);
      }
    });
  }

  /**
   * Starts the MCP server
   */
  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    this.logStartupInfo();
  }

  /**
   * Logs startup information
   */
  private logStartupInfo(): void {
    const safeConfig = getSafeConfig(this.config);

    console.error('===================================================');
    console.error(`${this.config.server.name} v${this.config.server.version}`);
    console.error('===================================================');
    console.error(`Connected to: ${safeConfig.url}`);
    console.error(`Company: ${safeConfig.company}`);
    console.error(`User: ${safeConfig.username}`);
    console.error(`Anonymization: ${safeConfig.anonymizeData ? 'ENABLED' : 'DISABLED'}`);
    console.error('Server running on stdio transport');
    console.error('===================================================');
  }
}