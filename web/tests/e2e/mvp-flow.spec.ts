import { expect, test } from "@playwright/test";

const apiBase = process.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";

test.beforeEach(async ({ request }) => {
  const response = await request.post(`${apiBase}/api/dev/reset`);
  expect(response.ok()).toBeTruthy();
});

test("runs demo flow and resumes the generated trip", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("system-status-panel")).toContainText(/ready|degraded/i);
  await page.getByTestId("run-demo-button").click();

  await expect(page.locator(".draft-item")).toHaveCount(5, { timeout: 45_000 });
  await expect(page.locator(".map-marker")).toHaveCount(4);
  await expect(page.getByTestId("frame-strip").locator(".frame-thumb")).toHaveCount(5);
  await expect(page.getByTestId("selected-gallery").locator("figure")).toHaveCount(5);
  await expect(page.locator(".story-item").first()).toBeVisible();

  await expect(page.getByTestId("resume-trip-button").first()).toBeVisible();
  await page.getByTestId("resume-trip-button").first().click();
  await expect(page.getByTestId("video-draft").locator(".draft-item")).toHaveCount(5);
});
