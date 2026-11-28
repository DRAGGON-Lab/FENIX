"""Read-only negative checks for the native M1 integration evidence gate."""
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse,itertools,json
from compare import compare,load
parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);args=parser.parse_args();root=args.root
with TemporaryDirectory(prefix='fenix-m1-compare-review-') as path:
 exchange=Path(path);environment=exchange/'environment/julia';environment.mkdir(parents=True)
 for name in ('Project.toml','Manifest.toml'):(environment/name).write_bytes((root/'conformance/julia_ode'/name).read_bytes())
 original=(environment/'Manifest.toml').read_bytes();(environment/'Manifest.toml').write_bytes(original+b'\n')
 try:compare(root,exchange,'reviewed')
 except AssertionError as error:assert error.args[0]==('installed Julia lock','Manifest.toml')
 else:raise AssertionError('altered installed lock accepted')
 (environment/'Manifest.toml').write_bytes(original)
 catalog=load(root/'conformance/community/cases.json');settings=load(root/'conformance/community/feasibility/settings.json')
 rows=[dict(key=f"{case['id']}/{method}/{setting['id']}") for case,method,setting in itertools.product(catalog['cases'],('DOP853','Radau'),settings['settings'])]
 producer=exchange/'python-produce.json';producer.write_text(json.dumps(dict(runtime='python',mode='produce',source_revision='stale',rows=rows)))
 try:compare(root,exchange,'reviewed')
 except AssertionError:pass
 else:raise AssertionError('stale source revision accepted')
 catalog=load(root/'conformance/community/cases.json');settings=load(root/'conformance/community/feasibility/settings.json')
 rows=[dict(key=f"{case['id']}/{method}/{setting['id']}") for case,method,setting in itertools.product(catalog['cases'],('DOP853','Radau'),settings['settings'])]
 producer.write_text(json.dumps(dict(runtime='python',mode='produce',source_revision='reviewed',rows=rows)))
 (exchange/'julia-read.json').write_text(json.dumps(dict(runtime='julia',mode='read',source_revision='reviewed',rows=rows[:-1])))
 try:compare(root,exchange,'reviewed')
 except AssertionError:pass
 else:raise AssertionError('missing peer receipt row accepted')
print('PASS installed-lock, stale-revision and missing-peer-row negative probes')
