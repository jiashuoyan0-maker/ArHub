# Path Policy

ArHub keeps installation files, build inputs, and per-user state separate.

| Area | Default | Override | Lifecycle |
|---|---|---|---|
| Installed application | `%LOCALAPPDATA%\Programs\ArHub` | Selected in the NSIS installer | Replaced by upgrades; removed by uninstall |
| Packaged runtime | `<install directory>\runtime` | None in a packaged build | Moves with the installed application |
| User data | `%APPDATA%\ArHub` | `ARHUB_DATA_DIR` for development and tests | Preserved across upgrades and uninstall |
| Source-build runtime | `<repository>\runtime` | `ARHUB_RUNTIME_DIR` or `-RuntimeDir` | Read-only build input |
| Workspaces | `<user data>\workspaces` | Inherited from `ARHUB_DATA_DIR` | Preserved across upgrades and uninstall |

## Invariants

- The packaged application derives its runtime from Electron's
  `process.resourcesPath`; it never assumes the default installation directory.
- Release tooling never discovers build inputs from an installed copy of ArHub.
- `ARHUB_RUNTIME_PROFILE=full|lite` changes only the packaged runtime filter;
  both profiles are built from the same explicitly selected, locked runtime.
- Changing the installation directory does not move or delete model settings,
  credentials, logs, databases, extensions, or workspaces.
- The installer remains per-user by default. Choosing a protected directory may
  require elevation, but it does not change the user-data location.
- Installer smoke tests use a non-default path containing spaces and verify that
  startup, runtime discovery, uninstall registration, cleanup, and user-data
  preservation all follow this policy.
