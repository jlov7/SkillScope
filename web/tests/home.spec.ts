import { expect, test } from "@playwright/test";

test("home loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /SkillScope/i })).toBeVisible();
});

test("demo loads", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText(/Sample dataset/i)).toBeVisible();
});
