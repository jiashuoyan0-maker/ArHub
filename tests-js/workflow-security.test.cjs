'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const workflowDir = path.join(__dirname, '..', '.github', 'workflows');

test('third-party workflow actions are pinned to immutable commits', () => {
  const workflows = fs.readdirSync(workflowDir).filter((name) => /\.ya?ml$/i.test(name));
  const unpinned = [];

  for (const name of workflows) {
    const text = fs.readFileSync(path.join(workflowDir, name), 'utf8');
    for (const [index, line] of text.split(/\r?\n/).entries()) {
      const match = line.match(/^\s*(?:-\s*)?uses:\s*([^\s#]+)/);
      if (!match || match[1].startsWith('./') || match[1].startsWith('docker://')) continue;
      if (!/@[0-9a-f]{40}$/i.test(match[1])) {
        unpinned.push(`${name}:${index + 1} (${match[1]})`);
      }
    }
  }

  assert.deepEqual(unpinned, []);
});

test('release upload and checksum asset allowlists stay aligned', () => {
  const releaseWorkflow = fs.readFileSync(path.join(workflowDir, 'release-windows.yml'), 'utf8');
  const checksumScript = fs.readFileSync(
    path.join(__dirname, '..', 'scripts', 'create-checksums.ps1'),
    'utf8',
  );
  const requiredPatterns = [
    'ArHub-Setup-*',
    '*.blockmap',
    'latest.yml',
    'sbom-*.cdx.json',
    'installer-smoke-report.json',
  ];
  for (const pattern of requiredPatterns) {
    assert.match(releaseWorkflow, new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    assert.match(checksumScript, new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  assert.doesNotMatch(checksumScript, /builder-debug\.yml/);
});

test('Windows CI uses portable Node test discovery and avoids duplicate branch runs', () => {
  const quality = fs.readFileSync(path.join(workflowDir, 'quality.yml'), 'utf8');
  const packageMetadata = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'),
  );
  assert.equal(packageMetadata.scripts['test:node'], 'node scripts/run-node-tests.cjs');
  assert.doesNotMatch(packageMetadata.scripts['test:node'], /[*?]/);
  assert.match(quality, /push:\s*\r?\n\s+branches:\s*\[main\]/);
  assert.match(quality, /pull_request:/);
});
