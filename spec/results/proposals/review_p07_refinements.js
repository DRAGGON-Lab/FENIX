// Bounded cross-check of proposed refinements, independent of native FENIX.
// Adapted from the retained independently authored initial ECMAScript audit.
// Does not validate arbitrary profiles, raw JSON, or large manifest integers:
// JSON.parse is used only for fixture structure, never as an integer-field oracle.
const fs = require('fs'), crypto = require('crypto');
const base = 'spec/results/proposals/examples/';
const read = path => JSON.parse(fs.readFileSync(path, 'utf8'));
const jcs = v => v === null || typeof v !== 'object' ? JSON.stringify(v) :
  Array.isArray(v) ? '[' + v.map(jcs).join(',') + ']' :
  '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + jcs(v[k])).join(',') + '}';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const bits = value => { const b = Buffer.alloc(8); b.writeDoubleBE(value); return b.toString('hex'); };
const assert = (condition, message) => { if (!condition) throw Error(message); };
const catalog = read(base + 'checksums.json');
for (const [name, expected] of Object.entries(catalog.artifacts)) {
  assert(sha(fs.readFileSync(base + name)) === expected, 'candidate checksum ' + name);
}
for (const name of ['late-first', 'zero-only', 'empty-observables', 'multi-observables']) {
  const prefix = base + name;
  const manifest = read(prefix + '.manifest.json'), result = read(prefix + '.result.json');
  const resultBytes = fs.readFileSync(prefix + '.result.json');
  assert(sha(resultBytes) === manifest.output.sha256, 'result checksum ' + name);
  assert(sha(Buffer.concat([resultBytes, Buffer.from(' ')])) !== manifest.output.sha256,
    'formatting checksum control ' + name);
  const model = read(name === 'multi-observables' ? base + 'multi-observables.fir.json' :
    'spec/fir/proposals/examples/production-decay' +
      (name === 'empty-observables' ? '-no-observables' : '') + '.json').model;
  for (const field of ['states', 'parameters', 'reactions', 'observables'])
    model[field].sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
  model.equations.sort((a, b) => a.state < b.state ? -1 : a.state > b.state ? 1 : 0);
  model.assumptions.sort();
  const digest = sha(Buffer.from(jcs({domain: 'fenix.fir', canonicalization_version: '0.1.0', model})));
  assert(digest === manifest.fir.digest && digest === result.fir_digest, 'FIR digest ' + name);
  assert(JSON.stringify(result.state_ids) === JSON.stringify(model.states.map(s => s.id)), 'state order');
  assert(JSON.stringify(result.state_units) === JSON.stringify(model.states.map(s => s.unit)), 'state units');
  assert(JSON.stringify(result.observable_ids) === JSON.stringify(model.observables.map(o => o.id)), 'observable order');
  assert(JSON.stringify(result.observable_state_ids) === JSON.stringify(model.observables.map(o => o.state)), 'observable mappings');
  assert(JSON.stringify(result.observable_units) === JSON.stringify(model.observables.map(o => o.unit)), 'observable units');
  assert(result.observable_values.length === result.times.length, 'observable sample count');
  result.observable_values.forEach((row, i) => {
    assert(row.length === model.observables.length, 'observable column count');
    row.forEach((value, j) => {
      const column = result.state_ids.indexOf(model.observables[j].state);
      assert(bits(value) === bits(result.state_values[i][column]), 'observable-state bits');
    });
  });
  assert(manifest.backend.profile === 'python-scipy-ode/0.1.0', 'backend profile');
  console.log('PASS candidate bytes, normalized FIR and observable columns:', name, digest);
}
const multi = read(base + 'multi-observables.experiment.json');
assert(sha(Buffer.from(jcs(multi.content))) === multi.digest, 'multi source content digest');
assert(JSON.stringify(multi.content.observables.map(o => o.id)) === '["z_amount","a_amount","m_amount"]',
  'source noncanonical order');
for (const probe of read(base + 'numeric-tokens.json').binary64)
  assert(bits(JSON.parse(probe.token)) === probe.bits, 'binary64 bits ' + probe.token);
console.log('PASS', Object.keys(catalog.artifacts).length,
  'catalog hashes, 4 result hashes/FIR identities/mappings, 1 source digest, 8 binary64 probes');
