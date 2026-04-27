import { expect, test } from "@playwright/test";

test("matrix is dense and reveals clicked cell detail beside the grid", async ({ page }) => {
  await page.goto("/matrix");

  const mainScroll = page.getByTestId("matrix-scroll-main");
  await expect(mainScroll).toBeVisible();
  await expect(page.locator(".matrix-legend").getByText("present")).toBeVisible();

  const detail = page.locator("#matrix-cell-detail");
  const cell = page.getByTestId("matrix-cell-opencode-instruction-files");
  await expect(cell).toBeVisible();
  await expect
    .poll(async () =>
      cell.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        return Math.round(rect.width);
      }),
    )
    .toBeLessThan(48);

  await cell.click();

  await expect(detail).toContainText("OpenCode / Instruction Files");
  await expect(detail).not.toContainText("Expanded cell");
  await expect(detail).not.toContainText("State:");
  await expect(detail).not.toContainText("Confidence:");
  await expect
    .poll(async () =>
      detail.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        return rect.top < window.innerHeight - 120 && rect.bottom > 120;
      }),
    )
    .toBe(true);

  await detail.getByRole("button", { name: "Ask the agent why" }).first().click();
  await expect(detail).toContainText("OpenCode / Instruction Files");
  await expect(detail).toContainText("Latest explanation");
  await expect(detail).not.toContainText("Select a cell");
});
