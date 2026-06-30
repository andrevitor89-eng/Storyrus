import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Alvo do proxy configurável: localhost em dev, http://api:8000 no docker-compose.
const apiTarget = process.env.VITE_API_PROXY ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/v1": apiTarget,
      "/health": apiTarget,
    },
  },
});
