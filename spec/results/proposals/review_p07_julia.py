"""Bounded independent proposal audit; no FENIX imports or solver execution.

Not a general source resolver/readback implementation. Semantic checks concern
only the four frozen source/result pairs and synthetic manifests.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import platform
import re
from datetime import datetime
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource

from review_p07 import bits, check_nearest, fixture_identity

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXAMPLES = HERE / 'julia-examples'
INPUTS: set[Path] = {Path(__file__), HERE / 'review_p07.py'}


def raw(path):
    INPUTS.add(path)
    return path.read_bytes()


def load(path):
    return json.loads(raw(path))


def sha(path):
    return hashlib.sha256(raw(path)).hexdigest()



class Token(str):
    pass


def decode_number(token, integer=False):
    if type(token) is not Token:
        raise ValueError('numeric token required')
    if integer:
        if not re.fullmatch(r'-?(0|[1-9][0-9]*)', token):
            raise ValueError('integer form required')
        return int(token)
    value = float(token)
    if not math.isfinite(value) or (value == 0 and Decimal(token) != 0):
        raise ValueError('binary64 range')
    return value


def strict_numbers(text):
    def invalid(token):
        raise ValueError(token)
    obj = json.loads(text, parse_int=Token, parse_float=Token, parse_constant=invalid)
    def visit(value, key=''):
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, key) for v in value]
        if isinstance(value, Token):
            return decode_number(value, key in ('revision', 'max_nfev', 'nfev', 'njev', 'nw', 'nlu', 'maxiters'))
        return value
    return visit(obj)


def reject(call):
    try:
        call()
    except (ValueError, AssertionError):
        return
    raise AssertionError('negative control accepted')


def semantics(m, r, original, model):
    """Fixed-pair relations; checks no claim of actual execution."""
    for field in ('kind', 'schema_version', 'status', 'repeatability', 'sources', 'fir', 'randomness', 'output'):
        assert m[field] == original[field], field
    assert r['fir_digest'] == m['fir']['digest'] == fixture_identity(model)
    assert r['state_ids'] == ['x'] and r['state_units'] == ['molecule'] and r['time_unit'] == 's'
    grid = m['execution']['time_grid']
    assert grid and all(math.isfinite(t) and t >= 0 for t in grid)
    assert all(a < b for a, b in zip(grid, grid[1:]))
    assert [bits(t) for t in grid] == [bits(t) for t in r['times']]
    assert all(math.isfinite(m['execution'][k]) and m['execution'][k] > 0 for k in ('rtol', 'atol', 'max_step'))
    assert 0 <= m['evaluations']['nfev'] <= m['execution']['max_nfev']
    opts = m['backend']['solver']['options']
    assert opts['save_start'] == (grid[0] == 0)
    zero = len(grid) == 1 and grid[0] == 0
    assert m['integration'] == ('skipped_zero_grid' if zero else 'performed')
    counters = [m['evaluations']['nfev'], *m['backend']['evaluations'].values()]
    assert all(c == 0 for c in counters) if zero else counters[0] > 0
    assert len(r['state_values']) == len(r['observable_values']) == len(grid)
    obs = sorted(model['observables'], key=lambda o: o['id'])
    assert r['observable_ids'] == [o['id'] for o in obs]
    assert r['observable_state_ids'] == [o['state'] for o in obs]
    assert r['observable_units'] == [o['unit'] for o in obs]
    for time, row, observed in zip(grid, r['state_values'], r['observable_values'], strict=True):
        assert len(row) == 1 and math.isfinite(row[0]) and row[0] >= 0
        if time == 0:
            assert row[0] == model['states'][0]['initial']
        assert len(observed) == len(obs)
        assert all(bits(v) == bits(row[0]) for v in observed)
    assert math.isfinite(m['timing']['elapsed_seconds']) and m['timing']['elapsed_seconds'] >= 0
    for k in ('started_at_utc', 'finished_at_utc'):
        datetime.strptime(m['timing'][k], '%Y-%m-%dT%H:%M:%S.%fZ')


def main():
    schema = load(HERE / 'run-manifest-julia-sciml-m0.schema.json')
    Draft7Validator.check_schema(schema)
    old_schema = load(HERE / 'run-manifest-m0.schema.json')
    registry = Registry().with_resource(old_schema['$id'], Resource.from_contents(old_schema))
    validator = Draft7Validator(schema, registry=registry)
    old_validator = Draft7Validator(old_schema)
    result_validator = Draft7Validator(load(HERE / 'ode-result-m0.schema.json'))
    catalog = load(EXAMPLES / 'checksums.json')
    assert catalog['status'] == 'PROPOSED_SYNTHETIC_NOT_EXECUTION_RECEIPTS'
    assert set(catalog['artifacts']) == {f'{n}.manifest.json' for n in ('late-first', 'zero-only', 'empty-observables', 'multi-observables')} | {f'../examples/{n}.result.json' for n in ('late-first', 'zero-only', 'empty-observables', 'multi-observables')}
    for name, digest in catalog['artifacts'].items():
        assert sha((EXAMPLES / name).resolve()) == digest
    pairs = []
    for name in ('late-first', 'zero-only', 'empty-observables', 'multi-observables'):
        m = strict_numbers(raw(EXAMPLES / f'{name}.manifest.json'))
        original = load(HERE / 'examples' / f'{name}.manifest.json')
        result_path = HERE / 'examples' / f'{name}.result.json'
        r = strict_numbers(raw(result_path))
        validator.validate(m)
        result_validator.validate(r)
        assert not old_validator.is_valid(m)
        old_validator.validate(original)
        assert m['output']['sha256'] == sha(result_path)
        model_path = HERE / 'examples/multi-observables.fir.json' if name == 'multi-observables' else ROOT / ('spec/fir/proposals/examples/production-decay-no-observables.json' if name == 'empty-observables' else 'spec/fir/proposals/examples/production-decay.json')
        model = load(model_path)['model']
        semantics(m, r, original, model)
        # Only selected Julia backend/producer/budget differ from the fixed core.
        expected_core = copy.deepcopy(original)
        expected_core['producer'] = m['producer']
        expected_core['backend'] = m['backend']
        expected_core['execution']['max_nfev'] = m['execution']['max_nfev']
        assert m == expected_core
        assert m['producer'] == {'name': 'Fenix', 'version': '0.0.0', 'build_id': None}
        pairs.append((m, r, original, model))
    assert pairs[1][0]['execution']['max_nfev'] > 2**63-1
    assert pairs[1][0]['backend']['solver']['options']['maxiters'] > 2**63-1

    structural = 0
    m = pairs[0][0]
    def closure(node, path=()):
        nonlocal structural
        if not isinstance(node, dict):
            return
        for key in (*node, 'unknown'):
            changed = copy.deepcopy(m)
            target = changed
            for part in path:
                target = target[part]
            if key == 'unknown':
                target[key] = True
            else:
                del target[key]
            assert not validator.is_valid(changed), (path, key)
            structural += 1
        for key, child in node.items():
            closure(child, (*path, key))
    closure(m)
    controls = [(('backend','profile'), 'python-scipy-ode/0.1.0'), (('backend','profile'), 'julia-sciml-ode/9'), (('schema_version',), '9'), (('backend','solver','method'), 'Radau'), (('backend','solver','options','jacobian'), 'not_supplied'), (('backend','solver','options','time_derivative'), 'not_supplied'), (('backend','solver','options','maxiters'), 0), (('backend','solver','options','maxiters'), True), (('backend','solver','options','maxiters'), 1.5), (('backend','evaluations','nw'), -1), (('backend','evaluations','nw'), True), (('backend','evaluations','nw'), 0.5), (('backend','solver','options','dtmin'), 0.0), (('backend','solver','options','dense'), True)]
    for path, value in controls:
        changed = copy.deepcopy(m)
        target = changed
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        assert not validator.is_valid(changed), path
        structural += 1
    # Julia accepts positive sub-floor tolerance; the Python schema rejects it.
    small = copy.deepcopy(m)
    small['execution']['rtol'] = 1e-15
    validator.validate(small)
    py = copy.deepcopy(pairs[0][2])
    py['execution']['rtol'] = 1e-15
    assert not old_validator.is_valid(py)

    semantic_count = 0
    for index, path, value in [(0, ('backend','solver','options','save_start'), True), (1, ('backend','evaluations','nw'), 1), (0, ('execution','max_nfev'), 1), (0, ('sources','experiment','id'), 'wrong_same_fir'), (0, ('integration',), 'skipped_zero_grid')]:
        changed = copy.deepcopy(pairs[index][0])
        target = changed
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        validator.validate(changed)  # These require semantic validation.
        reject(lambda: semantics(changed, *pairs[index][1:]))
        semantic_count += 1

    probes = load(HERE / 'examples/numeric-tokens.json')
    for probe in probes['binary64']:
        check_nearest(probe['token'], probe['bits'])
        assert bits(decode_number(Token(probe['token']))) == probe['bits']
    # Exact decimal midpoint and its upper neighbor: ties-to-even, no double rounding.
    roundings = [('1.00000000000000011102230246251565404236316680908203125', '3ff0000000000000'), ('1.00000000000000011102230246251565404236316680908203126', '3ff0000000000001')]
    for token, word in roundings:
        check_nearest(token, word)
        assert bits(decode_number(Token(token))) == word
    for integer in probes['integers'] + [2**63, 10**100]:
        assert decode_number(Token(str(integer)), True) == integer
    rejected = 0
    for token in probes['reject_binary64']:
        reject(lambda: decode_number(json.loads(token, parse_int=Token, parse_float=Token)))
        rejected += 1
    for token in probes['reject_integer']:
        reject(lambda: decode_number(json.loads(token, parse_int=Token, parse_float=Token), True))
        rejected += 1
    # Each Julia-only integer path must reject lexical decimal/exponent spellings.
    text = raw(EXAMPLES / 'late-first.manifest.json').decode()
    for key, value in [('maxiters', 9223372036854775807), ('njev', 12), ('nw', 18)]:
        for token in ('1.0', '1e0', 'true', '"1"'):
            changed = text.replace(f'"{key}": {value}', f'"{key}": {token}')
            assert changed != text
            def validate_changed():
                obj = strict_numbers(changed)
                # Non-numeric tokens are rejected by the structural schema.
                if not validator.is_valid(obj):
                    raise ValueError('schema')
            reject(validate_changed)
            rejected += 1
    for file in ('ADR-P07-Julia.md', 'julia-examples/README.md'):
        raw(HERE / file)
    print(json.dumps({'outcome':'PASS', 'status':'PROPOSED', 'implementation':'independent-python-profile-audit', 'runtime':platform.python_version(), 'jsonschema':version('jsonschema'), 'rfc8785':version('rfc8785'), 'pairs':len(pairs), 'structural_rejections':structural, 'semantic_rejections':semantic_count, 'numeric_rejections':rejected, 'binary64_probes':len(probes['binary64'])+len(roundings), 'native_capture_readback':'NOT RUN — gated on PI ratification', 'human_pi_ratification':'PENDING', 'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(INPUTS)}}, indent=2))


if __name__ == '__main__':
    main()
