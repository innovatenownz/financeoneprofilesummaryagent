import { NextRequest, NextResponse } from 'next/server';
import type { ZohoMetadataResponse } from '@/types/api';

/**
 * GET /api/zoho/metadata
 * 
 * Development utility for API name discovery
 * Fetches metadata for the current Zoho module to discover field API names
 * 
 * Query parameters:
 * - module?: string (optional) - Module name to fetch metadata for
 * 
 * Note: This endpoint requires Zoho SDK context and should only be used in development
 */
export async function GET(request: NextRequest) {
  try {
    // Check if we're in development mode
    const isDevelopment = process.env.NODE_ENV === 'development' || 
                         process.env.NEXT_PUBLIC_ENVIRONMENT === 'development';
    
    if (!isDevelopment) {
      return NextResponse.json(
        { error: 'This endpoint is only available in development mode' },
        { status: 403 }
      );
    }
    
    const searchParams = request.nextUrl.searchParams;
    const moduleName = searchParams.get('module');
    
    // Note: This endpoint would ideally use Zoho SDK, but since we're in a serverless
    // function, we can't directly access the client-side SDK. This endpoint should be
    // called from the client side where Zoho SDK is available.
    // 
    // For now, we'll return a helpful error message suggesting to use the client-side hook
    
    return NextResponse.json(
      { 
        error: 'This endpoint should be called from the client side',
        message: 'Use the useZohoSDK hook and call getMetadata() method instead',
        note: 'This endpoint is a placeholder. Metadata discovery should be done client-side using Zoho SDK.'
      },
      { status: 501 }
    );
  } catch (error) {
    console.error('Error in /api/zoho/metadata:', error);
    
    return NextResponse.json(
      { error: 'Internal server error', details: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}

/**
 * Alternative: Client-side metadata helper
 * This can be used from components that have access to Zoho SDK
 */
export interface MetadataHelper {
  /**
   * Fetch metadata for a module using Zoho SDK
   * This should be called from a client component with Zoho SDK access
   */
  fetchMetadata: (module: string) => Promise<ZohoMetadataResponse>;
}
