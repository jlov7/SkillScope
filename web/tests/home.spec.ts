import { expect, test } from "@playwright/test";

test("home loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /SkillScope/i })).toBeVisible();
});

test("demo loads", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText(/Sample dataset/i)).toBeVisible();
});

test("start page loads", async ({ page }) => {
  await page.goto("/start");
  await expect(page.getByRole("heading", { name: /60 seconds/i })).toBeVisible();
});

test("why page loads", async ({ page }) => {
  await page.goto("/why");
  await expect(page.getByRole("heading", { name: /how it works/i })).toBeVisible();
});

test("demo kit page loads", async ({ page }) => {
  await page.goto("/demo-kit");
  await expect(page.getByRole("heading", { name: /Presenter-ready scripts/i })).toBeVisible();
});

test("studio loads", async ({ page }) => {
  await page.goto("/studio");
  await expect(page.getByRole("heading", { name: /timeline replay/i })).toBeVisible();
});

test("studio deep link preloads guided demo", async ({ page }) => {
  await page.goto("/studio?demo=1&guide=1");
  await expect(page.getByRole("heading", { name: /Presenter Mode/i })).toBeVisible();
  await expect(page.getByText(/Deep link:/i)).toBeVisible();
  await expect(page.getByText(/Run summary/i)).toBeVisible();
});

test("studio includes in-app guide and help mechanics", async ({ page }) => {
  await page.goto("/studio?demo=1&guide=1");
  await expect(page.getByRole("heading", { name: /How to use Studio/i })).toBeVisible();
  await expect(page.getByText(/left\/right arrows to step/i)).toBeVisible();
  await page.getByRole("button", { name: /Jump to root causes/i }).click();
  await expect(page.getByRole("heading", { name: /Likely root causes/i })).toBeVisible();
});

test("studio demo comparison shows insights", async ({ page }) => {
  await page.goto("/studio");
  await page.getByRole("button", { name: /load demo runs/i }).click();
  await expect(page.getByText(/Run summary/i)).toBeVisible();
  await expect(page.getByRole("heading", { name: /Likely root causes/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Missing skills detected/i })).toBeVisible();
});
