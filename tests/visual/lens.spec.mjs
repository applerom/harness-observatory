import { expect, test } from "@playwright/test";

test("lens scoring page renders default lenses and refresh control", async ({ page }) => {
  await page.goto("/lenses");

  await expect(page.getByRole("heading", { name: "Scores by lens" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Refresh scores" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Research" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Lecturer" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Practical Selection" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ecosystem" })).toBeVisible();
  await expect(page.getByText("not a universal ranking")).toBeVisible();
});
