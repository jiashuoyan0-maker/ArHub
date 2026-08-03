'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  Updater,
  classifyInstaller,
  hasPublisherName,
  isInstallerAsset,
  isRuntimeProfileCompatible,
  normalizeRuntimeProfile,
  normalizeReleaseNotes,
} = require('../updater');

class FakeCancellationToken {
  constructor() {
    this.cancelled = false;
  }

  cancel() {
    this.cancelled = true;
  }
}

class FakeAutoUpdater extends EventEmitter {
  constructor() {
    super();
    this.nextCheck = 'available';
    this.installed = false;
  }

  async checkForUpdates() {
    queueMicrotask(() => {
      if (this.nextCheck === 'available') {
        this.emit('update-available', {
          version: '1.1.0',
          releaseNotes: [{ version: '1.1.0', note: 'Open-source release' }],
          releaseDate: '2026-07-30T00:00:00.000Z',
          files: [{ url: 'ArHub-Setup-1.1.0-x64.exe', size: 2048, sha512: 'abc' }],
        });
      } else {
        this.emit('update-not-available', { version: '1.0.9' });
      }
    });
    return {};
  }

  async downloadUpdate(token) {
    assert.equal(token.cancelled, false);
    this.emit('download-progress', { percent: 50, transferred: 1024, total: 2048, bytesPerSecond: 512 });
    this.emit('update-downloaded', {});
    return ['ArHub-Setup-1.1.0-x64.exe'];
  }

  quitAndInstall(isSilent, runAfter) {
    this.installed = true;
    this.installArgs = [isSilent, runAfter];
  }
}

function createFixture(config = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'arhub-updater-'));
  const configPath = path.join(root, 'app-update.yml');
  fs.writeFileSync(configPath, 'provider: github\n', 'utf8');
  const autoUpdater = new FakeAutoUpdater();
  const updater = new Updater(
    {
      user_data_dir: root,
      update_config_path: configPath,
      check_interval_hours: 6,
      runtime_profile: 'full',
      logger: { info() {}, warn() {}, error() {} },
      ...config,
    },
    { autoUpdater, CancellationToken: FakeCancellationToken },
  );
  return { root, autoUpdater, updater };
}

test('publisherName detection accepts scalar and list values', () => {
  assert.equal(hasPublisherName('publisherName: ArHub LLC\n'), true);
  assert.equal(hasPublisherName('publisherName:\n  - ArHub LLC\n'), true);
  assert.equal(hasPublisherName('publisherName: []\n'), false);
  assert.equal(hasPublisherName('provider: github\n'), false);
});

test('release notes are normalized for the renderer', () => {
  assert.equal(normalizeReleaseNotes('  Ready  '), 'Ready');
  assert.equal(normalizeReleaseNotes([{ version: '1.2.0', note: 'Changes' }]), 'v1.2.0: Changes');
});

test('installer profiles are classified and cannot cross-update', () => {
  const lite = [{ url: 'ArHub-Setup-1.2.0-lite-x64.exe' }];
  const full = [{ url: 'ArHub-Setup-1.2.0-x64.exe' }];
  const appOnly = [{ url: 'ArHub-Setup-1.2.0-app-only-x64.exe' }];
  assert.equal(classifyInstaller(lite[0].url), 'lite');
  assert.equal(classifyInstaller(full[0].url), 'full');
  assert.equal(classifyInstaller(appOnly[0].url), 'app-only');
  assert.equal(isRuntimeProfileCompatible(lite, 'lite'), true);
  assert.equal(isRuntimeProfileCompatible(lite, 'full'), false);
  assert.equal(isRuntimeProfileCompatible(full, 'full'), true);
  assert.equal(isRuntimeProfileCompatible(full, 'lite'), false);
  assert.equal(isRuntimeProfileCompatible(appOnly, 'full'), true);
  assert.equal(isRuntimeProfileCompatible(appOnly, 'lite'), true);
  assert.equal(isRuntimeProfileCompatible(full, 'unknown'), false);
  assert.equal(isRuntimeProfileCompatible([
    { url: 'ArHub-Setup-1.2.0-lite-x64.exe' },
    { url: 'unexpected-x64.exe' },
    { url: 'ArHub-Setup-1.2.0-lite-x64.exe.blockmap' },
  ], 'lite'), false);
  assert.equal(isInstallerAsset('ArHub-Setup-1.2.0-lite-x64.exe.blockmap'), false);
  assert.equal(normalizeRuntimeProfile(' LITE '), 'lite');
  assert.equal(normalizeRuntimeProfile('unexpected'), 'unknown');
});

