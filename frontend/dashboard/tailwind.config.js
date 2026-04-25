/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      // ─── Pajamas-inspired design tokens ─────────────────────────────────
      // Adopted from GitLab's Pajamas system, flavoured with our indigo accent.
      // Use these semantic names in components, not raw slate/gray utilities.
      colors: {
        gl: {
          sidebar:  '#1a1a1a',  // dark canvas — matches GitLab's near-black nav
          surface:  '#eef0f4',  // outer page stage — makes the panel pop
          panel:    '#ffffff',  // content container background
          border:   '#dcdcde',  // standard border (Pajamas neutral-100)
          divider:  '#ececef',  // subtle dividers (Pajamas neutral-50)
          ink:      '#1f1f1f',  // primary text (Pajamas neutral-950)
          subtle:   '#737278',  // secondary text (Pajamas neutral-700)
        },
        // Our character — indigo accent not in Pajamas, sets us apart
        accent: {
          DEFAULT: '#6366f1',
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          600: '#4f46e5',
          700: '#4338ca',
        },
      },

      fontFamily: {
        sans: ['"Fira Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"Fira Code"', 'ui-monospace', 'monospace'],
      },

      borderRadius: {
        panel: '0.875rem', // 14px — content container, slightly more than stock
      },

      boxShadow: {
        // Pajamas elevation: 1px/3px layered shadow, low opacity
        panel:  '0 1px 4px 0 rgba(0,0,0,0.07), 0 1px 2px -1px rgba(0,0,0,0.05)',
        raised: '0 4px 12px -2px rgba(0,0,0,0.10), 0 2px 4px -2px rgba(0,0,0,0.06)',
      },
    },
  },
  plugins: [],
}
