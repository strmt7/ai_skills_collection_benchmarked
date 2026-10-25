// Independent CLI contracts. Identical expectations apply to every candidate.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('Usage: node image_cli_acceptance_controls.mjs --package-root DIR --output NEW_JSON');
  process.exit(0);
}
function argument(name) {
  const index = args.indexOf(name);
  if (index < 0 || !args[index + 1]) throw new Error(`Missing ${name}`);
  return path.resolve(args[index + 1]);
}
const packageRoot = argument('--package-root');
const output = argument('--output');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const sourceHashes = {};
for (const relative of ['package.json', 'package-lock.json', 'bin/cli.js', 'src/logoFetcher.js',
  'src/geminiGenerator.js', 'src/imageValidator.js']) {
  sourceHashes[relative] = digest(await readFile(path.join(packageRoot, relative)));
}
const sharp = createRequire(path.join(packageRoot, 'package.json'))('sharp');
const png = await sharp({ create: { width: 32, height: 18, channels: 3, background: '#ff0000' } }).png().toBuffer();
const fixture = await mkdtemp(path.join(path.dirname(output), 'image-cli-acceptance-'));
const preload = path.join(fixture, 'preload.cjs');
await writeFile(preload, `
const os = require('node:os');
const fs = require('node:fs');
os.homedir = () => process.env.IMAGE_CONTROL_DIRECTORY;
require('node:module').syncBuiltinESMExports();
let qaCount = 0;
globalThis.fetch = async (_input, init) => {
  const body = JSON.parse(init.body);
  const qa = body.generationConfig?.responseMimeType === 'application/json';
  const mode = process.env.IMAGE_CONTROL_MODE;
  let text = 'fixture';
  if (qa) {
    qaCount++;
    if (mode === 'invalid' || (mode === 'retry' && qaCount === 1)) {
      text = JSON.stringify({isValid:false,issues:'controlled rejection'});
    } else if (mode === 'schema') {
      text = process.env.IMAGE_CONTROL_QA_TEXT;
    } else {
      text = JSON.stringify({isValid:true,issues:''});
    }
  }
  fs.appendFileSync(process.env.IMAGE_CONTROL_CALLS, JSON.stringify({
    kind:qa ? 'qa' : 'generate',
    previous_feedback:!qa && JSON.stringify(body.contents).includes('controlled rejection')
  }) + '\\n');
  return Response.json({candidates:[{content:{parts:qa ? [{text}] : [
    {text}, {inlineData:{data:process.env.IMAGE_CONTROL_PNG,mimeType:'image/png'}}
  ]}}]});
};
`, { flag: 'wx' });
await mkdir(path.join(fixture, 'config'));
const environment = { PATH: path.dirname(process.execPath), SystemRoot: process.env.SystemRoot ?? '',
  APPDATA: path.join(fixture, 'config'), LOCALAPPDATA: path.join(fixture, 'config'),
  XDG_CONFIG_HOME: path.join(fixture, 'config'), TMPDIR: fixture, TEMP: fixture, TMP: fixture,
  IMAGE_CONTROL_DIRECTORY: fixture, IMAGE_CONTROL_PNG: png.toString('base64'), NO_COLOR: '1' };
