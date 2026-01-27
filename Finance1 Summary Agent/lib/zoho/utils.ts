/**
 * Zoho helper functions
 */

import type { ZohoRecord, ZohoPageLoadData, ZohoAction } from './types';
import type { ZohoSDK } from './sdk';

/**
 * Check if Zoho SDK is available in the global scope
 * Per Zoho documentation, the SDK exposes ZOHO as the global object
 */
export function isZohoSDKAvailable(): boolean {
  return typeof window !== 'undefined' && typeof window.ZOHO !== 'undefined';
}

/**
 * Get the Zoho SDK instance from global scope
 * Per Zoho documentation, the SDK exposes ZOHO as the global object
 */
export function getZohoSDK(): ZohoSDK | null {
  if (!isZohoSDKAvailable()) {
    return null;
  }
  return window.ZOHO!;
}

/**
 * Wait for Zoho SDK to be loaded
 * @param timeout - Maximum time to wait in milliseconds (default: 10000)
 * @returns Promise that resolves when SDK is available
 */
export function waitForZohoSDK(timeout: number = 10000): Promise<ZohoSDK> {
  return new Promise((resolve, reject) => {
    if (isZohoSDKAvailable()) {
      resolve(window.ZOHO!);
      return;
    }

    const startTime = Date.now();
    const checkInterval = setInterval(() => {
      if (isZohoSDKAvailable()) {
        clearInterval(checkInterval);
        resolve(window.ZOHO!);
      } else if (Date.now() - startTime > timeout) {
        clearInterval(checkInterval);
        reject(new Error('Zoho SDK failed to load within timeout period'));
      }
    }, 100);
  });
}

/**
 * Load Zoho SDK script dynamically
 * @param onLoad - Callback when script is loaded
 * @param onError - Callback when script fails to load
 */
export function loadZohoSDK(
  onLoad?: () => void,
  onError?: (error: Error) => void
): void {
  if (typeof window === 'undefined') {
    onError?.(new Error('Window object is not available'));
    return;
  }

  // Check if already loaded
  if (isZohoSDKAvailable()) {
    onLoad?.();
    return;
  }

  // Check if script is already being loaded
  const existingScript = document.querySelector(
    'script[src*="ZohoEmbededAppSDK"]'
  ) as HTMLScriptElement | null;
  
  if (existingScript) {
    // Check if script has already finished loading (race condition fix)
    // readyState can be: 'loading', 'interactive', 'complete', or '' (for non-IE browsers)
    const isScriptLoaded = existingScript.readyState === 'complete' || 
                          existingScript.readyState === 'loaded' ||
                          (!existingScript.readyState && existingScript.complete);
    
    if (isScriptLoaded) {
      // Script already loaded, check if SDK is available
      // Use a small delay to allow SDK to initialize if it just finished loading
      setTimeout(() => {
        if (isZohoSDKAvailable()) {
          onLoad?.();
        } else {
          // Script loaded but SDK not ready yet, poll for it
          let checkInterval: ReturnType<typeof setInterval> | null = null;
          
          // Set timeout FIRST so it can be properly cleared
          const timeoutId = setTimeout(() => {
            if (checkInterval) {
              clearInterval(checkInterval);
            }
            onError?.(new Error('Zoho SDK script loaded but SDK not available'));
          }, 5000);
          
          // Start polling for SDK availability
          checkInterval = setInterval(() => {
            if (isZohoSDKAvailable()) {
              clearInterval(checkInterval!);
              clearTimeout(timeoutId); // Clear timeout when SDK loads successfully
              onLoad?.();
            }
          }, 50);
        }
      }, 100);
      return;
    }
    
    // Script is still loading, add event listeners with once: true to prevent duplicates
    const loadHandler = () => {
      // Give SDK a moment to initialize
      setTimeout(() => {
        if (isZohoSDKAvailable()) {
          onLoad?.();
        } else {
          onError?.(new Error('Zoho SDK script loaded but SDK not available'));
        }
      }, 100);
    };
    
    const errorHandler = () => {
      onError?.(new Error('Failed to load Zoho SDK script'));
    };
    
    // Use once: true to automatically remove listeners after first invocation
    existingScript.addEventListener('load', loadHandler, { once: true });
    existingScript.addEventListener('error', errorHandler, { once: true });
    return;
  }

  // Create and load script
  const script = document.createElement('script');
  script.src = 'https://live.zwidgets.com.au/js-sdk/1.1/ZohoEmbededAppSDK.min.js';
  script.async = true;
  script.onload = () => {
    // Give SDK a moment to initialize
    setTimeout(() => {
      if (isZohoSDKAvailable()) {
        onLoad?.();
      } else {
        onError?.(new Error('Zoho SDK script loaded but SDK not available'));
      }
    }, 100);
  };
  script.onerror = () => {
    onError?.(new Error('Failed to load Zoho SDK script'));
  };
  document.head.appendChild(script);
}

/**
 * Normalize entity type name (e.g., "Accounts" -> "Accounts")
 * Handles variations in naming
 */
export function normalizeEntityType(entityType: string): string {
  // Capitalize first letter and ensure proper casing
  return entityType.charAt(0).toUpperCase() + entityType.slice(1);
}

/**
 * Extract field value from Zoho record
 * @param record - Zoho record object
 * @param fieldName - Field API name
 * @returns Field value or null
 */
export function getFieldValue(
  record: ZohoRecord | null,
  fieldName: string
): any {
  if (!record) return null;
  return record[fieldName] ?? null;
}

/**
 * Format Zoho record for display
 * @param record - Zoho record object
 * @returns Formatted string representation
 */
export function formatRecordForDisplay(record: ZohoRecord | null): string {
  if (!record) return 'No record data';
  
  const entries = Object.entries(record)
    .filter(([key]) => !key.startsWith('$'))
    .map(([key, value]) => `${key}: ${value}`)
    .join(', ');
  
  return entries || 'Empty record';
}

/**
 * Execute a Zoho action using the SDK
 * @param sdk - Zoho SDK instance
 * @param action - Action to execute
 * @returns Promise that resolves with the result
 */
export async function executeZohoAction(
  sdk: ZohoSDK,
  action: ZohoAction
): Promise<any> {
  switch (action.type) {
    case 'UPDATE_FIELD':
      if (!action.field || action.value === undefined) {
        throw new Error('UPDATE_FIELD requires field and value');
      }
      return sdk.embeddedApp.execute('UPDATE_FIELD', {
        field: action.field,
        value: action.value,
      });

    case 'CREATE_RECORD':
      if (!action.module || !action.recordData) {
        throw new Error('CREATE_RECORD requires module and recordData');
      }
      return sdk.embeddedApp.execute('CREATE_RECORD', {
        module: action.module,
        recordData: action.recordData,
      });

    case 'SEND_EMAIL':
      if (!action.to) {
        throw new Error('SEND_EMAIL requires to (recipient email)');
      }
      return sdk.embeddedApp.execute('SEND_EMAIL', {
        to: action.to,
        subject: action.subject || '',
        body: action.body || '',
        templateId: action.templateId,
      });

    case 'CUSTOM':
      if (!action.zohoAction) {
        throw new Error('CUSTOM action requires zohoAction');
      }
      return sdk.embeddedApp.execute(action.zohoAction, action);

    default:
      throw new Error(`Unsupported action type: ${action.type}`);
  }
}

/**
 * Validate Zoho PageLoad data
 */
export function validatePageLoadData(data: any): data is ZohoPageLoadData {
  return (
    data &&
    typeof data === 'object' &&
    typeof data.EntityId === 'string' &&
    typeof data.Entity === 'string'
  );
}
