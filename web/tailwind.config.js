/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "media",
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#2563eb", dark: "#1d4ed8", light: "#dbeafe" },
        tg: {
          bg: "var(--tg-theme-bg-color, #ffffff)",
          text: "var(--tg-theme-text-color, #111827)",
          hint: "var(--tg-theme-hint-color, #6b7280)",
          button: "var(--tg-theme-button-color, #2563eb)",
          buttonText: "var(--tg-theme-button-text-color, #ffffff)",
          secondary: "var(--tg-theme-secondary-bg-color, #f3f4f6)",
        },
      },
      fontFamily: { sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"] },
    },
  },
  plugins: [],
};
