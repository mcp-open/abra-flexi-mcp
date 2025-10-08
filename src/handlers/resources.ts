/**
 * Resource handlers for Flexi MCP Server
 */

import { FlexiClient } from '../client/index.js';
import { NotFoundError } from '../errors/index.js';

export interface ResourceContent {
  contents: Array<{
    uri: string;
    mimeType: string;
    text: string;
  }>;
  [key: string]: any; // Allow additional properties for MCP compatibility
}

/**
 * Handles the evidences resource
 */
async function handleEvidencesResource(
  client: FlexiClient,
  uri: string
): Promise<ResourceContent> {
  const evidences = await client.listEvidences();

  return {
    contents: [
      {
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(evidences, null, 2),
      },
    ],
  };
}

/**
 * Handles the company-info resource
 */
async function handleCompanyInfoResource(
  client: FlexiClient,
  uri: string
): Promise<ResourceContent> {
  const companyInfo = await client.getCompanyInfo('full');

  return {
    contents: [
      {
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(companyInfo, null, 2),
      },
    ],
  };
}

/**
 * Main resource handler dispatcher
 */
export async function handleResourceRead(
  uri: string,
  client: FlexiClient
): Promise<ResourceContent> {
  switch (uri) {
    case 'flexibee://evidences':
      return handleEvidencesResource(client, uri);

    case 'flexibee://company-info':
      return handleCompanyInfoResource(client, uri);

    default:
      throw new NotFoundError(`Unknown resource: ${uri}`, uri);
  }
}

/**
 * Lists all available resources
 */
export function listResources() {
  return {
    resources: [
      {
        uri: 'flexibee://evidences',
        name: 'Available Evidences',
        description: 'List of all available Flexi evidences (tables) in the system',
        mimeType: 'application/json',
      },
      {
        uri: 'flexibee://company-info',
        name: 'Company Information',
        description: 'Current company configuration and settings',
        mimeType: 'application/json',
      },
    ],
  };
}