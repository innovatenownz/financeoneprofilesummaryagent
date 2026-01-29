/**
 * Edge Function: upload
 * Document upload to Supabase Storage. Matches FastAPI /upload contract.
 */

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

const BUCKET = "finance1summaryagentdocuments";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ success: false, error: "Method not allowed" }),
      { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  try {
    const formData = await req.formData();
    const file = formData.get("file") as File | null;
    const entityId = formData.get("entity_id") as string | null;
    const entityType = formData.get("entity_type") as string | null;

    if (!file) {
      return new Response(
        JSON.stringify({ success: false, error: "file is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    if (!entityId) {
      return new Response(
        JSON.stringify({ success: false, error: "entity_id is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    if (!entityType) {
      return new Response(
        JSON.stringify({ success: false, error: "entity_type is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    if (entityType !== "Accounts") {
      return new Response(
        JSON.stringify({ success: false, error: `Entity type '${entityType}' not yet supported.` }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const filename = file.name ?? "document";
    const path = `${entityType}/${entityId}/${filename}`;

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!supabaseUrl || !supabaseServiceKey) {
      return new Response(
        JSON.stringify({ success: false, error: "Supabase configuration missing" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);
    const arrayBuffer = await file.arrayBuffer();
    const { error } = await supabase.storage.from(BUCKET).upload(path, arrayBuffer, {
      contentType: file.type || "application/octet-stream",
      upsert: true,
    });

    if (error) {
      console.error("Storage upload error:", error);
      return new Response(
        JSON.stringify({ success: false, error: error.message, message: error.message }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const message = `Document '${filename}' uploaded successfully for ${entityType} ${entityId}`;
    return new Response(
      JSON.stringify({
        success: true,
        message,
        entity_id: entityId,
        entity_type: entityType,
        filename,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (e) {
    console.error("upload error:", e);
    return new Response(
      JSON.stringify({
        success: false,
        error: "Error uploading document",
        message: String(e),
      }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
