# Releasing ArHub for Windows

ArHub publishes a per-user, one-click NSIS installer. The desktop executable,
uninstaller and installer must carry a valid, timestamped Authenticode signature.
The release workflow refuses to publish an unsigned artifact.

The signing allowlist contains `ArHub.exe`, the packaged updater elevation
helper, and the generated NSIS installer/uninstaller. All other executables are
excluded. After packaging, the complete runtime is checked against the committed
byte counts and probe hashes so a release cannot replace Python, Node.js, Git,
Pandoc, Draw.io or MiKTeX vendor signatures.

## Required repository configuration

Choose one signing provider.

The release job targets the `windows-release` GitHub Environment. Store signing
secrets in that environment where possible so they are exposed only to the
release job; repository-level secrets with the same names also work. Never put a
certificate, password or Azure credential in a repository variable or file.

### PFX certificate

Create these GitHub Actions secrets:

- `ARHUB_PUBLISHER_NAME`: exact certificate common name shown by Windows.
- `WINDOWS_CERTIFICATE_BASE64`: base64-encoded public-trust code-signing PFX.
- `WINDOWS_CERTIFICATE_PASSWORD`: PFX password.

Set repository variable `ARHUB_SIGNING_PROVIDER` to `pfx`.

### Azure Trusted Signing

Set repository variable `ARHUB_SIGNING_PROVIDER` to `azure`, then configure:

- Variables: `AZURE_TRUSTED_SIGNING_ENDPOINT`, `AZURE_TRUSTED_SIGNING_ACCOUNT`,
  `AZURE_TRUSTED_SIGNING_PROFILE`.
- Secrets: `ARHUB_PUBLISHER_NAME`, `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
  `AZURE_SUBSCRIPTION_ID`.

The Azure identity must have permission to sign with the selected certificate
profile. GitHub Actions uses OIDC; do not store an Azure client secret.

## Locked runtime

The complete runtime is described by `packaging/runtime-manifest.json`, exact
directory statistics and probe hashes in `packaging/runtime-lock.json`, and the
full Python package set in `packaging/python-requirements.lock.txt`.

The runtime builder is intentionally a dedicated self-hosted Windows runner with
the label `arhub-runtime`. The same host also carries the `arhub-release` label
because a full build needs more disk than a standard hosted runner provides.
The runner account must have PowerShell 5.1 or newer, Git, and GitHub CLI 2.x on
`PATH`, plus at least 35 GiB of free disk space. Keep the runner process available
after reboot before dispatching either release workflow.
Configure repository variable `ARHUB_RUNTIME_DIR` on that runner, then run the
**Runtime Bundle** workflow. It validates the runtime, creates sub-2-GB component
archives, attests them, and publishes the locked `runtime-v<version>` prerelease
used by the Windows release job. Runtime releases are never marked latest, so
they cannot be mistaken for an application update.

To regenerate locks after an intentional runtime change:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\export-runtime-lock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\package-runtime.ps1 -UpdateRepositoryManifest
```

Review every lock diff before committing it.

For a local lock check, point `ARHUB_RUNTIME_DIR` at the restored runtime before
running `npm run runtime:check`. Without that variable, the command checks the
runtime in the installed per-user ArHub directory.

## Formal release

1. Run `npm ci`, `npm test`, and `npm run audit:open-source`.
2. Update `package.json` to the release version and commit all lock changes.
3. Create and push the matching tag, for example `v1.0.9`.
4. The **Signed Windows Release** workflow downloads the locked runtime, checks
   every archive against the committed hashes, builds
   the installer, verifies signatures and timestamps, emits CycloneDX SBOMs and
   SHA-256 checksums, installs and launches the application in smoke-test mode,
   verifies the installed uninstaller signature, uninstalls it, creates
   build-provenance attestations, and publishes the GitHub Release.

Local signed builds use the same gate:

```powershell
$env:ARHUB_PUBLISHER_NAME = 'Exact certificate common name'
$env:CSC_LINK = 'C:\secure\arhub-code-signing.pfx'
$env:CSC_KEY_PASSWORD = '<password>'
npm run package:win
```

`npm run package:win:unsigned` exists only for local installer validation. Its
artifact name contains `-unsigned`, its updater is disabled because no publisher
is present in `app-update.yml`, and it must never be attached to a public Release.

Run the same installation gate locally with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke-test-installer.ps1 `
  -InstallerPath release\ArHub-Setup-1.0.9-x64-unsigned.exe -AllowUnsigned
```

## Automated maintenance

- Dependabot checks npm, pip and GitHub Actions every week.
- **Scheduled Maintenance** runs Node and Python vulnerability audits, regression
  tests and the open-source file audit. Both the backend requirements and the
  complete locked Python runtime are audited. It opens one deduplicated issue
  while a failure remains and closes it after recovery.
- The same workflow compares the locked Python, Node.js, Claude Code, npm,
  Corepack, Git, Pandoc and Draw.io versions with upstream releases and maintains
  a runtime update issue.
- **CodeQL** scans JavaScript/TypeScript and Python on pushes, pull requests and
  a weekly schedule.
- External GitHub Actions are pinned to immutable commit SHAs; Dependabot keeps
  those pins current.
- Runtime changes remain review-gated. The large runtime bundle is rebuilt only
  on the dedicated `arhub-runtime` Windows runner after lock changes are reviewed;
  the scheduled workflow only reports available updates.