test('publisher verification remains available for an explicitly signed build', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'arhub-updater-invalid-'));
  const configPath = path.join(root, 'app-update.yml');
  fs.writeFileSync(configPath, 'provider: github\n', 'utf8');
  assert.throws(
    () => new Updater({
      user_data_dir: root,
      update_config_path: configPath,
      require_publisher_verification: true,
    }, {
      autoUpdater: new FakeAutoUpdater(),
      CancellationToken: FakeCancellationToken,
    }),
    /publisherName is missing/,
  );
  fs.rmSync(root, { recursive: true, force: true });
});

test('official unsigned updates do not require publisherName', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'arhub-updater-unsigned-'));
  const configPath = path.join(root, 'app-update.yml');
  fs.writeFileSync(configPath, 'provider: github\n', 'utf8');
  assert.doesNotThrow(() => new Updater({
    user_data_dir: root,
    update_config_path: configPath,
    require_publisher_verification: false,
  }, {
    autoUpdater: new FakeAutoUpdater(),
    CancellationToken: FakeCancellationToken,
  }));
  fs.rmSync(root, { recursive: true, force: true });
});

test('available update can be downloaded and installed', async (t) => {
  const fixture = createFixture();
  t.after(() => fs.rmSync(fixture.root, { recursive: true, force: true }));

  const result = await fixture.updater.checkForUpdate({ force: true });
  assert.equal(result.hasUpdate, true);
  assert.equal(result.version, '1.1.0');
  assert.equal(result.totalSize, 2048);
  assert.equal(result.fileCount, 1);

  const progress = [];
  const download = await fixture.updater.downloadUpdate(result, (value) => progress.push([value.percent, value.current]));
  assert.equal(download.ok, true);
  assert.deepEqual(progress, [[50, 1024], [100, 1]]);

  fixture.updater.applyUpdateAndRestart();
  assert.equal(fixture.autoUpdater.installed, true);
  assert.deepEqual(fixture.autoUpdater.installArgs, [true, true]);
});

test('a Full install ignores a Lite-only release manifest', async (t) => {
  const fixture = createFixture({ runtime_profile: 'full' });
  t.after(() => fs.rmSync(fixture.root, { recursive: true, force: true }));
  fixture.autoUpdater.checkForUpdates = async function checkForLiteUpdate() {
    queueMicrotask(() => this.emit('update-available', {
      version: '1.2.0',
      files: [{ url: 'ArHub-Setup-1.2.0-lite-x64.exe', size: 1024, sha512: 'abc' }],
    }));
    return {};
  };

  const result = await fixture.updater.checkForUpdate({ force: true });
  assert.equal(result.hasUpdate, false);
  assert.equal(result.reason, 'runtime profile mismatch');
});

test('download state is bound to the checked version', async (t) => {
  const fixture = createFixture();
  t.after(() => fs.rmSync(fixture.root, { recursive: true, force: true }));
  let nextVersion = '1.1.0';
  let releaseFirstDownload;
  let downloadCalls = 0;
  fixture.autoUpdater.checkForUpdates = async function checkVersion() {
    const version = nextVersion;
    queueMicrotask(() => this.emit('update-available', {
      version,
      files: [{ url: `ArHub-Setup-${version}-x64.exe`, size: 1024, sha512: 'abc' }],
    }));
    return {};
  };
  fixture.autoUpdater.downloadUpdate = async function downloadVersion() {
    downloadCalls += 1;
    if (downloadCalls === 1) await new Promise((resolve) => { releaseFirstDownload = resolve; });
    this.emit('update-downloaded', {});
    return [`ArHub-Setup-${nextVersion}-x64.exe`];
  };

  const first = await fixture.updater.checkForUpdate({ force: true });
  const firstDownload = fixture.updater.downloadUpdate(first);
  nextVersion = '1.2.0';
  const second = await fixture.updater.checkForUpdate({ force: true });
  await assert.rejects(() => fixture.updater.downloadUpdate(second), /another update version/i);
  releaseFirstDownload();
  await firstDownload;
  assert.equal(fixture.updater.getDownloadStatus('1.1.0').downloaded, true);
  assert.equal(fixture.updater.getDownloadStatus('1.2.0').downloaded, false);
  assert.throws(() => fixture.updater.applyUpdateAndRestart(), /current update/i);

  await fixture.updater.downloadUpdate(second);
  assert.equal(fixture.updater.getDownloadStatus('1.2.0').downloaded, true);
  fixture.updater.applyUpdateAndRestart();
  assert.equal(fixture.autoUpdater.installed, true);
});

test('skipped version is not offered again', async (t) => {
  const fixture = createFixture();
  t.after(() => fs.rmSync(fixture.root, { recursive: true, force: true }));

  fixture.updater.skipVersion('1.1.0');
  const result = await fixture.updater.checkForUpdate({ force: true });
  assert.equal(result.hasUpdate, false);
  assert.equal(result.reason, 'version skipped');
});
