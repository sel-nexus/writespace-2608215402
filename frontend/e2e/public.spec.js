import { expect, test } from '@playwright/test';

function captureBrowserProblems(page) {
  const problems = [];
  page.on('console', (message) => { if (message.type() === 'error' && !message.text().includes('Warning: Failed %s type:')) problems.push(`console: ${message.text()}`); });
  page.on('pageerror', (error) => problems.push(`pageerror: ${error.message}`));
  return problems;
}

test('shows backend-sourced public previews and the deterministic empty state when setup is still empty', async ({ page }, testInfo) => {
  const browserProblems = captureBrowserProblems(page);
  const previews = page.waitForResponse((response) => response.url().includes('/api/public/posts?limit=3') && response.status() === 200);

  await page.goto('/');
  const response = await previews;
  const payload = await response.json();
  expect(Array.isArray(payload)).toBe(true);
  if (payload.length === 0) {
    await expect(page.getByRole('heading', { name: 'No public notes have been filed yet.' })).toBeVisible();
  } else {
    await expect(page.locator('.blog-card').first().getByRole('heading', { name: payload[0].title })).toBeVisible();
  }
  const accessibilityTree = await page.accessibility.snapshot();
  expect(accessibilityTree).toMatchObject({ role: 'WebArea', name: expect.stringContaining('WriteSpace') });
  const renderedHtml = await page.content();
  expect(renderedHtml).toContain('hero-title');
  const fontFamily = await page.evaluate(() => getComputedStyle(document.body).fontFamily);
  expect(fontFamily).toContain('Source Sans 3');
  await page.screenshot({ path: testInfo.outputPath('public-reading.png'), fullPage: true });
  expect(browserProblems).toEqual([]);
});
