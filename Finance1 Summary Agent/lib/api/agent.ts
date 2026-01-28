/**
 * Agent API functions for communicating with the FastAPI backend
 * 
 * This module provides a clean interface for calling agent-related endpoints.
 * All requests go through Next.js API routes which proxy to the FastAPI backend.
 */

import type { ChatRequest, ChatResponse, ScanRequest, ScanResponse } from '@/types/api';

/**
 * Base URL for Next.js API routes
 * In production, this will be the same origin, but we support absolute URLs for development
 */
function getApiBaseUrl(): string {
  // In browser/client context, use relative URLs
  if (typeof window !== 'undefined') {
    return '';
  }
  
  // In server context (API routes), we might need absolute URL
  // For Next.js API routes, we can use relative paths
  return process.env.NEXT_PUBLIC_APP_URL || '';
}

/**
 * Make a request to a Next.js API route
 * 
 * @param endpoint - API route path (e.g., '/api/agent/chat')
 * @param options - Fetch options
 * @returns Promise resolving to parsed JSON response
 */
async function fetchApiRoute<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorDetails: string | undefined;
    
    try {
      const errorData = await response.json();
      errorMessage = errorData.error || errorData.message || errorMessage;
      errorDetails = errorData.details;
    } catch {
      // If response is not JSON, try to get text
      try {
        errorDetails = await response.text();
      } catch {
        // Ignore parsing errors
      }
    }
    
    const error = new Error(errorMessage) as Error & { status?: number; details?: string };
    error.status = response.status;
    error.details = errorDetails;
    throw error;
  }
  
  return response.json();
}

/**
 * Send a chat message to the agent
 * 
 * @param request - Chat request parameters
 * @returns Promise resolving to chat response
 * @throws {Error} If the request fails
 * 
 * @example
 * ```ts
 * const response = await chat({
 *   entity_id: '123456',
 *   entity_type: 'Accounts',
 *   query: 'What is the account status?'
 * });
 * ```
 */
export async function chat(request: ChatRequest): Promise<ChatResponse> {
  // Validate required fields
  if (!request.query) {
    throw new Error('query is required');
  }
  
  if (!request.entity_id && !request.account_id) {
    throw new Error('entity_id or account_id is required');
  }
  
  return fetchApiRoute<ChatResponse>('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Perform a proactive scan of a record
 * 
 * @param request - Scan request parameters
 * @returns Promise resolving to scan response with recommendations
 * @throws {Error} If the request fails
 * 
 * @example
 * ```ts
 * const response = await scan({
 *   entity_id: '123456',
 *   entity_type: 'Accounts'
 * });
 * ```
 */
export async function scan(request: ScanRequest): Promise<ScanResponse> {
  // Validate required fields
  if (!request.entity_id) {
    throw new Error('entity_id is required');
  }
  
  if (!request.entity_type) {
    throw new Error('entity_type is required');
  }
  
  return fetchApiRoute<ScanResponse>('/api/agent/scan', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
