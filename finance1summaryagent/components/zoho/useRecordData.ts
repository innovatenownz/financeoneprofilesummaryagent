'use client';

import { useMemo, useEffect, useState } from 'react';
import { useZohoContext } from './ZohoProvider';
import type { ZohoRecord } from '@/lib/zoho/types';
import { getFieldValue } from '@/lib/zoho/utils';

/**
 * Hook for managing and accessing current Zoho record data
 * 
 * Provides:
 * - Current record data
 * - Entity ID and type
 * - Loading and error states
 * - Helper methods to access field values
 * - Refresh functionality
 */
export function useRecordData() {
  const { recordContext, refreshRecord } = useZohoContext();
  const [localRecordData, setLocalRecordData] = useState<ZohoRecord | null>(
    recordContext.recordData
  );

  // Sync local state with context
  useEffect(() => {
    setLocalRecordData(recordContext.recordData);
  }, [recordContext.recordData]);

  /**
   * Get field value from current record
   */
  const getField = useMemo(
    () => (fieldName: string) => {
      return getFieldValue(localRecordData, fieldName);
    },
    [localRecordData]
  );

  /**
   * Check if record is loaded
   */
  const hasRecord = useMemo(() => {
    return recordContext.entityId !== null && recordContext.entityType !== null;
  }, [recordContext.entityId, recordContext.entityType]);

  /**
   * Check if record data is available
   */
  const hasRecordData = useMemo(() => {
    return localRecordData !== null && Object.keys(localRecordData).length > 0;
  }, [localRecordData]);

  /**
   * Update local record data (optimistic update)
   */
  const updateLocalRecord = (updates: Partial<ZohoRecord>) => {
    if (!localRecordData) return;
    setLocalRecordData({ ...localRecordData, ...updates });
  };

  /**
   * Refresh record data from Zoho
   */
  const refresh = async () => {
    await refreshRecord();
  };

  return {
    // Record identifiers
    entityId: recordContext.entityId,
    entityType: recordContext.entityType,
    
    // Record data
    recordData: localRecordData,
    hasRecord,
    hasRecordData,
    
    // State
    isLoading: recordContext.isLoading,
    error: recordContext.error,
    
    // Methods
    getField,
    updateLocalRecord,
    refresh,
  };
}
