import { expect, test } from "@playwright/test";

test("live studio form is projector friendly", async ({ page }) => {
  await page.goto("/live");

  await expect(page.getByRole("heading", { name: "Live Agent Studio" })).toBeVisible();
  await expect(page.getByLabel("Harness target")).toBeVisible();
  await expect(page.getByLabel("Runner")).toBeVisible();
  await expect(page.getByLabel("Task prompt")).toBeVisible();
  await expect(page.getByRole("button", { name: "Start live job" })).toBeVisible();
});
