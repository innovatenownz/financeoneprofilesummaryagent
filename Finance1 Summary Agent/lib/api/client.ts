/**
 * API client utilities for FastAPI backend
 * 
 * This module provides utilities for communicating with the FastAPI backend.
 * It's used by Next.js API routes to proxy requests to the backend.
 */

export interface ApiError {
  message: string;
  status?: number;
  details?: string;
}

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error implements ApiError {
  status?: number;
  details?: string;

  constructor(message: string, status?: number, details?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Get the FastAPI backend URL from environment variables
 * 
 * @returns The FastAPI backend base URL
 * @throws {ApiClientError} If the URL is not configured
 */
export function getFastAPIUrl(): string {
  const url = process.env.NEXT_PUBLIC_FASTAPI_URL || process.env.FASTAPI_URL;
  
  if (!url) {
    throw new ApiClientError(
      'FastAPI URL is not configured. Please set NEXT_PUBLIC_FASTAPI_URL or FASTAPI_URL environment variable.',
      500 // Internal Server Error - server misconfiguration
    );
  }
  
  return url.replace(/\/$/, ''); // Remove trailing slash
}

/**
 * Default timeout for API requests (30 seconds)
 */
const DEFAULT_TIMEOUT = 30000;

/**
 * Create a fetch request to the FastAPI backend with timeout support
 * 
 * @param endpoint - API endpoint path (e.g., '/chat')
 * @param options - Fetch options (method, body, headers, etc.)
 * @param timeout - Request timeout in milliseconds (default: 30000)
 * @returns Promise resolving to Response
 * @throws {ApiClientError} If the request fails or times out
 */
export async function fetchFastAPI(
  endpoint: string,
  options: RequestInit = {},
  timeout: number = DEFAULT_TIMEOUT
): Promise<Response> {
  const baseUrl = getFastAPIUrl();
  const url = `${baseUrl}${endpoint}`;
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      let errorText = 'Unknown error';
      try {
        const errorData = await response.json();
        errorText = errorData.detail || errorData.message || errorData.error || JSON.stringify(errorData);
      } catch {
        errorText = await response.text().catch(() => 'Unknown error');
      }
      
      throw new ApiClientError(
        `FastAPI request failed: ${response.status} ${response.statusText}`,
        response.status,
        errorText
      );
    }
    
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof ApiClientError) {
      throw error;
    }
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new ApiClientError(
          `Request timeout after ${timeout}ms`,
          408,
          'The request took too long to complete'
        );
      }
      
      throw new ApiClientError(
        `Network error: ${error.message}`,
        undefined,
        error.message
      );
    }
    
    throw new ApiClientError(
      'An unexpected error occurred',
      undefined,
      String(error)
    );
  }
}

/**
 * Parse JSON response with error handling
 * 
 * @param response - Fetch Response object
 * @returns Promise resolving to parsed JSON data
 * @throws {ApiClientError} If JSON parsing fails
 */
export async function parseJsonResponse<T>(response: Response): Promise<T> {
  try {
    const text = await response.text();
    if (!text) {
      throw new Error('Empty response body');
    }
    return JSON.parse(text) as T;
  } catch (error) {
    throw new ApiClientError(
      'Failed to parse response as JSON',
      response.status,
      error instanceof Error ? error.message : String(error)
    );
  }
}
