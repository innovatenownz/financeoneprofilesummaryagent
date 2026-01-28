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
          // Removed X-Frame-Options to allow Zoho CRM iframe embedding
          // Zoho widgets are loaded in iframes, so we need to allow this
        ],
      },
    ];
  },
};

module.exports = nextConfig;