# Update Strategy

ArHub updates are being migrated in two stages so existing Full installations
cannot be accidentally replaced by a Lite installer.

## Stage 1: safe automation foundation

- Packaged clients validate the installer profile before downloading an update.
- Updates download in the background and install silently when the app exits
  normally. Active Agent work is never interrupted by a forced restart.
- Failed automatic downloads retry after 5 and 30 minutes.
- A successful `Quality` workflow automatically builds a versioned Lite beta
  candidate on the self-hosted release runner. Candidate Releases are marked as
  prereleases and therefore do not replace the stable GitHub Latest Release.
- Full remains a manually published, low-frequency profile during this stage.

The beta gate is intentional. ArHub v1.0.11 clients predate profile validation;
publishing a Lite-only stable Release would allow an existing Full installation
to consume that Lite installer.

## Stage 2: application/runtime separation

The application payload will be updated independently from the locked runtime.
After a migration release establishes that layout, both Lite and Full installs
can receive the same small application update while retaining their own runtime.
Stage 2 also enables stable automatic publishing, startup rollback, optional
runtime components, the maintainable frontend build, and visual regression
coverage.

Authenticode publisher verification remains disabled until a publicly trusted
certificate is available. SHA-512 manifest verification, GitHub asset digests,
build provenance, and profile validation remain mandatory for unsigned builds.
