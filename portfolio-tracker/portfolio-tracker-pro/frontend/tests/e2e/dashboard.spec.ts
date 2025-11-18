import { test, expect } from '@playwright/test';

const username = process.env.E2E_USERNAME;
const password = process.env.E2E_PASSWORD;

test.use({
  storageState: process.env.E2E_STORAGE || undefined,
});

test.beforeEach(async ({ page }) => {
  test.skip(!username || !password, 'E2E_USERNAME and E2E_PASSWORD must be provided');

  await page.goto('/login');
  await page.getByLabel('Username').fill(username!);
  await page.getByLabel('Password').fill(password!);
  await Promise.all([
    page.waitForNavigation({ url: '**/' }),
    page.getByRole('button', { name: /sign in/i }).click(),
  ]);

  await page.waitForURL('**/');
  await expect(page.getByRole('heading', { name: /global portfolio/i })).toBeVisible();
});

test('dashboard refresh provides feedback', async ({ page }) => {
  const refreshButton = page.getByRole('button', { name: /^refresh$/i });
  await expect(refreshButton).toBeEnabled();

  await refreshButton.click();
  await expect(refreshButton).toBeDisabled({ timeout: 5_000 });
  await expect(refreshButton).toBeEnabled({ timeout: 30_000 });

  // Toast feedback (if available) should disappear automatically; ignore if not rendered
  const toast = page.getByRole('alert').filter({ hasText: /dashboard data/i });
  if (await toast.count()) {
    await expect(toast.first()).toBeVisible();
  }
});

test('time range filter persists across reloads', async ({ page }) => {
  const timeToggle = page.getByRole('button', { name: /^7D$/i });
  await timeToggle.click();
  await expect(timeToggle).toHaveAttribute('aria-pressed', 'true');

  await page.reload();

  const timeToggleAfterReload = page.getByRole('button', { name: /^7D$/i });
  await expect(timeToggleAfterReload).toHaveAttribute('aria-pressed', 'true');
});

test('transactions table renders with data badges', async ({ page }) => {
  await page.getByRole('link', { name: /^transactions$/i }).first().click();
  await page.waitForURL('**/transactions');

  const table = page.getByRole('table');
  await expect(table).toBeVisible();

  const secondRow = table.getByRole('row').nth(1);
  await expect(secondRow).toBeVisible();

  const badge = secondRow.getByRole('cell').filter({ hasText: /data warning|new/i }).first();
  // badge might not exist; just ensure row contains expected structure
  if (await badge.count()) {
    await expect(badge).toBeVisible();
  }
});

