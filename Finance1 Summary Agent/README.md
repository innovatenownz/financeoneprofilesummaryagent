# Finance1 Summary Agent

A Next.js 14+ widget for Zoho CRM that provides AI-powered record analysis and recommendations.

## Tech Stack

- **Next.js 14+** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **Zoho Widget SDK (ZSDK)**

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env.local
```

3. Update `.env.local` with your configuration:
   - `NEXT_PUBLIC_FASTAPI_URL`: Your FastAPI backend URL
   - `NEXT_PUBLIC_ZOHO_CLIENT_ID`: Your Zoho OAuth client ID

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

- `app/` - Next.js App Router pages and API routes
- `components/` - React components
- `lib/` - Utility libraries and API clients
- `types/` - TypeScript type definitions
- `hooks/` - Custom React hooks

## Deployment

This project is configured for Vercel deployment as a Zoho CRM embedded widget.

### Vercel Configuration

The project includes optimized Vercel settings in `vercel.json`:
- **Function Configuration**: API routes configured with 30s timeout and 1GB memory
- **CORS Headers**: Configured for API routes to allow cross-origin requests
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, and Referrer-Policy
- **Region**: Deployed to `iad1` (US East)

### Deploying to Vercel

1. **Connect Repository**:
   - Push your code to GitHub/GitLab/Bitbucket
   - Import the repository in Vercel dashboard
   - Vercel will auto-detect Next.js framework

2. **Configure Environment Variables**:
   
   In the Vercel project settings, add the following environment variables:
   
   **Required:**
   - `NEXT_PUBLIC_FASTAPI_URL` - Your FastAPI backend URL (e.g., `https://api.yourdomain.com`)
   - `NEXT_PUBLIC_ZOHO_CLIENT_ID` - Your Zoho OAuth client ID
   - `NEXT_PUBLIC_ENVIRONMENT` - Set to `production` for production deployments
   
   **Optional:**
   - `NEXT_PUBLIC_API_VERSION` - API version (defaults to "v1")
   - `NEXT_PUBLIC_ENABLE_SCAN` - Enable proactive scan feature (`true`/`false`)

3. **Deploy**:
   - Vercel will automatically deploy on every push to your main branch
   - Preview deployments are created for pull requests
   - Production deployments require manual approval (if configured)

4. **Configure Zoho Widget**:
   - Use your Vercel deployment URL in Zoho CRM widget configuration
   - Ensure the widget URL is whitelisted in your Zoho account settings

### Environment Variables Reference

See `.env.example` for a complete list of available environment variables with descriptions.

### API Routes Configuration

All API routes are configured as serverless functions with:
- **Max Duration**: 30 seconds
- **Memory**: 1024 MB
- **CORS**: Enabled for cross-origin requests

This ensures reliable proxy connections to your FastAPI backend.
