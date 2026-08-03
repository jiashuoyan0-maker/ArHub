/**
 * ArHub Desktop - Electron main process
 *
 * 职责：
 * 1. 启动内嵌 Python 后端（uvicorn）
 * 2. 等待后端 ready（轮询 /api/health）
 * 3. 创建 BrowserWindow 加载前端
 * 4. 托盘图标 + 关闭最小化到托盘
 * 5. 退出时杀掉 Python 子进程
 */

const { app, BrowserWindow, Tray, Menu, dialog, ipcMain, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');
const PACKAGE_METADATA = require('./package.json');
const RUNTIME_LOCK = require('./packaging/runtime-lock.json');
const {
  migrateLegacyRuntime,
  resolveRuntime,
  runtimeStoreRoot,
} = require('./runtime-store');
const {
  claimRollback,
  getStartupDecision,
  markUpdatePending,
  markVersionHealthy,
  preserveRollbackInstaller,
} = require('./update-health');

// 自动更新器
const { Updater, normalizeRuntimeProfile } = require('./updater');

// ── 路径 ──
const IS_DEV = !app.isPackaged;
const IS_SMOKE_TEST = process.argv.includes('--arhub-smoke-test') || process.env.ARHUB_SMOKE_TEST === '1';
const APP_ROOT = IS_DEV ? __dirname : path.join(process.resourcesPath, 'app');
const LEGACY_RUNTIME_DIR = IS_DEV
  ? path.join(__dirname, 'runtime')
  : path.join(path.dirname(process.resourcesPath), 'runtime');
// Packaged metadata is part of the signed/hashed application payload. An
// ambient environment variable must not be able to change update channels.
const PACKAGED_RUNTIME_PROFILE = normalizeRuntimeProfile(
  IS_DEV
    ? process.env.ARHUB_RUNTIME_PROFILE || PACKAGE_METADATA.arhubRuntimeProfile || 'full'
    : PACKAGE_METADATA.arhubRuntimeProfile,
);
const LOCAL_APP_DATA = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE || process.cwd(), 'AppData', 'Local');
const RUNTIME_STORE_ROOT = runtimeStoreRoot(LOCAL_APP_DATA);
const RUNTIME_RESOLUTION = resolveRuntime({
  isDev: IS_DEV,
  appRoot: __dirname,
  devRuntimeDir: LEGACY_RUNTIME_DIR,
  installDir: path.dirname(process.execPath),
  legacyRuntimeDir: LEGACY_RUNTIME_DIR,
  localAppData: LOCAL_APP_DATA,
  profile: PACKAGED_RUNTIME_PROFILE,
  storeRoot: RUNTIME_STORE_ROOT,
});
const RUNTIME_DIR = RUNTIME_RESOLUTION.runtimeDir;
const RUNTIME_PROFILE = RUNTIME_RESOLUTION.profile;

const PYTHON_EXE = path.join(RUNTIME_DIR, 'python', 'python.exe');
const BACKEND_DIR = IS_DEV
  ? path.join(__dirname, 'backend')
  : path.join(APP_ROOT, 'backend');

const PORT = 18088;
const ROAMING_DATA_DIR = process.env.APPDATA || path.join(process.env.USERPROFILE || process.cwd(), 'AppData', 'Roaming');
const USER_DATA_DIR = path.resolve(process.env.ARHUB_DATA_DIR || path.join(ROAMING_DATA_DIR, 'ArHub'));
const LOG_DIR = path.join(USER_DATA_DIR, 'logs');
const MAIN_LOG = path.join(LOG_DIR, 'desktop-main.log');
const UPDATE_HEALTH_PATH = path.join(USER_DATA_DIR, 'update-health.json');
const UPDATER_CACHE_ROOT = path.join(LOCAL_APP_DATA, 'arhub-updater');
const ROLLBACK_ROOT = path.join(LOCAL_APP_DATA, 'ArHub', 'rollback-installers');
const EXPECTED_RUNTIME_VERSION = String(
  PACKAGE_METADATA.arhubRuntimeVersion || RUNTIME_LOCK.runtimeVersion || '',
);
let RUNTIME_COMPATIBILITY_ERROR = '';
if (!IS_DEV && PACKAGE_METADATA.arhubRuntimeCompatibility?.requiresExternalRuntime) {
  const compatibleProfiles = PACKAGE_METADATA.arhubRuntimeCompatibility.profiles || [];
  if (RUNTIME_RESOLUTION.source !== 'store') {
    RUNTIME_COMPATIBILITY_ERROR = 'This application update requires a migrated external runtime. Install the bridge release first.';
  } else if (RUNTIME_RESOLUTION.version !== EXPECTED_RUNTIME_VERSION || !compatibleProfiles.includes(RUNTIME_PROFILE)) {
    RUNTIME_COMPATIBILITY_ERROR = `Runtime ${RUNTIME_RESOLUTION.version || 'unknown'} (${RUNTIME_PROFILE}) is not compatible with this application update.`;
  }
}

