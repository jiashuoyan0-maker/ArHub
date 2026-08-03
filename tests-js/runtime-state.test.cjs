'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  migrateLegacyRuntime,
  readJson,
  resolveRuntime,
  writeJsonAtomic,
} = require('../runtime-store');
const {
  claimRollback,
  getStartupDecision,
  markUpdatePending,
  preserveRollbackInstaller,
} = require('../update-health');

function fixture(name) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `arhub-${name}-`));
}

function createLiteRuntime(runtimeDir, marker = 'runtime') {
  fs.mkdirSync(path.join(runtimeDir, 'python'), { recursive: true });
  fs.writeFileSync(path.join(runtimeDir, 'python', 'python.exe'), marker, 'utf8');
  fs.writeFileSync(path.join(runtimeDir, 'python', 'python311.zip'), `${marker}-stdlib`, 'utf8');
}

test('atomic JSON writes replace an existing Windows destination without residue', (t) => {
  const root = fixture('atomic-json');
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const statePath = path.join(root, 'state', 'current.json');

  writeJsonAtomic(statePath, { generation: 1, payload: 'old' });
  writeJsonAtomic(statePath, { generation: 2, payload: 'new' });

  assert.deepEqual(readJson(statePath), { generation: 2, payload: 'new' });
  assert.deepEqual(fs.readdirSync(path.dirname(statePath)), ['current.json']);
});

test('legacy runtime is copied, validated, promoted, pointed to, then removed', (t) => {
  const root = fixture('runtime-migration');
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const legacyRuntimeDir = path.join(root, 'custom-install', 'runtime');
  const storeRoot = path.join(root, 'local-app-data', 'ArHub', 'runtime-store');
  createLiteRuntime(legacyRuntimeDir);

  const result = migrateLegacyRuntime({
    legacyRuntimeDir,
    storeRoot,
    runtimeVersion: '2026.07.30.3',
    profile: 'lite',
    lockMetadata: {
      schemaVersion: 1,
      runtimeVersion: '2026.07.30.3',
      architecture: 'x64',
      manifestSha256: '1'.repeat(64),
      lockSha256: '2'.repeat(64),
    },
  });

  assert.equal(result.migrated, true);
  assert.equal(result.legacyRemoved, true);
  assert.equal(fs.existsSync(legacyRuntimeDir), false);
  assert.equal(fs.readFileSync(path.join(result.runtimeDir, 'python', 'python.exe'), 'utf8'), 'runtime');
  const pointer = readJson(path.join(storeRoot, 'current.json'));
  assert.equal(pointer.runtimeVersion, '2026.07.30.3');
  assert.equal(pointer.profile, 'lite');
  assert.equal(pointer.lock.runtimeVersion, '2026.07.30.3');
  assert.equal(pointer.lock.profile, 'lite');
  assert.equal(pointer.lock.manifestSha256, '1'.repeat(64));
  assert.equal(pointer.lock.lockSha256, '2'.repeat(64));
  assert.equal(resolveRuntime({ storeRoot }).runtimeDir, result.runtimeDir);
});

test('an incomplete destination collision leaves current.json byte-for-byte unchanged', (t) => {
  const root = fixture('runtime-collision');
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const legacyRuntimeDir = path.join(root, 'install', 'runtime');
  const storeRoot = path.join(root, 'store');
  const destination = path.join(storeRoot, 'versions', '2026.07.30.3', 'lite');
  const pointerPath = path.join(storeRoot, 'current.json');
  createLiteRuntime(legacyRuntimeDir);
  fs.mkdirSync(destination, { recursive: true });
  fs.writeFileSync(path.join(destination, 'partial-download'), 'partial', 'utf8');
  fs.mkdirSync(storeRoot, { recursive: true });
  fs.writeFileSync(pointerPath, '{"sentinel":"unchanged"}\n', 'utf8');
  const before = fs.readFileSync(pointerPath);

  assert.throws(() => migrateLegacyRuntime({
    legacyRuntimeDir,
    storeRoot,
    runtimeVersion: '2026.07.30.3',
    profile: 'lite',
  }), /destination collision/);
  assert.deepEqual(fs.readFileSync(pointerPath), before);
  assert.equal(fs.existsSync(legacyRuntimeDir), true);
  assert.equal(fs.existsSync(path.join(destination, 'partial-download')), true);
});

test('pending update preserves a hashed installer outside updater cache and claims rollback once', (t) => {
  const root = fixture('rollback-once');
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const cacheRoot = path.join(root, 'arhub-updater');
  const rollbackRoot = path.join(root, 'ArHub', 'rollback-installers');
  const sourceInstaller = path.join(cacheRoot, 'installer.exe');
  const statePath = path.join(root, 'health.json');
  fs.mkdirSync(cacheRoot, { recursive: true });
  fs.writeFileSync(sourceInstaller, 'verified-v1-installer', 'utf8');

  const state = markUpdatePending(statePath, {
    currentVersion: '1.0.11',
    nextVersion: '1.0.12',
    previousInstaller: sourceInstaller,
    cacheRoot,
    rollbackRoot,
  });
  assert.equal(state.rollbackStatus, 'available');
  assert.equal(state.previousInstaller.startsWith(`${rollbackRoot}${path.sep}`), true);
  assert.equal(state.previousInstaller.startsWith(`${cacheRoot}${path.sep}`), false);
  assert.equal(getStartupDecision(statePath, '1.0.12', { cacheRoot, rollbackRoot }).action, 'probe');

  const first = claimRollback(statePath, '1.0.12', {
    cacheRoot,
    rollbackRoot,
    reason: 'backend health check failed',
  });
  assert.equal(first.action, 'rollback');
  assert.equal(first.state.rollbackAttempts, 1);
  assert.equal(first.state.rollbackStatus, 'claimed');
  assert.equal(first.installerPath, state.previousInstaller);

  const second = claimRollback(statePath, '1.0.12', { cacheRoot, rollbackRoot });
  assert.equal(second.action, 'continue');
  assert.equal(second.reason, 'rollback attempt already claimed');
  assert.equal(second.state.rollbackAttempts, 1);
});

test('tampering with a preserved rollback installer fails closed', (t) => {
  const root = fixture('rollback-hash');
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const rollbackRoot = path.join(root, 'rollback');
  const cacheRoot = path.join(root, 'cache');
  const sourceInstaller = path.join(cacheRoot, 'installer.exe');
  const statePath = path.join(root, 'health.json');
  fs.mkdirSync(cacheRoot, { recursive: true });
  fs.writeFileSync(sourceInstaller, 'known-installer', 'utf8');
  const preserved = preserveRollbackInstaller({
    sourceInstaller,
    rollbackRoot,
    cacheRoot,
    currentVersion: '1.0.11',
  });
  markUpdatePending(statePath, {
    currentVersion: '1.0.11',
    nextVersion: '1.0.12',
    rollbackInstaller: preserved,
    rollbackRoot,
    cacheRoot,
  });
  fs.writeFileSync(preserved.path, 'tampered-installer', 'utf8');

  const decision = getStartupDecision(statePath, '1.0.12', { rollbackRoot, cacheRoot });
  assert.equal(decision.action, 'continue');
  assert.match(decision.reason, /SHA-256/);
  const claim = claimRollback(statePath, '1.0.12', { rollbackRoot, cacheRoot });
  assert.equal(claim.action, 'continue');
  assert.equal(claim.state.rollbackStatus, 'unavailable');
  assert.equal(claim.state.rollbackAttempts, 1);
});
