/**
 * Edge Function: agent-scan
 * Proactive scan endpoint. Matches FastAPI /scan contract.
 */

import { getAccessToken } from "../_shared/zoho.ts";
import { getAccountData } from "../_shared/zohoCrm.ts";
import { recordToText } from "../_shared/crmToText.ts";
import {
  generateContent,
  parseStructuredResponse,
  SCAN_RESPONSE_JSON_PROMPT,
} from "../_shared/gemini.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

interface ScanBody {
  entity_id: string;
  entity_type: string;
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
    const body = (await req.json()) as ScanBody;
    if (!body.entity_id) {
      return new Response(
        JSON.stringify({ error: "entity_id is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    if (!body.entity_type) {
      return new Response(
        JSON.stringify({ error: "entity_type is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    const entityType = body.entity_type;
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

    const record = await getAccountData(body.entity_id, token);
    if (!record) {
      return new Response(
        JSON.stringify({ error: "Account not found in CRM" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const textData = recordToText(record, entityType);
    const prompt = SCAN_RESPONSE_JSON_PROMPT.replace("{{CONTEXT}}", textData);

    const rawResponse = await generateContent(prompt);
    const parsed = parseStructuredResponse(rawResponse, "scan");

    let recommendations = Array.isArray(parsed.recommendations) ? parsed.recommendations : [];
    if (recommendations.length === 0) {
      recommendations = [
        {
          type: "suggestion",
          message: "No specific recommendations at this time. Account data looks complete.",
          priority: "low",
          actions: [],
        },
      ];
    }

    return new Response(
      JSON.stringify({ recommendations }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (e) {
    console.error("agent-scan error:", e);
    return new Response(
      JSON.stringify({ error: "Error processing scan request", details: String(e) }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
