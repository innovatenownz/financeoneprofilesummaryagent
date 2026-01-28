/**
 * Zoho SDK type definitions
 * These types extend the global ZOHO interface from the Zoho Embedded App SDK
 */

/**
 * Global Zoho SDK interface
 * This represents the ZOHO object loaded from https://live.zwidgets.com.au/js-sdk/1.1/ZohoEmbededAppSDK.min.js
 * Per Zoho documentation: https://www.zoho.com/crm/developer/docs/widgets/create-widget.html
 */
export interface ZohoSDK {
  embeddedApp: {
    /**
     * Initialize the widget and start listening to CRM events
     * Per Zoho documentation: ZOHO.embeddedApp.init()
     */
    init(): void;

    /**
     * Listen for Zoho CRM events
     * Per Zoho documentation: ZOHO.embeddedApp.on("PageLoad", function(data){ ... })
     * @param event - Event type (e.g., "PageLoad", "RecordUpdate")
     * @param handler - Event handler function
     */
    on(event: string, handler: (data: any) => void): void;

    /**
     * Remove event listener
     * @param event - Event type
     * @param handler - Event handler function
     */
    off(event: string, handler: (data: any) => void): void;

    /**
     * Execute Zoho CRM actions
     * @param action - Action name (e.g., "UPDATE_FIELD", "CREATE_RECORD")
     * @param params - Action parameters
     * @returns Promise that resolves with the result
     */
    execute(action: string, params?: any): Promise<any>;

    /**
     * Get current record data
     * @returns Promise that resolves with the current record data
     */
    getRecordData(): Promise<any>;

    /**
     * Get metadata for the current module
     * @returns Promise that resolves with module metadata
     */
    getMetadata(): Promise<any>;
  };
}

/**
 * Global window interface extension for ZOHO
 * Per Zoho documentation, the SDK exposes ZOHO as the global object
 */
declare global {
  interface Window {
    ZOHO?: ZohoSDK;
  }
}

/**
 * Zoho SDK configuration
 */
export interface ZohoSDKConfig {
  clientId?: string;
  environment?: 'development' | 'production';
  onReady?: () => void;
  onError?: (error: Error) => void;
}
