import { expect, test } from "@playwright/test";

test("curation queue exposes post-publication confidence actions", async ({ page }) => {
  await page.goto("/curation");

  await expect(page.getByRole("heading", { name: "Unverified Insights" })).toBeVisible();
  await expect(page.getByText("Agent-produced Insights stay visible")).toBeVisible();
  await expect(page.getByRole("button", { name: "Mark verified" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Mark disputed" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Mark historical" }).first()).toBeVisible();
});
