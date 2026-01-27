/**
 * API request and response types matching FastAPI backend
 */

// Current /chat endpoint
/**
 * Chat request type. At least one of `entity_id` or `account_id` must be provided.
 * The handler will use `entity_id` if present, otherwise fall back to `account_id`.
 */
export interface ChatRequest {
  /** Modern entity identifier. At least one of entity_id or account_id is required. */
  entity_id?: string;
  /** Legacy account identifier. At least one of entity_id or account_id is required. */
  account_id?: string;
  /** Optional entity type, defaults to "Accounts" */
  entity_type?: string;
  /** User query string */
  query: string;
}

export interface ChatResponse {
  response: string;
  actions?: Action[];
}

// New /scan endpoint
export interface ScanRequest {
  entity_id: string;
  entity_type: string; // "Accounts", "Deals", "Contacts", etc.
}

export interface Recommendation {
  type: "alert" | "suggestion" | "action";
  message: string;
  priority: "high" | "medium" | "low";
  actions?: Action[];
}

export interface ScanResponse {
  recommendations: Recommendation[];
}

// Action structure for actionable UI
export interface Action {
  label: string;
  type: "UPDATE_FIELD" | "CREATE_RECORD" | "SEND_EMAIL" | "CUSTOM";
  field?: string; // For UPDATE_FIELD
  value?: any; // For UPDATE_FIELD
  zohoAction?: string; // ZSDK action name
  module?: string; // Target module for CREATE_RECORD
  recordData?: Record<string, any>; // Record data for CREATE_RECORD
  // For SEND_EMAIL
  to?: string | string[];
  subject?: string;
  body?: string;
  templateId?: string;
}

// Upload endpoint
export interface UploadRequest {
  entity_id: string;
  entity_type: string;
  file: File;
  file_type?: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
}

// Zoho execute endpoint
export interface ZohoExecuteRequest {
  action: Action;
  entity_id?: string;
  entity_type?: string;
}

export interface ZohoExecuteResponse {
  success: boolean;
  message: string;
  data?: any;
}

// Zoho metadata endpoint
export interface ZohoMetadataResponse {
  fields: Array<{
    api_name: string;
    display_name: string;
    data_type: string;
  }>;
  module: string;
}
