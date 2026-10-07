/** Local deterministic scheduling controls; no live sites or agent scores. */
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { resolve, dirname } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

const { values } = parseArgs({ options: {
  'package-root': { type: 'string' },
  'browser-cache': { type: 'string' },
  output: { type: 'string' },
}});
if (!values['package-root'] || !values['browser-cache'] || !values.output)
  throw new Error('Explicit package root, browser cache and new output path required');
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(values['browser-cache']);
const require = createRequire(resolve(values['package-root'], 'package.json'));
const { chromium, expect, errors } = require('@playwright/test');
const packageVersion = require('@playwright/test/package.json').version;
const html = `<!doctype html><label>Search<input aria-label="Search"></label>
<ul aria-label="Search results"></ul><script>
document.querySelector('input').addEventListener('input', async event => {
  const response = await fetch('/api/search?q=' + encodeURIComponent(event.target.value));
  const data = await response.json();
  document.querySelector('ul').replaceChildren(...data.map(text => {
    const row = document.createElement('li'); row.textContent = text; return row;
  }));
});
window.pollTimer = setInterval(() => fetch('/poll').catch(() => {}), 100);
</script>`;
const server = createServer((request, response) => {
  const url = new URL(request.url, 'http://fixture.invalid');
  if (url.pathname === '/api/search') {
    const query = url.searchParams.get('q');
    const rows = query === 'slow' ? ['slow one', 'slow two', 'slow three'] : [query + ' result'];
    setTimeout(() => {
      response.writeHead(200, { 'content-type': 'application/json' });
      response.end(JSON.stringify(rows));
    }, query === 'slow' ? 600 : 0);
  } else if (url.pathname === '/poll') {
    setTimeout(() => response.end('poll'), 350);
  } else {
    response.writeHead(200, { 'content-type': 'text/html' });
    response.end(html);
  }
});
await new Promise((done, reject) => {
  server.once('error', reject); server.listen(0, '127.0.0.1', done);
});
const origin = 'http://127.0.0.1:' + server.address().port;
let browser;
let report;
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  let blockedExternalRequests = 0;
  await context.route('**/*', async route => {
    if (new URL(route.request().url()).origin === origin) await route.continue();
    else { blockedExternalRequests++; await route.abort(); }
  });
  const page = await context.newPage();
  await page.goto(origin);
  const input = page.getByRole('textbox', { name: 'Search' });
  const results = page.getByRole('list', { name: 'Search results' });
  await input.fill('first');
  await expect(results).toHaveText('first result');
  let lateWaitTimedOut = false;
  try {
    await page.waitForResponse(response => new URL(response.url()).pathname === '/api/search', { timeout: 100 });
  } catch (error) {
    if (!(error instanceof errors.TimeoutError)) throw error;
    lateWaitTimedOut = true;
  }
  const responsePromise = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === '/api/search' && url.searchParams.get('q') === 'second'
      && response.request().method() === 'GET' && response.status() === 200;
  }, { timeout: 2000 });
  await input.fill('second');
  await responsePromise;
  await expect(results).toHaveText('second result');
  await input.fill('slow');
  const immediateCount = await results.getByRole('listitem').count();
  await expect(results.getByRole('listitem')).toHaveCount(3, { timeout: 3000 });
  let networkIdleTimedOut = false;
  try { await page.waitForLoadState('networkidle', { timeout: 1500 }); }
  catch (error) {
    if (!(error instanceof errors.TimeoutError)) throw error;
    networkIdleTimedOut = true;
  }
  await expect(results).toHaveText('slow oneslow twoslow three');
  await page.evaluate(() => clearInterval(window.pollTimer));
  const checks = {
    late_subscription_misses_completed_response: lateWaitTimedOut,
    prearmed_query_matched_response_and_ui: true,
    immediate_count_is_stale: immediateCount === 1,
    web_assertion_waits_for_complete_results: true,
    network_idle_fails_while_ui_ready: networkIdleTimedOut,
    no_external_requests: blockedExternalRequests === 0,
  };
  report = {
    schema_version: 1, evidence_class: 'local-playwright-scheduling-controls',
    node_version: process.version, playwright_version: packageVersion,
    browser_version: browser.version(), checks, all_controls_passed: Object.values(checks).every(Boolean),
    reproducer_sha256: createHash('sha256').update(await readFile(fileURLToPath(import.meta.url))).digest('hex'),
    scope: 'Actual headless Chromium and localhost scheduling controls. Late subscription is tested after known response completion; it demonstrates a valid missed-event schedule, not universal failure of every fill-then-wait sequence. No production operations, browser benchmark or agent efficacy score.',
  };
  await context.close();
} finally {
  if (browser) await browser.close();
  await new Promise(done => { server.close(done); server.closeIdleConnections(); });
}
await mkdir(dirname(resolve(values.output)), { recursive: true });
await writeFile(values.output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ all_controls_passed: report.all_controls_passed, checks: report.checks }) + '\n');
if (!report.all_controls_passed) process.exitCode = 1;
