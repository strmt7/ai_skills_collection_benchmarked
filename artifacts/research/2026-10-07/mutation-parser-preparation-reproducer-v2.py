import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

root=Path.cwd().resolve()
assets=root/'.venv/research-state/trailmark-parser-assets'
inputs={'parsers.json':('a2d026f2908897195e69b81e8b1473ed7a692a2a40daf7c9c5c5909d46af9ec3',30054),'parsers-linux-x86_64.tar.zst':('579428269cf83f853bf42f647296588bb3864eab07d739495909b0ae49e310b5',22729471),'libtree_sitter_python.so':('0a39a054ae5e50132fbf969697e3e5932a9d5636db3e4810b829c95d8019a281',826248)}
for name,(digest,size) in inputs.items():
    path=assets/name
    assert path.is_file() and not path.is_symlink() and path.stat().st_size==size and hashlib.sha256(path.read_bytes()).hexdigest()==digest
prepared=root/'artifacts/research/2026-10-07/mutation-tools-provider-preparation.json'
base=json.loads(prepared.read_bytes())
assert base['passed']
recipe=base['dockerfile']+f'LABEL ai-skills.dependency=mutation-tools-python-parser ai-skills.parser-sha256={inputs["libtree_sitter_python.so"][0]}\nENV TREE_SITTER_LANGUAGE_PACK_CACHE_DIR=/opt/parser-cache\nCOPY libtree_sitter_python.so /opt/parser-cache/tree-sitter-language-pack/v1.21.0/libs/libtree_sitter_python.so\nRUN python -c "from tree_sitter_language_pack import get_language; print(get_language(\'python\'))"\n'
with tempfile.TemporaryDirectory(prefix='trailmark-parser-image-') as directory:
    stage=Path(directory)
    shutil.copyfile(assets/'libtree_sitter_python.so',stage/'libtree_sitter_python.so')
    wheels=json.loads((root/'artifacts/research/2026-10-07/mutation-tools-wheel-inputs.json').read_bytes())['wheels']
    for item in wheels.values():
        path=root/'.venv/research-state/mutmut-current-wheels-2026-10-07'/item['filename']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        shutil.copyfile(path,stage/path.name)
    (stage/'Dockerfile').write_text(recipe,encoding='utf-8',newline='\n')
    result=subprocess.run(['docker','build','--network','none','--pull=false','--iidfile',str(stage/'iid'),str(stage)],capture_output=True,timeout=120)
    image=(stage/'iid').read_text().strip() if (stage/'iid').exists() else None
inspection=json.loads(subprocess.check_output(['docker','image','inspect',image],timeout=15))[0] if result.returncode==0 else {}
passed=result.returncode==0 and inspection.get('Id')==image and inspection.get('Config',{}).get('Labels',{}).get('ai-skills.parser-sha256')==inputs['libtree_sitter_python.so'][0]
report={'schema_version':1,'evidence_class':'offline-exact-parser-provider-preparation-not-agent-benchmark','passed':passed,'image':image,'parent_image':base['image'],'provider_receipt_sha256':hashlib.sha256(prepared.read_bytes()).hexdigest(),'inputs':{n:{'sha256':digest,'bytes':size} for n,(digest,size) in inputs.items()},'parser_release_commit':'09a36885b33ab6e4b010cf04acbb9876ddfb52cc','parser_release_url':'https://github.com/xberg-io/tree-sitter-language-pack/releases/tag/v1.21.0','languages_provisioned':['python'],'downloaded_bundle_other_languages_executed':False,'dockerfile':recipe,'build_output':(result.stdout+result.stderr).decode(errors='replace'),'reproducer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'agent_efficacy_scored':False}
target=root/'artifacts/research/2026-10-07/mutation-tools-python-parser-preparation-v2.json'
with target.open('x',encoding='utf-8') as stream: stream.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':passed,'image':image}))
raise SystemExit(0 if passed else 1)
