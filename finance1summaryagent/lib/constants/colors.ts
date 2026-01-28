/**
 * Design System Colors
 * 
 * Based on designguidance.md - "Calm & Trustworthy" financial interface
 * These colors match the Tailwind config for consistency across the codebase
 */

export const colors = {
  primary: {
    DEFAULT: '#1E293B', // Deep Slate Blue - Use for headers, primary buttons, and branding
    dark: '#0F172A',    // Darker variant for hover states
    light: '#334155',   // Lighter variant for subtle elements
  },
  secondary: {
    DEFAULT: '#F8FAFC', // Light Cloud Gray - Use for backgrounds
    white: '#FFFFFF',   // Crisp White - Alternative secondary
  },
  accent: {
    DEFAULT: '#10B981', // Emerald Green - Use for positive trends, "Success" states, and "Deposit" actions
    dark: '#059669',    // Darker variant for hover states
    light: '#34D399',   // Lighter variant for subtle elements
  },
  alert: {
    DEFAULT: '#EF4444', // Soft Terracotta - Use sparingly for errors or critical warnings
    dark: '#DC2626',    // Darker variant for hover states
    light: '#F87171',   // Lighter variant for subtle elements
  },
} as const;

/**
 * Color usage guidelines:
 * 
 * Primary (Stability): Deep Slate Blue
 * - Headers, primary buttons, branding
 * 
 * Secondary (Cleanliness): White / Light Cloud Gray
 * - Backgrounds, clean spaces
 * 
 * Accent (Growth): Emerald Green
 * - Positive trends, success states, deposit actions
 * 
 * Alert (Attention): Soft Terracotta
 * - Errors, critical warnings (use sparingly)
 */
