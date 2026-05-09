/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'sm': '0.375rem',
        DEFAULT: '0.75rem',
        'md': '1rem',
        'lg': '1.25rem',
        'xl': '1.5rem',
        '2xl': '2rem',
        '3xl': '3rem',
      },
      colors: {
        background: "#030305",
        foreground: "#e2e8f0",
        card: "rgba(255, 255, 255, 0.03)",
        accent: "#00f0ff",
        success: "#39ff14",
        danger: "#ff003c",
        warning: "#ffea00",
        muted: "#94a3b8",
      },
    },
  },
  plugins: [],
}
