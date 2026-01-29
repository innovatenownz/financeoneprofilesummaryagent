/**
 * Zoho OAuth token refresh for Edge Functions.
 * Port of server/zoho_auth.py
 */

export async function getAccessToken(): Promise<string | null> {
  const refreshToken = Deno.env.get("ZOHO_REFRESH_TOKEN");
  const clientId = Deno.env.get("ZOHO_CLIENT_ID");
  const clientSecret = Deno.env.get("ZOHO_CLIENT_SECRET");

  if (!refreshToken || !clientId || !clientSecret) {
    throw new Error("Missing required Zoho OAuth credentials (ZOHO_REFRESH_TOKEN, ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET)");
  }

  const authDomain = Deno.env.get("ZOHO_AUTH_DOMAIN") ?? "accounts.zoho.com";
  const url = new URL(`https://${authDomain}/oauth/v2/token`);
  url.searchParams.set("refresh_token", refreshToken);
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("client_secret", clientSecret);
  url.searchParams.set("grant_type", "refresh_token");

  const res = await fetch(url.toString(), { method: "POST" });
  if (!res.ok) {
    const text = await res.text();
    console.error("Zoho token refresh failed:", res.status, text);
    return null;
  }
  const data = await res.json();
  return data.access_token ?? null;
}
