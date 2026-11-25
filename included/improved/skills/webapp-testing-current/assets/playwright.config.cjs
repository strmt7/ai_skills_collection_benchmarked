const { defineConfig } = require('@playwright/test');

const origin = process.env.APP_TEST_ORIGIN;
if (!origin) throw new Error('Set APP_TEST_ORIGIN to the application test origin.');

module.exports = defineConfig({
  workers: 1,
  use: { baseURL: origin },
  webServer: {
    command: 'npm run test:serve',
    url: new URL('/health/ready', origin).href,
    reuseExistingServer: false,
    timeout: 10_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
