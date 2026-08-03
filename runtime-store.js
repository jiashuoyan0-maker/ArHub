'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const RUNTIME_STATE_SCHEMA = 2;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;

function normalizeRuntimeProfile(value) {
  const profile = String(value || '').trim().toLowerCase();
  return ['lite', 'full'].includes(profile) ? profile : 'unknown';
}

function runtimeStoreRoot(localAppData) {
  const base = String(localAppData || process.env.LOCALAPPDATA || '').trim();
  if (!base) throw new Error('LOCALAPPDATA is required to resolve the runtime store.');
  return path.resolve(base, 'ArHub', 'runtime-store');
}

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return null;
  }
}

function waitForRenameRetry(milliseconds) {
  const signal = new Int32Array(new SharedArrayBuffer(4));
  Atomics.wait(signal, 0, 0, milliseconds);
}

function writeJsonAtomic(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const suffix = `${process.pid}-${crypto.randomBytes(6).toString('hex')}`;
  const temporary = `${filePath}.${suffix}.tmp`;
  let descriptor;
  try {
    descriptor = fs.openSync(temporary, 'wx');
    fs.writeFileSync(descriptor, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
    fs.fsyncSync(descriptor);
    fs.closeSync(descriptor);
    descriptor = undefined;

    // Windows can briefly return EPERM when Defender or an indexer opens the
    // destination. rename still provides replacement semantics once released.
    for (let attempt = 0; ; attempt += 1) {
      try {
        fs.renameSync(temporary, filePath);
        break;
      } catch (error) {
        const transient = ['EACCES', 'EBUSY', 'EPERM'].includes(error.code);
        if (!transient || attempt >= 4) throw error;
        waitForRenameRetry(25 * (attempt + 1));
      }
    }
  } finally {
    if (descriptor !== undefined) fs.closeSync(descriptor);
    try { fs.rmSync(temporary, { force: true }); } catch {}
  }
}

function hashFileSha256(filePath) {
  const hash = crypto.createHash('sha256');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  const descriptor = fs.openSync(filePath, 'r');
  try {
    for (;;) {
      const bytesRead = fs.readSync(descriptor, buffer, 0, buffer.length, null);
      if (!bytesRead) break;
      hash.update(buffer.subarray(0, bytesRead));
    }
  } finally {
    fs.closeSync(descriptor);
  }
  return hash.digest('hex');
}

function inferRuntimeProfile(runtimeDir) {
  if (!runtimeDir || !fs.existsSync(path.join(runtimeDir, 'python', 'python.exe'))) return 'unknown';
  return fs.existsSync(path.join(runtimeDir, 'node', 'node.exe')) ? 'full' : 'lite';
}

function runtimeLooksUsable(runtimeDir, profile) {
  if (!runtimeDir || !fs.existsSync(path.join(runtimeDir, 'python', 'python.exe'))) return false;
  if (normalizeRuntimeProfile(profile) !== 'full') return true;
  return [
    ['node', 'node.exe'],
    ['git', 'cmd', 'git.exe'],
    ['pandoc', 'pandoc.exe'],
    ['draw.io', 'draw.io.exe'],
    ['texlive', 'miktex', 'bin', 'x64', 'xelatex.exe'],
  ].every((segments) => fs.existsSync(path.join(runtimeDir, ...segments)));
}

function normalizeSha256(value) {
  const hash = String(value || '').trim().toLowerCase();
  return SHA256_PATTERN.test(hash) ? hash : '';
}

function normalizeRuntimeLockMetadata(value, runtimeVersion, profile) {
  const lock = value && typeof value === 'object' ? value : {};
  const lockedVersion = String(lock.runtimeVersion || runtimeVersion || '').trim();
  if (lockedVersion && runtimeVersion && lockedVersion !== runtimeVersion) {
    throw new Error(`Runtime lock ${lockedVersion} does not match requested runtime ${runtimeVersion}.`);
  }
  return {
    schemaVersion: Number.isInteger(Number(lock.schemaVersion)) ? Number(lock.schemaVersion) : 0,
    runtimeVersion: String(runtimeVersion || lockedVersion),
    profile: normalizeRuntimeProfile(profile),
    architecture: String(lock.architecture || process.arch || '').trim(),
    manifestSha256: normalizeSha256(lock.manifestSha256),
    pythonRequirementsSha256: normalizeSha256(lock.pythonRequirementsSha256),
    lockSha256: normalizeSha256(lock.lockSha256 || lock.sha256),
  };
}

function requiredRuntimeComponents(profile) {
  return normalizeRuntimeProfile(profile) === 'full'
    ? new Set(['python', 'node', 'git', 'pandoc', 'draw.io', 'texlive'])
    : new Set(['python']);
}

function validateRuntimeProbes(runtimeDir, profile, runtimeLock) {
  if (!runtimeLooksUsable(runtimeDir, profile)) {
    throw new Error(`The ${profile} runtime is incomplete at ${runtimeDir}.`);
  }
  if (!runtimeLock || typeof runtimeLock.probes !== 'object') return;
  const components = requiredRuntimeComponents(profile);
  for (const [relativePath, expected] of Object.entries(runtimeLock.probes)) {
    const normalizedRelative = String(relativePath).replace(/\\/g, '/');
    if (!components.has(normalizedRelative.split('/')[0])) continue;
    const probePath = path.resolve(runtimeDir, ...normalizedRelative.split('/'));
    if (!probePath.startsWith(`${path.resolve(runtimeDir)}${path.sep}`) || !fs.existsSync(probePath)) {
      throw new Error(`Runtime probe is missing: ${relativePath}`);
    }
    const stat = fs.statSync(probePath);
    if (Number.isFinite(Number(expected.bytes)) && stat.size !== Number(expected.bytes)) {
      throw new Error(`Runtime probe size mismatch: ${relativePath}`);
    }
    const expectedHash = normalizeSha256(expected.sha256);
    if (expectedHash && hashFileSha256(probePath) !== expectedHash) {
      throw new Error(`Runtime probe hash mismatch: ${relativePath}`);
    }
  }
}

function runtimeInventory(runtimeDir) {
  const inventory = { files: 0, directories: 0, symlinks: 0, bytes: 0 };
  const pending = [runtimeDir];
  while (pending.length) {
    const current = pending.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const entryPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        inventory.directories += 1;
        pending.push(entryPath);
      } else if (entry.isSymbolicLink()) {
        inventory.symlinks += 1;
      } else if (entry.isFile()) {
        inventory.files += 1;
        inventory.bytes += fs.statSync(entryPath).size;
      } else {
        throw new Error(`Unsupported runtime entry: ${entryPath}`);
      }
    }
  }
  return inventory;
}

