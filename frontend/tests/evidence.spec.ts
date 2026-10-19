import { expect, test, type Page } from "@playwright/test";

const lake = (index: number) => ({ id: `context-${index}`, name: `Inventory lake ${index}`, country: "Nepal", basin: "Trishuli", lat: index === 0 ? null : 28, lng: index === 0 ? null : 85,
  geometry: null, properties: { source_link: "https://example.org/inventory", untrusted: "javascript:alert(1)" }, attribution: "Inventory test attribution", source_date: "2020" });

async function fixtures(page: Page, populationUnavailable = false) {
  const requests: string[] = [];
  await page.route("**/tile.openstreetmap.org/**", route => route.abort());
  await page.route("**/api/v1/public/context/**", async route => {
    const url = new URL(route.request().url());
    requests.push(url.pathname + url.search);
    const endpoint = url.pathname.split("/context/")[1];
    let json: unknown;
    if (endpoint === "catalog") json = { sources: [{ id: "inventory", name: "Glacial-lake inventory source", status: "available", count: 51, source_date: "2020", attribution: "Inventory test attribution", limitations: "Static inventory, not a risk score." }], districts: [{ id: "gorkha", name: "Gorkha" }, { id: "rasuwa", name: "Rasuwa" }], limitations: "Geographic context only." };
    else if (endpoint.startsWith("weather/")) {
      const simulated = endpoint.endsWith("gorkha");
      json = { provider: "Open-Meteo", mode: simulated ? "simulated" : "cached", freshness: simulated ? "demo" : "stale", error: simulated ? "Live provider disabled" : "Provider unavailable; cached forecast shown", last_success: "2026-10-19T00:00:00Z", source_observation_time: "2026-10-19", attribution: "Forecast attribution", daily: { time: ["2026-10-19"], precipitation_sum: [simulated ? 12 : 23], temperature_2m_max: [19] } };
    } else if (endpoint.startsWith("population/")) json = { status: populationUnavailable ? "unavailable" : "available", district: endpoint.split("/")[1], population: populationUnavailable ? null : 45678.4, year: 2026, units: "people", valid_cells: populationUnavailable ? null : 1000, method: "District boundary raster mask", source: "WorldPop R2025A", attribution: "Population test attribution", limitations: "Modelled population; boundary-limited estimate." };
    else if (endpoint === "lakes") {
      const filtered = !!url.searchParams.get("country") || !!url.searchParams.get("q") || !!url.searchParams.get("basin");
      const offset = Number(url.searchParams.get("offset") || 0);
      json = { items: filtered ? [lake(3)] : Array.from({ length: offset === 0 ? 50 : 1 }, (_, index) => lake(offset + index)), total: filtered ? 1 : 51, offset, limit: 50 };
    } else if (endpoint === "events") json = { items: [], total: 0, offset: 0, limit: 50 };
    else return route.fulfill({ status: 404, json: { detail: "Unknown fixture" } });
    await route.fulfill({ json });
  });
  return requests;
}

