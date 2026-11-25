import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API base URL is configured with VITE_API_URL (defaults to the dev proxy).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000", "/health": "http://localhost:8000" },
  },
  preview: {
    proxy: { "/api": "http://localhost:8000" },
  },
});
