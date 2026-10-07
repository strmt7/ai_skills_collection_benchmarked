import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

root=Path.cwd().resolve()
sys.path.insert(0,str(root/'tools'))
sys.path.insert(0,str(root/'.venv/research-state/cocoindex-providers-2026-10-07'))
import importlib.metadata as metadata
import msgspec
import prepare_semantic_corpus as corpus
import sqlite_vec
from cocoindex_code.file_walk import build_matcher,iter_included_files

assert sys.version.split()[0]=='3.14.8' and metadata.version('cocoindex')=='1.0.25' and metadata.version('cocoindex-code')=='0.2.42'
old=root/'.venv/semantic-corpus/full-resources-v7'
base=root/'.venv/semantic-corpus/full-resources-v8'
old_manifest=json.loads((old/'manifest.json').read_bytes())
assert not corpus.corpus_errors(old,old_manifest)
prepared=corpus.prepare(root,base,old_manifest['prefixes'],check=False)
assert prepared['ok'],prepared['errors']
manifest=json.loads((base/'manifest.json').read_bytes())
state=base/'tree/.cocoindex_code'
state.mkdir()
shutil.copyfile(old/'tree/.cocoindex_code/settings.yml',state/'settings.yml')
copied={}
assert not (old/'runtime/daemon.pid').exists(), 'original daemon must be stopped before copying LMDB'
cache=old/'tree/.cocoindex_code/cocoindex.db'
cache_hashes={p.relative_to(cache).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in cache.rglob('*') if p.is_file()}
assert set(cache_hashes)=={'mdb/data.mdb','mdb/lock.mdb'}
assert all(not p.is_symlink() for p in cache.rglob('*'))
shutil.copytree(cache,state/'cocoindex.db')
assert {p.relative_to(state/'cocoindex.db').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (state/'cocoindex.db').rglob('*') if p.is_file()}==cache_hashes
copied['cold_lmdb_files']=cache_hashes
for name in ('target_sqlite.db',):
    source=old/'tree/.cocoindex_code'/name
    destination=state/name
    origin=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)
    target=sqlite3.connect(destination)
    origin.backup(target)
    target.close()
    origin.close()
    copied[name]=hashlib.sha256(destination.read_bytes()).hexdigest()
assert {p.relative_to(cache).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in cache.rglob('*') if p.is_file()}==cache_hashes
config=base/'config'
config.mkdir()
shutil.copyfile(old/'config/global_settings.yml',config/'global_settings.yml')
runtime=base/'runtime'
runtime.mkdir()
env=dict(os.environ,PYTHONPATH=str(root/'.venv/research-state/cocoindex-providers-2026-10-07'),COCOINDEX_CODE_DIR=str(config),COCOINDEX_CODE_RUNTIME_DIR=str(runtime),COCOINDEX_DISABLE_USAGE_TRACKING='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',TOKENIZERS_PARALLELISM='false')
python=root/'.venv/environments/cocoindex-current/Scripts/python.exe'
cli=root/'.venv/environments/cocoindex-current/Scripts/ccc.exe'
proof=json.loads((root/'artifacts/research/2026-10-02/cocoindex-model-provision.json').read_bytes())
model=root/'.venv/cocoindex-model-qualified'
assert {p.relative_to(model).as_posix() for p in model.rglob('*') if p.is_file()}==set(proof['files'])
for name,digest in proof['files'].items(): assert hashlib.sha256(corpus.regular_file(model,name).read_bytes()).hexdigest()==digest
matched={relative.as_posix() for _,relative in iter_included_files(base/'tree',base/'tree',build_matcher(base/'tree',['**/*'],['.cocoindex_code/**'],corpus.MAX_FILE_BYTES))}
expected={name for name,item in manifest['files'].items() if item['excluded_reason'] is None}
assert matched==expected
result=subprocess.run([str(cli),'index'],cwd=base/'tree',env=env,capture_output=True,text=True,encoding='utf-8',timeout=3600)
(base/'index.stdout.txt').write_text(result.stdout,encoding='utf-8')
(base/'index.stderr.txt').write_text(result.stderr,encoding='utf-8')
status=subprocess.run([str(python),'-c','import sys,msgspec; from cocoindex_code.client import project_status; print(msgspec.json.encode(project_status(sys.argv[1])).decode())',str(base/'tree')],env=env,capture_output=True,text=True,timeout=180)
connection=sqlite3.connect((state/'target_sqlite.db').resolve().as_uri()+'?mode=ro',uri=True)
connection.enable_load_extension(True)
sqlite_vec.load(connection)
connection.enable_load_extension(False)
connection.execute('PRAGMA query_only=ON')
indexed={row[0] for row in connection.execute('select distinct file_path from code_chunks_vec')}
chunks=connection.execute('select count(*) from code_chunks_vec').fetchone()[0]
connection.close()
blank={name for name in expected if not corpus.regular_file(base/'tree',name).read_text(encoding='utf-8').strip()}
missing=expected-blank-indexed
unexpected=indexed-expected
freshness=corpus.prepare(root,base,manifest['prefixes'],check=True)
passed=result.returncode==status.returncode==0 and not missing and not unexpected and len(indexed)==len(expected)-len(blank) and freshness['ok']
report={'schema_version':1,'evidence_class':'fresh-source-bound-local-cocoindex-development-index-not-retrieval-benchmark','passed':passed,'python_version':sys.version.split()[0],'cocoindex_version':metadata.version('cocoindex'),'cocoindex_code_version':metadata.version('cocoindex-code'),'manifest_sha256':hashlib.sha256((base/'manifest.json').read_bytes()).hexdigest(),'prefixes':manifest['prefixes'],'selected_files':len(manifest['files']),'text_files':len(expected),'blank_file_paths':sorted(blank),'indexed_files':len(indexed),'chunks':chunks,'missing_indexed_paths':sorted(missing),'unexpected_indexed_paths':sorted(unexpected),'index_exit_code':result.returncode,'status':json.loads(status.stdout) if status.returncode==0 else {'error':status.stderr[:4096]},'source_freshness_after':{'ok':freshness['ok'],'errors':freshness['errors']},'cache_provenance':{'prior_manifest_sha256':hashlib.sha256((old/'manifest.json').read_bytes()).hexdigest(),'cold_lmdb_and_read_only_sqlite_snapshots':copied,'prior_corpus_or_database_modified':False},'local_model_hashes':proof['files'],'remote_embeddings':False,'usage_tracking':False,'device':'cpu','agent_efficacy_scored':False,'retrieval_quality_established':False,'reproducer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
target=root/'artifacts/research/2026-10-07/cocoindex-adapter-source-refresh-v8.json'
with target.open('x',encoding='utf-8') as stream: stream.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('local_model_hashes','blank_file_paths')}))
raise SystemExit(0 if passed else 1)
