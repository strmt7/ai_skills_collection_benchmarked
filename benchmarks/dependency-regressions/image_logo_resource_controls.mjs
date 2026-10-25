// Independent download, decoding and privacy contracts; no skill text defines the oracle.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import http from 'node:http';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('Usage: node image_logo_resource_controls.mjs --package-root DIR --output NEW_JSON');
  process.exit(0);
}
function argument(name) {
  const index = args.indexOf(name);
  if (index < 0 || !args[index + 1]) throw new Error(`Missing ${name}`);
  return path.resolve(args[index + 1]);
}
const packageRoot = argument('--package-root');
const output = argument('--output');
const sha256 = data => createHash('sha256').update(data).digest('hex');
const sharp = createRequire(path.join(packageRoot, 'package.json'))('sharp');
const { fetchLogo } = await import(pathToFileURL(path.join(packageRoot, 'src/logoFetcher.js')));
const png = await sharp({ create: { width: 32, height: 18, channels: 3, background: '#00ff00' } }).png().toBuffer();
const jpeg = await sharp(png).jpeg().toBuffer();
const svg = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="18"><rect width="32" height="18" fill="red"/></svg>');
const nativeFetch = globalThis.fetch;
const nativeTimeout = AbortSignal.timeout;
const nativeError = console.error;
let requests = [], errors = [], handler;
const server = http.createServer((request, response) => handler(request, response));
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}`;
function image(response, bytes = png, type = 'image/png') {
  response.writeHead(200, { 'Content-Type': type });
  response.end(bytes);
}
function route(operation) {
  handler = (request, response) => { requests.push(request.url); operation(request, response); };
}
const checks = [];
function summarized(value) {
  if (value === null || ['boolean', 'number', 'undefined'].includes(typeof value)) return value;
  if (typeof value === 'string') return { type: 'string', bytes: Buffer.byteLength(value), sha256: sha256(value) };
  return { type: Array.isArray(value) ? 'array' : typeof value, keys: Object.keys(value) };
}
async function check(name, operation) {
  requests = []; errors = [];
  globalThis.fetch = nativeFetch;
  AbortSignal.timeout = nativeTimeout;
  console.error = (...values) => errors.push(values.map(String).join(' '));
  try { checks.push({ name, passed: true, observed: await operation() }); }
  catch (error) { checks.push({ name, passed: false, error_type: error.name, error_code: error.code ?? null,
    actual: summarized(error.actual), expected: summarized(error.expected), requests: requests.length }); }
  finally { globalThis.fetch = nativeFetch; AbortSignal.timeout = nativeTimeout; console.error = nativeError; }
}
async function decoded(result) {
  assert.ok(result, 'A valid permitted logo must be returned');
  assert.equal(result.mimeType, 'image/png');
  const metadata = await sharp(Buffer.from(result.data, 'base64')).metadata();
  assert.equal(metadata.format, 'png');
  assert.equal(metadata.width, 32); assert.equal(metadata.height, 18);
  return { format: metadata.format, width: metadata.width, height: metadata.height };
}
function responseFixture(bytes, headers, chunks = [bytes]) {
  let cancelled = false, arrayBufferCalls = 0;
  const response = new Response(new ReadableStream({
    pull(controller) {
      const chunk = chunks.shift();
      if (chunk) controller.enqueue(chunk); else controller.close();
    },
    cancel() { cancelled = true; },
  }), { headers });
  const nativeArrayBuffer = response.arrayBuffer.bind(response);
  response.arrayBuffer = () => { arrayBufferCalls++; return nativeArrayBuffer(); };
  return { response, observed: () => ({ cancelled, array_buffer_calls: arrayBufferCalls }) };
}
try {
  for (const [name, bytes, mime] of [['png', png, 'image/png'], ['jpeg', jpeg, 'image/jpeg'], ['svg', svg, 'image/svg+xml']]) {
    await check(`native_http_${name}_normalizes_to_png`, async () => {
      route((_request, response) => image(response, bytes, mime));
      return decoded(await fetchLogo(base + '/logo'));
    });
  }
  await check('native_http_finite_redirects_preserve_valid_logo', async () => {
    route((request, response) => {
      const index = Number(request.url.slice(1));
      if (index < 2) { response.writeHead(302, { Location: '/' + (index + 1) }); response.end(); }
      else image(response);
    });
    const result = await decoded(await fetchLogo(base + '/0'));
    assert.equal(requests.length, 3);
    return { ...result, requests: requests.length };
  });
  await check('native_http_redirect_loop_is_bounded', async () => {
    route((_request, response) => { response.writeHead(302, { Location: '/loop' }); response.end(); });
    assert.equal(await fetchLogo(base + '/loop'), null);
    assert.ok(requests.length <= 4, 'At most three redirects may be followed');
    return { requests: requests.length };
  });
  await check('native_http_deadline_is_propagated', async () => {
    let requestedDeadline;
    AbortSignal.timeout = milliseconds => { requestedDeadline = milliseconds; return nativeTimeout(25); };
    route((_request, response) => { const timer = setTimeout(() => image(response), 200); response.on('close', () => clearTimeout(timer)); });
    assert.equal(await fetchLogo(base + '/slow'), null);
    assert.equal(requestedDeadline, 10000, 'The entire download chain has a ten-second production deadline');
    return { production_deadline_ms: requestedDeadline, control_deadline_ms: 25, real_loopback_http: true };
  });
  await check('declared_oversized_body_is_cancelled_before_buffering', async () => {
    const fixture = responseFixture(png, { 'Content-Type': 'image/png', 'Content-Length': String(4 * 1024 * 1024 + 1) });
    globalThis.fetch = async () => fixture.response;
    assert.equal(await fetchLogo('https://fixture.invalid/logo'), null);
    assert.equal(fixture.observed().cancelled, true);
    assert.equal(fixture.observed().array_buffer_calls, 0);
    return fixture.observed();
  });
  await check('streamed_oversized_body_is_cancelled', async () => {
    const chunks = [png, ...Array.from({ length: 65 }, () => new Uint8Array(65536))];
    const fixture = responseFixture(png, { 'Content-Type': 'image/png' }, chunks);
    globalThis.fetch = async () => fixture.response;
    assert.equal(await fetchLogo('https://fixture.invalid/logo'), null);
    assert.equal(fixture.observed().cancelled, true);
    return fixture.observed();
  });
  await check('large_decoded_dimensions_are_rejected', async () => {
    const large = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="5000" height="5000"><rect width="5000" height="5000" fill="red"/></svg>');
    route((_request, response) => image(response, large, 'image/svg+xml'));
    assert.equal(await fetchLogo(base + '/large'), null);
    return { source_width: 5000, source_height: 5000, image_rejected: true };
  });
  await check('non_image_media_type_is_rejected', async () => {
    route((_request, response) => image(response, png, 'application/not-image'));
    assert.equal(await fetchLogo(base + '/wrong-type'), null);
    return { image_rejected: true };
  });
  await check('credential_urls_do_not_disclose_values', async () => {
    const canary = 'fixture-credential-value';
    assert.equal(await fetchLogo(base.replace('http://', `http://user:${canary}@`) + '/logo'), null);
    assert.equal(errors.some(value => value.includes(canary)), false, 'Rejected URLs must not disclose credential values');
    assert.equal(requests.length, 0);
    return { value_disclosed: false, requests: requests.length };
  });
  await check('missing_input_is_nonfatal_and_performs_no_request', async () => {
    globalThis.fetch = async () => { throw new Error('Unexpected fetch'); };
    assert.equal(await fetchLogo(undefined), null);
    return { requests: 0 };
  });
  await check('domain_query_injection_is_rejected_before_request', async () => {
    let calls = 0;
    globalThis.fetch = async () => { calls++; return new Response(png, { headers: { 'Content-Type': 'image/png' } }); };
    assert.equal(await fetchLogo('example.com?other=1&c=fixture'), null);
    assert.equal(calls, 0);
    return { requests: calls };
  });
  await check('domain_fallbacks_and_client_id_encoding', async () => {
    const urls = [];
    globalThis.fetch = async input => {
      const url = new URL(input); urls.push(url);
      if (url.hostname === 'icon.horse') return new Response(png, { headers: { 'Content-Type': 'image/png' } });
      return new Response('unavailable', { status: 503 });
    };
    const result = await decoded(await fetchLogo('example.com', 'public&value=example'));
    assert.deepEqual(urls.map(url => url.hostname), ['cdn.brandfetch.io', 'logos.hunter.io', 'icon.horse']);
    assert.equal(urls[0].searchParams.get('c'), 'public&value=example');
    return { ...result, requests: urls.length, client_id_encoded: true };
  });
} finally {
  globalThis.fetch = nativeFetch; AbortSignal.timeout = nativeTimeout; console.error = nativeError;
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}
const examples = [];
for (const name of (await readdir(path.join(packageRoot, 'examples'))).sort()) {
  const bytes = await readFile(path.join(packageRoot, 'examples', name));
  const metadata = await sharp(bytes).metadata();
  // Metadata alone does not exercise pixel decoding.
  const { info } = await sharp(bytes).raw().toBuffer({ resolveWithObject: true });
  examples.push({ path: 'examples/' + name, sha256: sha256(bytes), format: metadata.format,
    width: info.width, height: info.height, pixels_decoded: true, visual_quality_scored: false });
}
const sourceHashes = {};
for (const name of ['package.json', 'package-lock.json', 'src/logoFetcher.js']) sourceHashes[name] = sha256(await readFile(path.join(packageRoot, name)));
const report = { schema_version: 1, evidence_class: 'independent-logo-resource-controls', node_version: process.version,
  evaluator_sha256: sha256(await readFile(fileURLToPath(import.meta.url))), source_file_sha256: sourceHashes,
  checks, examples, passed: checks.every(check => check.passed),
  task_evaluator_and_expected_results_defined_outside_skill_content: true,
  real_loopback_http_used: true, external_provider_requests_requested_by_evaluator: 0,
  process_wide_network_egress_monitored: false,
  timer_acceleration_disclosed: true, real_provider_qualified: false, agent_efficacy_scored: false };
await writeFile(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ passed: report.passed, checks: checks.length, checks_passed: checks.filter(check => check.passed).length,
  examples_decoded: examples.length, real_provider_qualified: false, agent_efficacy_scored: false }));
process.exitCode = report.passed ? 0 : 1;