let sequence = 0;
async function cli(arguments_, additions = {}) {
  const callsFile = path.join(fixture, `calls-${sequence++}.jsonl`);
  const result = spawnSync(process.execPath, ['--require', preload, path.join(packageRoot, 'bin/cli.js'), ...arguments_],
    { cwd: fixture, env: { ...environment, IMAGE_CONTROL_CALLS: callsFile, ...additions },
      encoding: 'utf8', timeout: 20000, maxBuffer: 256 * 1024 });
  if (result.error) throw result.error;
  const recorded = await readFile(callsFile, 'utf8').catch(error => {
    if (error.code !== 'ENOENT') throw error;
    return '';
  });
  return { ...result, calls: recorded.trim() ? recorded.trim().split('\n').map(line => JSON.parse(line)) : [] };
}
const checks = [];
async function check(name, operation) {
  try { checks.push({ name, passed: true, observed: await operation() }); }
  catch (error) { checks.push({ name, passed: false, error: `${error.name}: ${error.message}` }); }
}
async function absent(file) {
  await assert.rejects(readFile(file), error => error.code === 'ENOENT');
}
for (const [kind, label] of [['key', 'GEMINI_API_KEY'], ['brandfetch-id', 'BRANDFETCH_CLIENT_ID']]) {
  await check(`unset_${kind}_is_nonfatal`, async () => {
    assert.equal((await cli(['config', `delete-${kind}`])).status, 0);
    const result = await cli(['config', `get-${kind}`]);
    assert.equal(result.status, 0);
    assert.equal(result.calls.length, 0);
    return { exit_code: result.status };
  });
  for (const value of [...Array.from({ length: 12 }, (_, index) => 'x'.repeat(index + 1)), '秘密🙂']) {
    await check(`${kind}_configured_value_private_${Buffer.byteLength(value)}_bytes_${value.length}_units`, async () => {
      assert.equal((await cli(['config', `set-${kind}`, value])).status, 0);
      const result = await cli(['config', `get-${kind}`]);
      assert.equal(result.status, 0, 'Getter must not crash for a stored nonempty value');
      const line = result.stdout.split(/\r?\n/).find(item => item.startsWith(`${label}:`));
      assert.ok(line, 'Getter must report configured status');
      assert.equal(line.includes(value), false, 'Getter must not disclose the stored value');
      assert.equal(result.stderr.includes(value), false);
      assert.equal(result.calls.length, 0);
      return { exit_code: result.status, value_disclosed: false };
    });
  }
}
assert.equal((await cli(['config', 'set-key', '<FIXTURE_KEY>'])).status, 0);
await check('missing_title_fails_without_provider_request', async () => {
  const result = await cli(['generate']);
  assert.notEqual(result.status, 0); assert.equal(result.calls.length, 0);
  return { exit_code: result.status };
});
await check('accepted_image_writes_exact_bytes', async () => {
  const destination = path.join(fixture, 'accepted.png');
  const result = await cli(['generate', '-t', 'CONTROL TITLE', '-o', destination]);
  assert.equal(result.status, 0); assert.match(result.stdout, /Success! Image saved/);
  assert.deepEqual(await readFile(destination), png);
  assert.deepEqual(result.calls.map(item => item.kind), ['generate', 'qa']);
  return { exit_code: result.status, bytes: png.length, calls: result.calls };
});
for (const existing of [false, true]) {
  await check(`exhausted_qa_fails_and_${existing ? 'preserves_existing' : 'creates_no'}_output`, async () => {
    const destination = path.join(fixture, `rejected-${existing}.png`);
    const previous = Buffer.from('existing user artifact');
    if (existing) await writeFile(destination, previous, { flag: 'wx' });
    const result = await cli(['generate', '-t', 'CONTROL TITLE', '-o', destination], { IMAGE_CONTROL_MODE: 'invalid' });
    assert.notEqual(result.status, 0, 'Exhausted QA must fail');
    assert.doesNotMatch(result.stdout, /Success! Image saved/);
    assert.deepEqual(result.calls.map(item => item.kind), ['generate', 'qa', 'generate', 'qa', 'generate', 'qa']);
    if (existing) assert.deepEqual(await readFile(destination), previous);
    else await absent(destination);
    return { exit_code: result.status, calls: result.calls, existing_output_preserved: existing };
  });
}
await check('rejected_then_accepted_retries_with_feedback', async () => {
  const destination = path.join(fixture, 'retry.png');
  const result = await cli(['generate', '-t', 'CONTROL TITLE', '-o', destination], { IMAGE_CONTROL_MODE: 'retry' });
  assert.equal(result.status, 0); assert.deepEqual(await readFile(destination), png);
  assert.deepEqual(result.calls.map(item => item.kind), ['generate', 'qa', 'generate', 'qa']);
  assert.equal(result.calls[0].previous_feedback, false);
  assert.equal(result.calls[2].previous_feedback, true);
  return { exit_code: result.status, calls: result.calls };
});
for (const [name, text] of [
  ['string_false', '{"isValid":"false","issues":"wrong type"}'],
  ['numeric_one', '{"isValid":1,"issues":"wrong type"}'],
  ['missing_issues', '{"isValid":true}'],
  ['missing_decision', '{"issues":"missing decision"}'],
  ['array', '[]'], ['null', 'null'],
  ['numeric_issues', '{"isValid":true,"issues":1}'],
  ['malformed', 'not-json-RESPONSE-CONTENT'],
]) {
  await check(`invalid_qa_schema_${name}_fails_without_output`, async () => {
    const destination = path.join(fixture, `schema-${name}.png`);
    const result = await cli(['generate', '-t', 'CONTROL TITLE', '-o', destination],
      { IMAGE_CONTROL_MODE: 'schema', IMAGE_CONTROL_QA_TEXT: text });
    assert.notEqual(result.status, 0); assert.doesNotMatch(result.stdout, /Success! Image saved/);
    await absent(destination);
    assert.deepEqual(result.calls.map(item => item.kind), ['generate', 'qa']);
    if (name === 'malformed') assert.equal((result.stdout + result.stderr).includes(text), false);
    return { exit_code: result.status, calls: result.calls };
  });
}
await check('accepted_image_preserves_existing_destination_by_default', async () => {
  const destination = path.join(fixture, 'no-overwrite.png');
  const previous = Buffer.from('existing user artifact');
  await writeFile(destination, previous, { flag: 'wx' });
  const result = await cli(['generate', '-t', 'CONTROL TITLE', '-o', destination]);
  assert.notEqual(result.status, 0); assert.doesNotMatch(result.stdout, /Success! Image saved/);
  assert.deepEqual(await readFile(destination), previous);
  return { exit_code: result.status };
});
await check('explicit_overwrite_accepts_valid_output', async () => {
  const destination = path.join(fixture, 'explicit-overwrite.png');
  await writeFile(destination, 'existing user artifact', { flag: 'wx' });
  const result = await cli(['generate', '-t', 'CONTROL TITLE', '-o', destination, '--overwrite']);
  assert.equal(result.status, 0); assert.deepEqual(await readFile(destination), png);
  return { exit_code: result.status, bytes: png.length };
});
for (const [relative, hash] of Object.entries(sourceHashes)) {
  assert.equal(digest(await readFile(path.join(packageRoot, relative))), hash, `Input changed: ${relative}`);
}
const receipt = { schema_version: 1, evidence_class: 'image-cli-independent-acceptance-controls',
  node: process.version, source_file_sha256: sourceHashes,
  evaluator_sha256: digest(await readFile(fileURLToPath(import.meta.url))),
  independence: { task_defined_outside_skill: true, evaluator_defined_outside_skill: true,
    expected_result_defined_outside_skill: true,
    basis: 'CLI privacy, exit-status, structured-output and file-preservation contracts; identical expectations for all candidates' },
  checks, passed: checks.every(item => item.passed), external_requests: 0, agent_efficacy_scored: false,
  provider_responses: 'all fetch requests intercepted by deterministic fixtures',
  limits: ['No real provider/model availability, visual fidelity or coding-agent efficacy assessed',
    'Controls are correlated component checks, not independent tasks or a statistical skill effect',
    'Existing storage and provider configuration remain outside the repaired boundary'] };
await writeFile(output, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ passed: receipt.passed, total: checks.length,
  failed: checks.filter(item => !item.passed).map(item => item.name), output }));
if (!receipt.passed) process.exitCode = 1;
