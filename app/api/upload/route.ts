import { NextRequest, NextResponse } from 'next/server';
import { fetchSupabaseFunctionFormData, ApiClientError } from '@/lib/api/client';
import type { UploadResponse } from '@/types/api';

/**
 * POST /api/upload
 *
 * Proxies file uploads to the Supabase Edge Function upload (Storage bucket).
 *
 * Request (FormData): file, entity_id, entity_type, file_type?
 * Response: success, message, entity_id, entity_type, filename
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;
    const entityId = formData.get('entity_id') as string | null;
    const entityType = formData.get('entity_type') as string | null;

    if (!file) {
      return NextResponse.json({ error: 'file is required' }, { status: 400 });
    }
    if (!entityId) {
      return NextResponse.json({ error: 'entity_id is required' }, { status: 400 });
    }
    if (!entityType) {
      return NextResponse.json({ error: 'entity_type is required' }, { status: 400 });
    }

    const backendFormData = new FormData();
    backendFormData.append('file', file);
    backendFormData.append('entity_id', entityId);
    backendFormData.append('entity_type', entityType);
    const fileType = formData.get('file_type') as string | null;
    if (fileType) backendFormData.append('file_type', fileType);

    const response = await fetchSupabaseFunctionFormData('upload', backendFormData);

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      if (response.status === 404) {
        return NextResponse.json(
          { success: false, error: 'Upload endpoint not available', message: 'Upload not implemented.' },
          { status: 503 }
        );
      }
      throw new Error(`Upload failed: ${response.status} ${response.statusText}. ${errorText}`);
    }

    const data: UploadResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in /api/upload:', error);
    if (error instanceof ApiClientError) {
      return NextResponse.json(
        { success: false, error: error.message, message: error.details ?? error.message },
        { status: error.status ?? 502 }
      );
    }
    if (error instanceof Error) {
      if (error.message.includes('Supabase URL is not configured')) {
        return NextResponse.json(
          { success: false, error: 'Backend configuration error', message: error.message },
          { status: 500 }
        );
      }
      if (error.message.includes('Upload failed')) {
        return NextResponse.json(
          { success: false, error: 'Backend request failed', message: error.message },
          { status: 502 }
        );
      }
    }
    return NextResponse.json(
      { success: false, error: 'Internal server error', message: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
