/**
 * API Contract Definition
 * 
 * This file serves as the source of truth for all API endpoints, their request/response
 * structures, and documentation. It defines the contract between the Next.js frontend
 * and the FastAPI backend.
 * 
 * When the backend changes, update this file first, then update the corresponding
 * TypeScript types and Zod schemas.
 */

import type {
  ChatRequest,
  ChatResponse,
  ScanRequest,
  ScanResponse,
  UploadRequest,
  UploadResponse,
  ZohoExecuteRequest,
  ZohoExecuteResponse,
  ZohoMetadataResponse,
} from '@/types/api';

/**
 * API Version Configuration
 */
export const API_VERSION = 'v1' as const;
export const API_BASE_PATH = `/api/${API_VERSION}` as const;

/**
 * FastAPI Backend Endpoints
 * These are the actual backend endpoints that our Next.js API routes proxy to
 */
export const BACKEND_ENDPOINTS = {
  CHAT: '/chat',
  SCAN: '/scan',
  UPLOAD: '/upload',
} as const;

/**
 * Next.js API Routes (Frontend-facing)
 * These are the endpoints exposed by the Next.js application
 */
export const API_ROUTES = {
  AGENT_CHAT: '/api/agent/chat',
  AGENT_SCAN: '/api/agent/scan',
  UPLOAD: '/api/upload',
  ZOHO_METADATA: '/api/zoho/metadata',
  ZOHO_EXECUTE: '/api/zoho/execute',
} as const;

/**
 * API Endpoint Definitions
 * 
 * Each endpoint definition includes:
 * - Method: HTTP method
 * - Path: Next.js API route path
 * - BackendPath: FastAPI backend endpoint (if applicable)
 * - Description: What the endpoint does
 * - RequestType: TypeScript type for request body
 * - ResponseType: TypeScript type for response body
 * - Deprecated: Whether this endpoint is deprecated
 * - DeprecatedSince: Version when deprecated (if applicable)
 * - ReplacedBy: New endpoint that replaces this one (if applicable)
 */

export interface EndpointDefinition<TRequest, TResponse> {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  backendPath?: string;
  description: string;
  requestType: string; // TypeScript type name
  responseType: string; // TypeScript type name
  deprecated?: boolean;
  deprecatedSince?: string;
  replacedBy?: string;
  notes?: string;
}

/**
 * Agent Chat Endpoint
 * 
 * Allows users to chat with the AI agent about a specific record.
 * The agent has access to the record's data and can provide insights,
 * answer questions, and suggest actions.
 */
export const AGENT_CHAT_ENDPOINT: EndpointDefinition<ChatRequest, ChatResponse> = {
  method: 'POST',
  path: API_ROUTES.AGENT_CHAT,
  backendPath: BACKEND_ENDPOINTS.CHAT,
  description: 'Chat with the AI agent about a specific record',
  requestType: 'ChatRequest',
  responseType: 'ChatResponse',
  notes: `
    - Supports both entity_id (modern) and account_id (legacy) for backward compatibility
    - At least one of entity_id or account_id must be provided
    - The backend currently expects account_id, but we send both for compatibility
    - Response may include optional actions array for actionable UI
  `,
};

/**
 * Agent Scan Endpoint
 * 
 * Performs a silent analysis of a record without user input.
 * Returns proactive recommendations based on the record's current state.
 */
export const AGENT_SCAN_ENDPOINT: EndpointDefinition<ScanRequest, ScanResponse> = {
  method: 'POST',
  path: API_ROUTES.AGENT_SCAN,
  backendPath: BACKEND_ENDPOINTS.SCAN,
  description: 'Perform silent analysis and get proactive recommendations',
  requestType: 'ScanRequest',
  responseType: 'ScanResponse',
  notes: `
    - This endpoint performs analysis without requiring a user query
    - Returns an array of recommendations with priorities
    - Recommendations may include actionable items
    - If the backend endpoint is not implemented, returns 503 with empty recommendations array
  `,
};

/**
 * Document Upload Endpoint
 * 
 * Uploads a document associated with a record.
 * The document is processed and added to the vector store for future reference.
 */
