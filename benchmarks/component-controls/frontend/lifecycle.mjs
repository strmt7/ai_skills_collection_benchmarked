// Targeted qualification of the maintained example; not a comparative score.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const [workspace, modulePath] = process.argv.slice(2);
const require = createRequire(resolve(workspace, 'package.json'));
const React = require('react');
const { act, StrictMode } = React;
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const { createRoot } = require('react-dom/client');
const { useQuery } = await import(pathToFileURL(resolve(modulePath)).href);
const element = document.createElement('div');
document.body.append(element);
const root = createRoot(element);
const requests = [];
let value;
const fetcher = signal => new Promise((resolve, reject) => requests.push({ signal, resolve, reject }));
function View({ queryKey, enabled }) {
  value = useQuery(queryKey, fetcher, { enabled });
  return null;
}
const render = async (queryKey, enabled = true) => {
  await act(async () => root.render(React.createElement(StrictMode, null,
    React.createElement(View, { queryKey, enabled }))));
};
try {
  await render('a');
  assert.equal(requests.length, 2, 'Qualified React development StrictMode performs setup/cleanup/setup');
  assert.equal(requests[0].signal.aborted, true);
  assert.equal(requests[1].signal.aborted, false);
  await act(async () => requests[1].resolve('A'));
  await act(async () => requests[0].resolve('stale strict setup'));
  assert.equal(value.data, 'A');
  await render('b');
  assert.equal(value.data, null);
  assert.equal(value.loading, true);
  const failure = { reason: 'non-Error rejection' };
  await act(async () => requests.at(-1).reject(failure));
  assert.equal(value.error, failure);
  assert.equal(value.loading, false);
  await render('c');
  const active = requests.at(-1);
  await render('c', false);
  assert.equal(active.signal.aborted, true);
  assert.equal(value.loading, false);
  assert.equal(value.error, null);
  const before = requests.length;
  await act(async () => value.refetch());
  assert.equal(requests.length, before);
  await act(async () => active.resolve('late disabled'));
  assert.equal(value.data, null);
  await render('c');
  const last = requests.at(-1);
  await act(async () => root.unmount());
  assert.equal(last.signal.aborted, true);
  await act(async () => last.resolve('late unmounted'));
  console.log(JSON.stringify({ passed: true, assertions: [
    'StrictMode cleanup and stale result guard', 'key clears previous data',
    'non-Error rejection preserved', 'disable aborts and clears state',
    'disabled refetch is a no-op', 'unmount aborts active work',
  ] }));
} finally {
  // Repeated unmount is harmless; preserve cleanup even after an assertion fails.
  await act(async () => root.unmount());
  element.remove();
  dom.window.close();
}
