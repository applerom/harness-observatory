import { expect, test } from "@playwright/test";

test("matrix has top scroll affordance and reveals clicked cell detail", async ({ page }) => {
  await page.goto("/matrix");

  const topScroll = page.getByTestId("matrix-scroll-top");
  const mainScroll = page.getByTestId("matrix-scroll-main");
  await expect(topScroll).toBeVisible();
  await expect(mainScroll).toBeVisible();

  await topScroll.evaluate((element) => {
    element.scrollLeft = 320;
    element.dispatchEvent(new Event("scroll"));
  });
  await expect.poll(async () => mainScroll.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);

  const detail = page.locator("#matrix-cell-detail");
  const cell = page.getByTestId("matrix-cell-opencode-instruction-files");
  await expect(cell).toBeVisible();
  await cell.click();

  await expect(detail).toContainText("Expanded cell");
  await expect
    .poll(async () =>
      detail.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        return rect.top < window.innerHeight - 120 && rect.bottom > 120;
      }),
    )
    .toBe(true);
});
