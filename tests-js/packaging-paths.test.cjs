'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const projectRoot = path.resolve(__dirname, '..');

test('Windows installer exposes a custom installation directory', (t) => {
  const runtimeDir = fs.mkdtempSync(path.join(os.tmpdir(), 'arhub-runtime-'));
  const previousRuntime = process.env.ARHUB_RUNTIME_DIR;
  const previousSigning = process.env.ARHUB_REQUIRE_SIGNING;
  const previousProfile = process.env.ARHUB_RUNTIME_PROFILE;
  process.env.ARHUB_RUNTIME_DIR = runtimeDir;
  process.env.ARHUB_REQUIRE_SIGNING = '0';
  process.env.ARHUB_RUNTIME_PROFILE = 'full';

  t.after(() => {
    if (previousRuntime === undefined) delete process.env.ARHUB_RUNTIME_DIR;
    else process.env.ARHUB_RUNTIME_DIR = previousRuntime;
    if (previousSigning === undefined) delete process.env.ARHUB_REQUIRE_SIGNING;
    else process.env.ARHUB_REQUIRE_SIGNING = previousSigning;
    if (previousProfile === undefined) delete process.env.ARHUB_RUNTIME_PROFILE;
    else process.env.ARHUB_RUNTIME_PROFILE = previousProfile;
    fs.rmSync(runtimeDir, { recursive: true, force: true });
  });

  const configPath = path.join(projectRoot, 'electron-builder.config.cjs');
  delete require.cache[require.resolve(configPath)];
  const config = require(configPath);

  assert.equal(config.nsis.oneClick, false);
  assert.equal(config.nsis.allowToChangeInstallationDirectory, true);
  assert.equal(config.nsis.perMachine, false);
  assert.equal(config.nsis.deleteAppDataOnUninstall, false);
  assert.equal(path.resolve(config.extraFiles[0].from), path.resolve(runtimeDir));

  process.env.ARHUB_RUNTIME_PROFILE = 'lite';
  delete require.cache[require.resolve(configPath)];
  const liteConfig = require(configPath);
  assert.match(liteConfig.win.artifactName, /-lite-/);
  assert.ok(liteConfig.extraFiles[0].filter.includes('!node/**/*'));
  assert.ok(
    liteConfig.extraFiles[0].filter.includes(
      '!python/Lib/site-packages/tensorflow*/**/*',
    ),
  );
});

test('release tooling does not infer the runtime from an installed ArHub copy', () => {
  const files = [
    'electron-builder.config.cjs',
    'scripts/build-windows.ps1',
    'scripts/assert-runtime.ps1',
    'scripts/export-runtime-lock.ps1',
    'scripts/package-runtime.ps1',
    'scripts/generate-sbom.ps1',
  ];
  const legacyInstallRuntime = /Programs[\\/]ArHub[\\/]runtime/i;

  for (const relativePath of files) {
    const source = fs.readFileSync(path.join(projectRoot, relativePath), 'utf8');
    assert.doesNotMatch(source, legacyInstallRuntime, relativePath);
  }

  const smokeTest = fs.readFileSync(
    path.join(projectRoot, 'scripts', 'smoke-test-installer.ps1'),
    'utf8',
  );
  assert.match(smokeTest, /custom install\\ArHub/);
  assert.match(smokeTest, /StopRunningArHub/);
  assert.match(smokeTest, /registryEntriesBeforeTest/);
  assert.match(smokeTest, /reg\.exe import/);
  assert.match(smokeTest, /DisplayName -match '\^ArHub\(\?:\\s\|\$\)'/);
  assert.match(smokeTest, /\/D=' \+ \$install/);
  assert.doesNotMatch(smokeTest, /\/D=\\"/);
});

test('desktop backend receives explicit runtime, data, and frontend paths', () => {
  const source = fs.readFileSync(path.join(projectRoot, 'main.js'), 'utf8');
  assert.match(source, /ARHUB_RUNTIME_DIR:\s*RUNTIME_DIR/);
  assert.match(source, /ARHUB_DATA_DIR:\s*USER_DATA_DIR/);
  assert.match(source, /ARHUB_FRONTEND_DIST:\s*path\.join\(APP_ROOT, 'dist'\)/);
  assert.match(source, /user_data_dir:\s*USER_DATA_DIR/);
});