function appendMainLog(level, args) {
  try {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    const msg = args.map((item) => {
      if (typeof item === 'string') return item;
      try { return JSON.stringify(item); } catch { return String(item); }
    }).join(' ');
    fs.appendFileSync(MAIN_LOG, `${new Date().toISOString()} ${level} ${msg}\n`, 'utf8');
  } catch {}
}

for (const level of ['log', 'warn', 'error']) {
  const original = console[level].bind(console);
  console[level] = (...args) => {
    appendMainLog(level.toUpperCase(), args);
    original(...args);
  };
}

// ── 运行时完整性检查 ──

/**
 * 检查完整版本所需的关键 runtime 文件。
 * 这里只做快速存在性与体积检查；发布阶段会执行完整清单和签名校验。
 */
function verifyRuntime() {
  if (IS_DEV) return [];  // dev 模式跳过

  const checks = [
    { file: PYTHON_EXE,                                          name: 'python.exe',     minSize: 50 * 1024,  maxSize: 500 * 1024 },
    { file: path.join(RUNTIME_DIR, 'python', 'python311.dll'),   name: 'python311.dll',  minSize: 1024 * 1024 },
    { file: path.join(RUNTIME_DIR, 'python', 'python311.zip'),   name: 'python311.zip',  minSize: 1024 * 1024 },
  ];
  if (RUNTIME_PROFILE === 'full') {
    checks.push(
      { file: path.join(RUNTIME_DIR, 'node',   'node.exe'),        name: 'node.exe',       minSize: 10 * 1024 * 1024 },
      { file: path.join(RUNTIME_DIR, 'git', 'cmd', 'git.exe'),     name: 'git.exe',        minSize: 10 * 1024 },
      { file: path.join(RUNTIME_DIR, 'pandoc', 'pandoc.exe'),      name: 'pandoc.exe',     minSize: 10 * 1024 * 1024 },
      { file: path.join(RUNTIME_DIR, 'draw.io', 'draw.io.exe'),    name: 'draw.io.exe',    minSize: 50 * 1024 * 1024 },
      { file: path.join(RUNTIME_DIR, 'texlive', 'miktex', 'bin', 'x64', 'xelatex.exe'), name: 'xelatex.exe', minSize: 100 * 1024 },
    );
  }
  const issues = [];
  for (const c of checks) {
    if (!fs.existsSync(c.file)) {
      issues.push({ file: c.file, name: c.name, reason: '文件不存在' });
      continue;
    }
    try {
      const sz = fs.statSync(c.file).size;
      if (c.minSize && sz < c.minSize) {
        issues.push({ file: c.file, name: c.name, reason: `文件大小异常 (${sz} 字节)` });
      } else if (c.maxSize && sz > c.maxSize) {
        issues.push({ file: c.file, name: c.name, reason: `文件大小异常 (${sz} 字节)` });
      }
    } catch (e) {
      issues.push({ file: c.file, name: c.name, reason: `无法读取 (${e.message})` });
    }
  }
  return issues;
}

/**
 * 把 verifyRuntime 的结果格式化成对用户友好的中文诊断对话框。
 */
function showRuntimeIssueDialog(issues) {
  const installDir = path.dirname(process.execPath);
  const fileList = issues.map(i => `  • runtime\\${path.basename(path.dirname(i.file))}\\${i.name}  ${i.reason}`).join('\n');
  const detail = [
    '安装中的完整运行环境不完整，可能是下载或安装中断，也可能是安全软件隔离了文件。',
    '',
    '请先在安全软件的保护历史中确认文件来源，再从 ArHub 官方 GitHub Release',
    '重新下载带数字签名的安装器并执行覆盖安装。不要从第三方网盘补拷单个运行文件。',
    '',
    `当前安装目录：${installDir}`,
  ].join('\n');

  dialog.showMessageBoxSync({
    type: 'error',
    title: '启动失败：运行时文件被杀毒软件拦截',
    message: '检测到 ' + issues.length + ' 个关键运行时文件丢失或损坏：\n\n' + fileList,
    detail,
    buttons: ['退出'],
    defaultId: 0,
    noLink: true,
  });
}

let mainWindow = null;
let tray = null;
let pythonProcess = null;
let isQuitting = false;
let actualPort = PORT;  // 实际使用的端口（可能因占用而变）

function findCurrentInstaller(nextVersion) {
  const updaterRoot = path.join(LOCAL_APP_DATA, 'arhub-updater');
  const currentInstaller = path.join(updaterRoot, 'installer.exe');
  const installedVersion = String(app.getVersion() || '');
  if (fs.existsSync(currentInstaller)) {
    let fileVersion = '';
    try { fileVersion = String(app.getFileVersion(currentInstaller) || ''); } catch {}
    if (!fileVersion || fileVersion === installedVersion) return currentInstaller;
  }
  if (!fs.existsSync(updaterRoot)) return '';
  return fs.readdirSync(updaterRoot, { withFileTypes: true })
    .filter((entry) => entry.isFile() && /\.exe$/i.test(entry.name) && (!nextVersion || !entry.name.includes(nextVersion)))
    .map((entry) => path.join(updaterRoot, entry.name))
    .find((candidate) => {
      if (!fs.existsSync(candidate)) return false;
      let fileVersion = '';
      try { fileVersion = String(app.getFileVersion(candidate) || ''); } catch {}
      return !fileVersion || fileVersion === installedVersion;
    }) || '';
}

