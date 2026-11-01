'use strict';

const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const runner = path.resolve(__dirname, '../run.js');

test('the executor preserves existing NODE_PATH entries for files and inline code', t => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'playwright-node-path-test-'));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  const empty = path.join(temp, 'empty');
  const modules = path.join(temp, 'modules');
  fs.mkdirSync(empty);
  fs.mkdirSync(path.join(modules, 'fixture-helper'), { recursive: true });
  fs.writeFileSync(path.join(modules, 'fixture-helper/index.js'), "module.exports = 'fixture-ok';\n");
  const file = path.join(temp, 'probe.cjs');
  const source = "console.log(require('fixture-helper'));";
  fs.writeFileSync(file, source);
  const env = { ...process.env, NODE_PATH: [empty, modules].join(path.delimiter), PW_SCRIPT_DIR: '' };
  const run = args => execFileSync(process.execPath, [runner, ...args], { cwd: temp, env, encoding: 'utf8' }).trim();
  assert.equal(run([file]), 'fixture-ok');
  assert.equal(run(['-e', source]), 'fixture-ok');
});

test('the executor resolves its own Playwright when NODE_PATH is absent', t => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'playwright-no-node-path-test-'));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  const file = path.join(temp, 'probe.cjs');
  fs.writeFileSync(file, "console.log(require('playwright/package.json').version);\n");
  const env = { ...process.env, PW_SCRIPT_DIR: '' };
  delete env.NODE_PATH;
  const result = execFileSync(process.execPath, [runner, file], { cwd: temp, env, encoding: 'utf8' }).trim();
  assert.equal(result, require('../node_modules/playwright/package.json').version);
});
