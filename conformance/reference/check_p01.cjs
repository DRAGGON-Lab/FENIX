// Independent ECMAScript primitive encoding + UTF-16 sorting (RFC 8785 App. A).
// This cross-check never executes input strings or generates expected fixtures.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const directory = path.join(root, 'conformance/bioir');
const catalog = JSON.parse(fs.readFileSync(path.join(directory, 'catalog.json'), 'utf8'));
function canonical(v) {
  if (v === null || typeof v !== 'object') return JSON.stringify(v);
  if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']';
  return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canonical(v[k])).join(',') + '}';
}
let checked = 0;
for (const c of catalog.cases) {
  if (c.operation === 'canonical') {
    const v = JSON.parse(fs.readFileSync(path.join(directory, c.input), 'utf8'));
    assert.equal(canonical(v), c.expected.canonical_utf8, c.id);
    checked++;
  } else if (['design', 'experiment', 'revision'].includes(c.operation) && c.expected.category !== 'DIGEST') {
    const doc = JSON.parse(fs.readFileSync(path.join(directory, c.input), 'utf8'));
    const digest = crypto.createHash('sha256').update(canonical(doc.content), 'utf8').digest('hex');
    assert.equal(digest, doc.digest, c.id);
    checked++;
  }
}
console.log(`Independent ECMAScript cross-check passed: ${checked} candidate canonical/digest cases. Fixture approval remains pending.`);
