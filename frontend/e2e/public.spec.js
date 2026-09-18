import { expect, test } from '@playwright/test';

test('shows a backend-sourced public preview without browser errors', async ({ page }) => {
  const browserProblems = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      browserProblems.push(`console: ${message.text()}`);
    }
  });
  page.on('pageerror', (error) => {
    browserProblems.push(`pageerror: ${error.message}`);
  });

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Latest notes' })).toBeVisible();
  const preview = page.locator('.blog-card').filter({ hasNot: page.locator('.skeleton-card') }).first();
  await expect(preview).toBeVisible();
  await expect(preview.getByRole('heading')).not.toHaveText('');
  await expect(preview.locator('p').last()).not.toHaveText('');
  expect(browserProblems).toEqual([]);
});
