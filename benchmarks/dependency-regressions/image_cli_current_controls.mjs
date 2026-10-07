// Reproduce package/CLI contracts without contacting any external provider.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, writeFile, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('Usage: node image_cli_current_controls.mjs --package-root DIR --output NEW_JSON');
  process.exit(0);
}
function argument(name) {
  const index = args.indexOf(name);
  if (index < 0 || !args[index + 1]) throw new Error(`Missing ${name}`);
  return path.resolve(args[index + 1]);
}
const packageRoot = argument('--package-root');
const output = argument('--output');
const require = createRequire(path.join(packageRoot, 'package.json'));
const sharp = require('sharp');
const fixture = await mkdtemp(path.join(tmpdir(), 'image-cli-controls-'));
const checks = [];
const sourceHashes = {};
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
for (const relative of ['package.json', 'package-lock.json', 'bin/cli.js', 'src/logoFetcher.js',
  'src/geminiGenerator.js', 'src/imageValidator.js']) {
  sourceHashes[relative] = digest(await readFile(path.join(packageRoot, relative)));
}
async function check(name, operation) {
  try { checks.push({ name, passed: true, observed: await operation() }); }
  catch (error) { checks.push({ name, passed: false, error: `${error.name}: ${error.message}` }); }
}
const savedFetch = globalThis.fetch;
let calls = [];
let providerReply;
globalThis.fetch = async (input, init) => {
  const url = typeof input === 'string' ? input : input.url ?? String(input);
  calls.push({ url, method: init?.method ?? 'GET' });
  if (!providerReply) throw new Error('Unexpected fixture request');
  return providerReply(url, init);
};
try {
  const { fetchLogo, generateCoverImage } = await import(pathToFileURL(path.join(packageRoot, 'index.js')));
  const { validateImage } = await import(pathToFileURL(path.join(packageRoot, 'src/imageValidator.js')));
  for (const kind of ['svg', 'jpeg']) {
    await check(`${kind}_to_png_dimensions`, async () => {
      const image = kind === 'svg' ? Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="23" height="11"><rect width="23" height="11" fill="red"/></svg>')
        : await sharp({ create: { width: 23, height: 11, channels: 3, background: '#ff0000' } }).jpeg().toBuffer();
      providerReply = () => new Response(image, { headers: { 'content-type': `image/${kind}` } });
      const result = await fetchLogo('https://fixture.invalid/logo', 'fixture-client');
      assert.equal(result.mimeType, 'image/png');
      const metadata = await sharp(Buffer.from(result.data, 'base64')).metadata();
      assert.equal(metadata.width, 23); assert.equal(metadata.height, 11);
      return { width: metadata.width, height: metadata.height };
    });
  }
  await check('non_image_response_returns_null', async () => {
    providerReply = () => new Response('not an image', { headers: { 'content-type': 'text/plain' } });
    assert.equal(await fetchLogo('https://fixture.invalid/logo', 'fixture-client'), null);
    return null;
  });
  await check('all_logo_fallbacks_are_observed', async () => {
    calls = [];
    providerReply = () => new Response('missing', { status: 404, headers: { 'content-type': 'text/plain' } });
    assert.equal(await fetchLogo('fixture.invalid', 'fixture-client'), null);
    assert.deepEqual(calls.map(item => new URL(item.url).hostname), ['cdn.brandfetch.io', 'logos.hunter.io', 'icon.horse']);
    return { intercepted_requests: calls.length };
  });
  const png = await sharp({ create: { width: 23, height: 11, channels: 3, background: '#ff0000' } }).png().toBuffer();
  await check('current_google_sdk_image_response', async () => {
    calls = [];
    providerReply = () => Response.json({ candidates: [{ content: { parts: [{ text: 'fixture' }, { inlineData: { data: png.toString('base64'), mimeType: 'image/png' } }] } }] });
    const result = await generateCoverImage('CONTROL TITLE', null, '<FIXTURE_KEY>');
    assert.equal(result.base64Image, png.toString('base64'));
    assert.equal(result.textOutput.trim(), 'fixture'); assert.equal(calls.length, 1);
    return { intercepted_requests: calls.length, response_bytes: png.length };
  });
  await check('current_google_sdk_validation_response', async () => {
    calls = [];
    providerReply = () => Response.json({ candidates: [{ content: { parts: [{ text: '{"isValid":true,"issues":""}' }] } }] });
    assert.deepEqual(await validateImage(png.toString('base64'), 'CONTROL TITLE', false, '<FIXTURE_KEY>'), { isValid: true, issues: '' });
    assert.equal(calls.length, 1);
    return { intercepted_requests: calls.length };
  });
  // Child configuration and requests remain inside this unique fixture. No host
  // user profile or inherited provider/auth/proxy configuration is available.
  const preload = path.join(fixture, 'preload.cjs');
  await writeFile(preload, `
const os = require('node:os');
os.homedir = () => process.env.IMAGE_CONTROL_DIRECTORY;
require('node:module').syncBuiltinESMExports();
globalThis.fetch = async () => new Response(JSON.stringify({candidates:[{content:{parts:[
  {text:process.env.IMAGE_CONTROL_MODE === 'invalid' ? '{"isValid":false,"issues":"controlled rejection"}' : 'fixture'},
  {inlineData:{data:process.env.IMAGE_CONTROL_PNG,mimeType:'image/png'}}
]}}]}),{headers:{'content-type':'application/json'}});
`, { flag: 'wx' });
  await mkdir(path.join(fixture, 'config'));
  const environment = { PATH: path.dirname(process.execPath), SystemRoot: process.env.SystemRoot ?? '',
    APPDATA: path.join(fixture, 'config'), LOCALAPPDATA: path.join(fixture, 'config'),
    XDG_CONFIG_HOME: path.join(fixture, 'config'), TMPDIR: fixture, TEMP: fixture, TMP: fixture,
    IMAGE_CONTROL_DIRECTORY: fixture, IMAGE_CONTROL_PNG: png.toString('base64'), NO_COLOR: '1' };
  function cli(arguments_, additions = {}) {
    const result = spawnSync(process.execPath, ['--require', preload, path.join(packageRoot, 'bin/cli.js'), ...arguments_],
      { cwd: fixture, env: { ...environment, ...additions }, encoding: 'utf8', timeout: 20000, maxBuffer: 256 * 1024 });
    if (result.error) throw result.error;
    return result;
  }
  await check('cli_help_with_current_dependencies', async () => {
    const result = cli(['--help']); assert.equal(result.status, 0);
    assert.match(result.stdout, /generate/); return { exit_code: result.status };
  });
  await check('short_key_masking_defect_reproduced', async () => {
    assert.equal(cli(['config', 'set-key', 'abc']).status, 0);
    const result = cli(['config', 'get-key']); assert.notEqual(result.status, 0);
    assert.match(result.stderr, /RangeError/); return { exit_code: result.status, defect: 'short key crashes mask' };
  });
  await check('failed_qa_reported_as_success_defect_reproduced', async () => {
    assert.equal(cli(['config', 'set-key', '<FIXTURE_KEY>']).status, 0);
    const imagePath = path.join(fixture, 'controlled-output.png');
    const result = cli(['generate', '-t', 'CONTROL TITLE', '-o', imagePath], { IMAGE_CONTROL_MODE: 'invalid' });
    assert.equal(result.status, 0); assert.match(result.stdout, /QA failed after 3 attempts/);
    assert.match(result.stdout, /Success! Image saved/); assert.deepEqual(await readFile(imagePath), png);
    return { exit_code: result.status, qa_passed: false, image_saved: true };
  });
} finally {
  globalThis.fetch = savedFetch;
}
for (const [relative, hash] of Object.entries(sourceHashes)) {
  assert.equal(digest(await readFile(path.join(packageRoot, relative))), hash, `Input changed: ${relative}`);
}
const script = fileURLToPath(import.meta.url);
const receipt = { schema_version: 1, evidence_class: 'image-cli-current-dependency-and-negative-contract-controls',
  node: process.version, direct_dependencies: JSON.parse(await readFile(path.join(packageRoot, 'package.json'), 'utf8')).dependencies,
  sharp: sharp.versions, source_file_sha256: sourceHashes, reproducer_sha256: digest(await readFile(script)), checks,
  passed: checks.every(item => item.passed), external_requests: 0, provider_responses: 'intercepted controlled fixtures',
  limits: ['No real provider generation/model availability assessed', 'No coding-agent efficacy scored',
    'Successful defect reproduction does not mark original behavior correct', 'Configuration/output fixtures retained in temporary directory'] };
await writeFile(output, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ passed: receipt.passed, checks, output }));
if (!receipt.passed) process.exitCode = 1;
