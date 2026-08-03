'use strict';

const path = require('node:path');

const APP_EXECUTABLE = 'ArHub.exe';
const ELEVATION_HELPER = path.join('win-unpacked', 'resources', 'elevate.exe');

function getArtifactName(version, artifactSuffix = '', arch = 'x64', profileSuffix = '') {
  if (!version) throw new Error('A package version is required to build the signing policy.');
  return `ArHub-Setup-${version}${profileSuffix}-${arch}${artifactSuffix}.exe`;
}

function getSigningSuffixes(version, artifactSuffix = '', arch = 'x64', profileSuffix = '') {
  const artifactName = getArtifactName(version, artifactSuffix, arch, profileSuffix);
  const uninstallerName = artifactName.replace(/\.exe$/i, '.__uninstaller.exe');
  return [
    APP_EXECUTABLE,
    ELEVATION_HELPER,
    artifactName,
    uninstallerName,
    '!.exe',
  ];
}

// Mirrors electron-builder 26's signExts matching order. Positive suffixes are
// evaluated first; the final negative suffix blocks every other executable.
function shouldSign(file, version, artifactSuffix = '', arch = 'x64') {
  const suffixes = getSigningSuffixes(version, artifactSuffix, arch);
  if (suffixes.some((suffix) => !suffix.startsWith('!') && file.endsWith(suffix))) {
    return true;
  }
  if (suffixes.some((suffix) => suffix.startsWith('!') && file.endsWith(suffix.slice(1)))) {
    return false;
  }
  return file.endsWith('.exe');
}

module.exports = {
  APP_EXECUTABLE,
  ELEVATION_HELPER,
  getArtifactName,
  getSigningSuffixes,
  shouldSign,
};
