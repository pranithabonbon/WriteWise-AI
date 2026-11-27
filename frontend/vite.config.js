import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Browser calls /api/... on port 5173; Vite forwards it to Flask on 5001
      "/api": {
        // In Compose, Vite runs in its own container and must use the backend
        // service name. The loopback default keeps non-Docker local dev intact.
        target: process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:5001",
        changeOrigin: true,
      },
    },
  },
});
