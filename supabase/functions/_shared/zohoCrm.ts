/**
 * Zoho CRM API: fetch record data.
 * Port of server/zoho_crm_api_call.py (single record fetch).
 */

export async function getRecordData(
  entityType: string,
  entityId: string,
  token: string
): Promise<Record<string, unknown> | null> {
  const apiDomain = Deno.env.get("ZOHO_API_DOMAIN") ?? "www.zohoapis.com";
  const url = `https://${apiDomain}/crm/v3/${entityType}/${entityId}`;

  const res = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Zoho-oauthtoken ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const text = await res.text();
    console.error("Zoho CRM fetch failed:", res.status, text);
    return null;
  }

  const data = await res.json();
  if (data?.data?.length > 0) {
    return data.data[0] as Record<string, unknown>;
  }
  return null;
}

export async function getAccountData(
  accountId: string,
  token: string
): Promise<Record<string, unknown> | null> {
  return getRecordData("Accounts", accountId, token);
}

export async function getRelatedRecords(
  entityType: string,
  entityId: string,
  relatedModule: string,
  token: string,
  limit: number = 5
): Promise<Array<Record<string, unknown>> | null> {
  const apiDomain = Deno.env.get("ZOHO_API_DOMAIN") ?? "www.zohoapis.com";
  const url = new URL(`https://${apiDomain}/crm/v3/${entityType}/${entityId}/${relatedModule}`);
  url.searchParams.set("page", "1");
  url.searchParams.set("per_page", String(limit));

  const res = await fetch(url.toString(), {
    method: "GET",
    headers: {
      Authorization: `Zoho-oauthtoken ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const text = await res.text();
    console.warn(
      `Zoho CRM related list fetch failed for ${relatedModule}:`,
      res.status,
      text
    );
    return null;
  }

  const data = await res.json();
  if (Array.isArray(data?.data)) {
    return data.data as Array<Record<string, unknown>>;
  }
  return null;
}
