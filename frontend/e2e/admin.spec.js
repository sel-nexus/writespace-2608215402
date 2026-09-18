import { expect, test } from '@playwright/test';

function captureBrowserProblems(page) {
  const problems = [];
  page.on('console', (message) => { if (message.type() === 'error' && !message.text().includes('Warning: Failed %s type:')) problems.push(`console: ${message.text()}`); });
  page.on('pageerror', (error) => problems.push(`pageerror: ${error.message}`));
  return problems;
}

test('an administrator overrides another author post and deletes the eligible author while attribution remains', async ({ page }, testInfo) => {
  const consoleErrors = captureBrowserProblems(page);
  const suffix = Date.now();
  const username = `managed${suffix}`;
  const displayName = `Managed ${suffix}`;
  const originalTitle = `Contributor note ${suffix}`;
  const revisedTitle = `${originalTitle} revised by admin`;

  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  const stats = page.waitForResponse((response) => response.url().includes('/api/admin/stats') && response.status() === 200);
  await page.getByRole('link', { name: 'Admin' }).click();
  await stats;
  await expect(page.getByRole('heading', { name: 'Writing room overview' })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('admin-overview.png'), fullPage: true });

  await page.getByRole('link', { name: 'Manage accounts' }).click();
  await page.getByLabel('Display name').fill(displayName);
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill('managed-password-123');
  const accountCreated = page.waitForResponse((response) => response.url().endsWith('/api/users') && response.request().method() === 'POST' && response.status() === 201);
  await page.getByRole('button', { name: 'Create account' }).click();
  await accountCreated;
  await expect(page.getByRole('status')).toContainText('was created');

  await page.getByRole('button', { name: 'Log out' }).click();
  await page.getByRole('link', { name: 'Log in', exact: true }).click();
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill('managed-password-123');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.getByRole('link', { name: 'Write', exact: true }).click();
  await page.getByLabel('Title').fill(originalTitle);
  await page.getByLabel('Note', { exact: true }).fill('An eligible contributor wrote this live API post.');
  await page.getByRole('button', { name: 'Publish note' }).click();
  await expect(page.getByRole('heading', { name: originalTitle })).toBeVisible();

  await page.getByRole('button', { name: 'Log out' }).click();
  await page.getByRole('link', { name: 'Log in', exact: true }).click();
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.getByRole('link', { name: 'Library' }).click();
  await page.getByRole('link', { name: `Read ${originalTitle}` }).click();
  await page.getByRole('link', { name: 'Edit note' }).click();
  await page.getByLabel('Title').fill(revisedTitle);
  const overridden = page.waitForResponse((response) => /\/api\/posts\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(new URL(response.url()).pathname) && response.request().method() === 'PUT' && response.status() === 200);
  await page.getByRole('button', { name: 'Save changes' }).click();
  await overridden;
  await expect(page.getByRole('heading', { name: revisedTitle })).toBeVisible();
  await expect(page.getByText(`By ${displayName}`)).toBeVisible();

  await page.getByRole('link', { name: 'Users' }).click();
  await page.getByRole('button', { name: `Delete ${username}` }).click();
  const deleted = page.waitForResponse((response) => /\/api\/users\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(new URL(response.url()).pathname) && response.request().method() === 'DELETE' && response.status() === 204);
  await page.getByRole('dialog').getByRole('button', { name: 'Delete account' }).click();
  await deleted;
  await expect(page.getByRole('status')).toContainText('Existing notes keep their attribution.');
  await page.getByRole('link', { name: 'Library' }).click();
  await page.getByRole('link', { name: `Read ${revisedTitle}` }).click();
  await expect(page.getByText(`By ${displayName}`)).toBeVisible();
  expect(consoleErrors).toEqual([]);
});
