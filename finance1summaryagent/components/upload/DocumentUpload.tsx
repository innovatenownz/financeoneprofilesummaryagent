'use client';

import React, { useState, useRef } from 'react';
import { useRecordData } from '@/components/zoho/useRecordData';
import { DocumentList, type UploadedDocument } from './DocumentList';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { cn } from '@/lib/utils/cn';
import type { UploadResponse } from '@/types/api';

export interface DocumentUploadProps {
  className?: string;
  maxFileSize?: number; // Max file size in bytes (default: 10MB)
  acceptedFileTypes?: string[]; // Accepted MIME types
  onUploadSuccess?: (document: UploadedDocument) => void;
  onUploadError?: (error: string) => void;
}

/**
 * Document upload component
 * 
 * Features:
 * - Drag and drop file upload
 * - File type and size validation
 * - Upload progress indication
 * - List of uploaded documents
 * - Integration with FastAPI /upload endpoint
 */
export function DocumentUpload({
  className,
  maxFileSize = 10 * 1024 * 1024, // 10MB default
  acceptedFileTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'image/gif',
  ],
  onUploadSuccess,
  onUploadError,
}: DocumentUploadProps) {
  const { entityId, entityType, hasRecord } = useRecordData();
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize) {
      return `File size exceeds ${Math.round(maxFileSize / 1024 / 1024)}MB limit`;
    }
    
    // Check file type
    if (acceptedFileTypes.length > 0 && !acceptedFileTypes.includes(file.type)) {
      return `File type ${file.type} is not supported`;
    }
    
    return null;
  };
  
  const uploadFile = async (file: File) => {
    if (!entityId || !entityType) {
      const error = 'No record loaded. Please wait for a record to be selected.';
      setUploadError(error);
      onUploadError?.(error);
      return;
    }
    
    const validationError = validateFile(file);
    if (validationError) {
      setUploadError(validationError);
      onUploadError?.(validationError);
      return;
    }
    
    setIsUploading(true);
    setUploadError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('entity_id', entityId);
      formData.append('entity_type', entityType);
      formData.append('file_type', file.type);
      
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle 503 (endpoint not implemented) gracefully
        if (response.status === 503) {
          throw new Error('Upload endpoint is not yet implemented in the backend');
        }
        
        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
      }
      
      const data: UploadResponse = await response.json();
      
      if (!data.success) {
        throw new Error(data.message || 'Upload failed');
      }
      
      // Create document entry
      const document: UploadedDocument = {
        id: `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        size: file.size,
        type: file.type,
        uploadedAt: new Date(),
      };
      
      setDocuments((prev) => [...prev, document]);
      onUploadSuccess?.(document);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload file';
      setUploadError(errorMessage);
      onUploadError?.(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };
  
  const handleFileSelect = (file: File) => {
    uploadFile(file);
  };
  
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    // Reset input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) {
      setIsDragging(true);
    }
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };
  
  const handleRemove = (id: string) => {
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));
  };
  
  const handleClick = () => {
    fileInputRef.current?.click();
  };
  
  if (!hasRecord) {
    return null;
  }
  
  return (
    <div className={cn('w-full', className)}>
      <Card variant="outlined" className="border-primary/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Upload Documents</CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Upload area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleClick}
            className={cn(
              'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
              isDragging
                ? 'border-accent bg-accent/5'
                : 'border-primary/20 hover:border-primary/40 hover:bg-primary/5',
              isUploading && 'pointer-events-none opacity-50'
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileInputChange}
              accept={acceptedFileTypes.join(',')}
              disabled={isUploading}
            />
            
            {isUploading ? (
              <div className="flex flex-col items-center gap-3">
                <LoadingSpinner size="md" />
                <p className="text-sm text-primary/60">Uploading...</p>
              </div>
            ) : (
              <>
                <div className="mb-3">
                  <svg
                    className="w-12 h-12 mx-auto text-primary/40"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                </div>
                <p className="text-sm font-medium text-primary mb-1">
                  Drag and drop a file here, or click to select
                </p>
                <p className="text-xs text-primary/60">
                  Supported: PDF, Word, Excel, Images (max {Math.round(maxFileSize / 1024 / 1024)}MB)
                </p>
              </>
            )}
          </div>
          
          {/* Error message */}
          {uploadError && (
            <div className="bg-alert/5 border border-alert/20 rounded-lg p-3">
              <p className="text-sm text-alert">{uploadError}</p>
              <button
                onClick={() => setUploadError(null)}
                className="mt-2 text-xs text-alert hover:underline"
              >
                Dismiss
              </button>
            </div>
          )}
          
          {/* Uploaded documents list */}
          {documents.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-primary mb-2">
                Uploaded Documents ({documents.length})
              </h4>
              <DocumentList documents={documents} onRemove={handleRemove} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
