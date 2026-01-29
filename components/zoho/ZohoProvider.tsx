'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import type { ReactNode } from 'react';
import type { ZohoSDKState, ZohoPageLoadData, RecordContext } from '@/lib/zoho/types';
import type { ZohoSDK, ZohoSDKConfig } from '@/lib/zoho/sdk';
import { loadZohoSDK, waitForZohoSDK, getZohoSDK, isZohoSDKAvailable, validatePageLoadData } from '@/lib/zoho/utils';

/**
 * Zoho SDK Context
 */
interface ZohoContextValue {
  sdkState: ZohoSDKState;
  recordContext: RecordContext;
  sdk: ZohoSDK | null;
  refreshRecord: () => Promise<void>;
  executeAction: (action: string, params?: any) => Promise<any>;
}

const ZohoContext = createContext<ZohoContextValue | undefined>(undefined);

/**
 * ZohoProvider Props
 */
interface ZohoProviderProps {
  children: ReactNode;
  config?: ZohoSDKConfig;
}

/**
 * Zoho SDK Provider Component
 * 
 * This component:
 * - Loads and initializes the Zoho SDK
 * - Listens for PageLoad events to capture record context
 * - Provides SDK access and record data to child components
 */
export function ZohoProvider({ children, config }: ZohoProviderProps) {
  const [sdkState, setSdkState] = useState<ZohoSDKState>({ status: 'idle' });
  const [recordContext, setRecordContext] = useState<RecordContext>({
    entityId: null,
    entityType: null,
    recordData: null,
    isLoading: false,
    error: null,
  });

  // Track if SDK has been initialized to prevent multiple init() calls
  const isInitializedRef = useRef(false);
  
  // Use refs for callbacks to avoid stale closures and unnecessary re-initializations
  const onReadyRef = useRef(config?.onReady);
  const onErrorRef = useRef(config?.onError);
  
  // Update refs when config changes
  useEffect(() => {
    onReadyRef.current = config?.onReady;
    onErrorRef.current = config?.onError;
  }, [config?.onReady, config?.onError]);

  // Handle PageLoad event
  const handlePageLoad = useCallback(async (data: any) => {
    if (!validatePageLoadData(data)) {
      console.warn('Invalid PageLoad data:', data);
      return;
    }

    const pageLoadData = data as ZohoPageLoadData;

    setRecordContext((prev) => ({
      ...prev,
      entityId: pageLoadData.EntityId,
      entityType: pageLoadData.Entity,
      isLoading: true,
      error: null,
    }));

    try {
      // Fetch full record data if not provided - use ZOHO.CRM.API.getRecord (PageLoad only gives EntityId + Entity)
      let recordData = pageLoadData.recordData;

      if (!recordData) {
        const sdk = getZohoSDK();
        if (sdk?.CRM?.API?.getRecord) {
          try {
            const res = await sdk.CRM.API.getRecord({
              Entity: pageLoadData.Entity,
              RecordID: String(pageLoadData.EntityId),
            });
            recordData = res?.data?.[0] ?? null;
          } catch (error) {
            console.warn('Failed to fetch record data:', error);
          }
        }
      }

      setRecordContext({
        entityId: pageLoadData.EntityId,
        entityType: pageLoadData.Entity,
        recordData: recordData || null,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to load record data');
      setRecordContext((prev) => ({
        ...prev,
        isLoading: false,
        error: err,
      }));
    }
  }, []);

  // Initialize SDK - only run once on mount or when clientId changes
  useEffect(() => {
    let mounted = true;

    const initializeSDK = async () => {
      setSdkState({ status: 'loading' });

      try {
        // Load SDK script if not already loaded
        await new Promise<void>((resolve, reject) => {
          loadZohoSDK(
            () => {
              if (mounted) resolve();
            },
            (error) => {
              if (mounted) reject(error);
            }
          );
        });

        // Wait for SDK to be available
        const sdk = await waitForZohoSDK(10000);

        if (!mounted) return;

        setSdkState({ status: 'ready', sdk });

        // Initialize embeddedApp only once (required per Zoho documentation)
        // Per docs: ZOHO.embeddedApp.init() - initializes widget and starts listening to events
        if (!isInitializedRef.current) {
          sdk.embeddedApp.init();
          isInitializedRef.current = true;
        }

        // Set up PageLoad listener (per Zoho documentation: ZOHO.embeddedApp.on("PageLoad", ...))
        sdk.embeddedApp.on('PageLoad', handlePageLoad);

        // Call onReady callback if provided (use ref to get latest callback)
        onReadyRef.current?.();
      } catch (error) {
        if (!mounted) return;
        const err = error instanceof Error ? error : new Error('Failed to initialize Zoho SDK');
        setSdkState({ status: 'error', error: err });
        // Use ref to get latest callback
        onErrorRef.current?.(err);
      }
    };

    initializeSDK();

    return () => {
      mounted = false;
      // Clean up event listeners
      const sdk = getZohoSDK();
      if (sdk && sdk.embeddedApp) {
        sdk.embeddedApp.off('PageLoad', handlePageLoad);
      }
    };
  }, [config?.clientId, handlePageLoad]);

  // Refresh current record data via ZOHO.CRM.API.getRecord
  const refreshRecord = useCallback(async () => {
    const sdk = getZohoSDK();
    if (!sdk) {
      throw new Error('Zoho SDK is not available');
    }
    if (!recordContext.entityId || !recordContext.entityType) {
      throw new Error('No record context');
    }
    if (!sdk.CRM?.API?.getRecord) {
      throw new Error('ZOHO.CRM.API.getRecord is not available');
    }

    setRecordContext((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const res = await sdk.CRM.API.getRecord({
        Entity: recordContext.entityType,
        RecordID: String(recordContext.entityId),
      });
      const recordData = res?.data?.[0] ?? null;
      setRecordContext((prev) => ({
        ...prev,
        recordData,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to refresh record');
      setRecordContext((prev) => ({
        ...prev,
        isLoading: false,
        error: err,
      }));
      throw err;
    }
  }, [recordContext.entityId, recordContext.entityType]);

  // Execute Zoho SDK action
  const executeAction = useCallback(async (action: string, params?: any) => {
    const sdk = getZohoSDK();
    if (!sdk) {
      throw new Error('Zoho SDK is not available');
    }

    return sdk.embeddedApp.execute(action, params);
  }, []);

  const value: ZohoContextValue = {
    sdkState,
    recordContext,
    sdk: sdkState.status === 'ready' ? sdkState.sdk : null,
    refreshRecord,
    executeAction,
  };

  return <ZohoContext.Provider value={value}>{children}</ZohoContext.Provider>;
}

/**
 * Hook to access Zoho context
 * @throws Error if used outside ZohoProvider
 */
export function useZohoContext(): ZohoContextValue {
  const context = useContext(ZohoContext);
  if (context === undefined) {
    throw new Error('useZohoContext must be used within a ZohoProvider');
  }
  return context;
}
