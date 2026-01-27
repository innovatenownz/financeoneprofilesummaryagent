/**
 * Zoho-related TypeScript types
 * These types represent the structure of Zoho CRM data and SDK interactions
 */

/**
 * Zoho CRM record - dynamic structure based on module
 */
export interface ZohoRecord {
  [key: string]: any;
  id?: string;
}

/**
 * Zoho PageLoad event data structure
 * This is what we receive from ZSDK.embeddedApp.on("PageLoad")
 */
export interface ZohoPageLoadData {
  EntityId: string;
  Entity: string; // Module name: "Accounts", "Deals", "Contacts", etc.
  recordData?: ZohoRecord;
}

/**
 * Zoho SDK initialization state
 */
export type ZohoSDKState = 
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; sdk: ZohoSDK }
  | { status: 'error'; error: Error };

/**
 * Current record context
 */
export interface RecordContext {
  entityId: string | null;
  entityType: string | null;
  recordData: ZohoRecord | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Zoho SDK action types for executing operations
 */
export type ZohoActionType = 
  | 'UPDATE_FIELD'
  | 'CREATE_RECORD'
  | 'SEND_EMAIL'
  | 'CUSTOM';

/**
 * Action structure for actionable UI
 */
export interface ZohoAction {
  label: string;
  type: ZohoActionType;
  field?: string; // For UPDATE_FIELD
  value?: any; // For UPDATE_FIELD
  zohoAction?: string; // ZSDK action name
  module?: string; // Target module for CREATE_RECORD
  recordData?: ZohoRecord; // Record data for CREATE_RECORD
  // For SEND_EMAIL
  to?: string | string[]; // Email recipient(s)
  subject?: string; // Email subject
  body?: string; // Email body
  templateId?: string; // Email template ID (optional)
}

/**
 * Zoho SDK event types
 */
export type ZohoEventType = 
  | 'PageLoad'
  | 'RecordCreate'
  | 'RecordUpdate'
  | 'RecordDelete'
  | 'FieldChange';

/**
 * Zoho SDK event handler
 */
export type ZohoEventHandler = (data: any) => void;
