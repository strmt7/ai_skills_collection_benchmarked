import hashlib
import json
import subprocess
import sys
from pathlib import Path
root = Path.cwd().resolve()
sys.path.insert(0, str(root / 'tools'))
from prepare_semantic_corpus import prepare
from search_semantic_corpus import verify_response
base = root / '.venv/semantic-corpus/full-resources-v7'
raw = (base / 'manifest.json').read_bytes()
manifest = json.loads(raw)
observations = [{'query': 'ambiguous mutation mapping zero callers false positives', 'scope': 'included/improved/skills/genotoxic-current/**', 'response': json.loads((root / '.venv/research-state/cocoindex-adapter-v7-genotoxic.json').read_bytes()), 'exit_code': 0}]
for query, scope in [('Montgomery representation inverse mapping canonical public inputs', 'included/improved/skills/vector-forge-current/**'), ('private shared memory semaphore mutation tool container profile', 'tools/**')]:
    args = [str(root / '.venv/environments/latest-tools/Scripts/python.exe'), 'tools/search_semantic_corpus.py', '--corpus', str(base), '--python', str(root / '.venv/environments/cocoindex-current/Scripts/python.exe'), '--provider-dir', str(root / '.venv/research-state/cocoindex-providers-2026-10-07'), '--model-proof', 'artifacts/research/2026-10-02/cocoindex-model-provision.json', '--query', query, '--path', scope, '--limit', '3', '--json']
    result = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=240)
    observations.append({'query': query, 'scope': scope, 'response': json.loads(result.stdout), 'exit_code': result.returncode, 'stderr': result.stderr})
checks = {}
for index, item in enumerate(observations):
    value = item['response']
    checks[f'query_{index}_actual_client_returned_three_hits'] = item['exit_code'] == 0 and value.get('ok') is True and len(value.get('response', {}).get('results', [])) == 3
    checks[f'query_{index}_current_provider_runtime_and_manifest'] = value.get('python_version') == '3.14.8' and value.get('versions') == {'cocoindex': '1.0.25', 'cocoindex-code': '0.2.42'} and value.get('manifest_sha256') == hashlib.sha256(raw).hexdigest()
    checks[f'query_{index}_exact_source_scope_and_spans_rechecked'] = len(verify_response(value['response'], base, manifest, [item['scope']], 3)) == 3
checks['source_inventory_still_fresh'] = prepare(root, base, manifest['prefixes'], check=True)['ok'] and (base / 'manifest.json').read_bytes() == raw
report = {'schema_version': 1, 'evidence_class': 'source-bound-selected-development-retrieval-controls-not-efficacy-benchmark', 'passed': all(checks.values()), 'checks': checks, 'observations': observations,
          'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'adapter_sha256': hashlib.sha256((root / 'tools/search_semantic_corpus.py').read_bytes()).hexdigest(),
          'initial_cli_failures_and_probe_label_correction_retained': True, 'windows_cli_expansion_cause_verified': True,
          'query_scope_chosen_for_development_not_blind_evaluation': True, 'retrieval_quality_established': False,
          'agent_efficacy_scored': False, 'skill_runtime_benchmark_passes': 0,
          'reproducer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
target = root / 'artifacts/research/2026-10-07/cocoindex-adapter-v7-runtime-controls.json'
with target.open('x', encoding='utf-8') as stream: stream.write(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': checks, 'hit_paths': [[hit['file_path'] for hit in item['response']['response']['results']] for item in observations]}))
raise SystemExit(0 if report['passed'] else 1)
