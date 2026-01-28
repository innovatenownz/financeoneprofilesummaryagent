/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Design System Colors
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
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
      // Additional design tokens for consistency
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'medium': '0 4px 12px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
};