export const UPLOAD_ENDPOINT: EndpointDefinition<UploadRequest, UploadResponse> = {
  method: 'POST',
  path: API_ROUTES.UPLOAD,
  backendPath: BACKEND_ENDPOINTS.UPLOAD,
  description: 'Upload a document associated with a record',
  requestType: 'UploadRequest',
  responseType: 'UploadResponse',
  notes: `
    - Accepts multipart/form-data with file and entity information
    - File is processed and added to the vector store
    - Document becomes available for future agent queries
  `,
};

/**
 * Zoho Metadata Endpoint
 * 
 * Development utility for discovering Zoho CRM field API names.
 * Returns metadata about fields in a specific module.
 */
export const ZOHO_METADATA_ENDPOINT: EndpointDefinition<
  { module: string },
  ZohoMetadataResponse
> = {
  method: 'GET',
  path: API_ROUTES.ZOHO_METADATA,
  description: 'Get Zoho CRM field metadata for a module (development utility)',
  requestType: '{ module: string }',
  responseType: 'ZohoMetadataResponse',
  notes: `
    - Development-only endpoint for discovering field API names
    - Query parameter: ?module=Accounts
    - Returns field metadata including API names and display names
  `,
};

/**
 * Zoho Execute Endpoint
 * 
 * Executes a Zoho SDK action (e.g., update field, create record, send email).
 * This endpoint handles the execution of actions suggested by the agent.
 */
export const ZOHO_EXECUTE_ENDPOINT: EndpointDefinition<
  ZohoExecuteRequest,
  ZohoExecuteResponse
> = {
  method: 'POST',
  path: API_ROUTES.ZOHO_EXECUTE,
  description: 'Execute a Zoho SDK action (update field, create record, etc.)',
  requestType: 'ZohoExecuteRequest',
  responseType: 'ZohoExecuteResponse',
  notes: `
    - Executes actions suggested by the agent
    - Supports UPDATE_FIELD, CREATE_RECORD, SEND_EMAIL, and CUSTOM actions
    - Requires Zoho SDK to be initialized in the widget context
  `,
};

/**
 * All Endpoint Definitions
 * 
 * Central registry of all API endpoints for easy iteration and validation
 */
export const ALL_ENDPOINTS = {
  AGENT_CHAT: AGENT_CHAT_ENDPOINT,
  AGENT_SCAN: AGENT_SCAN_ENDPOINT,
  UPLOAD: UPLOAD_ENDPOINT,
  ZOHO_METADATA: ZOHO_METADATA_ENDPOINT,
  ZOHO_EXECUTE: ZOHO_EXECUTE_ENDPOINT,
} as const;

/**
 * Get endpoint definition by path
 */
export function getEndpointByPath(path: string): EndpointDefinition<any, any> | undefined {
  return Object.values(ALL_ENDPOINTS).find((endpoint) => endpoint.path === path);
}

/**
 * Get all backend endpoints
 */
export function getBackendEndpoints(): Array<{
  path: string;
  endpoint: EndpointDefinition<any, any>;
}> {
  return Object.values(ALL_ENDPOINTS)
    .filter((endpoint) => endpoint.backendPath)
    .map((endpoint) => ({
      path: endpoint.backendPath!,
      endpoint,
    }));
}

/**
 * API Contract Changelog
 * 
 * Document breaking changes and new features here
 */
export const API_CHANGELOG = [
  {
    date: '2026-01-28',
    version: 'v1.0.0',
    changes: [
      {
        type: 'added' as const,
        endpoint: 'AGENT_SCAN',
        description: 'Added /api/agent/scan endpoint for proactive recommendations',
      },
      {
        type: 'added' as const,
        endpoint: 'UPLOAD',
        description: 'Added /api/upload endpoint for document uploads',
      },
      {
        type: 'enhanced' as const,
        endpoint: 'AGENT_CHAT',
        description: 'Added optional actions array to chat response for actionable UI',
      },
      {
        type: 'added' as const,
        endpoint: 'ZOHO_EXECUTE',
        description: 'Added /api/zoho/execute endpoint for executing Zoho SDK actions',
      },
    ],
  },
] as const;
