import hashlib
import json
import os
import subprocess
from pathlib import Path
root = Path.cwd().resolve()
base = root / '.venv/semantic-corpus/full-resources-v6'
providers = root / '.venv/research-state/cocoindex-providers-2026-10-07'
env = dict(os.environ, PYTHONPATH=str(providers), COCOINDEX_CODE_DIR=str(base / 'config'), COCOINDEX_CODE_RUNTIME_DIR=str(base / 'runtime'))
scope = 'included/improved/skills/genotoxic-current/**'
code = '''import json,sys,importlib.metadata
import cocoindex_code.cli as cli
def spy(**request):
    print(json.dumps({'request':request,'click_version':importlib.metadata.version('click')}))
    raise SystemExit(0)
cli._search_with_wait_spinner=spy
mode=sys.argv.pop(1)
if mode=='default': cli.app()
else: cli.app(args=sys.argv[1:])
'''
observations = []
for mode in ('default', 'literal'):
    args = [str(root / '.venv/environments/cocoindex-current/Scripts/python.exe'), '-c', code, mode, 'search', 'ambiguous mutation mapping zero callers false positives', '--path', scope, '--limit', '3', '--json']
    result = subprocess.run(args, cwd=base / 'tree', env=env, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stderr
    observations.append({'mode': mode, 'request': json.loads(result.stdout), 'stderr': result.stderr})
checks = {'default_cli_changes_literal_glob': observations[0]['request']['request']['paths'] != [scope],
          'default_cli_appends_expanded_paths_to_query': observations[0]['request']['request']['query'] != 'ambiguous mutation mapping zero callers false positives',
          'explicit_args_preserve_path_and_query': observations[1]['request']['request']['paths'] == [scope] and observations[1]['request']['request']['query'] == 'ambiguous mutation mapping zero callers false positives'}
report = {'schema_version': 1, 'evidence_class': 'actual-upstream-cli-dispatch-controls-not-retrieval-quality', 'passed': all(checks.values()),
          'checks': checks, 'observations': observations, 'source_sha256': {'cocoindex_code/cli.py': hashlib.sha256((providers / 'cocoindex_code/cli.py').read_bytes()).hexdigest()},
          'mechanism': 'Click Command.main expands Windows sys.argv glob patterns before option parsing; explicitly supplied args and the client API retain literals.',
          'network_or_model_calls_in_dispatch_probe': False, 'real_retrieval_evidence': 'artifacts/research/2026-10-07/cocoindex-v6-cli-versus-true-client-retrieval.json',
          'correction_to_previous_labels': 'The client-repeat blocks in three earlier v6 receipts actually ran the CLI because startswith(cli) also matches client-repeat. Their execution outcomes are retained; this is not a client-API failure.',
          'affected_receipts': ['cocoindex-v6-repeated-retrieval-controls.json','cocoindex-v6-repeated-retrieval-after-route-probe.json','cocoindex-v6-retrieval-after-owned-restart.json'],
          'agent_efficacy_scored': False, 'reproducer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
target = root / 'artifacts/research/2026-10-07/cocoindex-windows-literal-path-dispatch-controls.json'
with target.open('x', encoding='utf-8') as stream: stream.write(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': checks, 'observations': observations}))
raise SystemExit(0 if report['passed'] else 1)
