'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { hashFileSha256, readJson, writeJsonAtomic } = require('./runtime-store');

const HEALTH_SCHEMA = 2;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;

function createInitialState(version = '') {
  return {
    schemaVersion: HEALTH_SCHEMA,
    healthyVersion: String(version || ''),
    previousVersion: '',
    previousInstaller: '',
    previousInstallerSha256: '',
    previousInstallerBytes: 0,
    pendingVersion: '',
    pendingSince: '',
    rollbackStatus: 'idle',
    rollbackAttempts: 0,
    rollbackClaimedAt: '',
    lastFailureAt: '',
    lastFailureReason: '',
  };
}

function loadHealthState(statePath, version = '') {
  const parsed = readJson(statePath);
  if (!parsed || ![1, HEALTH_SCHEMA].includes(parsed.schemaVersion)) return createInitialState(version);
  return { ...createInitialState(version), ...parsed, schemaVersion: HEALTH_SCHEMA };
}

function isPathInside(parent, child) {
  if (!String(parent || '').trim() || !String(child || '').trim()) return false;
  const relative = path.relative(path.resolve(parent), path.resolve(child));
  return Boolean(relative) && !relative.startsWith('..') && !path.isAbsolute(relative);
}

function rollbackStoreRoot(localAppData) {
  const base = String(localAppData || process.env.LOCALAPPDATA || '').trim();
  if (!base) throw new Error('LOCALAPPDATA is required to resolve the rollback store.');
  return path.resolve(base, 'ArHub', 'rollback-installers');
}

function normalizeSha256(value) {
  const hash = String(value || '').trim().toLowerCase();
  return SHA256_PATTERN.test(hash) ? hash : '';
}

function validateRollbackRoot(rollbackRoot, cacheRoot = '') {
  if (!String(rollbackRoot || '').trim()) throw new Error('A dedicated rollback root is required.');
  const resolved = path.resolve(rollbackRoot);
  if (String(cacheRoot || '').trim()) {
    const cache = path.resolve(cacheRoot);
    if (resolved === cache || isPathInside(cache, resolved) || isPathInside(resolved, cache)) {
      throw new Error('The rollback store must be separate from the updater cache.');
    }
  }
  return resolved;
}

function preserveRollbackInstaller(options = {}) {
  const sourceInstaller = path.resolve(options.sourceInstaller || '');
  const rollbackRoot = validateRollbackRoot(options.rollbackRoot, options.cacheRoot);
  const currentVersion = String(options.currentVersion || '').trim();
  if (!currentVersion || !fs.existsSync(sourceInstaller) || !fs.statSync(sourceInstaller).isFile()) {
    throw new Error('A current version and readable source installer are required for rollback preservation.');
  }

  const sourceHash = hashFileSha256(sourceInstaller);
  const expectedHash = normalizeSha256(options.expectedSha256);
  if (options.expectedSha256 && !expectedHash) throw new Error('The expected installer SHA-256 is invalid.');
  if (expectedHash && sourceHash !== expectedHash) throw new Error('The source installer SHA-256 does not match.');

  const safeVersion = currentVersion.replace(/[^0-9A-Za-z._-]/g, '_');
  const versionRoot = path.join(rollbackRoot, 'versions', safeVersion);
  const destination = path.join(versionRoot, `${sourceHash}.exe`);
  fs.mkdirSync(versionRoot, { recursive: true });
  if (fs.existsSync(destination)) {
    if (hashFileSha256(destination) !== sourceHash) {
      throw new Error(`Rollback installer collision: ${destination}`);
    }
    return { path: destination, sha256: sourceHash, bytes: fs.statSync(destination).size, version: currentVersion };
  }

  const staging = path.join(
    rollbackRoot,
    `.installer.staging-${process.pid}-${crypto.randomBytes(6).toString('hex')}`,
  );
  try {
    fs.copyFileSync(sourceInstaller, staging, fs.constants.COPYFILE_EXCL);
    const sourceBytes = fs.statSync(sourceInstaller).size;
    const copiedBytes = fs.statSync(staging).size;
    if (sourceBytes !== copiedBytes || hashFileSha256(staging) !== sourceHash) {
      throw new Error('The staged rollback installer failed verification.');
    }
    try {
      fs.renameSync(staging, destination);
    } catch (error) {
      if (!fs.existsSync(destination) || hashFileSha256(destination) !== sourceHash) throw error;
    }
  } finally {
    try { fs.rmSync(staging, { force: true }); } catch {}
  }
  return { path: destination, sha256: sourceHash, bytes: fs.statSync(destination).size, version: currentVersion };
}

function verifyRollbackInstaller(installerPath, expectedSha256, rollbackRoot) {
  const expectedHash = normalizeSha256(expectedSha256);
  if (!expectedHash || !isPathInside(rollbackRoot, installerPath) || !fs.existsSync(installerPath)) {
    return { valid: false, reason: 'preserved rollback installer is unavailable' };
  }
  try {
    if (!fs.statSync(installerPath).isFile() || hashFileSha256(installerPath) !== expectedHash) {
      return { valid: false, reason: 'preserved rollback installer failed SHA-256 verification' };
    }
  } catch {
    return { valid: false, reason: 'preserved rollback installer could not be verified' };
  }
  return { valid: true, path: path.resolve(installerPath), sha256: expectedHash };
}

