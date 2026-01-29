import { NextRequest, NextResponse } from 'next/server';
import { fetchSupabaseFunction, parseJsonResponse, ApiClientError } from '@/lib/api/client';
import type { ChatRequest, ChatResponse } from '@/types/api';

/**
 * POST /api/agent/chat
 *
 * Proxies chat requests to the Supabase Edge Function agent-chat.
 *
 * Request body:
 * - entity_id?: string (at least one of entity_id or account_id is required)
 * - account_id?: string (legacy)
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

    if (!body.query) {
      return NextResponse.json({ error: 'query is required' }, { status: 400 });
    }

    const entityId = body.entity_id || body.account_id;
    if (!entityId) {
      return NextResponse.json(
        { error: 'entity_id or account_id is required' },
        { status: 400 }
      );
    }

    const backendRequest = {
      entity_id: entityId,
      account_id: entityId,
      query: body.query,
      ...(body.entity_type && { entity_type: body.entity_type }),
    };

    const response = await fetchSupabaseFunction('agent-chat', {
      method: 'POST',
      body: backendRequest,
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
