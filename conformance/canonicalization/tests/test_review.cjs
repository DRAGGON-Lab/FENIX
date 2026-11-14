const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {canonical, review, validateCatalog, writeReport} = require('../review_p03.cjs');
const root = path.resolve(__dirname, '..');
test('UTF-16 recursive ordering and array positions', () => {
  assert.equal(canonical({'\ue000':1, '😀':2, '2':3, '10':4, '1':5}), '{"1":5,"10":4,"2":3,"😀":2,"\ue000":1}');
  assert.equal(canonical([3,{z:2,a:1},1]), '[3,{"a":1,"z":2},1]');
  for (const value of [NaN, Infinity, -Infinity, '\ud800', '\udfff']) assert.throws(() => canonical(value));
});
test('all fixed vectors emit bytes and leave contract checks unexecuted', () => {
  const report = review();
  assert.equal(report.report_version, 1);
  assert.equal(report.cases.filter(r => r.serialization === 'NOT_RUN').length, 17);
  for (const row of report.cases) {
    if (row.serialization === 'PASS') assert.match(row.canonical_hex, /^(?:[0-9a-f]{2})+$/);
    else assert.equal(row.canonical_hex, undefined);
  }
});
test('boundary rejects inconsistent stages and coverage', () => {
  const original = JSON.parse(fs.readFileSync(path.join(root, 'catalog.json')));
  for (const mutate of [
    c => {delete c.coverage['signed-zero'];},
    c => {c.coverage['signed-zero'] = ['unknown'];},
    c => {c.coverage['signed-zero'] = ['underflow'];},
    c => {c.coverage['signed-zero'].push(c.coverage['signed-zero'][0]);},
    c => {c.cases[0].stage = 'invalid';},
    c => {c.cases[0].expected_outcome = 'reject';},
    c => {c.cases[0].normalized = c.cases[0].canonical;},
    c => {c.cases.push(c.cases[0]);},
  ]) {
    const catalog = structuredClone(original); mutate(catalog);
    assert.throws(() => validateCatalog(catalog));
  }
});
test('artifact and evaluator outputs are protected through aliases', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'fenix-p03-'));
  try {
    const alias = path.join(tmp, 'alias');
    fs.symlinkSync(path.join(root, 'review_p03.cjs'), alias);
    assert.throws(() => writeReport(alias, {}));
    assert.throws(() => writeReport(path.join(root, 'inputs', 'new.input'), {}));
  } finally {fs.rmSync(tmp, {recursive:true, force:true});}
});

test('both supported catalog statuses preserve rows and reject unknown status', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'fenix-p03-status-'));
  try {
    fs.cpSync(root, tmp, {recursive:true});
    const catalog = JSON.parse(fs.readFileSync(path.join(tmp, 'catalog.json')));
    const originalRows = review().cases;
    for (const status of ['REVIEW_REQUIRED', 'APPROVED']) {
      catalog.status = status;
      fs.writeFileSync(path.join(tmp, 'catalog.json'), JSON.stringify(catalog));
      const report = review(tmp);
      assert.equal(report.fixture_status, status);
      assert.deepEqual(report.cases, originalRows);
    }
    catalog.status = 'UNKNOWN';
    assert.throws(() => validateCatalog(catalog));
  } finally {fs.rmSync(tmp, {recursive:true, force:true});}
});
