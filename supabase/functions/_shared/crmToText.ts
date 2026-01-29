/**
 * Convert Zoho CRM record to formatted text for LLM.
 * Port of server/crm_to_text.py
 */

export function recordToText(
  recordData: Record<string, unknown>,
  entityType: string = "Record"
): string {
  if (!recordData || Object.keys(recordData).length === 0) {
    return `${entityType} record: No data available`;
  }

  const lines: string[] = [`${entityType} Record Information:`, "=".repeat(50)];

  const recordId = recordData.id ?? recordData.Id;
  if (recordId != null) {
    lines.push(`ID: ${recordId}`);
  }

  const skipKeys = new Set(["id", "created_time", "modified_time", "created_by", "modified_by"]);

  for (const [key, value] of Object.entries(recordData)) {
    if (skipKeys.has(key.toLowerCase())) continue;

    const fieldName = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

    let formattedValue: string;
    if (value == null) {
      formattedValue = "Not set";
    } else if (typeof value === "object" && !Array.isArray(value) && value !== null) {
      const obj = value as Record<string, unknown>;
      if ("name" in obj) {
        formattedValue = String(obj.name);
      } else if ("id" in obj) {
        formattedValue = `${obj.name ?? "Unknown"} (ID: ${obj.id})`;
      } else {
        formattedValue = JSON.stringify(value);
      }
    } else if (Array.isArray(value)) {
      formattedValue = value.map((v) => String(v)).join(", ");
    } else {
      formattedValue = String(value);
    }

    lines.push(`${fieldName}: ${formattedValue}`);
  }

  return lines.join("\n");
}
