import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep ink with a hint of green — matches the floating-card hero aesthetic
        ink: {
          DEFAULT: "#0f1411",
          deep: "#080a09",
          soft: "#1a1f1c",
          line: "rgba(255,255,255,0.08)",
        },
        // Warm cream page background
        cream: {
          DEFAULT: "#efe9dd",
          paper: "#f6f1e7",
          warm: "#e6dfd0",
          deep: "#d8d0bd",
        },
        // Compatibility aliases (legacy components reference navy)
        navy: {
          DEFAULT: "#0f1411",
          deep: "#080a09",
          soft: "#1a1f1c",
        },
        // Vibrant emerald for positive numbers / accents
        signal: {
          DEFAULT: "#10b981",
          bright: "#34d399",
          deep: "#059669",
        },
        accent: {
          gold: "#d4a96a",
          rust: "#c26d4a",
          emerald: "#10b981",
          sage: "#10b981",
        },
        risk: {
          low: "#10b981",
          medium: "#d4a96a",
          high: "#dc5a3e",
        },
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-inter)", "var(--font-manrope)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,20,17,0.04), 0 8px 24px -8px rgba(15,20,17,0.12)",
        cardLg: "0 4px 12px rgba(15,20,17,0.06), 0 24px 48px -16px rgba(15,20,17,0.18)",
        inkCard: "0 1px 2px rgba(0,0,0,0.3), 0 12px 32px -12px rgba(0,0,0,0.4)",
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
    },
  },
  plugins: [],
};
export default config;
