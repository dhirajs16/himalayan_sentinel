import { defineConfig } from "@playwright/test";
import { readFileSync } from "node:fs";
const env = Object.fromEntries(readFileSync("../.env.example", "utf8").split(/\r?\n/).filter(l => l && !l.startsWith("#") && l.includes("=")).map(l => { const index = l.indexOf("="); return [l.slice(0, index), l.slice(index + 1)]; }));
export default defineConfig({
  testDir: "./tests", fullyParallel: false, workers: 1, timeout: 90000,
  expect: { timeout: 20000 }, reporter: "list",
  use: { baseURL: "http://127.0.0.1:3100", browserName: "chromium", channel: "chrome", headless: true, trace: "retain-on-failure" },
  webServer: [
    { command: `${process.platform === "win32" ? ".venv\\Scripts\\python.exe" : ".venv/bin/python"} tests/e2e_server.py`, cwd: "../backend", url: "http://127.0.0.1:8010/health", timeout: 120000, reuseExistingServer: false, env },
    { command: "npm run dev -- --hostname 127.0.0.1 --port 3100", url: "http://127.0.0.1:3100", timeout: 180000, reuseExistingServer: false, env: { NEXT_PUBLIC_API_URL: "http://127.0.0.1:8010", NEXT_DIST_DIR: ".next-test" } },
  ],
});
