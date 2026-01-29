/**
 * API Validation Schemas
 * 
 * Zod schemas for runtime validation of API requests and responses.
 * These schemas ensure type safety and catch breaking changes early.
 * 
 * When the backend changes, update these schemas to match the new contract.
 * This will cause validation errors that help identify breaking changes.
 */

import { z } from 'zod';

/**
 * Action Type Schema
 */
export const ActionTypeSchema = z.enum([
  'UPDATE_FIELD',
  'CREATE_RECORD',
  'SEND_EMAIL',
  'CUSTOM',
]);

/**
 * Action Schema
 * 
 * Validates action objects returned by the agent
 */
export const ActionSchema = z.object({
  label: z.string().min(1, 'Label is required'),
  type: ActionTypeSchema,
  field: z.string().optional(),
  value: z.any().optional(),
  zohoAction: z.string().optional(),
  module: z.string().optional(),
  recordData: z.record(z.any()).optional(),
  // For SEND_EMAIL
  to: z.union([z.string(), z.array(z.string())]).optional(),
  subject: z.string().optional(),
  body: z.string().optional(),
  templateId: z.string().optional(),
});

/**
 * Chat Request Schema
 * 
 * Validates chat request payloads
 */
export const ChatRequestSchema = z.object({
  entity_id: z.string().optional(),
  account_id: z.string().optional(), // Legacy support
  entity_type: z.string().optional(),
  modules: z.array(z.string()).optional(),
  query: z.string().min(1, 'Query is required'),
}).refine(
  (data) => data.entity_id || data.account_id,
  {
    message: 'At least one of entity_id or account_id is required',
    path: ['entity_id'], // Error will be shown on entity_id field
  }
);

/**
 * Chat Response Schema
 * 
 * Validates chat response from backend
 */
export const ChatResponseSchema = z.object({
  response: z.string(),
  actions: z.array(ActionSchema).optional(),
});

/**
 * Scan Request Schema
 * 
 * Validates scan request payloads
 */
export const ScanRequestSchema = z.object({
  entity_id: z.string().min(1, 'entity_id is required'),
  entity_type: z.string().min(1, 'entity_type is required'),
});

/**
 * Recommendation Type Schema
 */
export const RecommendationTypeSchema = z.enum([
  'alert',
  'suggestion',
  'action',
]);

/**
 * Priority Schema
 */
export const PrioritySchema = z.enum([
  'high',
  'medium',
  'low',
]);

/**
 * Recommendation Schema
 * 
 * Validates recommendation objects from scan endpoint
 */
export const RecommendationSchema = z.object({
  type: RecommendationTypeSchema,
  message: z.string().min(1, 'Message is required'),
  priority: PrioritySchema,
  actions: z.array(ActionSchema).optional(),
});

/**
 * Scan Response Schema
 * 
 * Validates scan response from backend
 */
export const ScanResponseSchema = z.object({
  recommendations: z.array(RecommendationSchema),
});

/**
 * Upload Request Schema
 * 
 * Note: File uploads use FormData, so this schema is for validation
 * of the metadata fields, not the file itself
 */
export const UploadRequestMetadataSchema = z.object({
  entity_id: z.string().min(1, 'entity_id is required'),
  entity_type: z.string().min(1, 'entity_type is required'),
  file_type: z.string().optional(),
});

/**
 * Upload Response Schema
 * 
 * Validates upload response from backend
 */
export const UploadResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
});

/**
 * Zoho Execute Request Schema
 * 
 * Validates Zoho execute request payloads
 */
export const ZohoExecuteRequestSchema = z.object({
  action: ActionSchema,
  entity_id: z.string().optional(),
  entity_type: z.string().optional(),
});

/**
 * Zoho Execute Response Schema
 * 
 * Validates Zoho execute response from backend
 */
export const ZohoExecuteResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: z.any().optional(),
});

/**
 * Zoho Field Metadata Schema
 */
export const ZohoFieldMetadataSchema = z.object({
  api_name: z.string(),
  display_name: z.string(),
  data_type: z.string(),
});

/**
 * Zoho Metadata Response Schema
 * 
 * Validates Zoho metadata response
 */
export const ZohoMetadataResponseSchema = z.object({
  fields: z.array(ZohoFieldMetadataSchema),
  module: z.string(),
});

/**
 * Error Response Schema
 * 
 * Standard error response format
 */
export const ErrorResponseSchema = z.object({
  error: z.string(),
  details: z.string().optional(),
  status: z.number().optional(),
});

/**
 * Validation Utilities
 */

/**
 * Validate and parse a request body
 * 
 * @param schema - Zod schema to validate against
 * @param data - Data to validate
 * @returns Parsed and validated data
 * @throws {z.ZodError} If validation fails
 */
export function validateRequest<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): T {
  return schema.parse(data);
}

/**
 * Safe validate - returns result instead of throwing
 * 
 * @param schema - Zod schema to validate against
 * @param data - Data to validate
 * @returns Validation result with success flag
 */
export function safeValidate<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: z.ZodError } {
  const result = schema.safeParse(data);
  
  if (result.success) {
    return { success: true, data: result.data };
  }
  
  return { success: false, error: result.error };
}

/**
 * Validate response with graceful error handling
 * 
 * If validation fails, logs the error and returns the original data
 * with a warning. This allows the app to continue functioning even
 * if the backend returns unexpected data (backward compatibility).
 * 
 * @param schema - Zod schema to validate against
 * @param data - Data to validate
 * @param endpoint - Endpoint name for error logging
 * @returns Result object with validated data and validation status
 */
export function validateResponse<T>(
  schema: z.ZodSchema<T>,
  data: unknown,
  endpoint: string
): { data: T; isValid: true } | { data: unknown; isValid: false; error: z.ZodError } {
  const result = schema.safeParse(data);
  
  if (result.success) {
    return { data: result.data, isValid: true };
  }
  
  // Log validation error but don't throw
  // This allows graceful degradation if backend changes
  console.warn(
    `[API Validation] Response validation failed for ${endpoint}:`,
    result.error.format()
  );
  
  // Return original data with validation status
  // Components should check isValid and handle missing fields gracefully
  return { data, isValid: false, error: result.error };
}

/**
 * Type exports for use in TypeScript
 */
export type Action = z.infer<typeof ActionSchema>;
export type ChatRequest = z.infer<typeof ChatRequestSchema>;
export type ChatResponse = z.infer<typeof ChatResponseSchema>;
export type ScanRequest = z.infer<typeof ScanRequestSchema>;
export type Recommendation = z.infer<typeof RecommendationSchema>;
export type ScanResponse = z.infer<typeof ScanResponseSchema>;
export type UploadRequestMetadata = z.infer<typeof UploadRequestMetadataSchema>;
export type UploadResponse = z.infer<typeof UploadResponseSchema>;
export type ZohoExecuteRequest = z.infer<typeof ZohoExecuteRequestSchema>;
export type ZohoExecuteResponse = z.infer<typeof ZohoExecuteResponseSchema>;
export type ZohoFieldMetadata = z.infer<typeof ZohoFieldMetadataSchema>;
export type ZohoMetadataResponse = z.infer<typeof ZohoMetadataResponseSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
