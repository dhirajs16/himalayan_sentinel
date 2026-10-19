import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
const values = Object.fromEntries(readFileSync("../.env.example", "utf8").split(/\r?\n/).filter(l => l && !l.startsWith("#") && l.includes("=")).map(l => { const i = l.indexOf("="); return [l.slice(0, i), l.slice(i + 1)]; }));
async function signIn(page: Page, kind: "ADMIN" | "GOVERNMENT") {
  await page.goto("/operations");
  await page.getByLabel("Email", { exact: true }).fill(values[`${kind}_EMAIL`]);
  await page.getByLabel("Password", { exact: true }).fill(values[`${kind}_PASSWORD`]);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: kind === "ADMIN" ? "System administration" : "Government workspace", exact: true })).toBeVisible();
  await page.getByRole("navigation", { name: "Staff workspace" }).getByRole("link", { name: "Citizen reports", exact: true }).click();
}
test("citizen image → admin moderation → government confirmation → public alert → resolution", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Simulated regional indicators" })).toBeVisible();
  await expect(page.locator(".leaflet-container").first()).toBeVisible();
  const form = page.locator("#report-incident");
  await form.getByLabel("Description", { exact: true }).fill("Demo river water rising near the bridge; submitted for human review.");
  const observed = new Date(Date.now() - 60000); const local = new Date(observed.getTime() - observed.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  await form.getByLabel("Observation time").fill(local);
  // Small synthetic image, never presented as authoritative field evidence.
  await form.locator('input[type="file"]').setInputFiles({ name: "demo.png", mimeType: "image/png", buffer: readFileSync("tests/fixtures/demo.png") });
  await form.getByLabel("I consent").check(); await form.getByLabel("This describes").check(); await form.getByLabel("I understand").check();
  await form.getByRole("button", { name: "Submit for review" }).click();
  await expect(form.getByText("Observation received", { exact: false })).toBeVisible();
  await signIn(page, "ADMIN");
  await page.getByRole("button", { name: "Inspect evidence" }).click();
  await expect(page.locator(".evidence-view img")).toBeVisible();
  await page.getByRole("button", { name: "Escalate to government" }).click();
  await expect(page.getByRole("article").getByText("Escalated", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await signIn(page, "GOVERNMENT");
  page.on("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Confirm incident" }).click();
  await expect(page.getByRole("article").getByText("Verified", { exact: true })).toBeVisible();
  await page.getByRole("navigation", { name: "Staff workspace" }).getByRole("link", { name: "Incidents", exact: true }).click();
  await page.getByRole("button", { name: "Compose alert" }).click();
  await page.getByRole("button", { name: "Generate AI-assisted draft" }).click();
  await expect(page.getByRole("status")).toContainText("deterministic-template");
  await page.getByLabel("Title", { exact: true }).fill("Browser workflow demonstration notice");
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByText("Draft", { exact: true })).toBeVisible();
  for (const action of ["submit", "approve", "publish"]) {
    await page.getByRole("button", { name: action, exact: true }).click();
    await expect(page.getByText(action === "submit" ? "Pending approval" : action === "approve" ? "Approved" : "Published", { exact: true })).toBeVisible();
  }
  const publicPage = await page.context().newPage(); await publicPage.goto("/");
  await expect(publicPage.getByRole("heading", { name: "Browser workflow demonstration notice" })).toBeVisible();
  await expect(publicPage.getByText("DEMO · local publication only")).toBeVisible();
  await page.getByRole("button", { name: "resolve", exact: true }).click();
  await expect(page.getByText("Resolved", { exact: true })).toBeVisible();
  await publicPage.reload(); await expect(publicPage.getByRole("heading", { name: "Browser workflow demonstration notice" })).toHaveCount(0);
  await page.screenshot({ path: "test-results/government-workspace.png", fullPage: true });
});

test("role protection, API error states and failed report submission", async ({ page }) => {
  await page.goto("/operations");
  await expect(page.getByRole("heading", { name: "Sign in to your assigned role" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirm incident" })).toHaveCount(0);
  await page.route("**/api/v1/public/lakes", route => route.abort());
  await page.goto("/");
  await expect(page.getByText("Lake API unavailable:", { exact: false })).toBeVisible();
  await page.route("**/api/v1/reports", route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Demo provider unavailable" }) }));
  const form = page.locator("#report-incident");
  await form.getByLabel("Description", { exact: true }).fill("Another synthetic observation for error feedback.");
  await form.getByLabel("Observation time").fill("2026-10-18T12:00");
  await form.locator('input[type="file"]').setInputFiles({ name: "demo.png", mimeType: "image/png", buffer: Buffer.from("demo") });
  await form.getByLabel("I consent").check(); await form.getByLabel("This describes").check(); await form.getByLabel("I understand").check();
  await form.getByRole("button", { name: "Submit for review" }).click();
  await expect(form.getByRole("alert")).toContainText("Demo provider unavailable");
  await expect(form.getByText("Observation received", { exact: false })).toHaveCount(0);
});

test("lake details expose baseline and missing contributions", async ({ page }) => {
  await page.route("**/api/v1/public/lakes/demo", route => route.fulfill({ json: {
    id: "demo", source_id: "synthetic", lat: 28, lng: 85, geometry: { type: "Point", coordinates: [85, 28] },
    properties: { name: "Synthetic test lake", rank: "I", country: "Nepal", basin: "Demo", attribution: "Synthetic test data", source_date: "2026-10-18" },
    assessment: { version: "test", assessed_at: "2026-10-18T00:00:00Z", mode: "simulated", freshness: "demo", human_review: "Pending", baseline_hazard: { rank: "I", score: 100 }, overall_monitoring_priority: { score: 35, level: "Moderate" }, components: [{ key: "population", value: null, weight: 8, contribution: 0, status: "missing" }], evidence_confidence: 25, completeness: 35, limitations: "Prototype test only." },
  } }));
  await page.goto("/lakes/demo");
  await expect(page.getByRole("heading", { name: "Synthetic test lake" })).toBeVisible();
  await expect(page.getByText("Unknown", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("ICIMOD rank", { exact: true })).toBeVisible();
});

test("public dashboard remains usable on mobile and exposes loading states", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/v1/public/lakes", async route => {
    await new Promise(resolve => setTimeout(resolve, 1500));
    await route.fulfill({ json: { items: [], total: 0 } });
  });
  await page.goto("/");
  await expect(page.getByRole("status").filter({ hasText: "Loading lake inventory" })).toBeVisible();
  await expect(page.getByText("No lake inventory imported", { exact: false })).toBeVisible();
  await expect(page.getByRole("link", { name: "Report an incident", exact: true })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
  await page.screenshot({ path: "test-results/public-mobile.png", fullPage: true });
});
