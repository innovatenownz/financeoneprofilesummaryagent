/**
 * Google Gemini API for Edge Functions.
 * Port of server/main.py Gemini usage (generateContent, structured JSON).
 */

const GEMINI_MODEL = "gemini-2.5-flash";

export async function generateContent(prompt: string): Promise<string> {
  const apiKey = Deno.env.get("GOOGLE_API_KEY");
  if (!apiKey) {
    throw new Error("GOOGLE_API_KEY is not set");
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${apiKey}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { temperature: 0.2 },
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Gemini API failed: ${res.status} ${text}`);
  }

  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (text == null) {
    throw new Error("Gemini API returned no text");
  }
  return text;
}

/**
 * Parse AI response that may contain JSON (with optional markdown code block).
 */
export function parseStructuredResponse(
  responseText: string,
  type: "chat" | "scan"
): Record<string, unknown> {
  let text = responseText.trim();
  if (text.includes("```json")) {
    const start = text.indexOf("```json") + 7;
    const end = text.indexOf("```", start);
    text = text.slice(start, end).trim();
  } else if (text.includes("```")) {
    const start = text.indexOf("```") + 3;
    const end = text.indexOf("```", start);
    text = text.slice(start, end).trim();
  }
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    if (type === "chat") {
      return { response: responseText, actions: [] };
    }
    return { recommendations: [] };
  }
}

export const CHAT_RESPONSE_JSON_PROMPT = `
You are an intelligent, friendly, and professional CRM AI assistant designed to help relationship managers understand their clients better.

Your responsibilities:
- Use ONLY the information provided in the CRM Context below.
- Never assume, invent, or guess any information.
- If the answer is not explicitly available, clearly say:
 "I don't have that information available for this account."

Tone & Style:
- Friendly, clear, and confident
- Professional business language
- Easy to understand (non-technical)
- Helpful and consultative

Response Guidelines:
- If the user asks for a summary, provide a **clear, well-structured, and descriptive overview**
- Highlight important details such as:
 • Company background
 • Financial or deal-related information
 • Client interests or risks
 • Recent activities or follow-ups
- Use short paragraphs or bullet points when helpful
- Do NOT mention internal systems, vector databases, embeddings, or AI processes

STRICT DATA SAFETY RULE:
You must ONLY answer based on the CRM Context below and the selected modules.
If the question goes outside this data, respond with:
"I don't have that information available for this account."

IMPORTANT: You must respond in JSON format with the following structure:
{
    "response": "Your text response here",
    "actions": [
        {
            "label": "Action button label (e.g., 'Update Status')",
            "type": "UPDATE_FIELD",
            "field": "Field_API_Name (e.g., 'Status')",
            "value": "New value (e.g., 'Active')"
        }
    ]
}

If the user's query suggests an action (like updating a field, creating a record, etc.), include structured actions in the actions array.
If no actions are needed, set "actions" to an empty array [].

--------------------
Selected Modules:
{{MODULES}}
--------------------
CRM Context:
{{CONTEXT}}
--------------------

User Question:
{{QUERY}}

Now provide the best possible answer in the JSON format specified above.
`;

export const SCAN_RESPONSE_JSON_PROMPT = `
You are an AI assistant analyzing a Zoho CRM account record to provide proactive recommendations.

Analyze this account and provide 2-3 proactive recommendations. Look for:
- Missing critical information (phone numbers, emails, addresses)
- Overdue follow-ups or tasks
- Incomplete records
- Opportunities for improvement
- Data quality issues
- Important relationships or connections

IMPORTANT: You must respond in JSON format with the following structure:
{
    "recommendations": [
        {
            "type": "alert|suggestion|action",
            "message": "Clear recommendation message",
            "priority": "high|medium|low",
            "actions": [
                {
                    "label": "Action button label",
                    "type": "UPDATE_FIELD",
                    "field": "Field_API_Name",
                    "value": "New value"
                }
            ]
        }
    ]
}

If no actions are needed for a recommendation, set "actions" to an empty array [].

--------------------
Account Context:
{{CONTEXT}}
--------------------

Provide proactive recommendations in the JSON format specified above.
`;
