import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During local dev the frontend runs on :5173 and proxies /api to the FastAPI
// dev server on :8000. In production on Vercel, /api is served by the Python
// serverless function at the same origin, so no proxy is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
