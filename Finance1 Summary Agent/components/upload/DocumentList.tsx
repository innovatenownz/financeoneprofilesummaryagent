'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { cn } from '@/lib/utils/cn';

export interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
}

export interface DocumentListProps {
  documents: UploadedDocument[];
  onRemove?: (id: string) => void;
  className?: string;
}

/**
 * Document list component for displaying uploaded documents
 * 
 * Shows list of uploaded documents with metadata
 * Supports removal if onRemove callback is provided
 */
export function DocumentList({ documents, onRemove, className }: DocumentListProps) {
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };
  
  const getFileIcon = (type: string): string => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
    if (type.includes('image')) return '🖼️';
    return '📎';
  };
  
  if (documents.length === 0) {
    return null;
  }
  
  return (
    <div className={cn('space-y-2', className)}>
      {documents.map((doc) => (
        <Card key={doc.id} variant="outlined" className="border-primary/10">
          <CardContent className="p-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="text-xl shrink-0">{getFileIcon(doc.type)}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-primary truncate">
                    {doc.name}
                  </p>
                  <p className="text-xs text-primary/60">
                    {formatFileSize(doc.size)} • {doc.uploadedAt.toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              {onRemove && (
                <button
                  onClick={() => onRemove(doc.id)}
                  className="shrink-0 text-primary/60 hover:text-alert transition-colors p-1"
                  title="Remove document"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
