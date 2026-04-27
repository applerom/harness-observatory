import { expect, test } from "@playwright/test";

test("curation queue exposes post-publication confidence actions", async ({ page }) => {
  await page.goto("/curation");

  await expect(page.getByRole("heading", { name: "Needs review" })).toBeVisible();
  await expect(page.getByText("These buttons only change the insight status/confidence labels.")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Curation view tabs" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Verify this insight" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Flag this insight as disputed" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Archive this insight as historical" }).first()).toBeVisible();
  await expect(page.getByText("Mark this as verified without deleting any evidence.").first()).toBeVisible();
  await expect(page.getByText("Mark this as disputed for follow-up review.").first()).toBeVisible();
  await expect(page.getByText("Archive as historical in this queue without deleting output.").first()).toBeVisible();

  await page.getByRole("button", { name: "Verify this insight" }).first().click();
  await expect(page).toHaveURL(/\/curation\?.*view=verified/);
  await expect(page.getByRole("heading", { name: "Verified" })).toBeVisible();
  await expect(page.getByText("Action applied:")).toBeVisible();
  await expect(page.locator(".status-badge", { hasText: "human-verified" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Undo" }).first()).toBeVisible();

  await page.getByRole("button", { name: "Undo" }).first().click();
  await expect(page).toHaveURL(/\/curation\?.*view=review/);
  await expect(page.getByRole("heading", { name: "Needs review" })).toBeVisible();
  await expect(page.getByText("Undo applied:")).toBeVisible();
  await expect(page.getByRole("button", { name: "Undo" })).toHaveCount(0);
});
