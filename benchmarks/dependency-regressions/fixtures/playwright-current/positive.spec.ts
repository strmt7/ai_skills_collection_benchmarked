import { defineConfig, expect, type Page } from '@playwright/test';
defineConfig({ outputDir: 'artifacts', use: { video: 'retain-on-failure', trace: 'retain-on-failure' } });
export async function search(page: Page, query: string) {
  const responsePromise = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === '/api/search' && url.searchParams.get('q') === query && response.status() === 200;
  });
  await page.getByRole('textbox', { name: 'Search' }).fill(query);
  await responsePromise;
  await expect(page.getByRole('list', { name: 'Search results' })).toContainText(query);
}
