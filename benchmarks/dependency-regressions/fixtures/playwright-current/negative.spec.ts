import { defineConfig, type Browser, type Page } from '@playwright/test';
defineConfig({ use: { video: 'retain-on-failure', videosPath: 'artifacts/videos/' } });
export async function invalidTracing(browser: Browser, page: Page) {
  await browser.startTracing(page, { path: 'artifacts/trace.json', screenshots: true, snapshots: true });
}
