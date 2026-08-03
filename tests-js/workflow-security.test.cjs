'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const workflowDir = path.join(__dirname, '..', '.github', 'workflows');

test('third-party workflow actions are pinned to immutable commits', () => {
  const workflows = fs.readdirSync(workflowDir).filter((name) => /\.ya?ml$/i.test(name));
  const unpinned = [];

  for (const name of workflows) {
    const text = fs.readFileSync(path.join(workflowDir, name), 'utf8');
    for (const [index, line] of text.split(/\r?\n/).entries()) {
      const match = line.match(/^\s*(?:-\s*)?uses:\s*([^\s#]+)/);
      if (!match || match[1].startsWith('./') || match[1].startsWith('docker://')) continue;
      if (!/@[0-9a-f]{40}$/i.test(match[1])) {
        unpinned.push(`${name}:${index + 1} (${match[1]})`);
      }
    }
  }

  assert.deepEqual(unpinned, []);
});

test('release upload and checksum asset allowlists stay aligned', () => {
  const releaseWorkflow = fs.readFileSync(path.join(workflowDir, 'release-windows.yml'), 'utf8');
  const checksumScript = fs.readFileSync(
    path.join(__dirname, '..', 'scripts', 'create-checksums.ps1'),
    'utf8',
  );
  const requiredPatterns = [
    'ArHub-Setup-*',
    '*.blockmap',
    'latest.yml',
    'sbom-*.cdx.json',
    'installer-smoke-report.json',
  ];
  for (const pattern of requiredPatterns) {
    assert.match(releaseWorkflow, new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    assert.match(checksumScript, new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  assert.doesNotMatch(checksumScript, /builder-debug\.yml/);
});

test('official Windows releases are explicitly unsigned and retain integrity artifacts', () => {
  const releaseWorkflow = fs.readFileSync(path.join(workflowDir, 'release-windows.yml'), 'utf8');
  const updaterConfig = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'updater-config.json'), 'utf8'),
  );
  assert.match(releaseWorkflow, /-UnsignedRelease\b/);
  assert.match(releaseWorkflow, /-RequireUnsigned\b/);
  assert.doesNotMatch(releaseWorkflow, /WINDOWS_CERTIFICATE|AZURE_TRUSTED_SIGNING|azure\/login/);
  assert.doesNotMatch(releaseWorkflow, /^\s*environment:\s*windows-release\s*$/m);
  assert.equal(updaterConfig.require_publisher_verification, false);
  assert.match(releaseWorkflow, /SHA256SUMS\.txt/);
  assert.match(releaseWorkflow, /attest-build-provenance/);
});

test('runtime archives exclude volatile timestamps for reproducible hashes', () => {
  const packageRuntime = fs.readFileSync(
    path.join(__dirname, '..', 'scripts', 'package-runtime.ps1'),
    'utf8',
  );
  for (const option of ['-mtm=off', '-mta=off', '-mtc=off']) {
    assert.ok(packageRuntime.includes(`'${option}'`));
  }
});

test('runtime inspection never rewrites embedded Python bytecode', () => {
  for (const relativePath of [
    'scripts/assert-runtime.ps1',
    'scripts/generate-sbom.ps1',
    'scripts/export-runtime-lock.ps1',
  ]) {
    const script = fs.readFileSync(path.join(__dirname, '..', relativePath), 'utf8');
    for (const line of script.split(/\r?\n/).filter((entry) => /&\s*\$pythonExe\b/.test(entry))) {
      assert.match(line, /\s-B\s+-X\s+utf8\b/, `${relativePath} must disable bytecode writes: ${line}`);
    }
  }
});

test('runtime workflow verifies and reuses only the explicitly configured locked cache', () => {
  const runtimeWorkflow = fs.readFileSync(path.join(workflowDir, 'runtime-bundle.yml'), 'utf8');
  const packageRuntime = fs.readFileSync(
    path.join(__dirname, '..', 'scripts', 'package-runtime.ps1'),
    'utf8',
  );
  const verifyRuntime = fs.readFileSync(
    path.join(__dirname, '..', 'scripts', 'verify-runtime-bundle.ps1'),
    'utf8',
  );
  assert.match(runtimeWorkflow, /ARHUB_RUNTIME_BUNDLE_CACHE/);
  assert.match(runtimeWorkflow, /-ArchiveSeedDir/);
  assert.match(runtimeWorkflow, /-ReuseExistingArchives/);
  assert.match(packageRuntime, /Locked archive seed size mismatch/);
  assert.match(packageRuntime, /Locked archive seed hash mismatch/);
  assert.match(packageRuntime, /Generated runtime bundle does not match the committed lock/);
  assert.match(packageRuntime, /Copy-Item -LiteralPath \$committedBundlePath -Destination \$bundlePath/);
  assert.match(verifyRuntime, /-replace "`r`n", "`n" -replace "`r", "`n"/);
  assert.match(verifyRuntime, /Runtime archive hash mismatch/);
  assert.match(verifyRuntime, /SHA256SUMS\.txt mismatch/);
  assert.doesNotMatch(runtimeWorkflow, /gh release view/);
  assert.match(runtimeWorkflow, /gh release list/);
  assert.match(runtimeWorkflow, /\.tagName -ceq \$tag/);
});

test('Windows CI uses portable Node test discovery and avoids duplicate branch runs', () => {
  const quality = fs.readFileSync(path.join(workflowDir, 'quality.yml'), 'utf8');
  const packageMetadata = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'),
  );
  assert.equal(packageMetadata.scripts['test:node'], 'node scripts/run-node-tests.cjs');
  assert.doesNotMatch(packageMetadata.scripts['test:node'], /[*?]/);
  assert.match(quality, /push:\s*\r?\n\s+branches:\s*\[main\]/);
  assert.match(quality, /pull_request:/);
});

test('automatic Lite publishing only trusts successful main pushes from this repository', () => {
  const workflow = fs.readFileSync(path.join(workflowDir, 'auto-lite-candidate.yml'), 'utf8');
  assert.match(workflow, /workflow_run\.event == 'push'/);
  assert.match(workflow, /workflow_run\.head_branch == 'main'/);
  assert.match(workflow, /workflow_run\.head_repository\.full_name == github\.repository/);
  assert.match(workflow, /workflow_run\.head_sha == github\.sha/);
  assert.match(workflow, /cancel-in-progress:\s*true/);
  assert.match(workflow, /-RuntimeProfile lite\b/);
  assert.match(workflow, /-SkipTests\b/);
  assert.match(workflow, /--target '\$\{\{ github\.event\.workflow_run\.head_sha \|\| github\.sha \}\}'/);
  assert.doesNotMatch(workflow, /git push origin/);
  assert.doesNotMatch(workflow, /scripts\/assert-runtime\.ps1/);
});

test('app-only candidates are isolated from Full builds and runtime inputs', () => {
  const workflow = fs.readFileSync(path.join(workflowDir, 'auto-app-only-candidate.yml'), 'utf8');
  assert.match(workflow, /workflow_run\.event == 'push'/);
  assert.match(workflow, /workflow_run\.head_branch == 'main'/);
  assert.match(workflow, /workflow_run\.head_repository\.full_name == github\.repository/);
  assert.match(workflow, /workflow_run\.head_sha.*git rev-parse HEAD/s);
  assert.match(workflow, /inputs\.publish == true/);
  assert.match(workflow, /source_sha:/);
  assert.match(workflow, /merge-base --is-ancestor \$expected origin\/main/);
  assert.doesNotMatch(workflow, /workflow_run\.head_sha \|\| github\.sha/);
  assert.match(workflow, /-RuntimeProfile app-only\b/);
  assert.match(workflow, /-SkipTests\b/);
  assert.match(workflow, /unexpected installer profile/);
  assert.match(workflow, /forbidden Full\/Lite runtime assets/);
  assert.doesNotMatch(workflow, /RuntimeProfile (?:full|lite)|ARHUB_RUNTIME_DIR|assert-runtime\.ps1/);
  assert.doesNotMatch(workflow, /git push origin/);

  const packageMetadata = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'),
  );
  assert.match(packageMetadata.scripts['package:win:app-only'], /-RuntimeProfile app-only\b/);

  const buildScript = fs.readFileSync(
    path.join(__dirname, '..', 'scripts', 'build-windows.ps1'),
    'utf8',
  );
  assert.match(buildScript, /ValidateSet\('full', 'lite', 'app-only'\)/);
  assert.match(buildScript, /if \(-not \$isAppOnly\)/);
  assert.match(buildScript, /unexpectedly contains a runtime directory/);
});

test('maintenance runs under PowerShell 7 and uses exact-title issue synchronization', () => {
  const maintenance = fs.readFileSync(path.join(workflowDir, 'maintenance.yml'), 'utf8');
  const issueSync = fs.readFileSync(
    path.join(__dirname, '..', 'scripts', 'sync-maintenance-issue.ps1'),
    'utf8',
  );
  const shellLines = maintenance
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('shell:'));

  assert.ok(shellLines.includes('shell: pwsh'));
  assert.ok(!shellLines.includes('shell: powershell'));
  assert.ok(maintenance.includes("Join-Path $env:RUNNER_TEMP 'arhub-maintenance'"));
  assert.ok(maintenance.includes('-ReportPath $runtimeReport'));
  assert.ok(!maintenance.includes('-FilePath maintenance-security-report.txt'));
  assert.ok(!maintenance.includes('-FilePath runtime-check-log.txt'));
  assert.match(maintenance, /sync-maintenance-issue\.ps1/);
  assert.doesNotMatch(maintenance, /gh issue list --state open --search/);
  assert.ok(issueSync.includes('Where-Object { $_.title -ceq $Title }'));
  assert.match(issueSync, /Superseded by/);
});
