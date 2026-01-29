import { NextRequest, NextResponse } from 'next/server';
import { fetchSupabaseFunction, ApiClientError } from '@/lib/api/client';
import type { ScanRequest, ScanResponse } from '@/types/api';

/**
 * POST /api/agent/scan
 *
 * Proxies scan requests to the Supabase Edge Function agent-scan.
 *
 * Request body:
 * - entity_id: string (required)
 * - entity_type: string (required)
 *
 * Response:
 * - recommendations: Recommendation[]
 */
export async function POST(request: NextRequest) {
  try {
    const body: ScanRequest = await request.json();

    if (!body.entity_id) {
      return NextResponse.json({ error: 'entity_id is required' }, { status: 400 });
    }
    if (!body.entity_type) {
      return NextResponse.json({ error: 'entity_type is required' }, { status: 400 });
    }

    const payload = { entity_id: body.entity_id, entity_type: body.entity_type };
    const response = await fetchSupabaseFunction('agent-scan', {
      method: 'POST',
      body: payload,
    });

    const data: ScanResponse = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in /api/agent/scan:', error);
    if (error instanceof ApiClientError) {
      return NextResponse.json(
        { error: error.message, details: error.details },
        { status: error.status ?? 502 }
      );
    }
    return NextResponse.json(
      { error: 'Internal server error', details: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
