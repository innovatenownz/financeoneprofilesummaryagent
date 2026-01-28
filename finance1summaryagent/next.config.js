/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // External script loading for Zoho SDK
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          // Allow iframe embedding from crm.zoho.com.au only
          {
            key: 'Content-Security-Policy',
            value: "frame-ancestors 'self' https://crm.zoho.com.au;",
          },
          // CORS for crm.zoho.com.au with credentials
          {
            key: 'Access-Control-Allow-Origin',
            value: 'https://crm.zoho.com.au',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization, X-Requested-With',
          },
          {
            key: 'Access-Control-Allow-Credentials',
            value: 'true',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;