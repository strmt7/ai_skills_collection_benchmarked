/** Owned localhost browser controls; all external resource requests are blocked. */
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdtemp, unlink, rmdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: {
  'package-root': { type: 'string' }, 'browser-cache': { type: 'string' },
  'fixture-root': { type: 'string' }, output: { type: 'string' },
} });
for (const name of ['package-root', 'browser-cache', 'fixture-root', 'output'])
  if (!values[name]) throw new Error(`Explicit ${name} required`);
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(values['browser-cache']);
const require = createRequire(resolve(values['package-root'], 'package.json'));
const { chromium, expect } = require('@playwright/test');
const manifest = JSON.parse(await readFile(resolve(values['fixture-root'], 'manifest.json'), 'utf8'));
const fixtures = {};
for (const [name, digest] of Object.entries(manifest.fixture_sha256)) {
  if (!/^[a-z-]+\.html$/.test(name)) throw new Error('Unsafe fixture name');
  const data = await readFile(resolve(values['fixture-root'], name));
  if (createHash('sha256').update(data).digest('hex') !== digest) throw new Error('Fixture changed');
  fixtures[name] = data;
}
let feedbackStatus = 200;
const posts = [];
const server = createServer((request, response) => {
  const url = new URL(request.url, 'http://owned-fixture.invalid');
  if (url.pathname === '/api/feedback') {
    let body = '';
    request.on('data', chunk => { body += chunk; });
    request.on('end', () => {
      if (request.method === 'POST') posts.push(JSON.parse(body));
      response.writeHead(request.method === 'POST' ? feedbackStatus : 200,
        { 'content-type': 'application/json' });
      response.end('{}');
    });
  } else if (fixtures[url.pathname.slice(1)]) {
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    response.end(fixtures[url.pathname.slice(1)]);
  } else { response.writeHead(404); response.end('Owned missing resource'); }
});
await new Promise((done, reject) => {
  server.once('error', reject); server.listen(0, '127.0.0.1', done);
});
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
let report;
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ serviceWorkers: 'block' });
  let blockedExternalRequests = 0;
  await context.route('**/*', route => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    blockedExternalRequests++; return route.abort();
  });
  const checks = {};
  const page = await context.newPage();
  await page.goto(`${origin}/normal.html`);
  await expect(page.locator('#prompt-text')).toHaveText('Owned normal prompt');
  await expect(page.locator('#outputs-body pre')).toHaveText('Owned text with <tag> characters');
  checks.normal_text_rendered_literally = true;
  for (const name of ['script-boundary', 'metadata', 'grading-count', 'evidence-attribute']) {
    await page.goto(`${origin}/${name}.html`);
    if (name === 'evidence-attribute') {
      await page.getByRole('button', { name: 'Benchmark', exact: true }).click();
      await page.locator('#benchmark-content span[title]').hover();
    }
    await page.waitForFunction(name => globalThis.__OWNED_REVIEW_CONTROL__ === name, name, { timeout: 3000 });
    checks[`${name.replaceAll('-', '_')}_executes_owned_sentinel`] = true;
  }
  feedbackStatus = 500;
  await page.goto(`${origin}/normal.html`);
  await page.locator('#feedback').fill('Owned unsaved feedback');
  const failedResponse = page.waitForResponse(r => r.url() === `${origin}/api/feedback` && r.request().method() === 'POST');
  await page.evaluate(() => saveCurrentFeedback());
  if ((await failedResponse).status() !== 500) throw new Error('Expected controlled HTTP failure');
  await expect(page.locator('#feedback-status')).toHaveText('Saved');
  checks.http_error_feedback_claims_saved = true;
  feedbackStatus = 200;
  await page.goto(`${origin}/two-runs.html`);
  if (await page.evaluate(() => visitedRuns.size) !== 1) throw new Error('Second run was already visited');
  const completeResponse = page.waitForResponse(r => r.url() === `${origin}/api/feedback` && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Submit All Reviews', exact: true }).click();
  await completeResponse;
  const complete = posts.findLast(p => p.status === 'complete');
  if (complete?.reviews.length !== 2 || !complete.reviews.every(r => r.feedback === ''))
    throw new Error('Expected completion rows for an unvisited run');
  checks.unvisited_run_marked_complete_with_empty_feedback = true;
  await page.goto(`${origin}/safe-offline.html`);
  const hostileText = '</script><img src="/owned-missing" onerror="globalThis.__OWNED_REVIEW_CONTROL__=1"><script>';
  await expect(page.locator('section').first().locator('pre').first()).toHaveText(hostileText);
  if (await page.evaluate(() => globalThis.__OWNED_REVIEW_CONTROL__) !== undefined)
    throw new Error('Safe viewer executed candidate markup');
  if (await page.locator('img').count() !== 0 || await page.locator('script').count() !== 1)
    throw new Error('Candidate markup changed active elements');
  checks.safe_overlay_renders_hostile_text_without_execution = true;
  const downloads = await mkdtemp(join(tmpdir(), 'owned-review-download-'));
  try {
    const exportFeedback = async name => {
      const pending = page.waitForEvent('download');
      await page.getByRole('button', { name: 'Export feedback', exact: true }).click();
      const download = await pending;
      if (download.suggestedFilename() !== 'feedback.json') throw new Error('Unexpected download name');
      const target = join(downloads, name);
      await download.saveAs(target);
      return JSON.parse(await readFile(target, 'utf8'));
    };
    const untouched = await exportFeedback('untouched.json');
    if (untouched.status !== 'in_progress' || !untouched.reviews.every(r => !r.reviewed && r.verdict === 'pending'))
      throw new Error('Safe viewer confused unreviewed with acceptable');
    await page.locator('select').first().selectOption('acceptable');
    await page.locator('textarea').first().fill('Owned exact feedback\nwith a second line');
    const partial = await exportFeedback('partial.json');
    if (partial.status !== 'in_progress' || partial.reviews[0].feedback !== 'Owned exact feedback\nwith a second line'
        || !partial.reviews[0].reviewed || partial.reviews[1].reviewed
        || partial.reviews[0].run_id !== 'owned" data-extra="changed') throw new Error('Partial feedback changed');
    checks.safe_overlay_preserves_ids_feedback_and_unreviewed_state = true;
    await page.locator('select').nth(1).selectOption('needs_change');
    const completeSafe = await exportFeedback('complete.json');
    if (completeSafe.status !== 'complete' || !completeSafe.reviews.every(r => r.reviewed)
        || completeSafe.reviews[1].verdict !== 'needs_change') throw new Error('Explicit completed feedback changed');
    checks.safe_overlay_completion_requires_all_explicit_reviews = true;
  } finally {
    for (const name of ['untouched.json', 'partial.json', 'complete.json']) {
      try { await unlink(join(downloads, name)); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
    }
    await rmdir(downloads);
  }
  await context.close();
  report = { schema_version: 1, evidence_class: 'actual-local-skill-review-browser-controls',
    node_version: process.version, playwright_version: require('@playwright/test/package.json').version,
    browser_version: browser.version(), checks, all_controls_passed: Object.values(checks).every(Boolean),
    blocked_external_resource_requests: blockedExternalRequests, external_requests_allowed: 0,
    fixture_manifest: manifest,
    reproducer_sha256: createHash('sha256').update(await readFile(fileURLToPath(import.meta.url))).digest('hex'),
    agent_efficacy_scored: false,
    scope: 'Owned localhost fixture, real Chromium, inert sentinels and controlled feedback server. No original port-killing helper, credentials, live providers or model sessions.' };
} finally {
  if (browser) await browser.close();
  await new Promise(done => { server.close(done); server.closeIdleConnections(); });
}
for (const [name, digest] of Object.entries(manifest.fixture_sha256))
  if (createHash('sha256').update(await readFile(resolve(values['fixture-root'], name))).digest('hex') !== digest)
    throw new Error('Fixture changed during controls');
await writeFile(values.output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ all_controls_passed: report.all_controls_passed, checks: report.checks }) + '\n');
if (!report.all_controls_passed) process.exitCode = 1;
