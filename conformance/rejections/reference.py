"""Independent Python M0 rejection references, never imported by a FENIX package.

Diagnostics are fixture expectations, not a public API or error-precedence contract.
Scientific structure is always checked by the original ratified schemas first.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'conformance/python'))
import p01

Rejection = p01.Rejection
pointer = p01.pointer
BIOIR = p01.SCHEMA
FIR = json.loads((ROOT / 'spec/fir/proposals/fir-m0.schema.json').read_bytes())
OPERATIONS = {
    'parse': {'primary'}, 'design': {'primary'},
    'experiment': {'primary', 'design'}, 'revision': {'primary', 'previous'},
    'model': {'primary'}, 'producer': {'primary', 'design', 'experiment'},
    'capability': {'primary', 'request'},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_artifact(artifact, root=ROOT):
    relative = Path(artifact['path'])
    path = (root / relative).resolve()
    if (relative.is_absolute() or '..' in relative.parts or '\\' in str(relative)
            or relative.as_posix() != artifact['path']
            or relative.parts[0] not in ('conformance', 'spec')
            or not path.is_relative_to(root.resolve())):
        raise ValueError('Invalid artifact path: ' + str(relative))
    raw = path.read_bytes()
    if sha(raw) != artifact['sha256']:
        raise ValueError('Artifact checksum mismatch: ' + str(relative))
    return raw


def load_catalog(directory=HERE, root=ROOT):
    catalog = p01.strict_parse((directory / 'catalog.json').read_bytes())
    schema = json.loads((directory / 'catalog.schema.json').read_bytes())
    try:
        Draft7Validator(schema).validate(catalog)
    except ValidationError as error:
        raise ValueError("Invalid catalog structure") from error
    cases = catalog['cases']
    index = {c['id']: c for c in cases}
    if len(index) != len(cases):
        raise ValueError('Duplicate catalog IDs')
    for group, ids in catalog['coverage'].items():
        if len(set(ids)) != len(ids) or not set(ids) <= index.keys():
            raise ValueError('Duplicate or unknown coverage references: ' + group)
    referenced = set()
    for case in cases:
        if set(case['inputs']) != OPERATIONS[case['operation']]:
            raise ValueError('Missing or extra dependencies: ' + case['id'])
        if (case['operation'] in ('design', 'experiment', 'revision') and case['contract'] != 'P01'
                or case['operation'] in ('model', 'producer', 'capability') and case['contract'] != 'P03'):
            raise ValueError('Wrong raw-input contract')
        if case['expected']['outcome'] == 'reject' and case['expected']['document'] not in case['inputs']:
            raise ValueError('Diagnostic identifies absent document')
        for artifact in case['inputs'].values():
            read_artifact(artifact, root)
            referenced.add(artifact['path'])
    physical = {p.relative_to(root).as_posix() for p in (directory / 'inputs').rglob('*') if p.is_file()}
    local = {p for p in referenced if p.startswith(directory.relative_to(root).as_posix() + '/inputs/')}
    if local != physical:
        raise ValueError('Orphaned or missing new input artifacts')
    # Register the required historical inputs, independently of their new case IDs.
    historical = json.loads((root / 'conformance/canonicalization/catalog.json').read_bytes())
    required = {('conformance/canonicalization/' + c['input']['path'], c['input']['sha256'], c['expected_outcome'])
                for c in historical['cases'] if c['stage'] == 'contract_only'}
    actual = {(index[id]['inputs']['primary']['path'], index[id]['inputs']['primary']['sha256'],
               index[id]['expected']['outcome']) for id in catalog['coverage']['p03-contract-only']}
    if len(catalog['coverage']['p03-contract-only']) != len(required) or actual != required:
        raise ValueError('Incomplete P03 contract-only coverage')
    examples = {p.relative_to(root).as_posix() for p in (root / 'spec/fir/proposals/examples').glob('*.json')}
    actual = {index[id]['inputs']['primary']['path'] for id in catalog['coverage']['p02-examples']}
    if len(catalog['coverage']['p02-examples']) != len(examples) or actual != examples:
        raise ValueError('Incomplete P02 example coverage')
    return catalog


def parse(raw, contract):
    if contract not in ('P01', 'P03'):
        raise ValueError('Unknown parser contract')
    return p01.strict_parse(raw, numeric_policy=contract.lower(), detailed=True)


def diagnostic_schema(schema, value, root):
    """Expand recognized discriminated branches solely to localize library errors.

    Full-schema acceptance is checked separately. No acceptance rule is replaced.
    Tuple item schemas let each expression choose its own recognized op branch.
    """
    if '$ref' in schema:
        target = root
        for key in schema['$ref'].split('/')[1:]:
            target = target[key]
        return diagnostic_schema(target, value, root)
    result = dict(schema)
    if 'oneOf' in schema and isinstance(value, dict):
        for branch in schema['oneOf']:
            resolved = branch
            if '$ref' in resolved:
                resolved = root['definitions'][resolved['$ref'].split('/')[-1]]
            if any(k in value and 'const' in prop and value[k] == prop['const']
                   for k, prop in resolved.get('properties', {}).items() if k in ('kind', 'op')):
                return diagnostic_schema(resolved, value, root)
    if isinstance(value, dict) and 'properties' in schema:
        result['properties'] = {k: diagnostic_schema(s, value[k], root) if k in value else s
                                for k, s in schema['properties'].items()}
    if isinstance(value, list) and isinstance(schema.get('items'), dict):
        result['items'] = [diagnostic_schema(schema['items'], v, root) for v in value]
    return result


def validate_structure(doc, schema):
    if Draft7Validator(schema).is_valid(doc):
        return
    localized = diagnostic_schema(schema, doc, schema)
    errors = list(Draft7Validator(localized).iter_errors(doc))
    if not errors:
        raise RuntimeError('Diagnostic schema masked a structural error')
    error = sorted(errors, key=lambda e: tuple(str(x) for x in e.absolute_path))[0]
    path = ''
    for segment in error.absolute_path:
        path = pointer(path, segment)
    if error.validator == 'required':
        path = pointer(path, sorted(set(error.schema['required']) - error.instance.keys())[0])
    elif error.validator == 'additionalProperties' and error.schema['additionalProperties'] is False:
        # Data and schema keys, never validator exception prose.
        extras = set(error.instance) - error.schema.get('properties', {}).keys()
        path = pointer(path, sorted(extras)[0])
    raise Rejection('SCHEMA', path)


def validate_bioir(doc, operation, dependencies):
    # P01 entry points retain their coarse structural diagnostics for the old runner.
    validate_structure(doc, BIOIR)
    if operation == 'design':
        p01.validate_design(doc)
    elif operation == 'experiment':
        p01.validate_experiment(doc, dependencies['design'])
    elif operation == 'revision':
        p01.validate_revision(doc, dependencies['previous'])


def validate_model(doc):
    validate_structure(doc, FIR)
    m = doc['model']
    states = p01.unique(m['states'], 'id', '/model/states')
    parameters = p01.unique(m['parameters'], 'id', '/model/parameters')
    reactions = p01.unique(m['reactions'], 'id', '/model/reactions')
    equations = p01.unique(m['equations'], 'state', '/model/equations')
    p01.unique(m['observables'], 'id', '/model/observables')
    for collection, key, expected in ((parameters, 'parameters', {'alpha', 'beta'}),
                                       (reactions, 'reactions', {'production', 'decay'}),
                                       (equations, 'equations', {'x'})):
        if set(collection) != expected:
            if key == 'equations':
                raise Rejection('REFERENCE', '/model/equations/0/state')
            raise Rejection('ROLE', '/model/' + key)
    for i, parameter in enumerate(m['parameters']):
        if parameter['unit'] != ('molecule/s' if parameter['id'] == 'alpha' else '1/s'):
            raise Rejection('UNIT', f'/model/parameters/{i}/unit')

    def references(expr, path):
        if expr['op'] in ('parameter', 'state'):
            namespace = parameters if expr['op'] == 'parameter' else states
            if expr['id'] not in namespace:
                raise Rejection('REFERENCE', path + '/id')
        else:
            references(expr['left'], path + '/left')
            references(expr['right'], path + '/right')

    for collection, field in (('reactions', 'flux'), ('equations', 'rhs')):
        for i, item in enumerate(m[collection]):
            references(item[field], f'/model/{collection}/{i}/{field}')
    for i, item in enumerate(m['observables']):
        if item['state'] not in states:
            raise Rejection('REFERENCE', f'/model/observables/{i}/state')
    alpha = {'op': 'parameter', 'id': 'alpha'}
    decay = {'op': 'multiply', 'left': {'op': 'parameter', 'id': 'beta'},
             'right': {'op': 'state', 'id': 'x'}}
    rhs = {'op': 'subtract', 'left': alpha, 'right': decay}
    for i, reaction in enumerate(m['reactions']):
        production = reaction['id'] == 'production'
        path = f'/model/reactions/{i}'
        if reaction['stoichiometry']['x'] != (1 if production else -1):
            raise Rejection('STOICHIOMETRY', path + '/stoichiometry/x')
        if reaction['flux'] != (alpha if production else decay):
            raise Rejection('TEMPLATE', path + '/flux')
    if m['equations'][0]['rhs'] != rhs:
        raise Rejection('TEMPLATE', '/model/equations/0/rhs')
    # Structural unit constraints + role units + exact templates establish dimensions;
    # no expression execution, numerical sampling, rewriting or algebraic repair.
    return doc


def validate_producer(doc, design, experiment):
    m = doc['model']
    if 'provenance' not in doc:
        raise Rejection('SOURCE_REQUIRED', '/provenance')
    p = doc['provenance']
    for key in ('design_digest', 'experiment_digest', 'symbol_map'):
        if key not in p:
            raise Rejection('SOURCE_REQUIRED', '/provenance/' + key)
    for key, source in (('design_digest', design), ('experiment_digest', experiment)):
        if p[key] != source['digest']:
            raise Rejection('SOURCE_DIGEST', '/provenance/' + key)
    d, e = design['content'], experiment['content']
    state = p['symbol_map']['states'][0]
    path = '/provenance/symbol_map/states/0'
    species = {s['id']: s for s in d['species']}
    if state['bioir_species_id'] not in species:
        raise Rejection('REFERENCE', path + '/bioir_species_id')
    s = species[state['bioir_species_id']]
    if state['bioir_port_id'] not in {p['id'] for p in s['ports']}:
        raise Rejection('REFERENCE', path + '/bioir_port_id')
    if state['bioir_compartment_id'] != s['compartment']:
        raise Rejection('REFERENCE', path + '/bioir_compartment_id')
    # P01 validation established compartment existence and molecular_count port kind.
    source_parameters = {p['id']: p for p in d['parameters']}
    functions = {f['id']: f for f in d['functions']}
    assignments = {p['parameter']: p['quantity'] for p in e['parameters']}
    fir_parameters = {p['id']: (i, p) for i, p in enumerate(m['parameters'])}
    for i, entry in enumerate(p['symbol_map']['parameters']):
        path = f'/provenance/symbol_map/parameters/{i}'
        parameter, function = entry['bioir_parameter_id'], entry['bioir_function_id']
        if parameter not in source_parameters:
            raise Rejection('REFERENCE', path + '/bioir_parameter_id')
        if function not in functions:
            raise Rejection('REFERENCE', path + '/bioir_function_id')
        f = functions[function]
        expected_kind = 'constitutive_production' if entry['fir_parameter_id'] == 'alpha' else 'first_order_decay'
        if (f['kind'] != expected_kind or f['parameter'] != parameter
                or f['target'] != {'species': s['id'], 'port': state['bioir_port_id']}):
            raise Rejection('SOURCE_ROLE', path + '/bioir_function_id')
        if entry['bioir_function_kind'] != f['kind']:
            raise Rejection('SOURCE_ROLE', path + '/bioir_function_kind')
        j, target = fir_parameters[entry['fir_parameter_id']]
        if target['unit'] != assignments[parameter]['unit']:
            raise Rejection('UNIT', f'/model/parameters/{j}/unit')
        if target['value'] != assignments[parameter]['value']:
            raise Rejection('SOURCE_VALUE', f'/model/parameters/{j}/value')
    initial = next(item['quantity'] for item in e['initial_counts'] if item['species'] == s['id'])
    if m['states'][0]['initial'] != initial['value']:
        raise Rejection('SOURCE_VALUE', '/model/states/0/initial')
    if m['states'][0]['unit'] != initial['unit']:
        raise Rejection('UNIT', '/model/states/0/unit')
    source_observables = {o['id']: o for o in e['observables']}
    for i, o in enumerate(m['observables']):
        path = f'/model/observables/{i}'
        if o['id'] not in source_observables:
            raise Rejection('SOURCE_OBSERVABLE', path + '/id')
        source = source_observables[o['id']]
        if (source['target'] != {'species': s['id'], 'port': state['bioir_port_id']}
                or o['state'] != state['fir_state_id']):
            raise Rejection('SOURCE_OBSERVABLE', path + '/state')
        if o['unit'] != m['states'][0]['unit']:
            raise Rejection('UNIT', path + '/unit')
    if {o['id'] for o in m['observables']} != source_observables.keys():
        raise Rejection('SOURCE_OBSERVABLE', '/model/observables')
    for key in p.get('display_labels', {}).get('observables', {}):
        if key not in {o['id'] for o in m['observables']}:
            raise Rejection('REFERENCE', pointer('/provenance/display_labels/observables', key))


def observe(case, root=ROOT):
    stage, document = 'parse', 'primary'
    try:
        doc = parse(read_artifact(case['inputs']['primary'], root), case['contract'])
        op = case['operation']
        dependencies = {}
        for identity in ('design', 'experiment', 'previous'):
            if identity in case['inputs']:
                document, stage = identity, 'parse'
                source = parse(read_artifact(case['inputs'][identity], root), 'P01')
                stage = 'structure'
                validate_structure(source, BIOIR)
                stage = 'semantic'
                if identity == 'experiment':
                    p01.validate_experiment(source, dependencies['design'])
                else:
                    p01.validate_design(source)
                dependencies[identity] = source
        document, stage = 'primary', 'structure'
        if op in ('design', 'experiment', 'revision'):
            validate_structure(doc, BIOIR)
            stage = 'semantic'
            validate_bioir(doc, op, dependencies)
        elif op in ('model', 'producer', 'capability'):
            validate_structure(doc, FIR)
            stage = 'semantic'
            validate_model(doc)
            if op == 'producer':
                stage = 'producer'
                validate_producer(doc, dependencies['design'], dependencies['experiment'])
            elif op == 'capability':
                document, stage = 'request', 'parse'
                request = parse(read_artifact(case['inputs']['request'], root), 'P03')
                if not isinstance(request, dict) or set(request) != {'profile'} or not isinstance(request['profile'], str):
                    raise ValueError('Invalid reference-harness capability request')
                stage = 'capability'
                if doc['model']['capabilities'].get(request['profile']) is not True:
                    raise Rejection('UNSUPPORTED_PROFILE', '/profile')
        return {'outcome': 'accept'}
    except Rejection as error:
        return dict(outcome='reject', stage=stage, category=error.category, document=document, path=error.path)
