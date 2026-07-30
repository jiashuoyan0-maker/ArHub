'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');
const test = require('node:test');

const {
  getArtifactName,
  getSigningSuffixes,
  shouldSign,
} = require('../packaging/signing-policy.cjs');

test('release artifact names are deterministic', () => {
  assert.equal(getArtifactName('1.0.9'), 'ArHub-Setup-1.0.9-x64.exe');
  assert.equal(getArtifactName('1.0.9', '-unsigned'), 'ArHub-Setup-1.0.9-x64-unsigned.exe');
});

test('signing policy includes only ArHub-owned Windows executables', () => {
  const suffixes = getSigningSuffixes('1.0.9');
  assert.deepEqual(suffixes, [
    'ArHub.exe',
    path.join('win-unpacked', 'resources', 'elevate.exe'),
    'ArHub-Setup-1.0.9-x64.exe',
    'ArHub-Setup-1.0.9-x64.__uninstaller.exe',
    '!.exe',
  ]);

  assert.equal(shouldSign('release\\win-unpacked\\ArHub.exe', '1.0.9'), true);
  assert.equal(shouldSign('release\\win-unpacked\\resources\\elevate.exe', '1.0.9'), true);
  assert.equal(shouldSign('release\\ArHub-Setup-1.0.9-x64.exe', '1.0.9'), true);
  assert.equal(shouldSign('release\\ArHub-Setup-1.0.9-x64.__uninstaller.exe', '1.0.9'), true);
});

test('signing policy preserves bundled third-party executables', () => {
  const vendorFiles = [
    'runtime\\python\\python.exe',
    'runtime\\node\\node.exe',
    'runtime\\git\\cmd\\git.exe',
    'runtime\\pandoc\\pandoc.exe',
    'runtime\\draw.io\\draw.io.exe',
    'runtime\\draw.io\\resources\\elevate.exe',
    'runtime\\texlive\\miktex\\bin\\x64\\xelatex.exe',
    'resources\\app\\tools\\vendor.exe',
  ];
  for (const file of vendorFiles) {
    assert.equal(shouldSign(file, '1.0.9'), false, file);
  }
});

test('unsigned candidate uses the same narrow signing policy', () => {
  assert.equal(
    shouldSign('release\\ArHub-Setup-1.0.9-x64-unsigned.exe', '1.0.9', '-unsigned'),
    true,
  );
  assert.equal(
    shouldSign('release\\ArHub-Setup-1.0.9-x64-unsigned.__uninstaller.exe', '1.0.9', '-unsigned'),
    true,
  );
  assert.equal(shouldSign('runtime\\python\\python.exe', '1.0.9', '-unsigned'), false);
});
