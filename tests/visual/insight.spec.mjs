import { expect, test } from "@playwright/test";

test("insight library exposes filters and engagement copy", async ({ page }) => {
  await page.goto("/insights");

  await expect(page.getByRole("heading", { name: "Insight Library" })).toBeVisible();
  await expect(page.getByLabel("Audience")).toBeVisible();
  await expect(page.getByLabel("Format")).toBeVisible();
  await expect(page.getByRole("button", { name: "Filter" })).toBeVisible();
});

