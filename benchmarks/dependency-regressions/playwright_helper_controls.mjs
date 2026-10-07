/** Unchanged helper logic under controlled API doubles; actual executor children. */
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, writeFile, copyFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { runInNewContext } from 'node:vm';
import assert from 'node:assert/strict';

const { values } = parseArgs({ options: {
  'package-root': { type: 'string' }, 'upstream-root': { type: 'string' }, output: { type: 'string' },
}});
if (!values['package-root'] || !values['upstream-root'] || !values.output)
  throw new Error('Explicit installed package, verified upstream checkout and new receipt required');
const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const original = join(repo, 'included/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-browser-automation');
const upstream = resolve(values['upstream-root'], 'skills/playwright-skill');
const packageRequire = createRequire(resolve(values['package-root'], 'package.json'));
packageRequire.resolve('playwright'); // Prevent the old executor's implicit installer from running.
const inputs = {};
for (const [label, directory] of [['original', original], ['upstream', upstream]]) {
  inputs[label] = {};
  for (const name of ['SKILL.md', 'run.js', 'lib/helpers.js', 'package.json'])
    inputs[label][name] = createHash('sha256').update(await readFile(join(directory, name))).digest('hex');
}
const silentConsole = { log() {}, warn() {}, error() {} };
function loadHelpers(source, environment = {}) {
  const captures = [];
  const browsers = Object.fromEntries(['chromium', 'firefox', 'webkit'].map(name => [name, {
    async launch(options) { captures.push({ name, options }); return options; },
  }]));
  const module = { exports: {} };
  const normalRequire = createRequire(import.meta.url);
  const require = name => name === 'playwright' ? browsers : normalRequire(name);
  runInNewContext('(function(require,module,exports,process,console,setTimeout){' + source + '\n})', {})
    (require, module, module.exports, { env: environment, getuid: () => 1000 }, silentConsole, setTimeout);
  return { helpers: module.exports, captures };
}
const oldSource = await readFile(join(original, 'lib/helpers.js'), 'utf8');
const newSource = await readFile(join(upstream, 'lib/helpers.js'), 'utf8');
const controls = [];
async function control(name, fn, execution) {
  try { const detail = await fn(); controls.push({ control: name, passed: true, execution, detail }); }
  catch (error) { controls.push({ control: name, passed: false, execution, error: error.message }); }
}
await control('old_readiness_swallows_failed_wait', async () => {
  let attempts = 0;
  await loadHelpers(oldSource).helpers.waitForPageReady({ async waitForLoadState() { attempts++; throw new Error('fixture timeout'); } });
  assert.equal(attempts, 1); return { rejected_api_wait: true, helper_resolved: true };
}, 'actual helper source with a rejecting page API double');
await control('old_authentication_swallows_both_failed_success_checks', async () => {
  const events = [];
  const page = {
    async waitForSelector(selector) { if (selector === 'success-fixture') throw new Error('fixture no success'); events.push(selector); },
    async fill() {}, async click() { events.push('submitted'); },
    async waitForNavigation() { throw new Error('fixture no navigation'); },
  };
  await loadHelpers(oldSource).helpers.authenticate(page, { username: 'fixture-user', password: '<FIXTURE_PASSWORD>' }, { successIndicator: 'success-fixture' });
  assert(events.includes('submitted')); return { navigation_failed: true, success_selector_failed: true, helper_resolved: true };
}, 'actual helper source with controlled failed navigation and success checks');
await control('old_context_options_drop_environment_headers_when_custom_headers_present', async () => {
  const browser = { async newContext(options) { return options; } };
  const env = { PW_HEADER_NAME: 'X-Fixture', PW_HEADER_VALUE: 'fixture-only' };
  const oldOptions = await loadHelpers(oldSource, env).helpers.createContext(browser, { extraHTTPHeaders: { 'X-Custom': 'custom' } });
  const newOptions = await loadHelpers(newSource, env).helpers.createContext(browser, { extraHTTPHeaders: { 'X-Custom': 'custom' } });
  assert.equal(oldOptions.extraHTTPHeaders['X-Fixture'], undefined);
  assert.equal(newOptions.extraHTTPHeaders['X-Fixture'], 'fixture-only');
  assert.equal(newOptions.extraHTTPHeaders['X-Custom'], 'custom');
  return { original_dropped_header: true, upstream_preserved_both: true };
}, 'actual old and current helper source with a context API double');
await control('upstream_removes_unconditional_sandbox_flags_for_nonroot', async () => {
  const oldOptions = await loadHelpers(oldSource).helpers.launchBrowser('chromium');
  const newOptions = await loadHelpers(newSource).helpers.launchBrowser('chromium');
  assert(oldOptions.args.includes('--no-sandbox')); assert.equal(newOptions.args, undefined);
  return { original_unconditional_flag: true, upstream_nonroot_flag_absent: true, actual_browser_launched: false };
}, 'actual launch option construction with browser API doubles');
await control('old_click_retry_repeats_effect_after_ambiguous_failure', async () => {
  let effects = 0;
  const page = { async waitForSelector() {}, async waitForTimeout() {}, async click() {
    effects++; if (effects === 1) throw new Error('fixture response lost after effect');
  } };
  await loadHelpers(oldSource).helpers.safeClick(page, 'fixture', { retries: 2 });
  assert.equal(effects, 2); return { effects, scope: 'One valid ambiguous-failure schedule; not a claim about all Playwright clicks' };
}, 'actual retry helper with a controlled effect-then-error API double');

