import { resolve } from "path";
import { readdirSync } from "fs";
import react from "@vitejs/plugin-react";
import { defineConfig, type UserConfig } from "vite";

// Build a single widget at a time (set WIDGET env var) so that
// inlineDynamicImports produces fully self-contained bundles.
// The build script loops over all widgets.
const srcDir = resolve(__dirname, "src");
const widget = process.env.WIDGET;

let config: UserConfig;

if (widget) {
  // Single widget build — fully self-contained (no code splitting)
  config = {
    plugins: [react()],
    root: resolve(srcDir, widget),
    base: "./",
    build: {
      outDir: resolve(__dirname, "assets", widget),
      emptyOutDir: true,
      assetsDir: ".",
      rollupOptions: {
        output: {
          inlineDynamicImports: true,
        },
      },
    },
  };
} else {
  // Fallback: multi-entry with code splitting (dev only)
  const widgetDirs = readdirSync(srcDir, { withFileTypes: true }).filter(
    (d) => d.isDirectory()
  );
  const input: Record<string, string> = {};
  for (const dir of widgetDirs) {
    input[dir.name] = resolve(srcDir, dir.name, "index.html");
  }
  config = {
    plugins: [react()],
    root: "src",
    base: "./",
    build: {
      outDir: resolve(__dirname, "assets"),
      emptyDirOnStart: true,
      assetsDir: "shared",
      rollupOptions: { input },
    },
  };
}

export default defineConfig(config);
