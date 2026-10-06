import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { applyOwnerPageMeta, OWNER_PAGES } from "./src/ownerPages";

// Alvo do proxy configurável: localhost em dev, http://api:8000 no docker-compose.
const apiTarget = process.env.VITE_API_PROXY ?? "http://localhost:8000";

function ownerPanelHtml(): Plugin {
  let outDir = "dist";
  return {
    name: "owner-panel-html",
    apply: "build",
    configResolved(config) {
      outDir = config.build.outDir;
    },
    closeBundle() {
      const indexPath = resolve(outDir, "index.html");
      if (!existsSync(indexPath)) return;
      const index = readFileSync(indexPath, "utf8");
      for (const page of OWNER_PAGES) {
        writeFileSync(resolve(outDir, page.file), applyOwnerPageMeta(index, page));
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), ownerPanelHtml()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/v1": apiTarget,
      "/health": apiTarget,
    },
  },
});
