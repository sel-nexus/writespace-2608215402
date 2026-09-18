import { expect, test } from '@playwright/test';

test('an authenticated writer creates, edits, and deletes a server-backed note', async ({ page }) => {
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => consoleErrors.push(error.message));

  const title = `Writer note ${Date.now()}`;
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.getByRole('link', { name: 'Write' }).click();
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Note').fill('Created across the real API boundary.');
  await page.getByRole('button', { name: 'Publish note' }).click();
  await expect(page.getByRole('heading', { name: title })).toBeVisible();

  await page.getByRole('link', { name: 'Edit note' }).click();
  await page.getByLabel('Title').fill(`${title} revised`);
  await page.getByRole('button', { name: 'Save changes' }).click();
  await expect(page.getByRole('heading', { name: `${title} revised` })).toBeVisible();

  await page.getByRole('button', { name: 'Delete note' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Delete note' }).click();
  await expect(page).toHaveURL(/\/blogs$/);
  expect(consoleErrors).toEqual([]);
});
