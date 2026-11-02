import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import express from 'express';
import { inventory } from './inventory.mjs';

function fixture(files, run) {
  const root = mkdtempSync(path.join(tmpdir(), 'docs-inventory-'));
  try {
    for (const [name, contents] of Object.entries(files)) {
      const dest = path.join(root, name);
      mkdirSync(path.dirname(dest), { recursive: true });
      writeFileSync(dest, contents);
    }
    return run(root);
  } finally { rmSync(root, { recursive: true, force: true }); }
}

test('identifies Next route exports, JS and TypeScript; excludes unrelated cache', () => {
  fixture({
    'package.json': '{"dependencies":{"next":"16.4.3"}}',
    'app/api/ping/route.ts': 'export async function GET(request: Request) { return new Response("pong"); }',
    'app/products/route.js': 'export const GET = () => new Response("products");',
    'src/unrelated.js': 'const cache = {}; cache.get("/wrong", handler);',
    'src/api.ts': 'export interface Item { id: string }; export function list(x: number): number { return x; }',
  }, root => {
    const result = inventory(root);
    assert.deepEqual(result.routes.map(({method, path}) => [method, path]), [['GET','/api/ping'], ['GET','/products']]);
    assert.ok(result.functions.some(x => x.name === 'list' && x.signature.includes('number')));
    assert.ok(result.types.some(x => x.name === 'Item'));
    assert.ok(result.files.some(x => x.file === 'src/unrelated.js'));
    assert.deepEqual(inventory(root), result);
  });
});

test('Next conventions preserve patterns and disclose unresolved cases', () => {
  fixture({
    'package.json': '{"devDependencies":{"next":"16.4.3"}}',
    'src/app/(group)/users/[id]/route.ts': 'export function GET() {}',
    'src/app/_private/route.ts': 'export function GET() {}',
    'src/app/@modal/route.js': 'export function POST() {}',
    'src/app/other/route.ts': 'export default function GET() {}',
    'src/app/ignored/route.tsx': 'export function GET() {}',
  }, root => {
    const routes = inventory(root).routes;
    assert.deepEqual(routes.map(({method,path,resolution}) => [method,path,resolution]), [
      ['GET','/users/[id]','filesystem_pattern'], ['POST',null,'unresolved'],
    ]);
  });
  fixture({'app/route.js': 'export function GET() {}'}, root => assert.equal(inventory(root).routes.length, 0));
});

test('tracks Express direct and mounted routers without treating arbitrary get as a route', () => {
  fixture({'index.js': `import express, {Router as R} from 'express';
const app = express(); const router = R(); const alias = router;
app.get('setting'); app.get('/direct', handler); app.GET('/wrong-case', handler); cache.get('/wrong', handler);
router.get('/users', handler); app.use('/api', alias); app.use('/v2', router); app.use('/root/', router);
const prefix = '/unknown'; app.use(prefix, router);
`}, root => {
    const routes = inventory(root).routes;
    assert.deepEqual(routes.map(x => [x.method,x.path,x.resolution]), [
      ['GET','/direct','direct'], ['GET','/api/users','same_file_mount'],
      ['GET','/v2/users','same_file_mount'], ['GET','/root/users','same_file_mount'], ['GET',null,'unresolved'],
    ]);
  });
});

test('CommonJS and reassignment are handled conservatively', () => {
  fixture({'index.cjs': `const express = require('express'); const app = express();
app.get('/before', handler); if (condition) app = cache; app.get('/after', handler);
const {Router: R} = require('express'); const r = R(); r.post('/x', handler);`,
    'types.ts': `import {type Router} from 'express'; const router = Router(); router.get('/not-runtime', handler);`}, root => {
    const routes = inventory(root).routes;
    assert.deepEqual(routes.map(x => [x.path,x.resolution]), [['/before','direct'], [null,'unresolved']]);
  });
});

test('malformed input fails atomically without executing target source', () => {
  fixture({'source.js': 'throw new Error("must not run");\nfunction bad( {', 'result.json': 'keep'}, root => {
    const script = new URL('./inventory.mjs', import.meta.url);
    const result = spawnSync(process.execPath, [fileURLToPath(script), root, path.join(root,'result.json')], {encoding:'utf8'});
    assert.equal(result.status, 2, result.stderr);
    assert.equal(readFileSync(path.join(root,'result.json'),'utf8'), 'keep');
  });
});

test('controlled Next.js 16 route handlers agree with filesystem candidates', {timeout: 90000}, () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL('./next-live.mjs', import.meta.url))], {
    encoding: 'utf8', timeout: 80000, env: {...process.env, NEXT_TELEMETRY_DISABLED: '1'},
  });
  assert.equal(result.status, 0, `${result.error ?? ''}\n${result.stdout}\n${result.stderr}`);
  assert.match(result.stdout, /Next.js route-handler control passed/);
});

test('Next fixture exits with failure after a controlled framework error', {timeout: 90000}, () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL('./next-live.mjs', import.meta.url)), '--controlled-failure'], {
    encoding: 'utf8', timeout: 80000, env: {...process.env, NEXT_TELEMETRY_DISABLED: '1'},
  });
  assert.equal(result.status, 1, `${result.error ?? ''}\n${result.stdout}\n${result.stderr}`);
  assert.match(result.stderr, /controlled Next failure/);
});

test('controlled Express 5 requests agree with direct and mounted route candidates', async () => {
  const files = {'index.js': `import express, {Router} from 'express';
const app = express(); const api = Router(); app.get('/health', handler); api.post('/items', handler); app.use('/v1/', api);`};
  const routes = fixture(files, root => inventory(root).routes);
  const app = express(); const api = express.Router();
  app.get('/health', (_req,res) => res.sendStatus(204)); api.post('/items', (_req,res) => res.sendStatus(204)); app.use('/v1/', api);
  const server = app.listen(0, '127.0.0.1');
  try {
    await new Promise((resolve, reject) => { server.once('listening', resolve); server.once('error', reject); });
    const port = server.address().port;
    for (const route of routes) {
      const response = await fetch(`http://127.0.0.1:${port}${route.path}`, { method: route.method });
      assert.equal(response.status, 204, `${route.method} ${route.path}`);
    }
    assert.equal((await fetch(`http://127.0.0.1:${port}/wrong`)).status, 404);
  } finally { await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve())); }
});