function verifyPackagedCapabilities() {
  if (IS_DEV) return [];
  try {
    require('./scripts/verify-capabilities.cjs');
    return [];
  } catch (error) {
    return [String(error && error.message ? error.message : error)];
  }
}

function rollbackPendingUpdate(reason) {
  const rollbackStarted = launchRollbackInstaller(reason);
  if (!rollbackStarted) return false;
  isQuitting = true;
  killBackend();
  setImmediate(() => app.quit());
  return true;
}

function launchRollbackInstaller(reason) {
  if (IS_DEV) return false;
  const decision = getStartupDecision(UPDATE_HEALTH_PATH, app.getVersion(), {
    cacheRoot: UPDATER_CACHE_ROOT,
    rollbackRoot: ROLLBACK_ROOT,
    maxRollbackAttempts: 1,
  });
  if (decision.action !== 'probe') return false;
  try {
    const claimed = claimRollback(UPDATE_HEALTH_PATH, app.getVersion(), {
      cacheRoot: UPDATER_CACHE_ROOT,
      rollbackRoot: ROLLBACK_ROOT,
      maxRollbackAttempts: 1,
      reason,
    });
    if (claimed.action !== 'rollback') return false;
    console.error(`[UpdateHealth] Startup failed; rolling back after: ${reason}`);
    spawn(claimed.installerPath, ['/S', '--force-run'], {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    }).unref();
    return true;
  } catch (error) {
    console.error('[UpdateHealth] Rollback launch failed:', error);
    return false;
  }
}

function prepareUpdateInstallation(nextVersion) {
  if (IS_DEV) return;
  let effectiveRuntime = RUNTIME_RESOLUTION;
  if (RUNTIME_RESOLUTION.source === 'legacy') {
    effectiveRuntime = migrateLegacyRuntime({
      legacyRuntimeDir: LEGACY_RUNTIME_DIR,
      localAppData: LOCAL_APP_DATA,
      profile: RUNTIME_PROFILE,
      runtimeLock: RUNTIME_LOCK,
      runtimeVersion: RUNTIME_LOCK.runtimeVersion,
      storeRoot: RUNTIME_STORE_ROOT,
    });
  }
  if (effectiveRuntime.source !== 'store' || effectiveRuntime.version !== EXPECTED_RUNTIME_VERSION) {
    throw new Error(`Runtime ${effectiveRuntime.version || 'unknown'} is not ready for an app-only update.`);
  }
  const healthDecision = getStartupDecision(UPDATE_HEALTH_PATH, nextVersion, {
    cacheRoot: UPDATER_CACHE_ROOT,
    rollbackRoot: ROLLBACK_ROOT,
    maxRollbackAttempts: 1,
  });
  let rollback = null;
  if (healthDecision.action !== 'probe') {
    const currentInstaller = findCurrentInstaller(nextVersion);
    if (!currentInstaller) {
      throw new Error('The verified current installer is unavailable; refusing an update without rollback protection.');
    }
    rollback = preserveRollbackInstaller({
      sourceInstaller: currentInstaller,
      cacheRoot: UPDATER_CACHE_ROOT,
      rollbackRoot: ROLLBACK_ROOT,
      currentVersion: app.getVersion(),
    });
  }
  markUpdatePending(UPDATE_HEALTH_PATH, {
    currentVersion: app.getVersion(),
    nextVersion,
    ...(rollback ? { rollbackInstaller: rollback } : {
      rollbackInstaller: {
        path: healthDecision.state.previousInstaller,
        sha256: healthDecision.state.previousInstallerSha256,
      },
    }),
    cacheRoot: UPDATER_CACHE_ROOT,
    rollbackRoot: ROLLBACK_ROOT,
  });
}

const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  isQuitting = true;
  app.quit();
} else {
  app.on('second-instance', () => {
    if (!mainWindow) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    if (!mainWindow.isVisible()) mainWindow.show();
    mainWindow.focus();
  });
}

// ── 端口检测 ──

function isPortAvailable(port) {
  return new Promise((resolve) => {
    const net = require('net');
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => { server.close(); resolve(true); });
    server.listen(port, '127.0.0.1');
  });
}

async function findAvailablePort(startPort, maxTries = 30) {
  for (let i = 0; i < maxTries; i++) {
    const port = startPort + i;
    if (await isPortAvailable(port)) {
      return port;
    }
    console.log(`[Port] ${port} is occupied, trying next...`);
  }
  throw new Error(`No available local port in range ${startPort}-${startPort + maxTries - 1}`);
}

// ── MiKTeX 自动安装 ──

