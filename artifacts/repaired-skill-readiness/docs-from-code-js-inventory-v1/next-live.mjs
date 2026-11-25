import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { withFixtureHttp } from './fixture-http.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import next from 'next';
import { inventory } from './inventory.mjs';

async function main() {
  const base = path.dirname(fileURLToPath(import.meta.url));
  // The parent owns this directory and removes it after this process exits.
  const root = mkdtempSync(path.join(base, 'next-fixture-'));
  const put = (name, text) => { const full = path.join(root, name); mkdirSync(path.dirname(full), { recursive: true }); writeFileSync(full, text); };
  const { dependencies } = JSON.parse(readFileSync(path.join(base, 'package.json'), 'utf8'));
  const nextDependencies = Object.fromEntries(['next', 'react', 'react-dom'].map(name => [name, dependencies[name]]));
  put('package.json', JSON.stringify({ private: true, dependencies: nextDependencies }));
  put('app/(shop)/products/route.js', 'export function GET() { return Response.json({ok:true}); }');
  put('app/api/ping/route.js', 'export function GET() { return new Response("pong"); }');
  put('app/_private/route.js', 'export function GET() { return new Response("private"); }');
  const candidates = inventory(root).routes;
  const app = next({ dev: true, dir: root, hostname: '127.0.0.1', port: 0 });
  try {
    await app.prepare();
    if (process.argv.includes('--controlled-failure')) throw new Error('controlled Next failure');
    await withFixtureHttp(app.getRequestHandler(), async request => {
      for (const route of candidates) {
        assert.equal(await request(route.path, route.method), 200, `${route.method} ${route.path}`);
      }
      assert.equal(candidates.length, 2);
      assert.equal(await request('/_private'), 404);
    });
    console.log('Next.js route-handler control passed: 2 routes and private-folder exclusion');
  } finally {
    await app.close();
  }
}
try {
  await main();
} catch (error) {
  console.error(error);
  process.exitCode = 1;
}
// Next leaves watchers open after close. Exit this child before the parent
// removes its fixture; report any failure and flush the captured output.
await Promise.all([new Promise(resolve => process.stdout.write('', resolve)), new Promise(resolve => process.stderr.write('', resolve))]);
process.exit(process.exitCode ?? 0);
