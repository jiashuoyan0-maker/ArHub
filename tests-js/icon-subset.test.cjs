'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
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

  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'arhub-icons-crlf-'));
  try {
    fs.mkdirSync(path.join(tempRoot, 'scripts'), { recursive: true });
    fs.mkdirSync(path.join(tempRoot, 'dist', 'assets'), { recursive: true });
    fs.copyFileSync(
      path.join(projectRoot, 'scripts', 'build-icon-subset.cjs'),
      path.join(tempRoot, 'scripts', 'build-icon-subset.cjs'),
    );
    fs.writeFileSync(
      path.join(tempRoot, 'dist', 'assets', 'arhub-icons.js'),
      source.replace(/\r?\n/g, '\r\n'),
      'utf8',
    );
    const crlfResult = spawnSync(process.execPath, ['scripts/build-icon-subset.cjs', '--check'], {
      cwd: tempRoot,
      encoding: 'utf8',
      env: {
        ...process.env,
        NODE_PATH: [path.join(projectRoot, 'node_modules'), process.env.NODE_PATH]
          .filter(Boolean)
          .join(path.delimiter),
      },
    });
    assert.equal(
      crlfResult.status,
      0,
      crlfResult.stderr || crlfResult.stdout || 'CRLF icon synchronization check failed',
    );
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
});
