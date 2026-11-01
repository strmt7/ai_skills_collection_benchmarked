'use strict';

const http = require('node:http');
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');

const SOURCE_HASHES = new Set([
  'f84ae93c159bf6ecef5a60c9735dc82d96bc5f977ef52eb71678b66722acf684',
  '8cfa22c35e5370c1f85400921d27e259cc99ba67a890625412bf2fc650a1d038',
]);
const OVERLAY_HASH = '997802fae03fb670386398ea342fe4434c11960e3f34388f505fc5d38ed22abd';
const SOURCE_LINES = "    await this.searchInput.fill(query)\n" +
  "    await this.page.waitForResponse(resp => resp.url().includes('/api/search'))";
const ORDERED_LINES = "    await Promise.all([this.page.waitForResponse(resp => resp.url().includes('/api/search')), " +
  'this.searchInput.fill(query)])';

function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

function readNormalized(file) {
  return fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n');
}

function extractMethods(source, overlay) {
  const sourceMatch = source.match(/  async search\(query: string\) \{\n([\s\S]*?)\n  \}/);
  const overlayMatch = overlay.match(/async search\(query: string\) \{\n([\s\S]*?)\n\}/);
  if (!sourceMatch || !overlayMatch || sourceMatch[1].split(SOURCE_LINES).length !== 2) {
    throw new Error('Expected source or overlay method not found');
  }
  // Only the hash-checked method bodies above are executed; the TypeScript
  // parameter annotation is removed when building these JavaScript functions.
  const compile = body => new Function('query', `return (async function(query) {${body}\n}).call(this, query)`);
  return {
    original: compile(sourceMatch[1]),
    ordering_only: compile(sourceMatch[1].replace(SOURCE_LINES, ORDERED_LINES)),
    overlay: compile(overlayMatch[1]),
  };
}

async function main() {
  if (process.argv.length !== 5) {
    throw new Error('Usage: node control.cjs SOURCE_SKILL OVERLAY_SKILL INSTALL_DIRECTORY');
  }
  const source = readNormalized(process.argv[2]);
  const overlay = readNormalized(process.argv[3]);
  const sourceHash = sha256(source);
  const overlayHash = sha256(overlay);
  if (!SOURCE_HASHES.has(sourceHash) || overlayHash !== OVERLAY_HASH) {
    throw new Error('Source or overlay does not match the reviewed content');
  }
  const methods = extractMethods(source, overlay);
  const install = path.resolve(process.argv[4]);
  const packageRoot = path.join(install, 'node_modules', '@playwright', 'test');
  const { chromium, expect } = require(packageRoot);
  const lockHash = sha256(fs.readFileSync(path.join(install, 'package-lock.json')));
  let served = 0;
  const server = http.createServer((req, res) => {
    if (req.url.startsWith('/api/search')) {
      served += 1;
      const query = new URL(req.url, 'http://localhost').searchParams.get('q');
      res.writeHead(query === 'bad-status' ? 500 : 200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ query }));
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`<input data-testid="search-input"><p data-testid="results"></p>
      <script>document.querySelector('input').addEventListener('input', e => {
        fetch('/api/search?q=' + encodeURIComponent(e.target.value))
          .then(r => r.json()).then(v => document.querySelector('p').textContent = v.query);
        const end = performance.now() + 100;
        while (performance.now() < end) {}
      })</script>`);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    page.setDefaultTimeout(1200);
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    const context = { page, searchInput: page.locator('[data-testid="search-input"]') };
    const names = Object.keys(methods);
    const counts = Object.fromEntries(names.map(name => [name, { passed: 0, timed_out: 0 }]));
    for (let i = 0; i < 10; i += 1) {
      for (let j = 0; j < names.length; j += 1) {
        const name = names[(i + j) % names.length];
        const query = `${name}${i}`;
        try {
          await methods[name].call(context, query);
          if (name === 'overlay') await expect(page.getByTestId('results')).toHaveText(query);
          counts[name].passed += 1;
        } catch (error) {
          if (error.name !== 'TimeoutError' || !error.message.includes('waitForResponse')) throw error;
          counts[name].timed_out += 1;
        }
      }
    }
    let rejectedBadStatus = false;
    try {
      await methods.overlay.call(context, 'bad-status');
    } catch (error) {
      if (error.message !== 'Search failed: 500') throw error;
      rejectedBadStatus = true;
    }
    if (served !== 31 || !rejectedBadStatus) throw new Error(`Unexpected server evidence: ${served}`);
    console.log(JSON.stringify({
      source_sha256: sourceHash,
      overlay_sha256: overlayHash,
      lock_sha256: lockHash,
      served,
      platform: process.platform,
      arch: process.arch,
      node: process.version,
      playwright: require(path.join(packageRoot, 'package.json')).version,
      browser: browser.version(),
      counts,
      rejected_bad_status: rejectedBadStatus,
      agent_efficacy_scored: false,
    }, null, 2));
  } finally {
    try {
      if (browser) await browser.close();
    } finally {
      await new Promise(resolve => server.close(resolve));
    }
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
