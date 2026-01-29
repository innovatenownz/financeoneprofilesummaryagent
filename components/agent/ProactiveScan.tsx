'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRecordData } from '@/components/zoho/useRecordData';
import { RecommendationCard } from './RecommendationCard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils/cn';
import type { ScanRequest, ScanResponse, Recommendation } from '@/types/api';

export interface ProactiveScanProps {
  className?: string;
  autoScan?: boolean; // Whether to automatically scan on record load
}

/**
 * Proactive scan component that displays recommendations on record load
 * 
 * Features:
 * - Automatically scans record when loaded
 * - Displays recommendations with priority and type
 * - Shows loading state during scan
 * - Handles errors gracefully
 * - Can be manually refreshed
 */
export function ProactiveScan({ className, autoScan = true }: ProactiveScanProps) {
  const { entityId, entityType, hasRecord } = useRecordData();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasScanned, setHasScanned] = useState(false);
  
  const performScan = useCallback(async () => {
    if (!entityId || !entityType) {
      setError('No record loaded');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const request: ScanRequest = {
        entity_id: entityId,
        entity_type: entityType,
      };
      
      const response = await fetch('/api/agent/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle 503 (endpoint not implemented) gracefully
        if (response.status === 503) {
          setRecommendations([]);
          setError(null); // Don't show error for unimplemented endpoint
          setHasScanned(true);
          return;
        }
        
        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
      }
      
      const data: ScanResponse = await response.json();
      setRecommendations(data.recommendations || []);
      setHasScanned(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to scan record';
      setError(errorMessage);
      setRecommendations([]);
    } finally {
      setIsLoading(false);
    }
  }, [entityId, entityType]);
  
  // Auto-scan when record loads
  useEffect(() => {
    if (autoScan && hasRecord && entityId && entityType && !hasScanned) {
      performScan();
    }
  }, [autoScan, hasRecord, entityId, entityType, hasScanned, performScan]);
  
  // Reset when record changes
  useEffect(() => {
    if (entityId) {
      setRecommendations([]);
      setError(null);
      setHasScanned(false);
    }
  }, [entityId]);
  
  if (!hasRecord) {
    return null;
  }
  
  return (
    <div className={cn('w-full', className)}>
      <Card variant="outlined" className="border-primary/10">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Recommendations</CardTitle>
            {hasScanned && !isLoading && (
              <button
                onClick={performScan}
                className="text-xs text-primary/70 hover:text-primary transition-colors"
              >
                Refresh
              </button>
            )}
          </div>
        </CardHeader>
        
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="flex flex-col items-center gap-3">
                <LoadingSpinner size="md" />
                <p className="text-sm text-primary/60">Analyzing record...</p>
              </div>
            </div>
          ) : error ? (
            <div className="py-4">
              <div className="bg-alert/5 border border-alert/20 rounded-lg p-3">
                <p className="text-sm text-alert">{error}</p>
                <button
                  onClick={performScan}
                  className="mt-2 text-xs text-alert hover:underline"
                >
                  Try again
                </button>
              </div>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="py-4 text-center">
              <p className="text-sm text-primary/60">
                {hasScanned
                  ? 'No recommendations at this time.'
                  : 'Click refresh to scan this record.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {recommendations.map((recommendation, index) => (
                <RecommendationCard
                  key={index}
                  recommendation={recommendation}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
