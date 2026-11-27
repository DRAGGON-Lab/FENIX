// Independent ECMAScript audit of literal M1 candidate bytes. No Python/native imports.
// JSON.stringify supplies ECMAScript binary64 number spelling. Object keys and
// the three declared collections use ECMAScript's UTF-16 code-unit ordering.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.join(__dirname, 'wire-candidates');
const parse = name => JSON.parse(fs.readFileSync(name, 'utf8'));
const jcs = value => {
  if (Array.isArray(value)) return '[' + value.map(jcs).join(',') + ']';
  if (value !== null && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(k => JSON.stringify(k)+':'+jcs(value[k])).join(',') + '}';
  }
  assert(!(typeof value === 'number') || Number.isFinite(value), 'nonfinite');
  return JSON.stringify(value);
};
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const catalog = parse(path.join(root, 'catalog.json'));
const digests = {};
for (const entry of catalog.positive) {
  const folder = path.join(root, entry.folder);
  const fir = parse(path.join(folder, 'fir.json'));
  const model = structuredClone(fir.model);
  for (const [name, key] of [['reactions','id'],['equations','state'],['observables','id']]) {
    assert.equal(new Set(model[name].map(v => v[key])).size, model[name].length);
    model[name].sort((a,b) => a[key] < b[key] ? -1 : a[key] > b[key] ? 1 : 0);
  }
  assert.deepEqual(model, parse(path.join(folder, 'normalized.json')));
  assert.equal(jcs(model), fs.readFileSync(path.join(folder,'model.jcs'),'utf8'));
  const identity = jcs({domain:'fenix.fir',canonicalization_version:'0.2.0',model});
  assert.equal(identity, fs.readFileSync(path.join(folder,'identity.jcs'),'utf8'));
  digests[entry.id] = sha(identity);
  assert.equal(digests[entry.id],fs.readFileSync(path.join(folder,'digest.txt'),'utf8').trim());
  for (const kind of ['design','experiment']) {
    const doc = parse(path.join(folder,kind+'.json'));
    assert.equal(sha(jcs(doc.content)),doc.digest);
  }
}
assert.equal(digests.renamed,digests['threshold-n1']);
assert.equal(digests.permuted,digests['threshold-n1']);
assert.equal(digests['late-first'],digests['threshold-n1']);
assert.notEqual(digests['empty-observables'],digests['threshold-n1']);
// Independent scalar boundaries, including ECMAScript's fixed/exponential cutovers.
for (const [number, expected] of [[-0,'0'],[5e-324,'5e-324'],[1e-6,'0.000001'],
  [1e-7,'1e-7'],[1e21,'1e+21'],[9007199254740993,'9007199254740992']]) {
  assert.equal(jcs(number),expected);
}
console.log('PASS independent ECMAScript source/model/identity bytes:',catalog.positive.length);
for (const row of parse(path.join(root,'transport-vectors.json'))) {
  const token = row.raw.match(/-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/)[0];
  if (row.bits) {
    const bytes=Buffer.alloc(8);bytes.writeDoubleBE(Number(token));
    assert.equal(bytes.toString('hex'),row.bits);
  } else assert.equal(BigInt(token).toString(),row.decimal);
}
