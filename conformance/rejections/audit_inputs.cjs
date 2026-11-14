// Independent ECMAScript RFC 8785 Appendix A digest audit. Never writes artifacts.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, 'catalog.json'), 'utf8'));
function canonical(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
}
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
let checked = 0;
for (const c of catalog.cases) {
  for (const [identity, artifact] of Object.entries(c.inputs)) {
    const raw = fs.readFileSync(path.join(root, artifact.path));
    assert.equal(sha(raw), artifact.sha256, c.id + ':' + identity);
    const bioir = ['design', 'experiment', 'previous'].includes(identity) ||
      (identity === 'primary' && ['design', 'experiment', 'revision'].includes(c.operation));
    if (!bioir) continue;
    const doc = JSON.parse(raw.toString('utf8'));
    const actual = sha(Buffer.from(canonical(doc.content), 'utf8'));
    const intendedDigestFault = c.expected.category === 'DIGEST' && c.expected.document === identity;
    if (intendedDigestFault) assert.notEqual(actual, doc.digest, c.id);
    else assert.equal(actual, doc.digest, c.id + ':' + identity);
    checked++;
  }
}
console.log(`PASS: ${checked} BioIR digest checks; semantic faults cannot hide behind stale content digests.`);