const temporary = await mkdtemp(join(tmpdir(), 'playwright-executor-controls-'));
const caller = join(temporary, 'caller');
await mkdir(caller); await writeFile(join(caller, 'sentinel.txt'), 'caller fixture');
const script = join(caller, 'check.cjs');
await writeFile(script, "const fs = require('node:fs'); console.log(fs.readFileSync('sentinel.txt', 'utf8'));\n");
await control('current_executor_preserves_caller_directory_while_original_changes_it', async () => {
  const observations = {};
  for (const [label, directory] of [['original', original], ['upstream', upstream]]) {
    const stage = join(temporary, label); await mkdir(stage);
    await copyFile(join(directory, 'run.js'), join(stage, 'run.js'));
    const env = { NODE_PATH: resolve(values['package-root'], 'node_modules'), TEMP: temporary, TMP: temporary };
    if (process.env.SystemRoot) env.SystemRoot = process.env.SystemRoot;
    const result = spawnSync(process.execPath, [join(stage, 'run.js'), script], {
      cwd: caller, env, timeout: 10000, maxBuffer: 262144, encoding: 'utf8',
    });
    assert.equal(result.error, undefined); assert.equal(result.signal, null);
    observations[label] = { returncode: result.status, stdout: result.stdout, stderr: result.stderr };
  }
  assert.equal(observations.original.returncode, 1);
  assert(observations.original.stderr.includes('ENOENT'));
  assert.equal(observations.upstream.returncode, 0);
  assert.equal(observations.upstream.stdout.trim(), 'caller fixture');
  return observations;
}, 'actual Node executor child processes with copied unchanged source; no browser or installer');
for (const [label, directory] of [['original', original], ['upstream', upstream]])
  for (const [name, hash] of Object.entries(inputs[label]))
    if (createHash('sha256').update(await readFile(join(directory, name))).digest('hex') !== hash)
      throw new Error('Input changed during controls: ' + label + '/' + name);
const receipt = { schema_version: 1, evidence_class: 'playwright-helper-api-doubles-and-actual-executor-controls',
  passed: controls.every(control => control.passed), node_version: process.version,
  playwright_version: packageRequire('playwright/package.json').version, source_file_sha256: inputs, controls,
  reproducer_sha256: createHash('sha256').update(await readFile(fileURLToPath(import.meta.url))).digest('hex'),
  browser_executed: false, network_requests_made: false, agent_efficacy_scored: false,
  scope: 'Helper doubles reproduce logic contracts; copied executor processes exercise real cwd behavior. Negative controls do not claim repaired mirrors or agent gains.',
};
await writeFile(resolve(values.output), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(receipt));
process.exitCode = receipt.passed ? 0 : 1;