function inventoriesMatch(left, right) {
  return ['files', 'directories', 'symlinks', 'bytes'].every((key) => left[key] === right[key]);
}

function pointerTargets(pointer, storeRoot, destination, runtimeVersion, profile, lockMetadata) {
  if (!pointer || pointer.schemaVersion !== RUNTIME_STATE_SCHEMA) return false;
  const pointerDir = path.resolve(storeRoot, String(pointer.relativePath || ''));
  return pointerDir === path.resolve(destination)
    && String(pointer.runtimeVersion || '') === runtimeVersion
    && normalizeRuntimeProfile(pointer.profile) === profile
    && JSON.stringify(pointer.lock || {}) === JSON.stringify(lockMetadata);
}

function resolveRuntime(options = {}) {
  if (options.isDev) {
    const runtimeDir = path.resolve(options.devRuntimeDir || path.join(options.appRoot || process.cwd(), 'runtime'));
    return { runtimeDir, profile: normalizeRuntimeProfile(options.profile), source: 'development' };
  }

  const storeRoot = path.resolve(options.storeRoot || runtimeStoreRoot(options.localAppData));
  const pointerPath = path.join(storeRoot, 'current.json');
  const pointer = readJson(pointerPath);
  if (pointer && pointer.schemaVersion === RUNTIME_STATE_SCHEMA) {
    const profile = normalizeRuntimeProfile(pointer.profile);
    const runtimeVersion = String(pointer.runtimeVersion || '');
    const runtimeDir = path.resolve(storeRoot, String(pointer.relativePath || ''));
    const storePrefix = `${storeRoot}${path.sep}`.toLowerCase();
    const lockMatches = pointer.lock
      && String(pointer.lock.runtimeVersion || '') === runtimeVersion
      && normalizeRuntimeProfile(pointer.lock.profile) === profile;
    if (runtimeDir.toLowerCase().startsWith(storePrefix)
      && runtimeVersion && profile !== 'unknown' && lockMatches
      && runtimeLooksUsable(runtimeDir, profile)) {
      return { runtimeDir, profile, source: 'store', version: runtimeVersion, lock: pointer.lock };
    }
  }

  const legacyRuntimeDir = path.resolve(options.legacyRuntimeDir || path.join(options.installDir || '', 'runtime'));
  const profile = normalizeRuntimeProfile(options.profile) === 'unknown'
    ? inferRuntimeProfile(legacyRuntimeDir)
    : normalizeRuntimeProfile(options.profile);
  return { runtimeDir: legacyRuntimeDir, profile, source: 'legacy' };
}

