import { expect, test } from '@playwright/test';

function captureBrowserProblems(page) {
  const problems = [];
  page.on('console', (message) => { if (message.type() === 'error' && !message.text().includes('Warning: Failed %s type:')) problems.push(`console: ${message.text()}`); });
  page.on('pageerror', (error) => problems.push(`pageerror: ${error.message}`));
  return problems;
}

test('an authenticated writer sees empty-submission feedback and creates, edits, and deletes a server-backed note', async ({ page }, testInfo) => {
  const consoleErrors = captureBrowserProblems(page);
  const title = `Writer note ${Date.now()}`;

  await page.goto('/login');
  const login = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200);
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  await login;
  await page.getByRole('link', { name: 'Write', exact: true }).click();
  await expect(page.getByLabel('Title').evaluate((input) => input.checkValidity())).resolves.toBe(false);
  await expect(page.getByLabel('Note', { exact: true }).evaluate((input) => input.checkValidity())).resolves.toBe(false);

  const created = page.waitForResponse((response) => response.url().endsWith('/api/posts') && response.request().method() === 'POST' && response.status() === 201);
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Note', { exact: true }).fill('Created across the real API boundary.');
  await page.getByRole('button', { name: 'Publish note' }).click();
  await created;
  await expect(page.getByRole('heading', { name: title })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('writer-post.png'), fullPage: true });

  await page.getByRole('link', { name: 'Edit note' }).click();
  await page.getByLabel('Title').fill(`${title} revised`);
  const updated = page.waitForResponse((response) => /\/api\/posts\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(new URL(response.url()).pathname) && response.request().method() === 'PUT' && response.status() === 200);
  await page.getByRole('button', { name: 'Save changes' }).click();
  await updated;
  await expect(page.getByRole('heading', { name: `${title} revised` })).toBeVisible();

  await page.getByRole('button', { name: 'Delete note' }).click();
  const deleted = page.waitForResponse((response) => /\/api\/posts\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(new URL(response.url()).pathname) && response.request().method() === 'DELETE' && response.status() === 204);
  await page.getByRole('dialog').getByRole('button', { name: 'Delete note' }).click();
  await deleted;
  await expect(page).toHaveURL(/\/blogs$/);
  expect(consoleErrors).toEqual([]);
});
