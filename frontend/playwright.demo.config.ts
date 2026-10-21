import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

// Reuses the isolated SQLite service and mock delivery adapters, never the user's DB.
export default defineConfig({
  ...base,
  testDir: "./demo",
  outputDir: "test-results/demo",
  timeout: 240000,
  use: {
    ...base.use,
    viewport: { width: 1440, height: 900 },
    video: { mode: "on", size: { width: 1440, height: 900 } },
    trace: "off",
  },
});
