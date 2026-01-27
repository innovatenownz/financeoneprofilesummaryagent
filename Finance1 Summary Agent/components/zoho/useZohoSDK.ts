'use client';

import { useMemo } from 'react';
import { useZohoContext } from './ZohoProvider';
import type { ZohoSDK } from '@/lib/zoho/sdk';
import type { ZohoAction } from '@/lib/zoho/types';
import { executeZohoAction } from '@/lib/zoho/utils';

/**
 * Hook for accessing Zoho SDK functionality
 * 
 * Provides:
 * - Direct access to Zoho SDK instance
 * - Helper methods for common SDK operations
 * - SDK state information
 */
export function useZohoSDK() {
  const { sdk, sdkState, executeAction } = useZohoContext();

  /**
   * Check if SDK is ready
   */
  const isReady = useMemo(() => {
    return sdkState.status === 'ready' && sdk !== null;
  }, [sdkState.status, sdk]);

  /**
   * Check if SDK is loading
   */
  const isLoading = useMemo(() => {
    return sdkState.status === 'loading';
  }, [sdkState.status]);

  /**
   * Check if there's an error
   */
  const error = useMemo(() => {
    return sdkState.status === 'error' ? sdkState.error : null;
  }, [sdkState]);

  /**
   * Execute a Zoho action using the action structure
   */
  const executeZohoActionWrapper = async (action: ZohoAction): Promise<any> => {
    if (!sdk) {
      throw new Error('Zoho SDK is not available');
    }
    return executeZohoAction(sdk, action);
  };

  /**
   * Get current record data
   */
  const getRecordData = async (): Promise<any> => {
    if (!sdk) {
      throw new Error('Zoho SDK is not available');
    }
    return sdk.embeddedApp.getRecordData();
  };

  /**
   * Get metadata for the current module
   */
  const getMetadata = async (): Promise<any> => {
    if (!sdk) {
      throw new Error('Zoho SDK is not available');
    }
    return sdk.embeddedApp.getMetadata();
  };

  /**
   * Listen for Zoho events
   */
  const on = (event: string, handler: (data: any) => void): void => {
    if (!sdk) {
      throw new Error('Zoho SDK is not available');
    }
    sdk.embeddedApp.on(event, handler);
  };

  /**
   * Remove event listener
   */
  const off = (event: string, handler: (data: any) => void): void => {
    if (!sdk) {
      throw new Error('Zoho SDK is not available');
    }
    sdk.embeddedApp.off(event, handler);
  };

  return {
    // SDK instance
    sdk: sdk as ZohoSDK | null,
    
    // State
    isReady,
    isLoading,
    error,
    
    // Methods
    executeAction,
    executeZohoAction: executeZohoActionWrapper,
    getRecordData,
    getMetadata,
    on,
    off,
  };
}
