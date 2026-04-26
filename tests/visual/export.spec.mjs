import { expect, test } from "@playwright/test";

test("exports page shows generation action and generated file list", async ({ page }) => {
  await page.goto("/exports");

  await expect(page.getByRole("heading", { name: "Generated Markdown Exports" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Generate Markdown" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Generated files" })).toBeVisible();
});
