const fs = require('fs');
const path = require('path');
const packageMetadata = require('./package.json');
const { getSigningSuffixes } = require('./packaging/signing-policy.cjs');

const projectDir = __dirname;
const runtimeDir = process.env.ARHUB_RUNTIME_DIR
  ? path.resolve(process.env.ARHUB_RUNTIME_DIR)
  : path.join(process.env.LOCALAPPDATA || '', 'Programs', 'ArHub', 'runtime');
const requireSigning = process.env.ARHUB_REQUIRE_SIGNING === '1';
const publisherName = String(process.env.ARHUB_PUBLISHER_NAME || '').trim();
const signingProvider = String(process.env.ARHUB_SIGNING_PROVIDER || 'pfx').toLowerCase();
const artifactSuffix = process.env.ARHUB_ARTIFACT_SUFFIX || '';
const signingSuffixes = getSigningSuffixes(packageMetadata.version, artifactSuffix);

if (!fs.existsSync(runtimeDir)) {
  throw new Error(`Full runtime was not found: ${runtimeDir}`);
}
if (requireSigning && !publisherName) {
  throw new Error('ARHUB_PUBLISHER_NAME is required for a signed release.');
}

const win = {
  target: [{ target: 'nsis', arch: ['x64'] }],
  icon: 'icon.ico',
  artifactName: `ArHub-Setup-\${version}-\${arch}${artifactSuffix}.\${ext}`,
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
  ],
  extraFiles: [
    {
      from: runtimeDir,
      to: 'runtime',
      filter: ['**/*'],
    },
  ],
  win,
  nsis: {
    oneClick: true,
    perMachine: false,
    allowElevation: true,
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
