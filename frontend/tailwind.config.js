/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        talus: {
          50: '#faf6f0',
          100: '#f3e9dd', // Card / panel background
          200: '#e5d8c9', // Secondary background
          300: '#d2c3b3', // Borders/dividers
          400: '#b8a695',
          500: '#997e67', // Secondary brown
          600: '#664930', // Brand primary dark brown
          700: '#523a25',
          800: '#3e2b1b',
          900: '#2b2119', // Primary text
          950: '#1c1510',
        },
        risk: {
          verylow: '#5e7f3a', // Safe 500
          low: '#a68a3c',     // Low 500
          moderate: '#d99a24',// Moderate 500
          high: '#d96b24',    // High 500
          critical: '#c74732' // Critical 500
        },
        mine: {
          darkest: '#ccbeb1', // Primary background — deprecated alias, use surface
          darker: '#e5d8c9',
          dark: '#ddd0c1',
          card: '#f3e9dd',
          border: '#d2c3b3',
          highlight: '#997e67',
          text: '#2b2119',
          muted: '#6f6256',
        },
        surface: {
          darkest: '#ccbeb1',
          darker: '#e5d8c9',
          dark: '#ddd0c1',
          card: '#f3e9dd',
          border: '#d2c3b3',
          highlight: '#997e67',
          text: '#2b2119',
          muted: '#6f6256',
        }
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      animation: {
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'radar-sweep': 'radarSweep 4s linear infinite',
      },
      keyframes: {
        radarSweep: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        }
      }
    },
  },
  plugins: [],
}
