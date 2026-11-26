// Development-only bridge to the existing independent RFC 8785 reference.
// Inputs are JSON data; nothing is evaluated as code. No native FENIX imports.
const readline = require('node:readline');
const { canonical } = require('../canonicalization/review_p03.cjs');
readline.createInterface({ input: process.stdin }).on('line', line => {
  try {
    const value = JSON.parse(JSON.parse(line).raw);
    process.stdout.write(JSON.stringify({ canonical: canonical(value) }) + '\n');
  } catch (error) {
    process.stdout.write(JSON.stringify({ error: String(error) }) + '\n');
  }
});
