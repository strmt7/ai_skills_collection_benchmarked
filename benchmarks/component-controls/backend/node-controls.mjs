import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { readFileSync } from 'node:fs';

const [dependencyRoot, modulePath] = process.argv.slice(2);
const require = createRequire(resolve(dependencyRoot, 'package.json'));
const { z } = require('zod');
const candidate = await import(pathToFileURL(resolve(modulePath)).href);
const contract = JSON.parse(readFileSync(new URL('./contract.json', import.meta.url), 'utf8'));
const results = [];
const diagnostics = [];
const originalError = console.error;
console.error = (...values) => diagnostics.push(values.map(String).join(' '));
const principal = { id: 'principal-1' };
const credential = 'fixture-token';

async function check(id, body) {
  try { await body(); results.push({ id, passed: true }); }
  catch (error) { results.push({ id, passed: false, reason: String(error?.message ?? error) }); }
}

function request(body, authorization) {
  const headers = { 'Content-Type': 'application/json' };
  if (authorization !== undefined) headers.Authorization = authorization;
  return new Request('https://example.invalid/users', { method: 'POST', headers, body });
}

function validVerifier(token) {
  if (token !== credential) throw new candidate.CredentialError('Invalid credential fixture');
  return Promise.resolve(principal);
}

async function withImmediateTimers(body) {
  const timeout = globalThis.setTimeout;
  const clear = globalThis.clearTimeout;
  const delays = [];
  globalThis.setTimeout = (callback, delay) => { delays.push(delay); queueMicrotask(callback); return delays.length; };
  globalThis.clearTimeout = () => {};
  try { await body(delays); }
  finally { globalThis.setTimeout = timeout; globalThis.clearTimeout = clear; }
}

await check('post-valid-created', async () => {
  let calls = 0;
  candidate.setCreateUser(async input => { calls++; return { id: 'record-1', ...input }; });
  const response = await candidate.post(request('{"email":"ada@example.com","name":"Ada"}'));
  assert.equal(response.status, 201);
  assert.equal(response.headers.get('Location'), '/api/v1/users/record-1');
  assert.deepEqual((await response.json()).data, { id: 'record-1', email: 'ada@example.com', name: 'Ada' });
  assert.equal(calls, 1);
});
await check('post-schema-rejected', async () => {
  let calls = 0;
  candidate.setCreateUser(async () => { calls++; throw new Error('Creation must not run'); });
  const response = await candidate.post(request('{"email":"invalid","name":""}'));
  assert.equal(response.status, 422);
  assert.equal(calls, 0);
});
await check('post-malformed-json', async () => {
  let calls = 0;
  const misses = [];
  candidate.setCreateUser(async () => { calls++; throw new Error('Creation must not run'); });
  for (const body of ['{', '{"email":"ada@example.com","name":"Ada"}{"extra":true}']) {
    try { assert.equal((await candidate.post(request(body))).status, 400); }
    catch (error) { misses.push(String(error.message)); }
  }
  assert.equal(calls, 0);
  assert.deepEqual(misses, [], 'Every malformed fixture must receive an explicit 400 response');
});
await check('auth-valid', async () => {
  candidate.setVerifier(validVerifier);
  const response = await candidate.auth(request('{}', 'Bearer ' + credential), (_request, user) => Response.json(user));
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), principal);
});
await check('auth-scheme-case', async () => {
  candidate.setVerifier(validVerifier);
  const response = await candidate.auth(request('{}', 'bEaReR ' + credential), (_request, user) => Response.json(user));
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), principal);
});
await check('auth-challenge', async () => {
  let calls = 0;
  candidate.setVerifier(async () => { calls++; return principal; });
  const response = await candidate.auth(request('{}'), () => { throw new Error('Handler must not run'); });
  assert.equal(response.status, 401);
  assert.match(response.headers.get('WWW-Authenticate') ?? '', /^Bearer(?:\s|$)/i);
  assert.equal(calls, 0);
});
await check('auth-invalid', async () => {
  candidate.setVerifier(validVerifier);
  let called = false;
  const response = await candidate.auth(request('{}', 'Bearer wrong'), () => { called = true; return Response.json({}); });
  assert.equal(response.status, 401);
  assert.equal(called, false);
});
for (const asynchronous of [false, true]) {
  await check('auth-downstream-' + (asynchronous ? 'async' : 'sync'), async () => {
    candidate.setVerifier(validVerifier);
    const failure = new Error('Controlled application failure');
    const handler = asynchronous ? async () => { throw failure; } : () => { throw failure; };
    await assert.rejects(candidate.auth(request('{}', 'Bearer ' + credential), handler), error => error === failure);
  });
}
await check('auth-verifier-unavailable', async () => {
  const failure = new Error('Controlled verification service outage');
  candidate.setVerifier(async () => { throw failure; });
  await assert.rejects(candidate.auth(request('{}', 'Bearer ' + credential), () => Response.json({})), error => error === failure);
});
await check('retry-transient-recovery', async () => withImmediateTimers(async delays => {
  let calls = 0;
  const result = await candidate.retryRead(async () => {
    if (++calls === 1) throw Object.assign(new Error('Transient fixture'), { transient: true });
    return 'ready';
  }, { maxAttempts: 3, retryable: error => error?.transient === true });
  assert.equal(result, 'ready');
  assert.equal(calls, 2);
  assert.deepEqual(delays, [1000]);
}));
await check('retry-permanent-stop', async () => withImmediateTimers(async delays => {
  let calls = 0;
  const failure = new Error('Permanent fixture');
  await assert.rejects(candidate.retryRead(async () => { calls++; throw failure; },
    { maxAttempts: 3, retryable: () => false }), error => error === failure);
  assert.equal(calls, 1);
  assert.deepEqual(delays, []);
}));
await check('retry-cancelled-before-start', async () => withImmediateTimers(async delays => {
  const controller = new AbortController();
  const reason = new DOMException('Controlled cancellation', 'AbortError');
  controller.abort(reason);
  let calls = 0;
  await assert.rejects(candidate.retryRead(async signal => { calls++; signal.throwIfAborted(); return 'unused'; },
    { maxAttempts: 3, retryable: () => true, signal: controller.signal }), error => error === reason);
  assert.equal(calls, 0);
  assert.deepEqual(delays, []);
}));
await check('zod4-error-issues', async () => {
  const parsed = z.string().safeParse(42);
  assert.equal(parsed.success, false);
  const response = candidate.errorResponse(parsed.error);
  const body = await response.json();
  assert.equal(response.status, 400);
  assert.ok(Array.isArray(body.details) && body.details.length > 0, 'Current Zod issues must be present');
});
await check('log-context-integrity', () => {
  const record = candidate.buildRecord('error', 'Trusted summary',
    { level: 'info', message: 'Overridden', timestamp: 'Overridden', requestId: 'request-1' });
  assert.equal(record.level, 'error');
  assert.equal(record.message, 'Trusted summary');
  assert.notEqual(record.timestamp, 'Overridden');
  assert.equal(record.requestId, 'request-1');
});
await check('exception-provenance', async () => {
  const original = new Error('Controlled underlying failure');
  await assert.rejects(candidate.preserveFailure(async () => { throw original; }), error => error === original || error.cause === original);
});

console.error = originalError;
assert.deepEqual(results.map(row => row.id).sort(), Object.keys(contract.node_contracts).sort());
console.log(JSON.stringify({ measurement_kind: 'component_contract_controls', results, diagnostics }));
