// RFC 8785 Appendix A serialization reference; not a FIR normalizer/parser.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = __dirname;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const artifactKeys = ['input', 'canonical', 'normalized', 'model_canonical'];
const requirements = ['utf16-key-ordering', 'signed-zero', 'numeric-spelling', 'exponent-thresholds',
  'subnormals', 'nonfinite-rejection', 'unicode-preservation', 'array-ordering', 'binary64-integer-boundary'];
function keys(object, required, allowed = required) {
  assert.ok(object && typeof object === 'object' && !Array.isArray(object), 'Expected object');
  for (const key of required) assert.ok(Object.hasOwn(object, key), `Missing ${key}`);
  for (const key of Object.keys(object)) assert.ok(allowed.includes(key), `Unknown ${key}`);
}
function validateCatalog(catalog) {
  // Explicit dependency-free boundary checks matching catalog.schema.json.
  // This validates the catalog, not the scientific contents of raw FIR inputs.
  keys(catalog, ['status', 'contract', 'cases', 'coverage']);
  assert.ok(['REVIEW_REQUIRED', 'APPROVED'].includes(catalog.status), 'Unknown catalog status');
  assert.equal(catalog.contract, 'ADR-P03/0.1.0');
  assert.ok(Array.isArray(catalog.cases) && catalog.cases.length > 0);
  const index = new Map();
  for (const c of catalog.cases) {
    keys(c, ['id','stage','input','reference','expected_outcome'],
      ['id','stage','reference','expected_outcome','binary64_bits','normalization_status', ...artifactKeys]);
    assert.equal(typeof c.id, 'string'); assert.match(c.id, /^[a-z0-9-]+$/);
    assert.ok(!index.has(c.id), 'Duplicate catalog ID'); index.set(c.id, c);
    assert.ok(['binary64_jcs','json_jcs','fir_identity','contract_only'].includes(c.stage));
    assert.ok(['accept','reject'].includes(c.expected_outcome));
    assert.equal(typeof c.reference, 'string'); assert.ok(c.reference.length > 0);
    for (const key of artifactKeys) if (Object.hasOwn(c, key)) {
      keys(c[key], ['path','sha256']);
      assert.equal(typeof c[key].path, 'string');
      assert.match(c[key].path, /^(inputs|expected)\/[a-z0-9.-]+$/);
      assert.equal(typeof c[key].sha256, 'string'); assert.match(c[key].sha256, /^[0-9a-f]{64}$/);
    }
    if (c.stage === 'binary64_jcs') {
      assert.equal(typeof c.binary64_bits, 'string'); assert.match(c.binary64_bits, /^[0-9a-f]{16}$/);
    } else assert.ok(!Object.hasOwn(c, 'binary64_bits'));
    if (c.stage === 'fir_identity') {
      for (const key of ['normalized','model_canonical','canonical','normalization_status']) assert.ok(Object.hasOwn(c, key));
      assert.equal(c.normalization_status, 'NOT_RUN'); assert.equal(c.expected_outcome, 'accept');
    } else {
      for (const key of ['normalized','model_canonical','normalization_status']) assert.ok(!Object.hasOwn(c, key));
    }
    if (c.stage === 'contract_only' || c.expected_outcome === 'reject') assert.ok(!Object.hasOwn(c, 'canonical'));
    else assert.ok(Object.hasOwn(c, 'canonical'));
  }
  keys(catalog.coverage, requirements);
  for (const ids of Object.values(catalog.coverage)) {
    assert.ok(Array.isArray(ids) && ids.length > 0);
    assert.equal(new Set(ids).size, ids.length, 'Duplicate coverage references');
    for (const id of ids) assert.ok(index.has(id), 'Unknown coverage reference');
    assert.ok(ids.some(id => index.get(id).stage !== 'contract_only'), 'Coverage requires executable cases');
  }
}
function artifact(record, directory = root) {
  const base = fs.realpathSync(directory);
  const target = fs.realpathSync(path.resolve(directory, record.path));
  assert.ok(target.startsWith(base + path.sep), 'Artifact path escapes catalog');
  const bytes = fs.readFileSync(target);
  assert.equal(sha(bytes), record.sha256, record.path);
  return bytes;
}
function files(directory) {
  return fs.readdirSync(directory, {withFileTypes:true}).flatMap(entry => {
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? files(target) : [target];
  });
}
function string(value) {
  // JSON.stringify alone permits lone surrogates, forbidden by RFC 8785.
  for (let i = 0; i < value.length; ++i) {
    const unit = value.charCodeAt(i);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(++i);
      if (!(next >= 0xdc00 && next <= 0xdfff)) throw new TypeError('Invalid Unicode');
    } else if (unit >= 0xdc00 && unit <= 0xdfff) throw new TypeError('Invalid Unicode');
  }
  return JSON.stringify(value);
}
function canonical(value) {
  if (typeof value === 'string') return string(value);
  if (typeof value === 'number' && !Number.isFinite(value)) throw new TypeError('Nonfinite');
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  return '{' + Object.keys(value).sort().map(k => string(k) + ':' + canonical(value[k])).join(',') + '}';
}
function review(directory = root) {
  const raw = fs.readFileSync(path.join(directory, 'catalog.json'));
  const catalog = JSON.parse(raw);
  validateCatalog(catalog);
  const referenced = new Set();
  for (const c of catalog.cases) for (const key of artifactKeys) if (c[key]) {
    artifact(c[key], directory); referenced.add(c[key].path);
  }
  const physical = new Set(['inputs','expected'].flatMap(folder => files(path.join(directory, folder)))
    .map(target => path.relative(directory, target).split(path.sep).join('/')));
  assert.deepEqual(referenced, physical, 'Unreferenced or missing fixture artifacts');
  const cases = [];
  for (const c of catalog.cases) {
    const input = artifact(c.input, directory);
    const row = {id:c.id, stage:c.stage, serialization:'NOT_RUN', fir_validation_normalization:'NOT_RUN'};
    if (c.stage !== 'contract_only') {
      let output, modelBytes;
      try {
        let value;
        if (c.stage === 'binary64_jcs') {
          assert.equal(input.toString(), c.binary64_bits);
          value = Buffer.from(c.binary64_bits, 'hex').readDoubleBE();
        } else if (c.stage === 'fir_identity') {
          value = {domain:'fenix.fir', canonicalization_version:'0.1.0', model:JSON.parse(artifact(c.normalized, directory))};
          modelBytes = Buffer.from(canonical(value.model));
          assert.deepEqual(modelBytes, artifact(c.model_canonical, directory));
        } else {
          value = JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(input));
        }
        output = Buffer.from(canonical(value));
      } catch (error) {
        if (!(error instanceof TypeError) || c.expected_outcome !== 'reject') throw error;
        row.serialization = 'REJECT_CONFIRMED';
      }
      if (output !== undefined) {
        assert.equal(c.expected_outcome, 'accept');
        assert.deepEqual(output, artifact(c.canonical, directory), c.id);
        Object.assign(row, {serialization:'PASS', canonical_hex:output.toString('hex'), canonical_sha256:sha(output)});
        if (modelBytes !== undefined) Object.assign(row, {model_canonical_hex:modelBytes.toString('hex'), model_canonical_sha256:sha(modelBytes)});
      }
    }
    cases.push(row);
  }
  return {report_version:1, catalog_sha256:sha(raw),
    catalog_schema_sha256:sha(fs.readFileSync(path.join(directory, 'catalog.schema.json'))),
    evaluator_sha256:sha(fs.readFileSync(path.join(directory, 'review_p03.cjs'))),
    fixture_status:catalog.status, implementation:'independent-ecmascript-rfc8785',
    runtime:{name:'node', version:process.versions.node, engine:'v8', engine_version:process.versions.v8,
      serializer:'ECMAScript JSON.stringify'}, cases};
}
function resolved(target) {
  // Resolve existing ancestors too, including a directory symlink for a new file.
  const absolute = path.resolve(target);
  if (fs.existsSync(absolute)) return fs.realpathSync(absolute);
  const parent = path.dirname(absolute);
  assert.notEqual(parent, absolute, 'Cannot resolve output');
  return path.join(resolved(parent), path.basename(absolute));
}
function writeReport(destination, report, directory = root) {
  const target = resolved(destination);
  const protectedFiles = ['catalog.json','catalog.schema.json','review_p03.py','review_p03.cjs']
    .map(name => path.join(directory, name));
  for (const folder of ['inputs','expected']) {
    const base = fs.realpathSync(path.join(directory, folder));
    assert.ok(target !== base && !target.startsWith(base + path.sep), 'Protected fixture output');
    protectedFiles.push(...files(path.join(directory, folder)));
  }
  for (const source of protectedFiles) {
    assert.notEqual(target, fs.realpathSync(source), 'Protected catalog/source output');
    if (fs.existsSync(target)) {
      const a = fs.statSync(target), b = fs.statSync(source);
      assert.ok(a.ino !== b.ino || a.dev !== b.dev, 'Protected hard-link output');
    }
  }
  fs.mkdirSync(path.dirname(target), {recursive:true});
  fs.writeFileSync(target, JSON.stringify(report, null, 2) + '\n');
}
if (require.main === module) {
  assert.equal(process.argv.length, 4, 'Usage: node review_p03.cjs --report PATH');
  assert.equal(process.argv[2], '--report');
  const report = review();
  writeReport(process.argv[3], report);
  console.log(`PASS: ${report.cases.length} entries inspected; fixture_status=${report.fixture_status}; FIR validation/normalization NOT RUN.`);
}
module.exports = {canonical, review, validateCatalog, writeReport};
