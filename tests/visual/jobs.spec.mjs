import { expect, test } from "@playwright/test";

test("job dashboard shows refresh schedule section", async ({ page }) => {
  await page.goto("/jobs");

  await expect(page.getByRole("heading", { name: "Job Dashboard" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Refresh schedules" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recent jobs" })).toBeVisible();
});
