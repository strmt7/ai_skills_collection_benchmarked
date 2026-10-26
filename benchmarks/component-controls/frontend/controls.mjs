// Functional controls. Run inside an isolated, provisioned workspace; no network.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const [workspace, modulePath] = process.argv.slice(2);
if (!workspace || !modulePath) throw new Error('Expected dependency workspace and compiled module');
const require = createRequire(resolve(workspace, 'package.json'));
const React = require('react');
const { act, useCallback } = React;
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const { createRoot } = require('react-dom/client');
const candidate = await import(pathToFileURL(resolve(modulePath)).href);
const results = [];
const originalFetch = globalThis.fetch;
const originalError = console.error;
const diagnostics = [];
console.error = (...values) => diagnostics.push(values.map(String).join(' '));

async function check(id, body) {
  try {
    await body();
    results.push({ id, passed: true });
  } catch (error) {
    results.push({ id, passed: false, reason: String(error.message) });
  } finally {
    globalThis.fetch = originalFetch;
  }
}

function deferred() {
  let resolvePromise;
  const promise = new Promise(resolve => { resolvePromise = resolve; });
  return { promise, resolve: resolvePromise };
}

async function mounted(body) {
  const element = document.createElement('div');
  document.body.append(element);
  const root = createRoot(element);
  let latest;
  function View({ queryKey, enabled = true, fetcher, inline = false }) {
    const stable = useCallback(() => fetcher(queryKey), [queryKey, fetcher]);
    latest = candidate.useQuery(queryKey, inline ? () => fetcher(queryKey) : stable,
      inline ? { enabled } : enabled ? undefined : { enabled: false });
    return null;
  }
  const render = async props => { await act(async () => root.render(React.createElement(View, props))); };
  try { await body({ render, value: () => latest }); }
  finally { await act(async () => root.unmount()); element.remove(); }
}

await check('sort-purity', () => {
  const input = Object.freeze([Object.freeze({ volume: 1 }), Object.freeze({ volume: 3 })]);
  const result = candidate.sorted(input);
  assert.deepEqual(result.map(item => item.volume), [3, 1]);
  assert.deepEqual(input.map(item => item.volume), [1, 3]);
});
await check('zod4-issues', () => {
  const issues = candidate.invalidIssues();
  assert.ok(Array.isArray(issues) && issues.length > 0, 'Invalid input must expose current Zod issues');
});
await check('http-status', async () => {
  globalThis.fetch = async () => new Response('{"accepted":true}', { status: 503 });
  await assert.rejects(candidate.fetchData('https://example.invalid/data'));
});
await check('failure-cause', async () => {
  const cause = new TypeError('controlled transport failure');
  globalThis.fetch = async () => { throw cause; };
  await assert.rejects(candidate.fetchData('https://example.invalid/data'),
    error => error === cause || error.cause === cause);
});
await check('inline-identity', async () => {
  const pending = [];
  const fetcher = () => {
    if (pending.length >= 16) return new Promise(() => {});
    const item = deferred(); pending.push(item); return item.promise;
  };
  await mounted(async ({ render }) => {
    await render({ queryKey: 'a', fetcher, inline: true });
    // Bound a broken effect loop without relying on wall-clock scheduling.
    for (let tick = 0; tick < 4; tick++) {
      await act(async () => { for (const item of [...pending]) item.resolve('ready'); });
      await render({ queryKey: 'a', fetcher, inline: true });
    }
    assert.equal(pending.length, 1, 'Incidental identity changes must not start another request');
  });
});
await check('key-race', async () => {
  const requests = { a: deferred(), b: deferred() };
  const fetcher = key => requests[key].promise;
  await mounted(async ({ render, value }) => {
    await render({ queryKey: 'a', fetcher });
    await render({ queryKey: 'b', fetcher });
    await act(async () => requests.b.resolve('B'));
    assert.equal(value().data, 'B');
    await act(async () => requests.a.resolve('A'));
    assert.equal(value().data, 'B', 'A late old key must not replace the current key');
    assert.equal(value().loading, false);
  });
});
await check('disable-race', async () => {
  const request = deferred();
  const fetcher = () => request.promise;
  await mounted(async ({ render, value }) => {
    await render({ queryKey: 'a', fetcher });
    await render({ queryKey: 'a', fetcher, enabled: false });
    assert.equal(value().loading, false, 'Disabled state must stop displaying loading');
    await act(async () => request.resolve('late'));
    assert.equal(value().data, null, 'Disabled state must not accept late data');
  });
});
await check('refresh-race', async () => {
  const requests = [deferred(), deferred()];
  let count = 0;
  const fetcher = () => requests[count++].promise;
  await mounted(async ({ render, value }) => {
    await render({ queryKey: 'a', fetcher });
    let refresh;
    await act(async () => { refresh = value().refetch(); });
    assert.equal(count, 2);
    await act(async () => { requests[1].resolve('new'); await refresh; });
    await act(async () => requests[0].resolve('old'));
    assert.equal(value().data, 'new', 'The newer refresh must win');
  });
});
console.error = originalError;
dom.window.close();
console.log(JSON.stringify({ measurement_kind: 'component_contract_controls', results, diagnostics }));
