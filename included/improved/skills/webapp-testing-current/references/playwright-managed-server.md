# A Playwright-managed local server

Use the example with a locked Playwright Test project that provides a
`test:serve` command. The command starts the intended application and reads
`APP_TEST_ORIGIN` and `APP_TEST_INSTANCE` from its environment. Supply an
isolated local origin and a fresh nonsecret instance value.

1. Copy or merge the [runner configuration](../assets/playwright.config.cjs).
   Its readiness URL is `/health/ready`. Replace it with the project's actual
   endpoint or equivalent condition and set a startup deadline for that app.
2. Adapt the [instance check](../assets/preview-health.spec.cjs). Its example
   expects HTTP 200 and a response body with the correct application and
   instance identity. Use a stable application marker or an isolated
   endpoint that your test can verify.
3. Run the project's locked test command in a run-owned workspace. Inspect
   the first failure, preserve useful startup output, and verify that the
   owned server and workers stopped. Start with one worker while qualifying
   startup.

The example keeps startup errors on stderr. If diagnosis requires stdout,
pipe it to a runner that can retain bounded logs. Test process-tree cleanup
on the actual operating system before using the configuration as a reusable
supervisor. [Playwright web server configuration](https://playwright.dev/docs/test-webserver)
