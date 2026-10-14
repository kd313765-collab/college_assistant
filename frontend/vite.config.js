import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api ki saari request Flask (port 5000) ko chali jayegi
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:5000" },
  },
});