function getMiKTeXDir() {
  const candidates = [
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'MiKTeX'),
    'C:\\Program Files\\MiKTeX',
  ];
  for (const p of candidates) {
    const xelatex = path.join(p, 'miktex', 'bin', 'x64', 'xelatex.exe');
    if (fs.existsSync(xelatex)) return p;
  }
  return null;
}

async function ensureMiKTeX() {
  // 完整版本优先使用随应用分发的 MiKTeX/TeX 运行时。
  const { execSync } = require('child_process');
  const bundledXelatex = path.join(RUNTIME_DIR, 'texlive', 'miktex', 'bin', 'x64', 'xelatex.exe');
  if (fs.existsSync(bundledXelatex)) {
    console.log('[MiKTeX] Using bundled runtime:', bundledXelatex);
    return;
  }
  
  // 先检查系统上有没有 xelatex
  let hasXelatex = false;
  try {
    execSync('where.exe xelatex', { stdio: 'ignore', timeout: 5000 });
    hasXelatex = true;
  } catch (e) {}
  
  if (!hasXelatex && getMiKTeXDir()) {
    // MiKTeX 装了但没有 xelatex，需要装 xetex 包
    const miktexDir = getMiKTeXDir();
    const miktexExe = path.join(miktexDir, 'miktex', 'bin', 'x64', 'miktex.exe');
    if (fs.existsSync(miktexExe)) {
      console.log('[MiKTeX] Installing xetex + Chinese packages...');
      const packages = ['xetex', 'ctex', 'xecjk', 'gbt7714', 'fontspec', 'booktabs', 'float', 'hyperref', 'amsmath', 'geometry', 'fancyhdr', 'caption', 'subcaption', 'multirow', 'listings', 'algorithm2e', 'pgfplots', 'xcolor', 'tcolorbox', 'biblatex', 'biber', 'natbib'];
      for (const pkg of packages) {
        try {
          execSync(`"${miktexExe}" packages install ${pkg}`, { stdio: 'ignore', timeout: 60000 });
        } catch (e) {} // 忽略已安装的包
      }
      console.log('[MiKTeX] Packages installed');
    }
    return;
  }
  
  if (hasXelatex) {
    console.log('[MiKTeX] xelatex already available');
    return;
  }

  // 没有 MiKTeX，用内嵌安装器安装
  const setupFile = path.join(RUNTIME_DIR, 'miktex-setup.exe');
  if (!fs.existsSync(setupFile)) {
    console.log('[MiKTeX] Installer not found at', setupFile);
    dialog.showMessageBox({
      type: 'warning',
      title: 'LaTeX 未安装',
      message: '未检测到 MiKTeX (LaTeX)，论文编译功能将不可用。\n请手动安装 MiKTeX: https://miktex.org/download',
    });
    return;
  }

  console.log('[MiKTeX] Installing from bundled installer (this may take several minutes)...');
  try {
    // MiKTeX 安装可能需要较长时间，给 15 分钟超时
    execSync(`"${setupFile}" --unattended --auto-install=yes --package-set=basic --paper-size=A4 --private`, {
      stdio: 'inherit',
      timeout: 900000,  // 15 分钟
    });
    console.log('[MiKTeX] Basic installation complete');
  } catch (e) {
    // 检查是否实际安装成功了（安装器可能返回非零退出码但实际装好了）
    if (getMiKTeXDir()) {
      console.log('[MiKTeX] Installation completed (installer returned non-zero but MiKTeX is present)');
    } else {
      console.error('[MiKTeX] Installation failed:', e.message);
      dialog.showMessageBox({
        type: 'warning',
        title: 'MiKTeX 安装失败',
        message: 'LaTeX 自动安装失败，论文编译功能可能不可用。\n请手动安装: https://miktex.org/download',
      });
      return;
    }
  }

  // 装完 basic 后，立刻装 xelatex 和中文包
  const newDir = getMiKTeXDir();
  if (newDir) {
    const miktexExe = path.join(newDir, 'miktex', 'bin', 'x64', 'miktex.exe');
    if (fs.existsSync(miktexExe)) {
      console.log('[MiKTeX] Installing xetex + Chinese packages...');
      const packages = ['xetex', 'ctex', 'xecjk', 'gbt7714', 'fontspec'];
      for (const pkg of packages) {
        try {
          execSync(`"${miktexExe}" packages install ${pkg}`, { stdio: 'ignore', timeout: 60000 });
        } catch (e) {}
      }
      // 启用自动安装缺失包
      const initexmf = path.join(newDir, 'miktex', 'bin', 'x64', 'initexmf.exe');
      try {
        execSync(`"${initexmf}" --set-config-value=[MPM]AutoInstall=1`, { stdio: 'ignore', timeout: 10000 });
      } catch (e) {}
      console.log('[MiKTeX] Full setup complete');
    }
  }
}

// ── Python 后端 ──

