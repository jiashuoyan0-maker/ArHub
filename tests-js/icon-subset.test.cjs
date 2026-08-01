'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const projectRoot = path.resolve(__dirname, '..');

test('generated Lucide subset stays synchronized and offline', () => {
  const result = spawnSync(process.execPath, ['scripts/build-icon-subset.cjs', '--check'], {
    cwd: projectRoot,
    encoding: 'utf8',
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);

  const source = fs.readFileSync(
    path.join(projectRoot, 'dist', 'assets', 'arhub-icons.js'),
    'utf8',
  );
  assert.match(source, /export function createIcon/);
  assert.match(source, /export function iconForFile/);
  assert.match(source, /export function fileVisual/);
  assert.match(source, /kind: "markdown"/);
  assert.match(source, /kind: "pdf"/);
  assert.match(source, /"Lightbulb"/);
  assert.match(source, /"Bot"/);
  const withoutSvgNamespace = source.replace('http://www.w3.org/2000/svg', '');
  assert.doesNotMatch(withoutSvgNamespace, /https?:\/\//);
  assert.ok(source.length < 150_000, `icon subset is unexpectedly large: ${source.length}`);
});
