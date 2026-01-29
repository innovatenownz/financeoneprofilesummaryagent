/**
 * Edge Function: agent-chat
 * Chat endpoint for user queries about a CRM record. Matches FastAPI /chat contract.
 */

import { getAccessToken } from "../_shared/zoho.ts";
import { getRecordData, getRelatedRecords } from "../_shared/zohoCrm.ts";
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
  modules?: string[];
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
    const selectedModules = Array.isArray(body.modules) ? body.modules.filter(Boolean) : [];
    if (!selectedModules.includes(entityType)) {
      selectedModules.unshift(entityType);
    }
    const uniqueModules = Array.from(new Set(selectedModules));

    const token = await getAccessToken();
    if (!token) {
      return new Response(
        JSON.stringify({ error: "Failed to get Zoho Token" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const record = await getRecordData(entityType, entityId, token);
    if (!record) {
      return new Response(
        JSON.stringify({ error: "Record not found in CRM" }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const contextSections: string[] = [];
    contextSections.push(recordToText(record, entityType));

    const relatedModules = uniqueModules.filter((module) => module !== entityType);
    if (relatedModules.length > 0) {
      const relatedResults = await Promise.all(
        relatedModules.map(async (module) => {
          const records = await getRelatedRecords(entityType, entityId, module, token, 5);
          return { module, records };
        })
      );

      relatedResults.forEach(({ module, records }) => {
        if (!records || records.length === 0) {
          contextSections.push(`${module}: No related records found.`);
          return;
        }

        const limited = records.slice(0, 3);
        const sectionLines: string[] = [
          `${module} (latest ${limited.length}):`,
        ];
        limited.forEach((recordItem, index) => {
          sectionLines.push(`--- ${module} ${index + 1} ---`);
          sectionLines.push(recordToText(recordItem, module));
        });
        contextSections.push(sectionLines.join("\n"));
      });
    }

    const context = contextSections.join("\n\n");

    const prompt = CHAT_RESPONSE_JSON_PROMPT
      .replace("{{CONTEXT}}", context)
      .replace("{{QUERY}}", body.query)
      .replace("{{MODULES}}", uniqueModules.join(", "));

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
