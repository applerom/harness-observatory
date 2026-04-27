import { expect, test } from "@playwright/test";

test("non-OpenCode dossier exposes target-generic refresh controls", async ({ page }) => {
  await page.goto("/harnesses/codex-cli");

  await expect(page.getByRole("heading", { name: "Codex CLI" })).toBeVisible();
  await expect(page.getByText("Refresh target: Codex CLI")).toBeVisible();
  await expect(page.getByRole("button", { name: "Run with Codex" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run with Claude" })).toBeVisible();
  await expect(page.getByText("Only OpenCode refresh")).toHaveCount(0);
});
