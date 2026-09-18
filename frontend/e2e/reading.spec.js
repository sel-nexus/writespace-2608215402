import { expect, test } from '@playwright/test';

test('an admin can read server-sourced library content', async ({ page }) => {
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => consoleErrors.push(error.message));

  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.getByRole('link', { name: 'Library' }).click();

  const firstTitle = page.locator('.blog-card h3').first();
  await expect(firstTitle).toBeVisible();
  const serverTitle = await firstTitle.textContent();
  await page.getByRole('link', { name: /Read / }).first().click();
  await expect(page.getByRole('heading', { name: serverTitle })).toBeVisible();
  await expect(page.locator('.post-content')).not.toBeEmpty();
  expect(consoleErrors).toEqual([]);
});
