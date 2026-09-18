import { expect, test } from '@playwright/test';

test('a reader can register, log in, and log out without browser errors', async ({ page }) => {
  const errors = [];
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', (error) => errors.push(error.message));
  const username = `reader${Date.now()}`;
  await page.goto('/register');
  await page.getByLabel('Display name').fill('E2E Reader');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password', { exact: true }).fill('reader-pass-123');
  await page.getByLabel('Confirm password').fill('reader-pass-123');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
  await page.getByRole('button', { name: 'Log out' }).click();
  await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
  await page.goto('/login');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill('reader-pass-123');
  await page.getByRole('button', { name: 'Log in' }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
  expect(errors).toEqual([]);
});