function startBackend() {
  // 查找可用的 Python
  let pythonPath;
  let pythonArgs;
  if (fs.existsSync(PYTHON_EXE)) {
    pythonPath = PYTHON_EXE;
    pythonArgs = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(actualPort), '--log-level', 'info'];
  } else {
    // 开发模式：按优先级查找可用 Python
    const candidates = [
      'C:\\Windows\\py.exe',                    // Windows Launcher
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python313', 'python.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python312', 'python.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python311', 'python.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python310', 'python.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python39', 'python.exe'),
    ];
    let found = false;
    for (const candidate of candidates) {
      if (candidate && fs.existsSync(candidate)) {
        if (candidate.endsWith('py.exe')) {
          pythonPath = candidate;
          pythonArgs = ['-3', '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(actualPort), '--log-level', 'info'];
        } else {
          pythonPath = candidate;
          pythonArgs = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(actualPort), '--log-level', 'info'];
        }
        found = true;
        break;
      }
    }
    if (!found) {
      pythonPath = 'python';
      pythonArgs = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(actualPort), '--log-level', 'info'];
    }
  }

  const env = Object.assign({}, process.env, {
    ARHUB_DESKTOP: '1',
    ARHUB_RUNTIME_DIR: RUNTIME_DIR,
    ARHUB_RUNTIME_PROFILE: RUNTIME_PROFILE,
    ARHUB_DATA_DIR: USER_DATA_DIR,
    ARHUB_FRONTEND_DIST: path.join(APP_ROOT, 'dist'),
    API_PORT: String(actualPort),
    ARHUB_API_PORT: String(actualPort),
    PYTHONDONTWRITEBYTECODE: '1',
    // 强制 UTF-8 编码（防止 Git Bash 写中文文件时乱码）
    LANG: 'en_US.UTF-8',
    LC_ALL: 'en_US.UTF-8',
    PYTHONIOENCODING: 'utf-8',
    PYTHONUTF8: '1',
  });

  // 把 runtime 工具链加入 PATH
  const extraPaths = [];
  const nodeDir = path.join(RUNTIME_DIR, 'node');
  if (fs.existsSync(nodeDir)) extraPaths.push(nodeDir);
  const texDir = path.join(RUNTIME_DIR, 'texlive', 'bin', 'windows');
  const texDirAlt = path.join(RUNTIME_DIR, 'texlive', 'miktex', 'bin', 'x64');
  if (fs.existsSync(texDir)) extraPaths.push(texDir);
  else if (fs.existsSync(texDirAlt)) extraPaths.push(texDirAlt);

  // Git Bash — Claude CLI 在 Windows 上必须有
  const gitBashPaths = [
    path.join(RUNTIME_DIR, 'git', 'bin', 'bash.exe'),
    'D:\\Git\\bin\\bash.exe',
    'C:\\Program Files\\Git\\bin\\bash.exe',
    'C:\\Program Files (x86)\\Git\\bin\\bash.exe',
  ];
  for (const bp of gitBashPaths) {
    if (fs.existsSync(bp)) {
      env.CLAUDE_CODE_GIT_BASH_PATH = bp;
      // 也把 git 的 cmd 和 bin 加入 PATH
      const gitBin = path.dirname(bp);
      extraPaths.push(gitBin);
      const gitCmd = path.join(path.dirname(gitBin), 'cmd');
      if (fs.existsSync(gitCmd)) extraPaths.push(gitCmd);
      console.log('[Backend] Git Bash:', bp);
      break;
    }
  }
  const pyDir = path.dirname(pythonPath);
  if (fs.existsSync(pyDir)) {
    extraPaths.push(pyDir);
    const scriptsDir = path.join(pyDir, 'Scripts');
    if (fs.existsSync(scriptsDir)) extraPaths.push(scriptsDir);
  }
  if (extraPaths.length) {
    env.PATH = extraPaths.join(';') + ';' + (env.PATH || '');
  }

  console.log('[Backend] Starting:', pythonPath, ...pythonArgs);
  console.log('[Backend] CWD:', BACKEND_DIR);

  pythonProcess = spawn(pythonPath, pythonArgs, {
    cwd: BACKEND_DIR,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  pythonProcess.stdout.on('data', (data) => {
    process.stdout.write(`[Backend] ${data}`);
  });
  pythonProcess.stderr.on('data', (data) => {
    process.stderr.write(`[Backend] ${data}`);
  });
  pythonProcess.on('exit', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
    if (!isQuitting) {
      if (!rollbackPendingUpdate(`Backend exited during startup verification (code=${code}).`)) {
        dialog.showErrorBox('后端异常退出', `Python 后端进程退出（code=${code}）。\n请检查日志或重启 ArHub。`);
      }
    }
  });
}

function killBackend() {
  if (!pythonProcess) return;
  try {
    // Windows: taskkill /T 杀掉整个进程树
    const { execSync } = require('child_process');
    execSync(`taskkill /T /F /PID ${pythonProcess.pid}`, { stdio: 'ignore', shell: true });
  } catch (e) {
    try { pythonProcess.kill('SIGTERM'); } catch (_) {}
  }
  pythonProcess = null;
}

// ── 健康检查 ──

