/** Capture working UI footage only. The entrant supplies narration and submission text. */
import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

const values = Object.fromEntries(readFileSync("../.env.example", "utf8").split(/\r?\n/)
  .filter(line => line && !line.startsWith("#") && line.includes("="))
  .map(line => { const i = line.indexOf("="); return [line.slice(0, i), line.slice(i + 1)]; }));
const hold = (page: Page, seconds: number) => page.waitForTimeout(seconds * 1000);

test.beforeAll(async ({ request }) => {
  // Compile routes before recording, so setup delays stay outside the footage.
  for (const path of ["/", "/evidence?district=rasuwa", "/operations"]) {
    const response = await request.get(path);
    expect(response.ok()).toBeTruthy();
  }
});

test("record the staged evidence-to-resolution journey", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("dialog", dialog => dialog.accept());
  await page.goto("/evidence?district=rasuwa");
  await expect(page.getByRole("heading", { name: "Explore district evidence" })).toBeVisible();
  await expect(page.getByText("Nepal district boundaries (Open Knowledge Nepal)", { exact: true })).toBeVisible();
  await hold(page, 5);
  await page.getByLabel("District context", { exact: true }).selectOption("gorkha");
  await page.getByRole("article", { name: "District population context", exact: true }).scrollIntoViewIfNeeded();
  await hold(page, 7);
  await page.getByRole("button", { name: "Historical events", exact: true }).click();
  await page.getByLabel("Country", { exact: true }).fill("Nepal");
  await page.getByRole("button", { name: "Apply filters", exact: true }).click();
  await page.locator(".context-map").scrollIntoViewIfNeeded();
  await expect(page.locator(".evidence-records li").first()).toBeVisible();
  await page.locator(".evidence-records li button").first().click();
  await page.getByRole("article", { name: "Selected record details" }).scrollIntoViewIfNeeded();
  await hold(page, 6);

  await page.goto("/");
  const form = page.locator("#report-incident");
  await form.scrollIntoViewIfNeeded();
  await form.getByLabel("Description", { exact: true }).fill("STAGED DEMO: river water rising near a bridge; submitted for human review, not a field observation.");
  const observed = new Date(Date.now() - 60000);
  await form.getByLabel("Observation time").fill(new Date(observed.getTime() - observed.getTimezoneOffset() * 60000).toISOString().slice(0, 16));
  await form.locator('input[type="file"]').setInputFiles({ name: "staged-demo.png", mimeType: "image/png", buffer: readFileSync("tests/fixtures/demo.png") });
  await form.getByLabel("I consent").check();
  await form.getByLabel("This describes").check();
  await form.getByLabel("I understand").check();
  await hold(page, 4);
  await form.getByRole("button", { name: "Submit for review" }).click();
  await expect(form.getByText("Observation received", { exact: false })).toBeVisible();
  await hold(page, 4);

  async function signIn(kind: "ADMIN" | "GOVERNMENT") {
    await page.goto("/operations");
    await page.getByLabel("Email", { exact: true }).fill(values[`${kind}_EMAIL`]);
    await page.getByLabel("Password", { exact: true }).fill(values[`${kind}_PASSWORD`]);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.getByRole("heading", { name: kind === "ADMIN" ? "System administration" : "Government workspace", exact: true })).toBeVisible();
    await page.getByRole("navigation", { name: "Staff workspace" }).getByRole("link", { name: "Citizen reports", exact: true }).click();
  }
  await signIn("ADMIN");
  await page.getByRole("button", { name: "Inspect evidence", exact: true }).click();
  await expect(page.locator(".evidence-view img")).toBeVisible();
  await hold(page, 5);
  await page.getByRole("button", { name: "Escalate to government", exact: true }).click();
  await expect(page.getByRole("article").getByText("Escalated", { exact: true })).toBeVisible();
  await hold(page, 3);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await signIn("GOVERNMENT");
  await page.getByRole("button", { name: "Confirm incident", exact: true }).click();
  await expect(page.getByRole("article").getByText("Verified", { exact: true })).toBeVisible();
  await hold(page, 4);
  await page.getByRole("navigation", { name: "Staff workspace" }).getByRole("link", { name: "Incidents", exact: true }).click();
  await page.getByRole("button", { name: "Compose alert", exact: true }).click();
  await page.getByRole("button", { name: "Generate AI-assisted draft", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("deterministic-template");
  await page.getByLabel("Title", { exact: true }).fill("STAGED DEMO — reviewed local notice");
  await hold(page, 6);
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByText("Draft", { exact: true })).toBeVisible();
  for (const [action, status] of [["submit", "Pending approval"], ["approve", "Approved"], ["publish", "Published"]]) {
    await page.getByRole("button", { name: action, exact: true }).click();
    await expect(page.getByText(status, { exact: true })).toBeVisible();
    await hold(page, 4);
  }
  await page.goto("/");
  const notice = page.getByRole("heading", { name: "STAGED DEMO — reviewed local notice", exact: true });
  await expect(notice).toBeVisible();
  await notice.scrollIntoViewIfNeeded();
  await expect(page.getByText("DEMO · local publication only", { exact: true })).toBeVisible();
  await hold(page, 7);
  await page.goto("/operations");
  await page.getByRole("navigation", { name: "Staff workspace" }).getByRole("link", { name: "Incidents", exact: true }).click();
  await page.getByRole("button", { name: "resolve", exact: true }).click();
  await expect(page.getByText("Resolved", { exact: true })).toBeVisible();
  await hold(page, 4);
  await page.goto("/");
  await expect(notice).toHaveCount(0);
  await hold(page, 4);
  expect(errors).toEqual([]);
});
