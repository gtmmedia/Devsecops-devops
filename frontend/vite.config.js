import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev (npm run dev) the browser calls /api on :5173 and Vite forwards it to
// the FastAPI backend. In Docker/Kubernetes nginx or the Ingress does the same job.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
