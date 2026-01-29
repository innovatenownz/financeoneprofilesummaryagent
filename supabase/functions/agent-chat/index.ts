/**
 * Edge Function: agent-chat
 * Chat endpoint for user queries about a CRM record. Matches FastAPI /chat contract.
 */

import { getAccessToken } from "../_shared/zoho.ts";
import { getAccountData } from "../_shared/zohoCrm.ts";
import { recordToText } from "../_shared/crmToText.ts";
import {
  generateContent,
  parseStructuredResponse,
  CHAT_RESPONSE_JSON_PROMPT,
} from "../_shared/gemini.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

interface ChatBody {
  entity_id?: string;
  account_id?: string;
  entity_type?: string;
  query: string;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ error: "Method not allowed" }),
      { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  try {
    const body = (await req.json()) as ChatBody;
    const entityId = body.entity_id ?? body.account_id;
    if (!entityId) {
      return new Response(
        JSON.stringify({ error: "entity_id or account_id is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    if (!body.query) {
      return new Response(
        JSON.stringify({ error: "query is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    const entityType = body.entity_type ?? "Accounts";
    if (entityType !== "Accounts") {
      return new Response(
        JSON.stringify({ error: `Entity type '${entityType}' not yet supported. Currently only 'Accounts' is supported.` }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const token = await getAccessToken();
    if (!token) {
      return new Response(
        JSON.stringify({ error: "Failed to get Zoho Token" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const record = await getAccountData(entityId, token);
    if (!record) {
      return new Response(
        JSON.stringify({ error: "Account not found in CRM" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const textData = recordToText(record, entityType);
    const context = textData;

    const prompt = CHAT_RESPONSE_JSON_PROMPT
      .replace("{{CONTEXT}}", context)
      .replace("{{QUERY}}", body.query);

    const rawResponse = await generateContent(prompt);
    const parsed = parseStructuredResponse(rawResponse, "chat");

    const response = (parsed.response as string) ?? rawResponse;
    const actions = Array.isArray(parsed.actions) ? parsed.actions : [];

    return new Response(
      JSON.stringify({ response, actions }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (e) {
    console.error("agent-chat error:", e);
    return new Response(
      JSON.stringify({ error: "Error processing chat request", details: String(e) }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
