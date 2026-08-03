const fs = require('fs');
const path = require('path');
const packageMetadata = require('./package.json');
const { getSigningSuffixes } = require('./packaging/signing-policy.cjs');

const projectDir = __dirname;
const runtimeDir = process.env.ARHUB_RUNTIME_DIR
  ? path.resolve(process.env.ARHUB_RUNTIME_DIR)
  : path.join(projectDir, 'runtime');
const requireSigning = process.env.ARHUB_REQUIRE_SIGNING === '1';
const publisherName = String(process.env.ARHUB_PUBLISHER_NAME || '').trim();
const signingProvider = String(process.env.ARHUB_SIGNING_PROVIDER || 'pfx').toLowerCase();
const artifactSuffix = process.env.ARHUB_ARTIFACT_SUFFIX || '';
const runtimeProfile = String(process.env.ARHUB_RUNTIME_PROFILE || 'full').toLowerCase();
if (!['full', 'lite'].includes(runtimeProfile)) {
  throw new Error(`Unsupported ARHUB_RUNTIME_PROFILE: ${runtimeProfile}`);
}
const profileSuffix = runtimeProfile === 'lite' ? '-lite' : '';
const signingSuffixes = getSigningSuffixes(packageMetadata.version, artifactSuffix);

const liteExcludedComponents = ['node', 'git', 'pandoc', 'draw.io', 'texlive'];
const liteExcludedPythonPackages = [
  'tensorflow*',
  'torch*',
  'functorch*',
  'paddle*',
  'catboost*',
  'cv2*',
  'opencv*',
  'xgboost*',
  'llvmlite*',
  'numba*',
  'clang*',
  'ortools*',
  'pyarrow*',
  'transformers*',
  'modelscope*',
  'rdkit*',
  'pyogrio*',
];
const runtimeFilter = ['**/*'];
if (runtimeProfile === 'lite') {
  for (const component of liteExcludedComponents) {
    runtimeFilter.push(`!${component}`, `!${component}/**/*`);
  }
  for (const packagePattern of liteExcludedPythonPackages) {
    runtimeFilter.push(
      `!python/Lib/site-packages/${packagePattern}`,
      `!python/Lib/site-packages/${packagePattern}/**/*`,
    );
  }
}

if (!fs.existsSync(runtimeDir)) {
  throw new Error(`Full runtime was not found: ${runtimeDir}`);
}
if (requireSigning && !publisherName) {
  throw new Error('ARHUB_PUBLISHER_NAME is required for a signed release.');
}

const win = {
  target: [{ target: 'nsis', arch: ['x64'] }],
  icon: 'icon.ico',
  artifactName: `ArHub-Setup-\${version}${profileSuffix}-\${arch}${artifactSuffix}.\${ext}`,
  requestedExecutionLevel: 'asInvoker',
  signAndEditExecutable: true,
  signExecutable: requireSigning,
  // Sign only ArHub's executable, updater elevation helper and generated NSIS
  // artifacts. The final negative suffix preserves all bundled vendor binaries.
  signExts: signingSuffixes,
  verifyUpdateCodeSignature: requireSigning,
};

if (publisherName) {
  win.publisherName = [publisherName];
}

if (signingProvider === 'azure') {
  const azure = {
    endpoint: process.env.AZURE_TRUSTED_SIGNING_ENDPOINT,
    codeSigningAccountName: process.env.AZURE_TRUSTED_SIGNING_ACCOUNT,
    certificateProfileName: process.env.AZURE_TRUSTED_SIGNING_PROFILE,
    publisherName,
  };
  const missing = Object.entries(azure).filter(([, value]) => !value).map(([key]) => key);
  if (requireSigning && missing.length > 0) {
    throw new Error(`Azure Trusted Signing configuration is incomplete: ${missing.join(', ')}`);
  }
  if (missing.length === 0) {
    win.azureSignOptions = azure;
  }
}

module.exports = {
  appId: 'io.github.jiashuoyan0-maker.arhub',
  productName: 'ArHub',
  copyright: 'Copyright (c) ArHub contributors',
  asar: false,
  compression: 'maximum',
  npmRebuild: false,
  forceCodeSigning: requireSigning,
  extraMetadata: {
    arhubRuntimeProfile: runtimeProfile,
  },
  directories: {
    output: 'release',
    buildResources: '.',
  },
  files: [
    'main.js',
    'preload.js',
    'updater.js',
    'updater-config.json',
    'package.json',
    'extension.schema.json',
    'LICENSE',
    'THIRD_PARTY_NOTICES.md',
    'backend/**/*',
    'dist/**/*',
    'extensions/**/*',
    'licenses/**/*',
    'skills/**/*',
    'templates/**/*',
    'tools/**/*',
    '!**/__pycache__/**',
    '!**/*.py[co]',
    '!**/*.log',
    '!tools/**/node_modules/**',
    // Chromium 只会下载 woff2；ttf/woff 是编译产物里的冗余 fallback，打包排除即可。
    '!dist/assets/KaTeX_*.ttf',
    '!dist/assets/KaTeX_*.woff',
  ],
  extraFiles: [
    {
      from: runtimeDir,
      to: 'runtime',
      filter: runtimeFilter,
    },
  ],
  win,
  nsis: {
    oneClick: false,
    perMachine: false,
    allowElevation: true,
    allowToChangeInstallationDirectory: true,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    shortcutName: 'ArHub',
    uninstallDisplayName: 'ArHub',
    deleteAppDataOnUninstall: false,
    runAfterFinish: true,
    installerIcon: 'icon.ico',
    uninstallerIcon: 'icon.ico',
  },
  publish: [
    {
      provider: 'github',
      owner: 'jiashuoyan0-maker',
      repo: 'ArHub',
      releaseType: 'release',
    },
  ],
};
