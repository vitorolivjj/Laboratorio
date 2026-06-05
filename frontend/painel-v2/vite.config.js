import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Servido pelo FastAPI em /painel — base precisa bater com o mount.
export default defineConfig({
  plugins: [react()],
  base: "/painel/",
  build: { outDir: "dist", emptyOutDir: true },
});
