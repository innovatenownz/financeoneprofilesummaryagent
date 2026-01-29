/**
 * API client utilities for Supabase Edge Functions.
 * Backend is Supabase; agent/chat, agent/scan, and upload proxy to Edge Functions.
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

/** Default timeout for API requests (30 seconds). */
const DEFAULT_TIMEOUT = 30000;

/**
 * Get the Supabase Edge Functions base URL (e.g. https://xxx.supabase.co/functions/v1).
 */
export function getSupabaseEdgeUrl(): string {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
  if (!url) {
    throw new ApiClientError(
      'Supabase URL is not configured. Set NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL when using Supabase backend.',
      500
    );
  }
  const base = url.replace(/\/$/, '');
  return `${base}/functions/v1`;
}

/** Options for calling a Supabase Edge Function (JSON body). */
export interface SupabaseFunctionOptions {
  method?: string;
  headers?: HeadersInit;
  /** Request body: object (will be JSON.stringify'd) or string. */
  body?: string | object;
}

/**
 * Call a Supabase Edge Function by name.
 * Uses SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY for Authorization.
 */
export async function fetchSupabaseFunction(
  functionName: string,
  options: SupabaseFunctionOptions = {},
  timeout: number = DEFAULT_TIMEOUT
): Promise<Response> {
  const edgeUrl = getSupabaseEdgeUrl();
  const url = `${edgeUrl}/${functionName}`;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!key) {
    throw new ApiClientError(
      'Supabase anon or service role key is not configured. Set SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY when using Supabase backend.',
      500
    );
  }
  const body = options.body !== undefined
    ? (typeof options.body === 'string' ? options.body : JSON.stringify(options.body))
    : undefined;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, {
      method: options.method ?? 'POST',
      body,
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    clearTimeout(timeoutId);
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new ApiClientError(
        `Supabase Edge Function ${functionName} failed: ${response.status} ${response.statusText}`,
        response.status,
        errorText
      );
    }
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiClientError) throw error;
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiClientError(`Request timeout after ${timeout}ms`, 408, 'The request took too long to complete');
    }
    throw new ApiClientError(
      error instanceof Error ? error.message : String(error),
      undefined,
      String(error)
    );
  }
}

/**
 * Call a Supabase Edge Function with FormData (e.g. for file upload).
 * Does not set Content-Type so the runtime can set multipart boundary.
 */
export async function fetchSupabaseFunctionFormData(
  functionName: string,
  formData: FormData,
  timeout: number = DEFAULT_TIMEOUT
): Promise<Response> {
  const edgeUrl = getSupabaseEdgeUrl();
  const url = `${edgeUrl}/${functionName}`;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!key) {
    throw new ApiClientError(
      'Supabase anon or service role key is not configured. Set SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY when using Supabase backend.',
      500
    );
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      headers: { Authorization: `Bearer ${key}` },
    });
    clearTimeout(timeoutId);
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new ApiClientError(
        `Supabase Edge Function ${functionName} failed: ${response.status} ${response.statusText}`,
        response.status,
        errorText
      );
    }
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiClientError) throw error;
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiClientError(`Request timeout after ${timeout}ms`, 408, 'The request took too long to complete');
    }
    throw new ApiClientError(
      error instanceof Error ? error.message : String(error),
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
