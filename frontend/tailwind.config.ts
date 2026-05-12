import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#f8f6f1',
          muted: '#f0ede6',
          panel: '#fffdf9',
        },
        line: '#d9d2c5',
        ink: {
          DEFAULT: '#1f1c17',
          soft: '#5b5348',
          faint: '#8b8377',
        },
        accent: '#5f7cff',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
      boxShadow: {
        panel: '0 18px 60px rgba(31, 28, 23, 0.08)',
      },
    },
  },
  plugins: [],
}

export default config
