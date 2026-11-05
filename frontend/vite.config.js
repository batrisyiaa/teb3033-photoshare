import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, "/api" requests are forwarded to the Flask server on port 5000.
// In production, nginx does the same job (see deploy/nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:5000" },
  },
});