test("context filters, actual totals, unmapped records and safe source attributes", async ({ page }) => {
  const requests = await fixtures(page);
  await page.goto("/");
  const explorer = page.locator("#evidence-context");
  await expect(explorer.getByRole("heading", { name: "Explore district evidence" })).toBeVisible();
  await expect(explorer.getByLabel("District context", { exact: true })).toHaveValue("rasuwa");
  await expect(explorer.getByText("1–50 of 51 records", { exact: true })).toBeVisible();
  await expect(explorer.getByText("context-0 · Unmapped: coordinates unavailable", { exact: true })).toBeVisible();
  await explorer.getByRole("button", { name: "Next page" }).click();
  await expect(explorer.getByText("51–51 of 51 records", { exact: true })).toBeVisible();
  await expect(explorer.getByRole("button", { name: "Next page" })).toBeDisabled();
  await explorer.getByLabel("Country", { exact: true }).fill("Nepal");
  await explorer.getByLabel("Basin", { exact: true }).fill("Trishuli");
  await explorer.getByLabel("Search records", { exact: true }).fill("lake");
  await explorer.getByLabel("Limit records to selected district").check();
  await explorer.getByRole("button", { name: "Apply filters" }).click();
  await expect(explorer.getByText("1–1 of 1 records", { exact: true })).toBeVisible();
  expect(requests.some(request => request.includes("country=Nepal") && request.includes("basin=Trishuli") && request.includes("district=rasuwa") && request.includes("offset=0"))).toBe(true);
  await explorer.getByRole("button", { name: "Inventory lake 3", exact: false }).click();
  await explorer.getByText("All retained source attributes", { exact: true }).click();
  await expect(explorer.getByRole("link", { name: "https://example.org/inventory", exact: true })).toHaveAttribute("rel", "noopener noreferrer");
  await expect(explorer.getByText("javascript:alert(1)", { exact: true })).toBeVisible();
  await expect(explorer.locator('a[href^="javascript:"]')).toHaveCount(0);
  await explorer.getByRole("button", { name: "Historical events", exact: true }).click();
  await expect(explorer.getByText("No matching records", { exact: true })).toBeVisible();
  // Changing unrelated filters must not refetch the district weather.
  expect(requests.filter(request => request.includes("weather/rasuwa"))).toHaveLength(1);
});

test("forecast modes and unavailable population remain clear on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await fixtures(page, true);
  await page.goto("/");
  const explorer = page.locator("#evidence-context");
  const forecast = explorer.getByRole("article", { name: "District forecast" });
  await expect(forecast.getByText("cached · stale", { exact: true })).toBeVisible();
  await expect(forecast.getByRole("cell", { name: "23", exact: true })).toBeVisible();
  await expect(explorer.getByText("Population unavailable", { exact: true })).toBeVisible();
  await expect(explorer.getByText("This is not a count of people exposed to a flood.", { exact: false })).toBeVisible();
  await explorer.getByLabel("District context", { exact: true }).selectOption("gorkha");
  await expect(forecast.getByText("simulated · demo", { exact: true })).toBeVisible();
  await expect(forecast.getByText("Live provider disabled", { exact: true })).toBeVisible();
  await expect(forecast.getByRole("cell", { name: "12", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
  await explorer.screenshot({ path: "test-results/evidence-mobile.png" });
});

test("weather failure and obsolete district requests cannot replace current data", async ({ page }) => {
  await fixtures(page);
  await page.route("**/api/v1/public/context/weather/rasuwa", async route => {
    await new Promise(resolve => setTimeout(resolve, 1200));
    await route.fulfill({ json: { provider: "Old district response", mode: "live", freshness: "fresh", attribution: "Old", daily: { time: [], precipitation_sum: [], temperature_2m_max: [] } } });
  });
  await page.goto("/");
  const explorer = page.locator("#evidence-context");
  await expect(explorer.getByLabel("District context", { exact: true })).toHaveValue("rasuwa");
  await explorer.getByLabel("District context", { exact: true }).selectOption("gorkha");
  await expect(explorer.getByText("simulated · demo", { exact: true })).toBeVisible();
  await page.waitForTimeout(1400); // Deliberately let the obsolete response arrive.
  await expect(explorer.getByText("Old district response", { exact: false })).toHaveCount(0);
  await page.route("**/api/v1/public/context/weather/rasuwa", route => route.fulfill({ status: 503, json: { detail: "Weather temporarily unavailable" } }));
  await explorer.getByLabel("District context", { exact: true }).selectOption("rasuwa");
  await expect(explorer.getByRole("alert").filter({ hasText: "Weather temporarily unavailable" })).toBeVisible();
  await expect(explorer.getByText("45,678 people", { exact: true })).toBeVisible();
});

test("staff evidence link accepts a district name and selects its actual catalog ID", async ({ page }) => {
  await fixtures(page);
  await page.goto("/evidence?district=Gorkha");
  const explorer = page.locator("#evidence-context");
  await expect(explorer.getByLabel("District context", { exact: true })).toHaveValue("gorkha");
  await expect(explorer.getByText("simulated · demo", { exact: true })).toBeVisible();
});
