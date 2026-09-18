import { expect, test } from '@playwright/test';

function captureBrowserProblems(page) {
  const problems = [];
  page.on('console', (message) => { if (message.type() === 'error' && !message.text().includes('Warning: Failed %s type:')) problems.push(`console: ${message.text()}`); });
  page.on('pageerror', (error) => problems.push(`pageerror: ${error.message}`));
  return problems;
}

test('redirects a guest from the protected library, rejects invalid login, then restores the intended route after registration', async ({ page }) => {
  const errors = captureBrowserProblems(page);
  const username = `reader${Date.now()}`;

  await page.goto('/blogs');
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('heading', { name: 'Log in' })).toBeVisible();

  const failedLogin = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 401);
  await page.getByLabel('Username').fill('not-a-real-reader');
  await page.getByLabel('Password').fill('incorrect-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await failedLogin;
  await expect(page.getByRole('alert')).toContainText(/invalid|incorrect|credentials/i);
  await expect.poll(() => errors.filter((error) => !error.includes('status of 401 (Unauthorized)'))).toEqual([]);
  errors.length = 0;

  await page.getByRole('main').getByRole('link', { name: 'Register', exact: true }).click();
  const registered = page.waitForResponse((response) => response.url().includes('/api/auth/register') && response.status() === 201);
  await page.getByLabel('Display name').fill('E2E Reader');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password', { exact: true }).fill('reader-pass-123');
  await page.getByLabel('Confirm password').fill('reader-pass-123');
  await page.getByRole('button', { name: 'Create account' }).click();
  await registered;
  await expect(page).toHaveURL(/\/$/);
  await page.getByRole('link', { name: 'Library' }).click();
  await expect(page.getByRole('heading', { name: 'Reading room' })).toBeVisible();
  await page.getByRole('button', { name: 'Log out' }).click();
  await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
  expect(errors).toEqual([]);
});
