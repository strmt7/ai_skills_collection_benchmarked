import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import next from 'next';
import { inventory } from './inventory.mjs';

const base = path.dirname(fileURLToPath(import.meta.url));
const root = mkdtempSync(path.join(base, 'next-fixture-'));
const put = (name, text) => { const full = path.join(root, name); mkdirSync(path.dirname(full), { recursive: true }); writeFileSync(full, text); };
put('package.json', JSON.stringify({ private: true, dependencies: { next: '16.4.3', react: '19.3.1', 'react-dom': '19.3.1' } }));
put('app/(shop)/products/route.js', 'export function GET() { return Response.json({ok:true}); }');
put('app/api/ping/route.js', 'export function GET() { return new Response("pong"); }');
put('app/_private/route.js', 'export function GET() { return new Response("private"); }');
const candidates = inventory(root).routes;
const app = next({ dev: true, dir: root, hostname: '127.0.0.1', port: 0 });
let server;
try {
  await app.prepare();
  server = createServer(app.getRequestHandler());
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port;
  for (const route of candidates) {
    const response = await fetch(`http://127.0.0.1:${port}${route.path}`, {method:route.method});
    assert.equal(response.status, 200, `${route.method} ${route.path}`);
  }
  assert.equal(candidates.length, 2);
  assert.equal((await fetch(`http://127.0.0.1:${port}/_private`)).status, 404);
  console.log('Next.js route-handler control passed: 2 routes and private-folder exclusion');
} finally {
  if (server) await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  await app.close();
  rmSync(root, {recursive:true, force:true});
}
// Next's development server leaves file watchers open after close. This controlled
// qualification runs in its own process, so close those remaining handles on exit.
process.exit(0);
