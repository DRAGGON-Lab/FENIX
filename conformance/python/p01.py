"""P01 reference validation, independent of the native FENIX implementation."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import rfc8785
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / 'spec/bioir/proposals/bioir-m0.schema.json').read_text())
VALIDATOR = Draft7Validator(SCHEMA)


class Rejection(ValueError):
    def __init__(self, category: str, path: str = ''):
        self.category, self.path = category, path
        super().__init__(f'{category} at {path or "/"}')


class Pairs(list):
    """Preserve duplicate object members until their paths are available."""


def pointer(parent, key):
    return parent + '/' + str(key).replace('~', '~0').replace('/', '~1')


def strict_parse(raw: bytes, *, numeric_policy="p01", detailed=False):
    if numeric_policy not in ("p01", "p03"):
        raise ValueError("Unknown numeric policy")

    class NumericToken(str):
        pass

    def number(token):
        if numeric_policy == 'p01' and re.fullmatch(r'-?(0|[1-9][0-9]*)', token):
            # Lexical range check avoids constructing an arbitrarily large integer.
            digits = token.lstrip('-')
            if len(digits) > 16 or (len(digits) == 16 and digits > '9007199254740991'):
                raise Rejection('INTEGER_RANGE')
            return int(token)
        value = float(token)
        if not math.isfinite(value):
            raise Rejection('NUMBER_RANGE')
        if value == 0 and any(ch in '123456789' for ch in re.split('[eE]', token)[0]):
            raise Rejection('NUMBER_UNDERFLOW')
        return value

    def constant(_):
        raise Rejection('JSON_SYNTAX')

    def visit(value, path=''):
        if isinstance(value, NumericToken):
            try:
                return number(value)
            except Rejection as error:
                raise Rejection(error.category, path if detailed else '') from None
        if isinstance(value, str):
            try:
                value.encode('utf-8', errors='strict')
            except UnicodeEncodeError:
                raise Rejection('INVALID_UNICODE', path) from None
        elif isinstance(value, Pairs):
            result = {}
            for key, item in value:
                child = pointer(path, key)
                visit(key, child)
                if key in result:
                    raise Rejection('DUPLICATE_KEY', child)
                result[key] = visit(item, child)
            return result
        elif isinstance(value, list):
            return [visit(item, pointer(path, i)) for i, item in enumerate(value)]
        return value

    try:
        text = raw.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        raise Rejection('INVALID_UNICODE') from None
    try:
        parsed = json.loads(text, object_pairs_hook=Pairs, parse_int=NumericToken,
                            parse_float=NumericToken, parse_constant=constant)
    except json.JSONDecodeError:
        raise Rejection('JSON_SYNTAX') from None
    return visit(parsed)


def content_digest(document):
    return hashlib.sha256(rfc8785.dumps(document['content'])).hexdigest()


def validate_structure(document):
    if not VALIDATOR.is_valid(document):
        # oneOf diagnostics vary by validator; structural rejection is rooted here.
        raise Rejection('SCHEMA', '')


def unique(items, key, path):
    result = {}
    for i, item in enumerate(items):
        if item[key] in result:
            raise Rejection('DUPLICATE_ID', pointer(pointer(path, i), key))
        result[item[key]] = item
    return result


def validate_design(document):
    validate_structure(document)
    c = document['content']
    if c['kind'] != 'Design':
        raise Rejection('SCHEMA')
    compartments = unique(c['compartments'], 'id', '/content/compartments')
    species = unique(c['species'], 'id', '/content/species')
    parameters = unique(c['parameters'], 'id', '/content/parameters')
    unique(c['functions'], 'id', '/content/functions')
    for i, item in enumerate(c['species']):
        if item['compartment'] not in compartments:
            raise Rejection('REFERENCE', f'/content/species/{i}/compartment')
        unique(item['ports'], 'id', f'/content/species/{i}/ports')
    kinds, used = set(), set()
    for i, fn in enumerate(c['functions']):
        path = f'/content/functions/{i}'
        target = fn['target']
        if target['species'] not in species:
            raise Rejection('REFERENCE', path + '/target/species')
        if target['port'] not in {p['id'] for p in species[target['species']]['ports']}:
            raise Rejection('REFERENCE', path + '/target/port')
        if fn['parameter'] not in parameters:
            raise Rejection('REFERENCE', path + '/parameter')
        expected = 'molecule/s' if fn['kind'] == 'constitutive_production' else '1/s'
        if parameters[fn['parameter']]['unit'] != expected:
            raise Rejection('UNIT', path + '/parameter')
        if fn['kind'] in kinds or fn['parameter'] in used:
            raise Rejection('FUNCTION_ROLE', path)
        kinds.add(fn['kind'])
        used.add(fn['parameter'])
    if used != set(parameters):
        raise Rejection('REFERENCE', '/content/parameters')
    if content_digest(document) != document['digest']:
        raise Rejection('DIGEST', '/digest')
    return document


def validate_experiment(document, design):
    validate_structure(document)
    validate_design(design)
    c, d = document['content'], design['content']
    if c['kind'] != 'Experiment':
        raise Rejection('SCHEMA')
    for key in ('id', 'revision', 'digest'):
        expected = design['digest'] if key == 'digest' else d[key]
        if c['design'][key] != expected:
            raise Rejection('DESIGN_REFERENCE', '/content/design/' + key)
    assignments = unique(c['parameters'], 'parameter', '/content/parameters')
    initial = unique(c['initial_counts'], 'species', '/content/initial_counts')
    unique(c['observables'], 'id', '/content/observables')
    parameters = {p['id']: p for p in d['parameters']}
    for i, item in enumerate(c['parameters']):
        path = f'/content/parameters/{i}'
        if item['parameter'] not in parameters:
            raise Rejection('REFERENCE', path + '/parameter')
        if item['quantity']['unit'] != parameters[item['parameter']]['unit']:
            raise Rejection('UNIT', path + '/quantity/unit')
    if set(assignments) != set(parameters):
        raise Rejection('REFERENCE', '/content/parameters')
    species = {s['id']: s for s in d['species']}
    if set(initial) != set(species):
        raise Rejection('REFERENCE', '/content/initial_counts')
    for i, item in enumerate(c['observables']):
        target = item['target']
        path = f'/content/observables/{i}/target'
        if target['species'] not in species:
            raise Rejection('REFERENCE', path + '/species')
        if target['port'] not in {p['id'] for p in species[target['species']]['ports']}:
            raise Rejection('REFERENCE', path + '/port')
    if content_digest(document) != document['digest']:
        raise Rejection('DIGEST', '/digest')
    return document


def validate_revision(document, previous):
    validate_design(document)
    validate_design(previous)
    current, old = document['content'], previous['content']
    if current['id'] != old['id']:
        raise Rejection('REFERENCE', '/content/id')
    if document['digest'] != previous['digest'] and current['revision'] <= old['revision']:
        raise Rejection('IMMUTABLE_REVISION', '/content/revision')
    return document


def evaluate(case, directory):
    document = strict_parse((directory / case['input']).read_bytes())
    operation = case['operation']
    if operation == 'design':
        validate_design(document)
    elif operation == 'experiment':
        design = strict_parse((directory / case['design']).read_bytes())
        validate_experiment(document, design)
    elif operation == 'revision':
        validate_revision(document, strict_parse((directory / case['previous']).read_bytes()))
    elif operation not in ('parse', 'canonical'):
        raise ValueError(f'Unknown catalog operation: {operation}')
    return document
