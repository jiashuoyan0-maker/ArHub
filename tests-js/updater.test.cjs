'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { Updater, hasPublisherName, normalizeReleaseNotes } = require('../updater');

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
          releaseNotes: [{ version: '1.1.0', note: 'Signed release' }],
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

function createFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'arhub-updater-'));
  const configPath = path.join(root, 'app-update.yml');
  fs.writeFileSync(configPath, 'provider: github\npublisherName:\n  - ArHub Test Publisher\n', 'utf8');
  const autoUpdater = new FakeAutoUpdater();
  const updater = new Updater(
    {
      user_data_dir: root,
      update_config_path: configPath,
      check_interval_hours: 6,
      logger: { info() {}, warn() {}, error() {} },
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

test('secure updater refuses a config without publisher verification', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'arhub-updater-invalid-'));
  const configPath = path.join(root, 'app-update.yml');
  fs.writeFileSync(configPath, 'provider: github\n', 'utf8');
  assert.throws(
    () => new Updater({ user_data_dir: root, update_config_path: configPath }, {
      autoUpdater: new FakeAutoUpdater(),
      CancellationToken: FakeCancellationToken,
    }),
    /publisherName is missing/,
  );
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
  const download = await fixture.updater.downloadUpdate(result, (value) => progress.push(value.percent));
  assert.equal(download.ok, true);
  assert.deepEqual(progress, [50, 100]);

  fixture.updater.applyUpdateAndRestart();
  assert.equal(fixture.autoUpdater.installed, true);
  assert.deepEqual(fixture.autoUpdater.installArgs, [false, true]);
});

test('skipped version is not offered again', async (t) => {
  const fixture = createFixture();
  t.after(() => fs.rmSync(fixture.root, { recursive: true, force: true }));

  fixture.updater.skipVersion('1.1.0');
  const result = await fixture.updater.checkForUpdate({ force: true });
  assert.equal(result.hasUpdate, false);
  assert.equal(result.reason, 'version skipped');
});
