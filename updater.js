'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_CONFIG = Object.freeze({
  check_interval_hours: 6,
  allow_prerelease: false,
  require_publisher_verification: false,
  auto_download: false,
  install_on_quit: true,
  runtime_profile: 'unknown',
  user_data_dir: null,
  update_config_path: null,
});

function classifyInstaller(url) {
  const name = String(url || '').split(/[?#]/, 1)[0].replace(/\\/g, '/').split('/').pop() || '';
  if (!/^ArHub-Setup-.*-x64\.exe$/i.test(name)) return null;
  if (/-app-only-x64\.exe$/i.test(name)) return 'app-only';
  return /-lite-x64\.exe$/i.test(name) ? 'lite' : 'full';
}

function isInstallerAsset(url) {
  const name = String(url || '').split(/[?#]/, 1)[0].replace(/\\/g, '/').split('/').pop() || '';
  return /\.exe$/i.test(name);
}

function normalizeRuntimeProfile(value) {
  const profile = String(value || '').trim().toLowerCase();
  return ['lite', 'full'].includes(profile) ? profile : 'unknown';
}

function isRuntimeProfileCompatible(files, runtimeProfile) {
  const profile = normalizeRuntimeProfile(runtimeProfile);
  if (profile === 'unknown') return false;
  const installers = (Array.isArray(files) ? files : []).filter((file) => isInstallerAsset(file && file.url));
  return installers.length > 0 && installers.every((file) => {
    const installerProfile = classifyInstaller(file && file.url);
    return installerProfile === profile || installerProfile === 'app-only';
  });
}

function normalizeReleaseNotes(releaseNotes) {
  if (typeof releaseNotes === 'string') return releaseNotes.trim();
  if (!Array.isArray(releaseNotes)) return '';
  return releaseNotes
    .map((entry) => {
      if (typeof entry === 'string') return entry;
      if (!entry || typeof entry !== 'object') return '';
      const prefix = entry.version ? `v${entry.version}: ` : '';
      return `${prefix}${entry.note || ''}`.trim();
    })
    .filter(Boolean)
    .join('\n\n');
}

function hasPublisherName(yamlText) {
  const lines = String(yamlText || '').split(/\r?\n/);
  const index = lines.findIndex((line) => /^publisherName\s*:/.test(line));
  if (index < 0) return false;

  const inlineValue = lines[index].replace(/^publisherName\s*:/, '').trim();
  if (inlineValue && inlineValue !== '[]' && inlineValue !== 'null') return true;

  for (let i = index + 1; i < lines.length; i += 1) {
    if (/^\S/.test(lines[i])) break;
    if (/^\s*-\s*\S/.test(lines[i])) return true;
  }
  return false;
}

class Updater {
  constructor(config = {}, dependencies = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.statePath = path.join(this.config.user_data_dir || process.cwd(), 'updater-state.json');
    this._lastCheck = null;
    this._checkPromise = null;
    this._cancellationToken = null;
    this._downloadedVersion = '';
    this._downloadPromise = null;
    this._downloadPromiseVersion = '';
    this._downloadError = '';
    this._progressCallback = null;

    const updaterModule = dependencies.updaterModule
      || (dependencies.autoUpdater && dependencies.CancellationToken ? null : require('electron-updater'));
    this.autoUpdater = dependencies.autoUpdater || updaterModule.autoUpdater;
    this.CancellationToken = dependencies.CancellationToken || updaterModule.CancellationToken;

    this._assertSecureConfiguration();
    this._configureUpdater();
  }

  _assertSecureConfiguration() {
    if (!this.config.require_publisher_verification) return;
    const configPath = this.config.update_config_path;
    if (!configPath || !fs.existsSync(configPath)) {
      throw new Error('Secure updater disabled: app-update.yml is missing.');
    }
    const yaml = fs.readFileSync(configPath, 'utf8');
    if (!hasPublisherName(yaml)) {
      throw new Error('Secure updater disabled: publisherName is missing from app-update.yml.');
    }
  }

  _configureUpdater() {
    // Profile validation happens after the manifest is read, before a download
    // starts. Keeping electron-updater's automatic download disabled preserves
    // that safety boundary between Lite and Full installers.
    this.autoUpdater.autoDownload = false;
    this.autoUpdater.autoInstallOnAppQuit = this.config.install_on_quit !== false;
    this.autoUpdater.autoRunAppAfterInstall = false;
    this.autoUpdater.allowPrerelease = Boolean(this.config.allow_prerelease);
    this.autoUpdater.allowDowngrade = false;
    this.autoUpdater.disableWebInstaller = true;
    this.autoUpdater.logger = this.config.logger || console;

    this.autoUpdater.on('download-progress', (info) => {
      if (!this._progressCallback) return;
      this._progressCallback({
        percent: Number(info.percent || 0),
        current: Number(info.transferred || 0),
        transferred: Number(info.transferred || 0),
        total: Number(info.total || 0),
        bytesPerSecond: Number(info.bytesPerSecond || 0),
        file: 'ArHub update',
      });
    });
    this.autoUpdater.on('update-downloaded', () => {
      if (this._progressCallback) {
        this._progressCallback({ percent: 100, current: 1, transferred: 1, total: 1, bytesPerSecond: 0, file: 'ArHub update' });
      }
    });
    this.autoUpdater.on('error', (error) => {
      this._downloadError = String(error && error.message ? error.message : error);
      console.error('[Updater] electron-updater error:', error);
    });
  }

  _loadState() {
    try {
      return JSON.parse(fs.readFileSync(this.statePath, 'utf8'));
    } catch {
      return { last_check: 0, skipped_version: '' };
    }
  }

  _saveState(state) {
    fs.mkdirSync(path.dirname(this.statePath), { recursive: true });
    fs.writeFileSync(this.statePath, JSON.stringify(state, null, 2), 'utf8');
  }

  _normalizeUpdateInfo(info) {
    const files = Array.isArray(info && info.files) ? info.files : [];
    const changedFiles = files.map((file) => ({
      rel: file.url || 'ArHub installer',
      size: Number(file.size || 0),
      sha512: file.sha512 || '',
    }));
    return {
      hasUpdate: true,
      version: String((info && info.version) || ''),
      changelog: normalizeReleaseNotes(info && info.releaseNotes),
      releaseDate: (info && info.releaseDate) || '',
      changedFiles,
      fileCount: changedFiles.length,
      totalSize: changedFiles.reduce((sum, file) => sum + file.size, 0),
    };
  }

  async checkForUpdate(options = {}) {
    if (this._checkPromise) return this._checkPromise;
    this._checkPromise = this._checkForUpdate(Boolean(options.force));
    try {
      return await this._checkPromise;
    } finally {
      this._checkPromise = null;
    }
  }

  async _checkForUpdate(force) {
    const state = this._loadState();
    const intervalMs = Math.max(0, Number(this.config.check_interval_hours || 0)) * 60 * 60 * 1000;
    const now = Date.now();
    if (!force && intervalMs > 0 && now - Number(state.last_check || 0) < intervalMs) {
      return { hasUpdate: false, reason: 'check throttled', nextCheckAt: Number(state.last_check) + intervalMs };
    }

    return new Promise((resolve, reject) => {
      let settled = false;
      const timeout = setTimeout(() => finish(reject, new Error('Update check timed out.')), 60_000);
      const cleanup = () => {
        clearTimeout(timeout);
        this.autoUpdater.removeListener('update-available', onAvailable);
        this.autoUpdater.removeListener('update-not-available', onNotAvailable);
        this.autoUpdater.removeListener('error', onError);
      };
      const finish = (callback, value) => {
        if (settled) return;
        settled = true;
        cleanup();
        callback(value);
      };
      const saveCheckTime = () => {
        state.last_check = Date.now();
        this._saveState(state);
      };
      const onAvailable = (info) => {
        saveCheckTime();
        const normalized = this._normalizeUpdateInfo(info);
        if (!isRuntimeProfileCompatible(info && info.files, this.config.runtime_profile)) {
          this._lastCheck = null;
          finish(resolve, {
            hasUpdate: false,
            reason: 'runtime profile mismatch',
            version: normalized.version,
            runtimeProfile: this.config.runtime_profile,
          });
          return;
        }
        if (state.skipped_version && state.skipped_version === normalized.version) {
          this._lastCheck = null;
          finish(resolve, { hasUpdate: false, reason: 'version skipped', version: normalized.version });
          return;
        }
        this._lastCheck = normalized;
        finish(resolve, normalized);
      };
      const onNotAvailable = (info) => {
        saveCheckTime();
        this._lastCheck = null;
        finish(resolve, { hasUpdate: false, reason: 'latest version installed', version: info && info.version });
      };
      const onError = (error) => finish(reject, error instanceof Error ? error : new Error(String(error)));

      this.autoUpdater.once('update-available', onAvailable);
      this.autoUpdater.once('update-not-available', onNotAvailable);
      this.autoUpdater.once('error', onError);

      Promise.resolve(this.autoUpdater.checkForUpdates())
        .then((result) => {
          if (result === null) finish(resolve, { hasUpdate: false, reason: 'updater inactive' });
        })
        .catch(onError);
    });
  }

  async downloadUpdate(_updateInfo, onProgress) {
    if (!this._lastCheck || !this._lastCheck.hasUpdate) {
      throw new Error('No update is available for download.');
    }
    const targetVersion = String(_updateInfo && _updateInfo.version || this._lastCheck.version || '');
    if (!targetVersion || targetVersion !== String(this._lastCheck.version || '')) {
      throw new Error('The requested update is no longer the current available version.');
    }
    if (this._downloadedVersion === targetVersion) return { ok: true, files: [], alreadyDownloaded: true };
    if (this._downloadPromise) {
      if (this._downloadPromiseVersion === targetVersion) return this._downloadPromise;
      throw new Error('Another update version is currently downloading.');
    }

    this._downloadError = '';
    this._progressCallback = typeof onProgress === 'function' ? onProgress : null;
    this._cancellationToken = new this.CancellationToken();
    this._downloadPromiseVersion = targetVersion;
    let downloadPromise;
    downloadPromise = (async () => {
      try {
        const files = await this.autoUpdater.downloadUpdate(this._cancellationToken);
        this._downloadedVersion = targetVersion;
        this._downloadError = '';
        return { ok: true, files };
      } catch (error) {
        this._downloadError = String(error && error.message ? error.message : error);
        throw error;
      } finally {
        this._cancellationToken = null;
        this._progressCallback = null;
        if (this._downloadPromise === downloadPromise) {
          this._downloadPromise = null;
          this._downloadPromiseVersion = '';
        }
      }
    })();
    this._downloadPromise = downloadPromise;
    return downloadPromise;
  }

  getDownloadStatus(version = '') {
    const targetVersion = String(version || (this._lastCheck && this._lastCheck.version) || '');
    return {
      version: targetVersion,
      current: Boolean(targetVersion && this._lastCheck && this._lastCheck.version === targetVersion),
      downloaded: Boolean(targetVersion && this._downloadedVersion === targetVersion),
      downloading: Boolean(targetVersion && this._downloadPromiseVersion === targetVersion && this._downloadPromise),
    };
  }

  abortDownload() {
    if (this._cancellationToken) this._cancellationToken.cancel();
  }

  skipVersion(version) {
    const state = this._loadState();
    state.skipped_version = String(version || '');
    this._saveState(state);
    if (this._lastCheck && this._lastCheck.version === state.skipped_version) this._lastCheck = null;
  }

  applyUpdateAndRestart() {
    const status = this.getDownloadStatus();
    if (!status.current || !status.downloaded) throw new Error('The current update has not finished downloading.');
    this.autoUpdater.quitAndInstall(true, true);
  }
}

module.exports = {
  Updater,
  classifyInstaller,
  hasPublisherName,
  isInstallerAsset,
  isRuntimeProfileCompatible,
  normalizeRuntimeProfile,
  normalizeReleaseNotes,
};
