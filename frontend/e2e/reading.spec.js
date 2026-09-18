import { expect, test } from '@playwright/test';

function captureBrowserProblems(page) {
  const problems = [];
  page.on('console', (message) => { if (message.type() === 'error' && !message.text().includes('Warning: Failed %s type:')) problems.push(`console: ${message.text()}`); });
  page.on('pageerror', (error) => problems.push(`pageerror: ${error.message}`));
  return problems;
}

test('a mobile reader opens server-sourced library content through visible links', async ({ page }) => {
  const consoleErrors = captureBrowserProblems(page);
  await page.setViewportSize({ width: 390, height: 844 });

  const title = `Mobile reader note ${Date.now()}`;
  const content = 'A server-backed note created for the mobile reading journey.';

  await page.goto('/login');
  const login = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200);
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Log in' }).click();
  await login;
  await page.getByRole('link', { name: 'Write', exact: true }).click();
  const created = page.waitForResponse((response) => response.url().endsWith('/api/posts') && response.request().method() === 'POST' && response.status() === 201);
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Note', { exact: true }).fill(content);
  await page.getByRole('button', { name: 'Publish note' }).click();
  const createResponse = await created;
  const createdPost = await createResponse.json();
  expect(createdPost.title).toBe(title);
  expect(createdPost.content).toBe(content);
  await expect(page.getByRole('heading', { name: title })).toBeVisible();

  const library = page.waitForResponse((response) => response.url().includes('/api/posts?limit=100') && response.status() === 200);
  await page.getByRole('link', { name: 'Library', exact: true }).click();
  const libraryResponse = await library;
  const posts = await libraryResponse.json();
  expect(posts).toEqual(expect.arrayContaining([expect.objectContaining({ title, content })]));
  const post = page.waitForResponse((response) => /\/api\/posts\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(new URL(response.url()).pathname) && response.status() === 200);
  await page.getByRole('link', { name: `Read ${title}` }).click();
  const postResponse = await post;
  const fetchedPost = await postResponse.json();
  expect(fetchedPost).toMatchObject({ title, content });
  await expect(page.getByRole('heading', { name: title })).toBeVisible();
  await expect(page.locator('.post-content')).toContainText(content);
  expect(consoleErrors).toEqual([]);
});
