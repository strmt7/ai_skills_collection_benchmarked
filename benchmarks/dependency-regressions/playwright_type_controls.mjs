/** Compile trusted contract fixtures against an explicitly provisioned graph. */
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: {
  'package-root': { type: 'string' }, output: { type: 'string' },
}});
if (!values['package-root'] || !values.output)
  throw new Error('Explicit provisioned package root and new receipt required');
const root = resolve(values['package-root']);
const fixtures = resolve(dirname(fileURLToPath(import.meta.url)), 'fixtures/playwright-current');
const names = ['package.json', 'package-lock.json', 'negative.spec.ts', 'positive.spec.ts'];
const hashes = {};
for (const name of names) {
  const expected = await readFile(resolve(fixtures, name));
  if (!expected.equals(await readFile(resolve(root, name))))
    throw new Error('Stage differs from frozen fixture: ' + name);
  hashes[name] = createHash('sha256').update(expected).digest('hex');
}
const require = createRequire(resolve(root, 'package.json'));
const versions = Object.fromEntries(['@playwright/test', 'typescript', '@types/node'].map(name =>
  [name, require(name + '/package.json').version]));
const declared = require('./package.json').devDependencies;
if (Object.entries(versions).some(([name, version]) => declared[name] !== version))
  throw new Error('Installed direct versions differ from frozen graph');
const controls = [];
const compiler = resolve(dirname(require.resolve('typescript/package.json')), require('typescript/package.json').bin.tsc);
for (const name of ['negative.spec.ts', 'positive.spec.ts']) {
  const command = [compiler, '--noEmit', '--strict',
    '--target', 'es2022', '--module', 'node16', '--moduleResolution', 'node16',
    '--types', 'node', name];
  const result = spawnSync(process.execPath, command, {
    cwd: root, timeout: 60000, maxBuffer: 1024 * 1024, encoding: 'utf8',
  });
  const diagnostics = result.stdout + result.stderr;
  const codes = [...diagnostics.matchAll(/error (TS\d+):/g)].map(match => match[1]);
  const passed = !result.error && !result.signal && (name === 'negative.spec.ts'
    ? result.status === 1 && codes.length === 2 && codes[0] === 'TS2769' && codes[1] === 'TS2353'
      && diagnostics.includes("'videosPath'") && diagnostics.includes("'snapshots'")
    : result.status === 0 && diagnostics === '');
  controls.push({ control: name, passed, returncode: result.status, signal: result.signal,
    diagnostics, error: result.error?.message ?? null, compiler_arguments: command.slice(1) });
}
const unsupportedFlag = spawnSync(process.execPath, [
  resolve(dirname(require.resolve('playwright/package.json')), require('playwright/package.json').bin.playwright),
  'test', '--slowmo=1000', '--list',
], { cwd: root, timeout: 10000, maxBuffer: 262144, encoding: 'utf8' });
controls.push({ control: 'unsupported_test_cli_slowmo_flag',
  passed: !unsupportedFlag.error && !unsupportedFlag.signal && unsupportedFlag.status === 1
    && unsupportedFlag.stderr.includes("unknown option '--slowmo=1000'"),
  returncode: unsupportedFlag.status, diagnostics: unsupportedFlag.stdout + unsupportedFlag.stderr,
  error: unsupportedFlag.error?.message ?? null });
for (const name of names)
  if (createHash('sha256').update(await readFile(resolve(root, name))).digest('hex') !== hashes[name])
    throw new Error('Fixture changed during compilation: ' + name);
const receipt = {
  schema_version: 1, evidence_class: 'actual-playwright-types-contract-controls',
  passed: controls.every(control => control.passed), versions, node_version: process.version,
  fixture_sha256: hashes, controls,
  reproducer_sha256: createHash('sha256').update(await readFile(fileURLToPath(import.meta.url))).digest('hex'),
  dependencies_installed_by_this_tool: false, browser_executed: false, agent_efficacy_scored: false,
};
await writeFile(resolve(values.output), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(receipt));
process.exitCode = receipt.passed ? 0 : 1;
