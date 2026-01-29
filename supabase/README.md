# Supabase setup for Finance1 Summary Agent

## Phase 1: One-time setup in Supabase Dashboard

1. **Enable pgvector**
   - Database → Extensions → enable `vector`.
   - Run migrations: `supabase db push` (or apply [migrations/20250129000001_enable_pgvector.sql](migrations/20250129000001_enable_pgvector.sql) manually).

2. **Create Storage bucket**
   - Storage → New bucket.
   - Name: `documents`.
   - Set to private (or your policy). Used by the `upload` Edge Function.

3. **Set Edge Function secrets**
   - Project Settings → Edge Functions → secrets (or CLI: `supabase secrets set`).
   - Add the same values as in `server/.env`:
     - `ZOHO_REFRESH_TOKEN`
     - `ZOHO_CLIENT_ID`
     - `ZOHO_CLIENT_SECRET`
    - `ZOHO_API_DOMAIN` (e.g. `www.zohoapis.com` or `www.zohoapis.com.au`)
    - `ZOHO_AUTH_DOMAIN` (e.g. `accounts.zoho.com` or `accounts.zoho.com.au`)
     - `GOOGLE_API_KEY`

## Deploy Edge Functions

From project root:

```bash
supabase link --project-ref YOUR_PROJECT_REF
supabase functions deploy agent-chat
supabase functions deploy agent-scan
supabase functions deploy upload
```

Replace `YOUR_PROJECT_REF` with your Supabase project reference (from Dashboard URL or Settings → General).
