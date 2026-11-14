// RFC 8785 Appendix A serialization reference; not a FIR normalizer/parser.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = __dirname;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function artifact(record) {
  const target = path.resolve(root, record.path);
  assert.ok(target.startsWith(root + path.sep), 'Artifact path escapes catalog');
  const bytes = fs.readFileSync(target);
  assert.equal(sha(bytes), record.sha256, record.path);
  return bytes;
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
const raw = fs.readFileSync(path.join(root, 'catalog.json'));
const catalog = JSON.parse(raw);
assert.equal(catalog.status, 'REVIEW_REQUIRED');
assert.equal(new Set(catalog.cases.map(c => c.id)).size, catalog.cases.length);
const cases = [];
for (const c of catalog.cases) {
  const input = artifact(c.input);
  for (const key of ['canonical', 'normalized', 'model_canonical']) if (c[key]) artifact(c[key]);
  const row = {id:c.id, serialization:'NOT_RUN', fir_validation_normalization:'NOT_RUN'};
  if (c.stage !== 'contract_only') {
    let output;
    try {
      let value;
      if (c.stage === 'binary64_jcs') {
        assert.equal(input.toString(), c.binary64_bits);
        value = Buffer.from(c.binary64_bits, 'hex').readDoubleBE();
      } else if (c.stage === 'fir_identity') {
        value = {domain:'fenix.fir', canonicalization_version:'0.1.0', model:JSON.parse(artifact(c.normalized))};
        assert.deepEqual(Buffer.from(canonical(value.model)), artifact(c.model_canonical));
      } else {
        assert.equal(c.stage, 'json_jcs');
        value = JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(input));
      }
      output = Buffer.from(canonical(value));
    } catch (error) {
      if (!(error instanceof TypeError) || c.expected_outcome !== 'reject') throw error;
      row.serialization = 'REJECT_CONFIRMED';
    }
    if (output !== undefined) {
      assert.equal(c.expected_outcome, 'accept');
      assert.deepEqual(output, artifact(c.canonical), c.id);
      row.serialization = 'PASS'; row.canonical_sha256 = sha(output);
    }
  }
  cases.push(row);
}
const report = {catalog_sha256:sha(raw), fixture_status:catalog.status, implementation:'independent-ecmascript-rfc8785', cases};
assert.equal(process.argv.length, 4, 'Usage: node review_p03.cjs --report PATH');
assert.equal(process.argv[2], '--report');
fs.mkdirSync(path.dirname(process.argv[3]), {recursive:true});
fs.writeFileSync(process.argv[3], JSON.stringify(report, null, 2) + '\n');
console.log(`PASS: ${cases.length} entries inspected; FIR validation/normalization NOT RUN.`);