function markUpdatePending(statePath, options = {}) {
  const currentVersion = String(options.currentVersion || '');
  const nextVersion = String(options.nextVersion || '');
  const rollbackRoot = validateRollbackRoot(options.rollbackRoot, options.cacheRoot);
  if (!nextVersion || nextVersion === currentVersion) throw new Error('A distinct pending update version is required.');
  const suppliedRollback = options.rollbackInstaller || {};
  const preserved = suppliedRollback.path
    ? suppliedRollback
    : preserveRollbackInstaller({
      sourceInstaller: options.sourceInstaller || options.previousInstaller,
      rollbackRoot,
      cacheRoot: options.cacheRoot,
      currentVersion,
      expectedSha256: options.expectedSha256 || options.previousInstallerSha256,
    });
  const installerPath = path.resolve(preserved.path || '');
  const installerHash = normalizeSha256(preserved.sha256);
  const verification = verifyRollbackInstaller(installerPath, installerHash, rollbackRoot);
  if (!verification.valid) throw new Error(verification.reason);

  const state = loadHealthState(statePath, currentVersion);
  state.healthyVersion = state.healthyVersion || currentVersion;
  state.previousVersion = currentVersion;
  state.previousInstaller = verification.path;
  state.previousInstallerSha256 = verification.sha256;
  state.previousInstallerBytes = fs.statSync(verification.path).size;
  state.pendingVersion = nextVersion;
  state.pendingSince = new Date().toISOString();
  state.rollbackStatus = 'available';
  state.rollbackAttempts = 0;
  state.rollbackClaimedAt = '';
  state.lastFailureAt = '';
  state.lastFailureReason = '';
  writeJsonAtomic(statePath, state);
  return state;
}

function getStartupDecision(statePath, currentVersion, options = {}) {
  const state = loadHealthState(statePath, currentVersion);
  const maxRollbackAttempts = Math.max(1, Number(options.maxRollbackAttempts || 1));
  if (!state.pendingVersion || state.pendingVersion !== String(currentVersion || '')) {
    return { action: 'continue', state };
  }
  if (state.rollbackAttempts >= maxRollbackAttempts || state.rollbackStatus === 'claimed') {
    return { action: 'continue', state, reason: 'rollback attempt already claimed' };
  }
  let rollbackRoot;
  try {
    rollbackRoot = validateRollbackRoot(options.rollbackRoot, options.cacheRoot);
  } catch (error) {
    return { action: 'continue', state, reason: error.message };
  }
  const verification = verifyRollbackInstaller(
    state.previousInstaller,
    state.previousInstallerSha256,
    rollbackRoot,
  );
  if (!verification.valid) return { action: 'continue', state, reason: verification.reason };
  return { action: 'probe', state };
}

function claimRollback(statePath, currentVersion, options = {}) {
  const state = loadHealthState(statePath, currentVersion);
  const maxRollbackAttempts = Math.max(1, Number(options.maxRollbackAttempts || 1));
  if (!state.pendingVersion || state.pendingVersion !== String(currentVersion || '')) {
    return { action: 'continue', state, reason: 'no rollback is pending for this version' };
  }
  if (state.rollbackAttempts >= maxRollbackAttempts || state.rollbackStatus === 'claimed') {
    return { action: 'continue', state, reason: 'rollback attempt already claimed' };
  }

  let verification;
  try {
    const rollbackRoot = validateRollbackRoot(options.rollbackRoot, options.cacheRoot);
    verification = verifyRollbackInstaller(
      state.previousInstaller,
      state.previousInstallerSha256,
      rollbackRoot,
    );
  } catch (error) {
    verification = { valid: false, reason: error.message };
  }

  state.lastFailureAt = new Date().toISOString();
  state.lastFailureReason = String(options.reason || 'startup health check failed');
  if (!verification.valid) {
    state.rollbackAttempts = maxRollbackAttempts;
    state.rollbackStatus = 'unavailable';
    state.lastFailureReason = `${state.lastFailureReason}: ${verification.reason}`;
    writeJsonAtomic(statePath, state);
    return { action: 'continue', state, reason: verification.reason };
  }

  // Persist the claim before launching the installer. A crash cannot cause a
  // second rollback launch on the next startup.
  state.rollbackAttempts += 1;
  state.rollbackStatus = 'claimed';
  state.rollbackClaimedAt = new Date().toISOString();
  writeJsonAtomic(statePath, state);
  return {
    action: 'rollback',
    state,
    installerPath: verification.path,
    installerSha256: verification.sha256,
    targetVersion: state.previousVersion,
  };
}

function recordStartupFailure(statePath, currentVersion, options = {}) {
  return claimRollback(statePath, currentVersion, options).state;
}

function markVersionHealthy(statePath, currentVersion) {
  const state = loadHealthState(statePath, currentVersion);
  state.healthyVersion = String(currentVersion || '');
  state.pendingVersion = '';
  state.pendingSince = '';
  state.rollbackStatus = 'idle';
  state.rollbackAttempts = 0;
  state.rollbackClaimedAt = '';
  state.lastFailureAt = '';
  state.lastFailureReason = '';
  writeJsonAtomic(statePath, state);
  return state;
}

function clearFailedPendingVersion(statePath, currentVersion) {
  const state = loadHealthState(statePath, currentVersion);
  state.pendingVersion = '';
  state.pendingSince = '';
  state.rollbackStatus = state.rollbackAttempts > 0 ? 'exhausted' : 'idle';
  writeJsonAtomic(statePath, state);
  return state;
}

module.exports = {
  HEALTH_SCHEMA,
  claimRollback,
  clearFailedPendingVersion,
  createInitialState,
  getStartupDecision,
  isPathInside,
  loadHealthState,
  markUpdatePending,
  markVersionHealthy,
  preserveRollbackInstaller,
  recordStartupFailure,
  rollbackStoreRoot,
  verifyRollbackInstaller,
};
