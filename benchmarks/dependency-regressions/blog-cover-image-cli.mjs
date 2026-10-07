// Exercise the real pinned image-conversion implementation with local fixtures.
// No provider credentials, external HTTP requests, or paid generation calls.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = resolve(process.argv[2]);
const require = createRequire(resolve(root, 'package.json'));
const sharp = require('sharp');
const { fetchLogo } = await import(pathToFileURL(resolve(root, 'src/logoFetcher.js')));
const originalFetch = globalThis.fetch;
const checks = [];
try {
  const svg = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="20"><rect width="32" height="20" fill="red"/></svg>');
  const jpeg = await sharp(svg).jpeg().toBuffer();
  for (const [format, input, contentType] of [['svg', svg, 'image/svg+xml'], ['jpeg', jpeg, 'image/jpeg']]) {
    globalThis.fetch = async () => new Response(input, { headers: { 'content-type': contentType } });
    const result = await fetchLogo('https://fixture.invalid/image');
    assert.equal(result.mimeType, 'image/png');
    const output = await sharp(Buffer.from(result.data, 'base64')).metadata();
    assert.deepEqual([output.format, output.width, output.height], ['png', 32, 20]);
    checks.push({ case: `${format}_to_png_preserves_dimensions`, passed: true });
  }
  globalThis.fetch = async () => new Response('not an image', { headers: { 'content-type': 'text/html' } });
  assert.equal(await fetchLogo('https://fixture.invalid/text'), null);
  checks.push({ case: 'non_image_response', passed: true });
  let requests = 0;
  globalThis.fetch = async () => {
    requests += 1;
    return new Response('', { status: 404 });
  };
  assert.equal(await fetchLogo('fixture.invalid'), null);
  assert.equal(requests, 3);
  checks.push({ case: 'provider_fallback_exhaustion', passed: true });
  console.log(JSON.stringify({ node: process.version, sharp: sharp.versions, checks }, null, 2));
} finally {
  globalThis.fetch = originalFetch;
}
