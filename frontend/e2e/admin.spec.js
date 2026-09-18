import { expect, test } from '@playwright/test';

test('an administrator sees backend statistics and manages a user', async ({ page }) => {
  const consoleErrors = [];
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('pageerror', (error) => consoleErrors.push(error.message));
  const suffix = Date.now();
  const username = `adminmanaged${suffix}`;

  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.getByRole('link', { name: 'Admin' }).click();
  await expect(page.getByRole('heading', { name: 'Writing room overview' })).toBeVisible();
  await expect(page.getByLabel(/Total accounts:/)).toBeVisible();

  await page.getByRole('link', { name: 'Users' }).click();
  await page.getByLabel('Display name').fill(`Managed ${suffix}`);
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill('managed-password-123');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('status')).toContainText('was created');
  await expect(page.getByText(username)).toBeVisible();
  await page.getByRole('button', { name: `Deactivate ${username}` }).click();
  await expect(page.getByRole('status')).toContainText('was deactivated');
  expect(consoleErrors).toEqual([]);
});
