import { expect, test } from "@playwright/test";

const apiBase = process.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";

test.beforeEach(async ({ request }) => {
  const response = await request.post(`${apiBase}/api/dev/reset`);
  expect(response.ok()).toBeTruthy();
});

test("runs health monitoring demo flow", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("system-status-panel")).toContainText(/ready|degraded/i);
  await page.getByTestId("run-demo-button").click();

  await expect(page.getByTestId("score-grid")).toContainText("综合健康分", { timeout: 45_000 });
  await expect(page.getByTestId("device-card")).toContainText("Insta360");
  await expect(page.getByTestId("behavior-list").locator(".behavior-item")).toHaveCount(5);
  await expect(page.getByTestId("daily-card")).toContainText("高糖饮食");
  await expect(page.getByTestId("weekly-report")).toContainText("下周目标");

  await page.getByText("夜间加餐").click();
  await page.getByTestId("manual-capture-button").click();
  await expect(page.getByTestId("behavior-list").locator(".behavior-item")).toHaveCount(5);

  await page.getByTestId("weekly-report-button").click();
  await expect(page.getByTestId("weekly-report")).toContainText("个性化建议");
});
