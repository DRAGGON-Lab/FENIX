// Independent review only: exact byte checksums, complete P03 order and IEEE bits.
const fs = require('fs'), crypto = require('crypto');
const read = path => JSON.parse(fs.readFileSync(path, 'utf8'));
const jcs = v => v === null || typeof v !== 'object' ? JSON.stringify(v) :
  Array.isArray(v) ? '[' + v.map(jcs).join(',') + ']' :
  '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + jcs(v[k])).join(',') + '}';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const catalog = read('spec/results/proposals/examples/checksums.json');
for (const [name, expected] of Object.entries(catalog.artifacts)) {
  if (sha(fs.readFileSync('spec/results/proposals/examples/' + name)) !== expected)
    throw Error('candidate checksum ' + name);
}
for (const name of ['late-first', 'zero-only', 'empty-observables']) {
  const prefix = 'spec/results/proposals/examples/' + name;
  const manifest = read(prefix + '.manifest.json'), result = read(prefix + '.result.json');
  if (sha(fs.readFileSync(prefix + '.result.json')) !== manifest.output.sha256)
    throw Error('result checksum ' + name);
  const model = read('spec/fir/proposals/examples/production-decay' +
    (name === 'empty-observables' ? '-no-observables' : '') + '.json').model;
  for (const field of ['states', 'parameters', 'reactions', 'observables'])
    model[field].sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
  model.equations.sort((a, b) => a.state < b.state ? -1 : a.state > b.state ? 1 : 0);
  model.assumptions.sort();
  const digest = sha(Buffer.from(jcs({domain: 'fenix.fir', canonicalization_version: '0.1.0', model})));
  if (digest !== manifest.fir.digest || digest !== result.fir_digest)
    throw Error('FIR digest ' + name);
  console.log('PASS independent ECMAScript bytes and FIR:', name, digest);
}
for (const probe of read('spec/results/proposals/examples/numeric-tokens.json').binary64) {
  const buffer = Buffer.alloc(8);
  buffer.writeDoubleBE(JSON.parse(probe.token));
  if (buffer.toString('hex') !== probe.bits) throw Error('binary64 bits ' + probe.token);
}
console.log('PASS 7 catalog hashes, 3 result hashes and normalized FIR identities, 8 binary64 probes');
