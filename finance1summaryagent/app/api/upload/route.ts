import { NextRequest, NextResponse } from 'next/server';
import { getFastAPIUrl } from '@/lib/api/client';
import type { UploadResponse } from '@/types/api';

/**
 * POST /api/upload
 * 
 * Proxies file upload requests to the FastAPI backend /upload endpoint
 * 
 * Request (FormData):
 * - file: File (required)
 * - entity_id: string (required)
 * - entity_type: string (required)
 * - file_type?: string (optional)
 * 
 * Response:
 * - success: boolean
 * - message: string
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    
    // Validate required fields
    const file = formData.get('file') as File | null;
    const entityId = formData.get('entity_id') as string | null;
    const entityType = formData.get('entity_type') as string | null;
    
    if (!file) {
      return NextResponse.json(
        { error: 'file is required' },
        { status: 400 }
      );
    }
    
    if (!entityId) {
      return NextResponse.json(
        { error: 'entity_id is required' },
        { status: 400 }
      );
    }
    
    if (!entityType) {
      return NextResponse.json(
        { error: 'entity_type is required' },
        { status: 400 }
      );
    }
    
    // Prepare FormData for FastAPI backend
    const backendFormData = new FormData();
    backendFormData.append('file', file);
    backendFormData.append('entity_id', entityId);
    backendFormData.append('entity_type', entityType);
    
    const fileType = formData.get('file_type') as string | null;
    if (fileType) {
      backendFormData.append('file_type', fileType);
    }
    
    // Get FastAPI URL
    const baseUrl = getFastAPIUrl();
    const url = `${baseUrl}/upload`;
    
    // Proxy to FastAPI backend
    const response = await fetch(url, {
      method: 'POST',
      body: backendFormData,
      // Don't set Content-Type header - let browser set it with boundary
    });
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      
      // If backend returns 404, the endpoint might not be implemented yet
      if (response.status === 404) {
        return NextResponse.json(
          { 
            success: false,
            error: 'Upload endpoint not available', 
            message: 'The /upload endpoint is not yet implemented in the backend'
          },
          { status: 503 }
        );
      }
      
      throw new Error(
        `FastAPI request failed: ${response.status} ${response.statusText}. ${errorText}`
      );
    }
    
    const data: UploadResponse = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in /api/upload:', error);
    
    if (error instanceof Error) {
      // Check if it's a configuration error
      if (error.message.includes('FastAPI URL is not configured')) {
        return NextResponse.json(
          { 
            success: false,
            error: 'Backend configuration error', 
            message: error.message 
          },
          { status: 500 }
        );
      }
      
      // Check if it's a FastAPI request error
      if (error.message.includes('FastAPI request failed')) {
        return NextResponse.json(
          { 
            success: false,
            error: 'Backend request failed', 
            message: error.message 
          },
          { status: 502 }
        );
      }
    }
    
    return NextResponse.json(
      { 
        success: false,
        error: 'Internal server error', 
        message: 'An unexpected error occurred' 
      },
      { status: 500 }
    );
  }
}
