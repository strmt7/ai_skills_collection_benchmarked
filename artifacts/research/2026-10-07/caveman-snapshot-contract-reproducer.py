import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path.cwd().resolve()
sys.path.insert(0, str(root / 'tools'))
from isolated_python import IMAGE, run_isolated

checkout = root / '.venv/source-checkouts/JuliusBrussee__caveman-v3.1.0'
commit = '8af1f1b9b1346bca0722a1556f119b4e6675cc96'
def git_blob(path):
    return subprocess.run(['git', '-C', str(checkout), 'show', f'{commit}:{path}'], capture_output=True, check=True).stdout
assert subprocess.run(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], capture_output=True, check=True, text=True).stdout.strip() == commit
contract = git_blob('evals/snapshot_contract.py')
snapshot = git_blob('evals/snapshots/results.json')
valid = {'metadata': {'generated_at': '2026-10-07T00:00:00Z', 'claude_cli_version': 'fixture-not-provider', 'model': 'fixture-not-provider', 'n_prompts': 2, 'terse_prefix': 'Answer concisely.'},
         'prompts': ['Externally defined example one', 'Externally defined example two'],
         'arms': {'__baseline__': ['Response one', 'Response two'], '__terse__': ['One', 'Two'], 'caveman': ['One', 'Two']}}
cases = []
def case(name, edit, expected):
    value = copy.deepcopy(valid)
    edit(value)
    cases.append({'name': name, 'snapshot': value, 'expected_acceptance': expected})
case('complete_matrix', lambda value: None, True)
case('unequal_skill_count_rejected', lambda value: value['arms']['caveman'].pop(), False)
case('unequal_control_count_rejected', lambda value: value['arms']['__terse__'].pop(), False)
case('missing_control_rejected', lambda value: value['arms'].pop('__baseline__'), False)
case('boolean_prompt_count_rejected', lambda value: value['metadata'].update(n_prompts=True), False)
case('nonstring_output_rejected', lambda value: value['arms']['caveman'].__setitem__(0, None), False)
case('empty_skill_responses_accepted_but_no_fidelity_proof', lambda value: value['arms'].update(caveman=['', '']), True)
case('whitespace_skill_responses_accepted_but_no_fidelity_proof', lambda value: value['arms'].update(caveman=[' ', '\n']), True)
case('unknown_model_metadata_accepted_but_not_resolved_identity', lambda value: value['metadata'].update(model='unknown'), True)
case('empty_controls_accepted_but_no_success_proof', lambda value: value['arms'].update(__baseline__=['', ''], __terse__=['', '']), True)
request = {'cases': [{key: value for key, value in item.items() if key != 'expected_acceptance'} for item in cases]}
candidate = b'''import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from snapshot_contract import SnapshotContractError,validate_snapshot,load_snapshot
def run(request):
    outcomes=[]
    for case in request["cases"]:
        try:
            validate_snapshot(case["snapshot"])
            outcome={"name":case["name"],"accepted":True,"error":None}
        except SnapshotContractError as error:
            outcome={"name":case["name"],"accepted":False,"error":str(error)}
        outcomes.append(outcome)
    original=load_snapshot(Path(__file__).parent/"results.json")
    raw=(Path(__file__).parent/"results.json").read_text()
    duplicate=raw.replace('"n_prompts": 10','"n_prompts": 999, "n_prompts": 10')
    path=Path('/tmp/duplicate-snapshot.json')
    path.write_text(duplicate)
    duplicate_result=load_snapshot(path)
    return {"outcomes":outcomes,"published_matrix_prompts":len(original["prompts"]),"published_matrix_arms":sorted(original["arms"]),"duplicate_key_accepted":duplicate_result["metadata"]["n_prompts"]==10}
'''
with tempfile.TemporaryDirectory(prefix='caveman-contract-inputs-') as name:
    stage = Path(name)
    for path, raw in {'candidate.py': candidate, 'snapshot_contract.py': contract, 'results.json': snapshot}.items():
        (stage / path).write_bytes(raw)
    execution = run_isolated(stage, ['candidate.py', 'snapshot_contract.py', 'results.json'], request, timeout=30)
checks = {'bounded_execution_and_verified_cleanup': execution['status'] == 'completed' and execution['cleanup_verified'] is True and not execution.get('cleanup_error')}
if execution.get('candidate_response', {}).get('worker_status') != 'returned':
    with (root / '.venv/research-state/caveman-snapshot-contract-execution-failure.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(execution, indent=2) + '\n')
    raise RuntimeError(execution.get('candidate_response'))
result = execution['candidate_response']['result']
assert len(result['outcomes']) == len(cases)
for expected, actual in zip(cases, result['outcomes'], strict=True):
    checks[expected['name']] = actual['name'] == expected['name'] and actual['accepted'] == expected['expected_acceptance']
checks['published_complete_10_prompt_5_arm_matrix_validates'] = result['published_matrix_prompts'] == 10 and result['published_matrix_arms'] == ['__baseline__', '__terse__', 'caveman', 'megacave', 'ultracave']
checks['duplicate_json_count_key_last_value_accepted'] = result['duplicate_key_accepted'] is True
report = {'schema_version': 1, 'evidence_class': 'upstream-evaluation-contract-controls-not-skill-effectiveness',
          'passed': all(checks.values()), 'checks': checks, 'repository': 'https://github.com/JuliusBrussee/caveman',
          'release': 'v3.1.0', 'commit': commit, 'image': IMAGE, 'source_sha256': {'evals/snapshot_contract.py': hashlib.sha256(contract).hexdigest(), 'evals/snapshots/results.json': hashlib.sha256(snapshot).hexdigest()},
          'fixture_sha256': hashlib.sha256(candidate).hexdigest(), 'fixture_input_sha256': hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
          'execution': execution, 'observed_gaps': ['Empty or whitespace responses and empty controls satisfy the shape validator; no correctness or successful generation is proved.', 'Model name unknown satisfies metadata validation; resolved provider identity is not bound.', 'Duplicate JSON keys use last-value parsing; no unique-key artifact integrity guarantee is proved.'],
          'upstream_improvements_verified': ['Unequal matrix counts fail before zip-based measurement.', 'Published pinned snapshot has ten prompts and five complete arms.'],
          'new_agent_calls_performed': False, 'agent_efficacy_scored': False, 'skill_runtime_benchmark_passes': 0,
          'controls_use_synthetic_fixed_inputs_not_model_outputs_except_validation_of_the_published_snapshot': True,
          'reproducer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
target = root / 'artifacts/research/2026-10-07/caveman-310-snapshot-contract-controls.json'
with target.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': checks, 'agent_efficacy_scored': False}))
raise SystemExit(0 if report['passed'] else 1)
