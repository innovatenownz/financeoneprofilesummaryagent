import { NextRequest, NextResponse } from 'next/server';
import { fetchFastAPI, parseJsonResponse, ApiClientError } from '@/lib/api/client';
import type { ChatRequest, ChatResponse } from '@/types/api';

/**
 * POST /api/agent/chat
 * 
 * Proxies chat requests to the FastAPI backend /chat endpoint
 * 
 * Request body:
 * - entity_id?: string (at least one of entity_id or account_id is required)
 * - account_id?: string (legacy support - at least one of entity_id or account_id is required)
 * - entity_type?: string (optional, defaults to "Accounts")
 * - query: string (required)
 * 
 * Response:
 * - response: string
 * - actions?: Action[]
 */
export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json();
    
    // Validate required fields
    if (!body.query) {
      return NextResponse.json(
        { error: 'query is required' },
        { status: 400 }
      );
    }
    
    // Support both entity_id and legacy account_id
    const entityId = body.entity_id || body.account_id;
    if (!entityId) {
      return NextResponse.json(
        { error: 'entity_id or account_id is required' },
        { status: 400 }
      );
    }
    
    // Prepare request for FastAPI backend
    // Backend currently expects account_id, but we'll send both for compatibility
    const backendRequest = {
      account_id: entityId, // Backend compatibility
      query: body.query,
      // Include entity_type if provided (for future backend support)
      ...(body.entity_type && { entity_type: body.entity_type }),
    };
    
    // Proxy to FastAPI backend
    const response = await fetchFastAPI('/chat', {
      method: 'POST',
      body: JSON.stringify(backendRequest),
    });
    
    const data = await parseJsonResponse<ChatResponse>(response);
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in /api/agent/chat:', error);
    
    // Handle ApiClientError with proper status codes
    if (error instanceof ApiClientError) {
      return NextResponse.json(
        { 
          error: error.message,
          details: error.details 
        },
        { status: error.status || 502 }
      );
    }
    
    // Handle other errors
    if (error instanceof Error) {
      return NextResponse.json(
        { 
          error: 'Backend request failed',
          details: error.message 
        },
        { status: 500 }
      );
    }
    
    return NextResponse.json(
      { error: 'Internal server error', details: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
