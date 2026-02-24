import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        /* Cores CalorIA — macronutrientes */
        caloria: {
          calorias: "#f97316",
          proteina: "#22c55e",
          carbs: "#eab308",
          gordura: "#3b82f6",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 8px)",
      },
      boxShadow: {
        "glass-sm": "0 2px 12px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.06)",
        "glass-md": "0 4px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.07)",
        "glass-lg": "0 8px 40px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.08)",
        "neu-sm": "4px 4px 10px rgba(0,0,0,0.3), -3px -3px 8px rgba(255,255,255,0.04)",
        "neu-md": "8px 8px 20px rgba(0,0,0,0.4), -6px -6px 16px rgba(255,255,255,0.04)",
        "neu-inset": "inset 3px 3px 7px rgba(0,0,0,0.3), inset -2px -2px 6px rgba(255,255,255,0.03)",
        "glow-primary": "0 0 18px hsl(142 68% 52% / 0.32), 0 0 36px hsl(142 68% 52% / 0.14)",
        "glow-accent": "0 0 18px hsl(28 90% 58% / 0.32), 0 0 36px hsl(28 90% 58% / 0.14)",
        "glow-sm": "0 0 10px hsl(142 68% 52% / 0.25)",
      },
      backdropBlur: {
        xs: "4px",
        sm: "8px",
        DEFAULT: "12px",
        md: "14px",
        lg: "16px",
        xl: "20px",
        "2xl": "28px",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.97)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "scale-in": "scale-in 0.25s ease-out",
        shimmer: "shimmer 2.5s linear infinite",
        float: "float 4s ease-in-out infinite",
        "pulse-glow": "pulse-glow 2.5s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