function migrateLegacyRuntime(options = {}) {
  if (!String(options.legacyRuntimeDir || '').trim()) {
    throw new Error('The legacy runtime directory is required for migration.');
  }
  const legacyRuntimeDir = path.resolve(options.legacyRuntimeDir || '');
  const storeRoot = path.resolve(options.storeRoot || runtimeStoreRoot(options.localAppData));
  const sourceRelativeToStore = path.relative(storeRoot, legacyRuntimeDir);
  if (!sourceRelativeToStore
    || (!sourceRelativeToStore.startsWith('..') && !path.isAbsolute(sourceRelativeToStore))) {
    throw new Error('The legacy runtime must be outside the runtime store.');
  }
  const runtimeVersion = String(options.runtimeVersion || 'legacy').trim();
  if (!runtimeVersion) throw new Error('A runtime version is required for migration.');
  const requestedProfile = normalizeRuntimeProfile(options.profile);
  const profile = requestedProfile === 'unknown' ? inferRuntimeProfile(legacyRuntimeDir) : requestedProfile;
  const runtimeLock = options.runtimeLock && typeof options.runtimeLock === 'object' ? options.runtimeLock : {};
  const lockMetadata = normalizeRuntimeLockMetadata(
    options.lockMetadata || runtimeLock,
    runtimeVersion,
    profile,
  );
  const safeVersion = runtimeVersion.replace(/[^0-9A-Za-z._-]/g, '_');
  const destination = path.join(storeRoot, 'versions', safeVersion, profile);
  const pointerPath = path.join(storeRoot, 'current.json');

  if (fs.existsSync(destination)) {
    const pointer = readJson(pointerPath);
    if (pointerTargets(pointer, storeRoot, destination, runtimeVersion, profile, lockMetadata)) {
      validateRuntimeProbes(destination, profile, runtimeLock);
      return {
        runtimeDir: destination,
        profile,
        source: 'store',
        version: runtimeVersion,
        lock: lockMetadata,
        migrated: false,
        legacyRemoved: !fs.existsSync(legacyRuntimeDir),
      };
    }
    throw new Error(`Runtime destination collision; current.json was not changed: ${destination}`);
  }

  validateRuntimeProbes(legacyRuntimeDir, profile, runtimeLock);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  const staging = path.join(
    path.dirname(destination),
    `.${profile}.staging-${process.pid}-${crypto.randomBytes(6).toString('hex')}`,
  );
  let promoted = false;
  try {
    fs.cpSync(legacyRuntimeDir, staging, {
      recursive: true,
      errorOnExist: true,
      force: false,
      preserveTimestamps: true,
      verbatimSymlinks: true,
    });
    validateRuntimeProbes(staging, profile, runtimeLock);
    if (!inventoriesMatch(runtimeInventory(legacyRuntimeDir), runtimeInventory(staging))) {
      throw new Error('The staged runtime inventory does not match the legacy runtime.');
    }

    // staging and destination share a parent, so this promotion never crosses volumes.
    fs.renameSync(staging, destination);
    promoted = true;
    const pointer = {
      schemaVersion: RUNTIME_STATE_SCHEMA,
      runtimeVersion,
      profile,
      relativePath: path.relative(storeRoot, destination),
      lock: lockMetadata,
      updatedAt: new Date().toISOString(),
    };
    try {
      writeJsonAtomic(pointerPath, pointer);
    } catch (error) {
      try { fs.rmSync(destination, { recursive: true, force: true }); } catch {}
      promoted = false;
      throw error;
    }
  } finally {
    if (!promoted) {
      try { fs.rmSync(staging, { recursive: true, force: true }); } catch {}
    }
  }

  let legacyRemoved = false;
  let cleanupError = '';
  try {
    fs.rmSync(legacyRuntimeDir, { recursive: true, force: true });
    legacyRemoved = !fs.existsSync(legacyRuntimeDir);
  } catch (error) {
    cleanupError = String(error && error.message ? error.message : error);
  }
  return {
    runtimeDir: destination,
    profile,
    source: 'store',
    version: runtimeVersion,
    lock: lockMetadata,
    migrated: true,
    legacyRemoved,
    cleanupError,
  };
}

function listRuntimeComponents(runtimeDir) {
  const components = ['python', 'node', 'git', 'pandoc', 'draw.io', 'texlive'];
  return components.map((name) => ({ name, installed: fs.existsSync(path.join(runtimeDir, name)) }));
}

module.exports = {
  RUNTIME_STATE_SCHEMA,
  hashFileSha256,
  inferRuntimeProfile,
  listRuntimeComponents,
  migrateLegacyRuntime,
  normalizeRuntimeLockMetadata,
  normalizeRuntimeProfile,
  readJson,
  resolveRuntime,
  runtimeLooksUsable,
  runtimeStoreRoot,
  validateRuntimeProbes,
  writeJsonAtomic,
};
