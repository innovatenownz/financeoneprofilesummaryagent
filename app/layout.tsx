import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Script from 'next/script';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'Finance1 Summary Agent',
  description: 'Zoho CRM Widget for AI-powered record analysis',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans`}>
        {/* Zoho SDK Script - Load early for widget initialization */}
        <Script
          src="https://live.zwidgets.com/js-sdk/1.5/ZohoEmbededAppSDK.min.js"
          strategy="afterInteractive"
        />
        {children}
      </body>
    </html>
  );
}
