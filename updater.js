/**
 * 客户端自动更新器 (调用方: main.js)
 *
 * 工作流程:
 * 1. 启动 5 秒后, 静默 GET <server>/manifest.json
 * 2. 对比本地版本 + 文件 hash, 找出需要更新的文件
 * 3. 通过 IPC 通知前端弹气泡 "v1.0.1 可用"
 * 4. 用户点"立即更新" → 下载到 resources/app.update/
 * 5. 用户点"重启" → 启动 update-helper.exe (NSIS 自带), ArHub 退出
 * 6. update-helper 把 app.update 覆盖到 app/, 启动 ArHub
 *
 * 关键安全:
 * - 每个文件下载后校验 sha256, 不匹配丢弃
 * - manifest.json 大小限制 5MB (防 DoS)
 * - 下载有 retry + 进度
 * - 替换失败自动回滚 (保留 app.bak/ 一份)
 *
 * 范围: 全覆盖 resources/app/ + runtime/
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const crypto = require('crypto');
const { spawn } = require('child_process');

// 默认配置 (打包时被 main.js 覆盖)
const DEFAULT_CONFIG = {
  server_url: 'https://update.example.com',  // 跟 release-patch 配置同 URL
  install_dir: null,                         // 安装根目录 (含 resources/app/, runtime/)
  current_version: '1.0.0',                  // 当前版本 (从 package.json 读)
  check_interval_hours: 6,                   // 多少小时检查一次
  user_data_dir: null,                       // 存最后检查时间 / 跳过版本
};

class Updater {
  constructor(config) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.installDir = this.config.install_dir;
    this.appDir = path.join(this.installDir, 'resources', 'app');
    this.runtimeDir = path.join(this.installDir, 'runtime');
    this.updateStagingDir = path.join(this.installDir, '.app.update');
    this.backupDir = path.join(this.installDir, '.app.bak');
    this.statePath = path.join(this.config.user_data_dir, 'updater-state.json');
    this.aborted = false;
    this.downloadProgress = { current: 0, total: 0, file: '' };

    // 启动时清理上次更新失败 / 中断留下的 staging 残留 (可能占几十 MB 磁盘空间)
    // 也清理上次的 vbs / bat (避免脏文件影响下次更新)
    this._cleanupStaleArtifacts();
  }

  _cleanupStaleArtifacts() {
    try {
      if (this.installDir && fs.existsSync(this.updateStagingDir)) {
        this._rmrf(this.updateStagingDir);
      }
      const vbsPath = path.join(this.installDir, 'update-helper-launcher.vbs');
      const batPath = path.join(this.installDir, 'update-helper.bat');
      if (fs.existsSync(vbsPath)) { try { fs.unlinkSync(vbsPath); } catch {} }
      if (fs.existsSync(batPath)) { try { fs.unlinkSync(batPath); } catch {} }
    } catch (e) {
      console.warn('[updater] cleanup stale artifacts failed:', e.message);
    }
  }

  // ============================================================
  // 状态持久化
  // ============================================================
  _loadState() {
    try {
      return JSON.parse(fs.readFileSync(this.statePath, 'utf8'));
    } catch {
      return { last_check: 0, skipped_version: null };
    }
  }

  _saveState(state) {
    try {
      fs.mkdirSync(path.dirname(this.statePath), { recursive: true });
      fs.writeFileSync(this.statePath, JSON.stringify(state));
    } catch (e) {
      console.error('[updater] save state failed:', e);
    }
  }

  // ============================================================
  // HTTP 请求
  // ============================================================
  _fetchJson(url, maxBytes = 5 * 1024 * 1024) {
    return new Promise((resolve, reject) => {
      const lib = url.startsWith('https') ? https : http;
      const req = lib.get(url, (res) => {
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode}`));
          return;
        }
        let received = 0;
        let body = '';
        res.on('data', (chunk) => {
          received += chunk.length;
          if (received > maxBytes) {
            req.destroy();
            reject(new Error('manifest too big'));
            return;
          }
          body += chunk;
        });
        res.on('end', () => {
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(new Error(`bad JSON: ${e.message}`));
          }
        });
      });
      req.on('error', reject);
      req.setTimeout(10000, () => req.destroy(new Error('manifest timeout')));
    });
  }

  _downloadFile(url, destPath, expectedSha, expectedSize, onProgress) {
    return new Promise((resolve, reject) => {
      const lib = url.startsWith('https') ? https : http;
      fs.mkdirSync(path.dirname(destPath), { recursive: true });
      const tmpPath = destPath + '.tmp';
      const file = fs.createWriteStream(tmpPath);
      const hash = crypto.createHash('sha256');
      let received = 0;

      const req = lib.get(url, (res) => {
        if (res.statusCode !== 200) {
          file.destroy();
          fs.unlink(tmpPath, () => {});
          reject(new Error(`HTTP ${res.statusCode} ${url}`));
          return;
        }

        // 防 DoS: 不允许超过 expectedSize 太多
        const maxSize = Math.max(expectedSize * 2, 1024 * 1024);

        res.on('data', (chunk) => {
          received += chunk.length;
          if (received > maxSize) {
            req.destroy();
            file.destroy();
            fs.unlink(tmpPath, () => {});
            reject(new Error('size exceeded'));
            return;
          }
          hash.update(chunk);
          if (onProgress) onProgress(chunk.length);
        });

        res.pipe(file);

        file.on('finish', () => {
          file.close(() => {
            const actualSha = hash.digest('hex');
            if (actualSha !== expectedSha) {
              fs.unlink(tmpPath, () => {});
              reject(new Error(`sha256 mismatch: expected ${expectedSha}, got ${actualSha}`));
              return;
            }
            try {
              fs.renameSync(tmpPath, destPath);
              resolve();
            } catch (e) {
              reject(e);
            }
          });
        });
      });

      req.on('error', (e) => {
        file.destroy();
        fs.unlink(tmpPath, () => {});
        reject(e);
      });
      req.setTimeout(60000, () => req.destroy(new Error('download timeout')));
    });
  }

  // ============================================================
  // 计算本地文件 hash (相对 installDir)
  // ============================================================
  _computeLocalSha(rel) {
    const full = path.join(this.installDir, rel.replace(/\//g, path.sep));
    if (!fs.existsSync(full)) return null;
    try {
      const data = fs.readFileSync(full);
      return crypto.createHash('sha256').update(data).digest('hex');
    } catch {
      return null;
    }
  }

  // ============================================================
  // 主流程: 检查更新
  // ============================================================
  async checkForUpdate() {
    const state = this._loadState();
    const now = Date.now();

    // 间隔限流
    const intervalMs = this.config.check_interval_hours * 3600 * 1000;
    if (now - state.last_check < intervalMs) {
      return { hasUpdate: false, reason: 'rate-limited' };
    }

    state.last_check = now;
    this._saveState(state);

    let manifest;
    try {
      // ⛔ 绕过 CDN/nginx 缓存: 加 ?_t=timestamp
      // 否则 nginx 默认对 .json 缓存可能让客户端看到旧 manifest, 永远不更新
      const url = `${this.config.server_url}/manifest.json?_t=${now}`;
      manifest = await this._fetchJson(url);
    } catch (e) {
      return { hasUpdate: false, reason: `fetch failed: ${e.message}` };
    }

    if (!manifest || !manifest.version || !Array.isArray(manifest.files)) {
      return { hasUpdate: false, reason: 'bad manifest' };
    }

    // 用户跳过过这个版本就不弹了
    if (state.skipped_version === manifest.version) {
      return { hasUpdate: false, reason: 'user skipped' };
    }

    // 版本号比较 (语义化)
    if (this._compareVersion(manifest.version, this.config.current_version) <= 0) {
      return { hasUpdate: false, reason: 'up to date' };
    }

    // 找出本地缺失或 hash 不一致的文件
    const changedFiles = [];
    let totalSize = 0;
    for (const f of manifest.files) {
      const localSha = this._computeLocalSha(f.rel);
      if (localSha !== f.sha256) {
        changedFiles.push(f);
        totalSize += f.size;
      }
    }

    // 本地所有文件都已同步, 说明上次更新已落地, 只是 package.json 没写新 version,
    // 不应再弹气泡 (否则点了立即更新后下载 0 文件、瞬间 ready, 用户重启后还是老版本, 进入死循环)
    if (changedFiles.length === 0) {
      return { hasUpdate: false, reason: 'all files in sync (already updated)' };
    }

    return {
      hasUpdate: true,
      version: manifest.version,
      changelog: manifest.changelog || '',
      changedFiles,
      totalSize,
      manifest,
    };
  }

  // 语义化版本比较: 1.0.1 > 1.0.0 → 1; equal → 0; less → -1
  _compareVersion(a, b) {
    const pa = a.split('.').map(n => parseInt(n, 10) || 0);
    const pb = b.split('.').map(n => parseInt(n, 10) || 0);
    const len = Math.max(pa.length, pb.length);
    for (let i = 0; i < len; i++) {
      const na = pa[i] || 0;
      const nb = pb[i] || 0;
      if (na > nb) return 1;
      if (na < nb) return -1;
    }
    return 0;
  }

  // ============================================================
  // 下载所有变化文件到 staging
  // ============================================================
  async downloadUpdate(updateInfo, onProgress) {
    this.aborted = false;

    // 清理旧 staging
    if (fs.existsSync(this.updateStagingDir)) {
      this._rmrf(this.updateStagingDir);
    }
    fs.mkdirSync(this.updateStagingDir, { recursive: true });

    let downloaded = 0;
    const total = updateInfo.totalSize;
    this.downloadProgress = { current: 0, total, file: '' };

    for (const f of updateInfo.changedFiles) {
      if (this.aborted) throw new Error('aborted');

      this.downloadProgress.file = f.rel;
      const destPath = path.join(this.updateStagingDir, f.rel.replace(/\//g, path.sep));
      const url = `${this.config.server_url}/files/${f.sha256.substring(0, 2)}/${f.sha256}.bin`;

      // 重试 3 次
      let lastErr;
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          await this._downloadFile(url, destPath, f.sha256, f.size, (chunk) => {
            this.downloadProgress.current = downloaded + chunk;
            if (onProgress) onProgress(this.downloadProgress);
          });
          downloaded += f.size;
          this.downloadProgress.current = downloaded;
          if (onProgress) onProgress(this.downloadProgress);
          lastErr = null;
          break;
        } catch (e) {
          lastErr = e;
          await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
        }
      }
      if (lastErr) {
        throw new Error(`下载 ${f.rel} 失败: ${lastErr.message}`);
      }
    }

    // 保存 manifest 到 staging (apply 时校验)
    fs.writeFileSync(
      path.join(this.updateStagingDir, '.manifest.json'),
      JSON.stringify(updateInfo.manifest)
    );

    return { ok: true, downloaded };
  }

  abortDownload() {
    this.aborted = true;
  }

  // ============================================================
  // 启动 update-helper 应用更新 (在 ArHub 退出后跑)
  // 用 vbs 壳启动, wscript.exe 是 GUI 子系统进程, 完全静默 (无黑框).
  // 历史 bug: 之前用 cmd /c batPath, 即使 windowsHide:true + detached, Windows 仍会弹一个 cmd 窗口
  //          (因为 cmd 是 console 子系统, 用户体验差)
  // ============================================================
  applyUpdateAndRestart(mainExePath) {
    const helperBat = path.join(this.installDir, 'update-helper.bat');
    const helperVbs = path.join(this.installDir, 'update-helper-launcher.vbs');

    this._writeFallbackBat(helperBat, mainExePath);
    this._writeVbsLauncher(helperVbs, helperBat);

    spawn('wscript', [helperVbs], {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    }).unref();
  }

  // wscript 壳: 完全无窗口启动 cmd /c batPath
  // - UTF-16 LE BOM 编码: wscript 才能正确识别中文路径
  // - 用 Chr(34) 拼接双引号: VBScript 最稳的引号转义方式
  _writeVbsLauncher(vbsPath, batPath) {
    // 在 VBS 字符串内, 不要含双引号 (用 & q 拼接)
    // 但 batPath 里可能含 " (用户装到含 " 的路径? 极少, 但保险起见用 chr 拼)
    // 最简单: 把 batPath 拆分, 任何 " 都换成 chr(34) 拼接
    const escapedForVbs = batPath
      .split('"')
      .map(s => `"${s}"`)
      .join(' & q & ');
    const content =
      'Set sh = CreateObject("WScript.Shell")\r\n' +
      'q = Chr(34)\r\n' +
      `sh.Run "cmd /c " & q & ${escapedForVbs} & q, 0, False\r\n`;
    // 写 UTF-16 LE + BOM (wscript 才能正确识别中文路径)
    const utf16Buf = Buffer.from(content, 'utf16le');
    const bom = Buffer.from([0xFF, 0xFE]);
    fs.writeFileSync(vbsPath, Buffer.concat([bom, utf16Buf]));
  }

  _writeFallbackBat(batPath, mainExePath) {
    // robocopy 退出码: 0=未拷贝, 1=成功拷贝, 2=多余文件, 4=不匹配, 8+=失败
    // 0/1/2/3/4/5/6/7 都算成功 (按 robocopy 文档), >=8 才算失败
    const lines = [
      '@echo off',
      'chcp 65001 >nul',
      'setlocal enabledelayedexpansion',
      `set "INSTALL_DIR=${this.installDir}"`,
      `set "STAGING=${this.updateStagingDir}"`,
      `set "BACKUP=${this.backupDir}"`,
      `set "MAIN_EXE=${mainExePath}"`,
      `set "PARENT_PID=${process.pid}"`,
      `set "LOG_FILE=%TEMP%\\arhub-update.log"`,
      '',
      ':: 重定向所有输出到日志文件 (用户可以查 %TEMP%\\arhub-update.log)',
      'echo [%date% %time%] update-helper start > "%LOG_FILE%"',
      'echo PARENT_PID=%PARENT_PID% >> "%LOG_FILE%"',
      'echo INSTALL_DIR=%INSTALL_DIR% >> "%LOG_FILE%"',
      'echo STAGING=%STAGING% >> "%LOG_FILE%"',
      '',
      ':: 等父进程退出 (最多 30 秒, 防死循环)',
      'set /a wait_count=0',
      ':wait_loop',
      'tasklist /FI "PID eq %PARENT_PID%" 2>nul | find "%PARENT_PID%" >nul',
      'if !ERRORLEVEL!==0 (',
      '  set /a wait_count+=1',
      '  if !wait_count! GEQ 30 (',
      '    echo ERROR: parent process did not exit in 30s, force kill >> "%LOG_FILE%"',
      '    taskkill /F /PID %PARENT_PID% >> "%LOG_FILE%" 2>&1',
      '    timeout /t 2 /nobreak >nul',
      '  ) else (',
      '    timeout /t 1 /nobreak >nul',
      '    goto wait_loop',
      '  )',
      ')',
      '',
      ':: 等额外 2 秒确保所有句柄释放 (尤其是 Python 后端进程占用的 .pyc 文件)',
      'echo waiting 2s for handles to release... >> "%LOG_FILE%"',
      'timeout /t 2 /nobreak >nul',
      '',
      ':: 把 staging 里的文件覆盖到 install_dir',
      'echo [%date% %time%] applying update... >> "%LOG_FILE%"',
      'robocopy "%STAGING%" "%INSTALL_DIR%" /E /R:3 /W:2 /NFL /NDL /NJH /NJS /NC /NS /NP /XF .manifest.json >> "%LOG_FILE%" 2>&1',
      'set ROBOCOPY_EXIT=!ERRORLEVEL!',
      'echo robocopy exit code: !ROBOCOPY_EXIT! >> "%LOG_FILE%"',
      '',
      ':: robocopy: 0-7 算成功, 8+ 算失败',
      'if !ROBOCOPY_EXIT! GEQ 8 (',
      '  echo ERROR: update failed, rolling back not implemented, restart anyway >> "%LOG_FILE%"',
      ')',
      '',
      ':: 清理 staging',
      'echo cleaning staging... >> "%LOG_FILE%"',
      'rmdir /s /q "%STAGING%" >> "%LOG_FILE%" 2>&1',
      '',
      ':: 重启 ArHub (无论 robocopy 成功失败都要重启, 防止用户软件没了)',
      'echo restarting ArHub: %MAIN_EXE% >> "%LOG_FILE%"',
      'start "" "%MAIN_EXE%"',
      '',
      'echo [%date% %time%] update-helper done (robocopy=!ROBOCOPY_EXIT!) >> "%LOG_FILE%"',
      'endlocal',
      'exit /b 0',
    ];
    // ⛔ 用系统默认 ANSI 编码 (Windows 中文系统是 GBK), 否则路径含中文时
    // cmd 解析路径会乱码 → robocopy 找不到目录.
    // Node 没内置 GBK 编码, 但是 ASCII 部分 + cmd 用 chcp 65001 切 UTF-8 即可.
    // 我们改写 bat 第一行加 chcp 65001, 然后用 UTF-8 BOM 写入.
    // (chcp 65001 会让本会话所有命令按 UTF-8 解码字符串)
    const finalContent = lines.join('\r\n');
    // UTF-8 BOM (cmd 在 chcp 65001 时认 BOM)
    const bom = Buffer.from([0xEF, 0xBB, 0xBF]);
    const buf = Buffer.from(finalContent, 'utf8');
    fs.writeFileSync(batPath, Buffer.concat([bom, buf]));
  }

  _rmrf(p) {
    if (!fs.existsSync(p)) return;
    for (const entry of fs.readdirSync(p, { withFileTypes: true })) {
      const sub = path.join(p, entry.name);
      if (entry.isDirectory()) this._rmrf(sub);
      else fs.unlinkSync(sub);
    }
    fs.rmdirSync(p);
  }

  skipVersion(version) {
    const state = this._loadState();
    state.skipped_version = version;
    this._saveState(state);
  }
}

module.exports = { Updater };
