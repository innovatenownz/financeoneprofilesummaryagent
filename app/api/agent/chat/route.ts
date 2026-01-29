import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';

/**
 * POST /api/agent/chat
 *
 * Proxies chat requests to the Railway backend.
 * Supports streaming responses.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { entity_id, entity_type, query } = body;

    if (!query) {
      return NextResponse.json({ error: 'query is required' }, { status: 400 });
    }

    if (!entity_id) {
      return NextResponse.json({ error: 'entity_id is required' }, { status: 400 });
    }

    const backendUrl = process.env.RAILWAY_BACKEND_URL;
    if (!backendUrl) {
      return NextResponse.json({ error: 'Backend URL not configured' }, { status: 500 });
    }

    // Prepare request for Railway Backend
    const backendRequest = {
      id: entity_id,
      module: entity_type || 'Accounts', // Default to Accounts if not provided
      query: query
    };

    const response = await fetch(`${backendUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendRequest),
    });

    if (!response.ok) {
        const errorText = await response.text();
        return NextResponse.json(
            { error: `Backend error: ${response.status}`, details: errorText },
            { status: response.status }
        );
    }

    // Handle Streaming Response
    // If the content-type is text/plain or text/event-stream, we stream it back
    const contentType = response.headers.get('content-type');
    if (contentType && (contentType.includes('text/plain') || contentType.includes('event-stream'))) {
        return new Response(response.body, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        });
    }

    // Handle JSON Response
    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error in /api/agent/chat:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
