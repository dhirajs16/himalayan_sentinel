import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

const values = Object.fromEntries(readFileSync("../.env.example", "utf8").split(/\r?\n/).filter(line => line && !line.startsWith("#") && line.includes("=")).map(line => {
  const split = line.indexOf("="); return [line.slice(0, split), line.slice(split + 1)];
}));

test("admin navigation supports collapse, history, every section and mobile keyboard access", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/operations");
  await page.getByLabel("Email", { exact: true }).fill(values.ADMIN_EMAIL);
  await page.getByLabel("Password", { exact: true }).fill(values.ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "System administration", exact: true })).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Staff workspace" });
  await expect(page.locator(".ops-metric-card").first()).not.toContainText("Loading workspace");
  await expect(nav.getByRole("link")).toHaveCount(10);
  await page.screenshot({ path: "test-results/admin-desktop.png", fullPage: true });
  await page.getByRole("button", { name: "Collapse sidebar" }).click();
  await expect(page.locator(".ops-layout")).toHaveClass(/is-collapsed/);
  await nav.getByRole("link", { name: "Users & access", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Accounts and jurisdiction assignments" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Users & access", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Expand sidebar" })).toHaveAttribute("aria-expanded", "false");
  await page.getByRole("button", { name: "Expand sidebar" }).click();
  for (const name of ["Data providers", "Rules & templates", "Audit log", "Sync history", "Notification logs", "Data quality", "Citizen reports", "Lake monitoring", "Overview"]) {
    await nav.getByRole("link", { name, exact: true }).click();
    await expect(nav.getByRole("link", { name, exact: true })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("status").filter({ hasText: /Loading|Updating/ })).toHaveCount(0);
    await expect(page.locator(".error-message")).toHaveCount(0);
  }
  await page.goBack();
  await expect(nav.getByRole("link", { name: "Lake monitoring", exact: true })).toHaveAttribute("aria-current", "page");
  await nav.getByRole("link", { name: "Overview", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  const menu = page.getByRole("button", { name: "Open navigation", exact: true });
  await expect(menu).toBeVisible();
  await expect(nav).not.toBeVisible();
  await menu.click();
  await expect(page.getByRole("dialog", { name: "Workspace navigation" })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Workspace navigation" }).getByRole("button", { name: "Close navigation", exact: true })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(menu).toBeFocused();
  await menu.click();
  await nav.getByRole("link", { name: "Users & access", exact: true }).click();
  await expect(nav).not.toBeVisible();
  await expect(page.getByRole("heading", { name: "Users & access", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
  await menu.click();
  await nav.getByRole("link", { name: "Overview", exact: true }).click();
  await page.screenshot({ path: "test-results/admin-mobile.png", fullPage: true });
  await menu.click();
  await page.screenshot({ path: "test-results/admin-mobile-navigation.png", fullPage: true });
});
