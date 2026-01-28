import { NextRequest, NextResponse } from 'next/server';
import { fetchFastAPI } from '@/lib/api/client';
import type { ScanRequest, ScanResponse } from '@/types/api';

/**
 * POST /api/agent/scan
 * 
 * Proxies scan requests to the FastAPI backend /scan endpoint
 * Performs silent analysis without user query and returns proactive recommendations
 * 
 * Request body:
 * - entity_id: string (required)
 * - entity_type: string (required) - "Accounts", "Deals", "Contacts", etc.
 * 
 * Response:
 * - recommendations: Recommendation[]
 */
export async function POST(request: NextRequest) {
  try {
    const body: ScanRequest = await request.json();
    
    // Validate required fields
    if (!body.entity_id) {
      return NextResponse.json(
        { error: 'entity_id is required' },
        { status: 400 }
      );
    }
    
    if (!body.entity_type) {
      return NextResponse.json(
        { error: 'entity_type is required' },
        { status: 400 }
      );
    }
    
    // Proxy to FastAPI backend
    const response = await fetchFastAPI('/scan', {
      method: 'POST',
      body: JSON.stringify({
        entity_id: body.entity_id,
        entity_type: body.entity_type,
      }),
    });
    
    const data: ScanResponse = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in /api/agent/scan:', error);
    
    if (error instanceof Error) {
      // Check if it's a configuration error
      if (error.message.includes('FastAPI URL is not configured')) {
        return NextResponse.json(
          { error: 'Backend configuration error', details: error.message },
          { status: 500 }
        );
      }
      
      // Check if it's a FastAPI request error
      if (error.message.includes('FastAPI request failed')) {
        // If backend returns 404, the endpoint might not be implemented yet
        if (error.message.includes('404')) {
          return NextResponse.json(
            { 
              error: 'Scan endpoint not available', 
              details: 'The /scan endpoint is not yet implemented in the backend',
              recommendations: [] // Return empty array for graceful degradation
            },
            { status: 503 }
          );
        }
        
        return NextResponse.json(
          { error: 'Backend request failed', details: error.message },
          { status: 502 }
        );
      }
    }
    
    return NextResponse.json(
      { error: 'Internal server error', details: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
