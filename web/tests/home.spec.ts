import { expect, test } from "@playwright/test";

test("home loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /SkillScope/i })).toBeVisible();
});

test("demo loads", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText(/Sample dataset/i)).toBeVisible();
});

test("studio loads", async ({ page }) => {
  await page.goto("/studio");
  await expect(page.getByRole("heading", { name: /timeline replay/i })).toBeVisible();
});

test("studio demo comparison shows insights", async ({ page }) => {
  await page.goto("/studio");
  await page.getByRole("button", { name: /load demo runs/i }).click();
  await expect(page.getByText(/Run summary/i)).toBeVisible();
  await expect(page.getByRole("heading", { name: /Likely root causes/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Missing skills detected/i })).toBeVisible();
});