function waitForBackend(maxRetries = 60, interval = 500) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const healthUrl = `http://127.0.0.1:${actualPort}/api/health`;
    const check = () => {
      attempts++;
      const req = http.get(healthUrl, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else if (attempts < maxRetries) {
          setTimeout(check, interval);
        } else {
          reject(new Error(`Backend not ready after ${maxRetries} attempts`));
        }
      });
      req.on('error', () => {
        if (attempts < maxRetries) {
          setTimeout(check, interval);
        } else {
          reject(new Error(`Backend not ready after ${maxRetries} attempts`));
        }
      });
      req.setTimeout(2000, () => { req.destroy(); });
    };
    check();
  });
}

// ── 窗口 ──

function isLocalBackendUrl(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    return parsed.protocol === 'http:' &&
      parsed.hostname === '127.0.0.1' &&
      parsed.port === String(actualPort);
  } catch {
    return false;
  }
}

function openSafeExternalUrl(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    if (!['http:', 'https:', 'mailto:'].includes(parsed.protocol)) return false;
    shell.openExternal(parsed.toString());
    return true;
  } catch {
    return false;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: 'ArHub',
    icon: path.join(__dirname, 'icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  });

  if (IS_SMOKE_TEST) {
    let smokeFinished = false;
    mainWindow.webContents.once('did-finish-load', () => {
      if (smokeFinished) return;
      smokeFinished = true;
      console.log('[SmokeTest] Frontend loaded');
      setTimeout(() => {
        isQuitting = true;
        app.quit();
      }, 500);
    });
    mainWindow.webContents.once('did-fail-load', (_event, errorCode, errorDescription, validatedURL, isMainFrame) => {
      if (!isMainFrame || smokeFinished) return;
      smokeFinished = true;
      process.exitCode = 1;
      console.error(`[SmokeTest] Frontend failed to load (${errorCode}): ${errorDescription} ${validatedURL}`);
      isQuitting = true;
      app.quit();
    });
  }

  // 缓存策略由后端 Cache-Control 控制（无哈希资源 no-cache 协商 + 304）。
  // 不要恢复 clearCache()：它会连 V8 code cache 一起清掉，每次启动都重新编译 1.2MB 的主 bundle。

  // 后端就绪前先显示 splash，whenReady 流程在健康检查通过后再 loadURL 换真页面。
  // 冒烟测试直接等真实前端，避免 splash 的 did-finish-load 误报成功。
  if (!IS_SMOKE_TEST) {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'splash.html'));
  }

  // 外部链接用系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (isLocalBackendUrl(url)) return { action: 'allow' };
    openSafeExternalUrl(url);
    return { action: 'deny' };
  });
  mainWindow.webContents.on('will-navigate', (e, url) => {
    if (!isLocalBackendUrl(url)) {
      e.preventDefault();
      openSafeExternalUrl(url);
    }
  });

  mainWindow.once('ready-to-show', () => {
    if (!IS_SMOKE_TEST) mainWindow.show();
  });

  // 关闭时最小化到托盘
  mainWindow.on('close', (e) => {
    if (!isQuitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });
}

// ── 托盘 ──

