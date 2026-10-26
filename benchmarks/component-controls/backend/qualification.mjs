import assert from 'node:assert/strict';
import { getEventListeners } from 'node:events';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const candidate = await import(pathToFileURL(resolve(process.argv[2])).href);
const checks = [];
const cancelled = new DOMException('Controlled cancellation', 'AbortError');

// Inspect timer/listener ownership without waiting for a wall-clock backoff.
const originalTimeout = globalThis.setTimeout;
const originalClear = globalThis.clearTimeout;
const controller = new AbortController();
let scheduled;
const waiting = new Promise(resolve => { scheduled = resolve; });
const timers = new Set();
globalThis.setTimeout = callback => { const token = { callback }; timers.add(token); scheduled(); return token; };
globalThis.clearTimeout = token => { timers.delete(token); };
try {
  let calls = 0;
  const retry = candidate.retryRead(async () => { calls++; throw new Error('Transient fixture'); },
    { maxAttempts: 3, retryable: () => true, signal: controller.signal });
  const rejected = assert.rejects(retry, error => error === cancelled);
  await waiting;
  assert.equal(timers.size, 1);
  assert.equal(getEventListeners(controller.signal, 'abort').length, 1);
  controller.abort(cancelled);
  await rejected;
  assert.equal(calls, 1);
  assert.equal(timers.size, 0);
  assert.equal(getEventListeners(controller.signal, 'abort').length, 0);
  checks.push('abort-during-backoff-cleans-timer-and-listener');
} finally {
  globalThis.setTimeout = originalTimeout;
  globalThis.clearTimeout = originalClear;
}

const late = new AbortController();
await assert.rejects(candidate.retryRead(async () => { late.abort(cancelled); return 'stale'; },
  { maxAttempts: 3, retryable: () => true, signal: late.signal }), error => error === cancelled);
checks.push('late-value-after-abort-rejected');
let calls = 0;
await assert.rejects(candidate.retryRead(async () => { calls++; throw cancelled; },
  { maxAttempts: 3, retryable: () => true }), error => error === cancelled);
assert.equal(calls, 1);
checks.push('abort-error-never-retried');
for (const maxAttempts of [0, -1, 1.5, Infinity]) {
  await assert.rejects(candidate.retryRead(async () => { throw new Error('Must not run'); },
    { maxAttempts, retryable: () => true }), RangeError);
}
checks.push('invalid-attempt-budget-rejected');

const delays = [];
const failure = new Error('Controlled exhaustion');
globalThis.setTimeout = (callback, delay) => { delays.push(delay); queueMicrotask(callback); return delays.length; };
globalThis.clearTimeout = () => {};
try {
  let attempts = 0;
  await assert.rejects(candidate.retryRead(async () => { attempts++; throw failure; },
    { maxAttempts: 8, retryable: () => true }), error => error === failure);
  assert.equal(attempts, 8);
  assert.deepEqual(delays, [1000, 2000, 4000, 8000, 16000, 30000, 30000]);
  checks.push('retry-exhaustion-preserves-failure-and-caps-backoff');
} finally {
  globalThis.setTimeout = originalTimeout;
  globalThis.clearTimeout = originalClear;
}

candidate.setVerifier(async () => { throw new Error('Malformed credential must not reach verification'); });
const invalid = await candidate.auth(new Request('https://example.invalid/',
  { headers: { authorization: 'Bearer fixture,other' } }), () => { throw new Error('Must not run'); });
assert.equal(invalid.status, 401);
assert.equal(invalid.headers.get('Cache-Control'), 'no-store');
checks.push('malformed-bearer-rejected-without-cacheable-response');

const hidden = candidate.buildRecord('error', 'Public summary',
  { authorization: 'private fixture', body: 'private fixture', method: 'POST', route: 'x'.repeat(257), requestId: 'r1' });
assert.deepEqual(Object.keys(hidden).sort(), ['level', 'message', 'method', 'requestId', 'timestamp']);
checks.push('logging-context-allowlist-and-length-bound');
const error = candidate.errorResponse(new Error('Private infrastructure detail'));
assert.equal(error.status, 500);
assert.deepEqual(await error.json(), { error: 'Internal server error' });
checks.push('unexpected-error-does-not-disclose-details');

console.log(JSON.stringify({ passed: true, measurement_kind: 'maintained_boundary_qualification', checks }));
