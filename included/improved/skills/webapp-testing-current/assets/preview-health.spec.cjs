const { expect, test } = require('@playwright/test');

test('the intended preview instance is ready', async ({ request }) => {
  const instance = process.env.APP_TEST_INSTANCE;
  if (!instance) throw new Error('Set APP_TEST_INSTANCE to a unique test value.');
  const reply = await request.get('/health/ready', { maxRedirects: 0, timeout: 5_000 });
  expect(reply.status()).toBe(200);
  expect(await reply.json()).toMatchObject({
    application: 'preview',
    instance,
    ready: true,
  });
});