function createTray() {
  const iconPath = path.join(__dirname, 'icon.ico');
  // 如果 icon 不存在，跳过托盘
  if (!fs.existsSync(iconPath)) {
    console.log('[Tray] icon.ico not found, skipping tray');
    return;
  }

  tray = new Tray(iconPath);
  tray.setToolTip('ArHub — AI 科研助手');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

// ── 生命周期 ──

app.on('ready', async () => {
  createTray();

  if (RUNTIME_COMPATIBILITY_ERROR) {
    const rollbackStarted = launchRollbackInstaller(RUNTIME_COMPATIBILITY_ERROR);
    if (!rollbackStarted) dialog.showErrorBox('运行时不兼容', RUNTIME_COMPATIBILITY_ERROR);
    isQuitting = true;
    app.quit();
    return;
  }

  const capabilityIssues = verifyPackagedCapabilities();
  if (capabilityIssues.length > 0) {
    console.error('[Capabilities] Startup verification failed:', capabilityIssues);
    const reason = capabilityIssues.join('\n');
    const rollbackStarted = launchRollbackInstaller(reason);
    if (!rollbackStarted) dialog.showErrorBox('能力资源缺失', reason);
    isQuitting = true;
    app.quit();
    return;
  }

  // ⛔ 启动前完整性检查：python.exe 等关键文件是否被杀毒软件误删/隔离
  const runtimeIssues = verifyRuntime();
  if (runtimeIssues.length > 0) {
    console.error('[Runtime] Integrity check failed:', runtimeIssues);
    showRuntimeIssueDialog(runtimeIssues);
    isQuitting = true;
    app.quit();
    return;
  }

  try {
    // 自动选择可用端口（避免端口占用导致启动失败）
    actualPort = await findAvailablePort(PORT);
    if (actualPort !== PORT) {
      console.log(`[Port] Default port ${PORT} occupied, using ${actualPort} instead`);
    } else {
      console.log(`[Port] Using port ${actualPort}`);
    }

    // 先建窗口显示 splash：Chromium 预热与 MiKTeX 检查、Python 启动并行，
    // 用户不再对着无窗口的空白等待。
    createWindow();

    // 首次启动：自动安装 MiKTeX（如果系统上没有）
    try {
      await ensureMiKTeX();
    } catch (e) {
      console.error('[MiKTeX] Setup error:', e.message);
      // 不阻塞启动，编译功能可能不可用但其他功能正常
    }

    startBackend();
    await waitForBackend();
    console.log('[App] Backend is ready');
    if (mainWindow && !mainWindow.isDestroyed()) {
      await mainWindow.loadURL(`http://127.0.0.1:${actualPort}`);
    }
    if (!IS_DEV) {
      const healthDecision = getStartupDecision(UPDATE_HEALTH_PATH, app.getVersion(), {
        cacheRoot: UPDATER_CACHE_ROOT,
        rollbackRoot: ROLLBACK_ROOT,
        maxRollbackAttempts: 1,
      });
      if (healthDecision.action === 'probe') {
        healthConfirmationTimer = setTimeout(() => {
          try {
            if (!pythonProcess || !mainWindow || mainWindow.isDestroyed()) {
              throw new Error('Startup health did not remain stable through the verification window.');
            }
            markVersionHealthy(UPDATE_HEALTH_PATH, app.getVersion());
            console.log(`[UpdateHealth] v${app.getVersion()} marked healthy.`);
          } catch (error) {
            console.error('[UpdateHealth] Delayed health confirmation failed:', error);
            rollbackPendingUpdate(error.message);
          }
        }, 30_000);
        healthConfirmationTimer.unref();
      } else {
        markVersionHealthy(UPDATE_HEALTH_PATH, app.getVersion());
      }
    }
    // 启动 5 秒后静默检查更新
    setTimeout(() => initUpdater().catch(e => console.error('[Updater] init failed:', e)), 5000);
  } catch (err) {
    console.error('[App] Startup failed:', err);
    const rollbackStarted = launchRollbackInstaller(err.message);
    if (!rollbackStarted) dialog.showErrorBox('启动失败', `${err.message}\n\n日志位置：${MAIN_LOG}`);
    isQuitting = true;
    killBackend();
    app.quit();
  }
});

// ============================================================
// 自动更新
// ============================================================
let updater = null;
let updaterTimer = null;
let updaterRetryTimer = null;
let preparedUpdateVersion = '';
let updateInstallationStarted = false;
let preparedUpdateSource = 'manual';
let healthConfirmationTimer = null;

function sendUpdateProgress(progress) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send('update-progress', progress);
}

function startAutomaticUpdateDownload(result, attempt = 0) {
  if (!updater || !result || !result.hasUpdate || updater.config.auto_download !== true) return;
  if (!updater.getDownloadStatus(result.version).current) return;
  updater.downloadUpdate(result, sendUpdateProgress)
    .then(() => {
      const status = updater.getDownloadStatus(result.version);
      if (!status.current || !status.downloaded) return;
      try {
        prepareUpdateInstallation(result.version);
        preparedUpdateVersion = result.version;
        preparedUpdateSource = 'automatic';
      } catch (error) {
        console.error('[Updater] update preparation failed:', error);
        return;
      }
      console.log(`[Updater] v${result.version} downloaded; it will install on normal app exit.`);
      sendUpdateAvailable({ ...result, downloaded: true });
    })
    .catch((error) => {
      console.error('[Updater] automatic download failed:', error);
      if (attempt >= 2 || isQuitting || !updater.getDownloadStatus(result.version).current) return;
      const delay = attempt === 0 ? 5 * 60 * 1000 : 30 * 60 * 1000;
      if (updaterRetryTimer) clearTimeout(updaterRetryTimer);
      updaterRetryTimer = setTimeout(() => startAutomaticUpdateDownload(result, attempt + 1), delay);
      updaterRetryTimer.unref();
    });
}

