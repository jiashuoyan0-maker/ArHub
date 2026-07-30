'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const projectRoot = path.resolve(__dirname, '..');
const testDir = path.join(projectRoot, 'tests-js');
const tests = fs.readdirSync(testDir, { withFileTypes: true })
  .filter((entry) => entry.isFile() && entry.name.endsWith('.test.cjs'))
  .map((entry) => path.join(testDir, entry.name))
  .sort();

if (tests.length === 0) {
  console.error(`No Node.js tests were found in ${testDir}.`);
  process.exit(1);
}

const result = spawnSync(process.execPath, ['--test', ...tests], {
  cwd: projectRoot,
  env: process.env,
  stdio: 'inherit',
});
if (result.error) throw result.error;
process.exit(result.status === null ? 1 : result.status);
