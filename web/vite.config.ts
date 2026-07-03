import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // Static-demo deploys (e.g. GitHub Pages project sites) set DEMO_BASE=/ForkCast/;
  // local dev, tests and the offline preflight build keep the root base.
  base: process.env.DEMO_BASE ?? "/",
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
