import email
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

root = Path.cwd().resolve()
sys.path.insert(0, str(root/'tools'))
from isolated_python import IMAGE

directory = root/'.venv/research-state/mutmut-current-wheels-2026-10-07'
target = root/'artifacts/research/2026-10-07/mutation-tools-provider-preparation.json'
assert not target.exists()
wheels = {}
for path in sorted(directory.glob('*.whl')):
    with zipfile.ZipFile(path) as archive:
        metadata = email.message_from_bytes(archive.read(next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))))
    name, version = metadata['Name'], metadata['Version']
    assert name not in wheels
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=30) as response:
        release = json.load(response)
    asset = next(a for a in release['urls'] if a['filename'] == path.name)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert not asset['yanked'] and digest == asset['digests']['sha256'] and path.stat().st_size == asset['size']
    wheels[name] = {'version':version,'filename':path.name,'sha256':digest,'bytes':path.stat().st_size,'url':asset['url'],'requires_python':asset['requires_python'],'upload_time':asset['upload_time_iso_8601'],'requires_dist':release['info']['requires_dist']}
assert wheels['mutmut']['version'] == '3.8.0' and wheels['trailmark']['version'] == '0.5.0'
manifest = {'base_image':IMAGE,'wheels':wheels,'resolution_scope':'latest released primary tools with compatible binary transitive requirements; not an assertion that every constrained transitive is globally latest'}
manifest_path = root/'artifacts/research/2026-10-07/mutation-tools-wheel-inputs.json'
manifest_bytes = (json.dumps(manifest,indent=2)+'\n').encode()
with manifest_path.open('xb') as stream: stream.write(manifest_bytes)
recipe = f'FROM {IMAGE}\nLABEL ai-skills.dependency=mutation-tool-controls ai-skills.inputs-sha256={hashlib.sha256(manifest_bytes).hexdigest()}\nCOPY *.whl /tmp/wheels/\nRUN python -m pip install --no-cache-dir --disable-pip-version-check --no-index /tmp/wheels/*.whl && python -m pip check\n'
with tempfile.TemporaryDirectory(prefix='mutation-provider-') as temporary:
    stage = Path(temporary)
    for item in wheels.values(): shutil.copyfile(directory/item['filename'],stage/item['filename'])
    (stage/'Dockerfile').write_text(recipe,encoding='utf-8',newline='\n')
    result = subprocess.run(['docker','build','--network','none','--pull=false','--iidfile',str(stage/'iid'),str(stage)],capture_output=True,timeout=180)
    image = (stage/'iid').read_text().strip() if (stage/'iid').exists() else None
inspection = json.loads(subprocess.check_output(['docker','image','inspect',image],timeout=15))[0] if result.returncode == 0 else {}
assert inspection.get('Id') == image and inspection.get('Config',{}).get('Labels',{}).get('ai-skills.inputs-sha256') == hashlib.sha256(manifest_bytes).hexdigest()
for item in wheels.values(): assert hashlib.sha256((directory/item['filename']).read_bytes()).hexdigest() == item['sha256']
report = {'schema_version':1,'evidence_class':'offline-mutation-tool-provider-preparation-not-agent-benchmark','passed':result.returncode == 0,'image':image,'base_image':IMAGE,'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'wheel_count':len(wheels),'build_output':(result.stdout+result.stderr).decode(errors='replace'),'dockerfile':recipe,'agent_efficacy_scored':False,'reproducer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with target.open('x',encoding='utf-8') as stream: stream.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'image':image,'wheel_count':len(wheels)}))