function sendUpdateAvailable(result) {
  if (!result || !result.hasUpdate || !mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send('update-available', {
    version: result.version,
    changelog: result.changelog,
    fileCount: result.fileCount || result.changedFiles.length,
    totalSize: result.totalSize,
    downloaded: result.downloaded === true,
  });
}

async function checkAndNotifyUpdate(force = false) {
  if (!updater) return { hasUpdate: false, reason: 'updater not initialized' };
  const result = await updater.checkForUpdate({ force });
  if (result.hasUpdate) {
    console.log(`[Updater] update available: v${result.version} (${result.fileCount} artifacts, ${(result.totalSize / 1024 / 1024).toFixed(2)} MB)`);
    if (updater.config.auto_download === true) startAutomaticUpdateDownload(result);
    else sendUpdateAvailable(result);
  } else {
    console.log(`[Updater] no update: ${result.reason}`);
  }
  return result;
}

async function initUpdater() {
  // 仅打包模式下启用更新 (开发模式不更新)
  if (IS_DEV) {
    console.log('[Updater] Dev mode, skip auto-update');
    return;
  }

  // 发布源由打包生成的 app-update.yml 固定到官方 GitHub Releases。
  let updateCfg = {
    enabled: true,
    check_interval_hours: 6,
    allow_prerelease: false,
    require_publisher_verification: false,
    auto_download: true,
    install_on_quit: true,
  };
  try {
    const cfgPath = path.join(APP_ROOT, 'updater-config.json');
    if (fs.existsSync(cfgPath)) {
      Object.assign(updateCfg, JSON.parse(fs.readFileSync(cfgPath, 'utf8')));
    }
  } catch (e) {
    console.warn('[Updater] config load failed:', e.message);
  }
  if (!updateCfg.enabled || Number(updateCfg.check_interval_hours) <= 0) {
    console.log('[Updater] disabled by config');
    return;
  }

  updater = new Updater({
    check_interval_hours: updateCfg.check_interval_hours,
    allow_prerelease: updateCfg.allow_prerelease,
    require_publisher_verification: updateCfg.require_publisher_verification === true,
    auto_download: updateCfg.auto_download !== false,
    install_on_quit: false,
    runtime_profile: RUNTIME_PROFILE,
    user_data_dir: USER_DATA_DIR,
    update_config_path: path.join(process.resourcesPath, 'app-update.yml'),
    logger: console,
  });

  updaterTimer = setInterval(() => {
    checkAndNotifyUpdate(false).catch((error) => console.error('[Updater] scheduled check failed:', error));
  }, 60 * 60 * 1000);
  updaterTimer.unref();

  try {
    await checkAndNotifyUpdate(false);
  } catch (e) {
    console.error('[Updater] check error:', e);
  }
}

// IPC: 前端触发开始下载
ipcMain.handle('updater:start-download', async () => {
  if (!updater || !updater._lastCheck || !updater._lastCheck.hasUpdate) {
    return { ok: false, error: 'no update available' };
  }
  try {
    await updater.downloadUpdate(updater._lastCheck, (progress) => {
      sendUpdateProgress(progress);
    });
    prepareUpdateInstallation(updater._lastCheck.version);
    preparedUpdateVersion = updater._lastCheck.version;
    preparedUpdateSource = 'manual';
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
});

// IPC: 前端触发应用更新 + 重启
ipcMain.handle('updater:apply-and-restart', async () => {
  if (!updater) return { ok: false, error: 'updater not initialized' };
  try {
    const status = updater.getDownloadStatus();
    if (preparedUpdateVersion !== status.version) prepareUpdateInstallation(status.version);
    preparedUpdateVersion = status.version;
    preparedUpdateSource = 'manual';
    isQuitting = true;
    killBackend();
    updateInstallationStarted = true;
    setTimeout(() => updater.applyUpdateAndRestart(), 250);
    return { ok: true };
  } catch (error) {
    updateInstallationStarted = false;
    isQuitting = false;
    return { ok: false, error: error.message };
  }
});

// IPC: 前端取消下载
ipcMain.handle('updater:abort', async () => {
  if (updater) updater.abortDownload();
  return { ok: true };
});

// IPC: 前端跳过版本
ipcMain.handle('updater:skip-version', async (_e, version) => {
  if (updater) updater.skipVersion(version);
  return { ok: true };
});

// IPC: 前端拉取缓存的检查结果 (用户激活通过后调用, 不会重新查 manifest)
ipcMain.handle('updater:get-cached', async () => {
  if (!updater) return { hasUpdate: false, reason: 'updater not initialized' };
  if (updater.config.auto_download === true) {
    const status = updater.getDownloadStatus();
    if (status.current && status.downloaded && updater._lastCheck) {
      return { ...updater._lastCheck, downloaded: true };
    }
    if (status.downloading) return { hasUpdate: false, reason: 'automatic update in progress' };
  }

  return updater._lastCheck || { hasUpdate: false, reason: 'no check yet' };
});

// IPC: 前端手动检查更新
ipcMain.handle('updater:check-now', async () => {
  if (!updater) return { hasUpdate: false, reason: 'not initialized' };
  return checkAndNotifyUpdate(true);
});

app.on('before-quit', () => {
  if (!IS_DEV && updater && preparedUpdateVersion && preparedUpdateSource === 'automatic' && !updateInstallationStarted) {
    const status = updater.getDownloadStatus(preparedUpdateVersion);
    if (status.current && status.downloaded) {
      updateInstallationStarted = true;
      setImmediate(() => {
        try {
          updater.applyUpdateAndRestart();
        } catch (error) {
          console.error('[Updater] install-on-quit failed:', error);
        }
      });
    }
  }
  isQuitting = true;
  if (healthConfirmationTimer) clearTimeout(healthConfirmationTimer);
  if (updaterTimer) clearInterval(updaterTimer);
  if (updaterRetryTimer) clearTimeout(updaterRetryTimer);
  killBackend();
});

app.on('window-all-closed', () => {
  // macOS 上不退出（但本项目只针对 Windows）
  if (process.platform !== 'darwin') {
    // 不退出，保持托盘运行
  }
});

app.on('activate', () => {
  if (mainWindow) {
    mainWindow.show();
  }
});
