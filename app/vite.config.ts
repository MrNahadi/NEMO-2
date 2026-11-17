import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the app runs on Vite and forwards /api to the local NEMO engine.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8765" },
  },
  build: {
    outDir: "dist",
    chunkSizeWarningLimit: 1500,
  },
});
