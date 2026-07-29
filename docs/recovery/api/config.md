# `config` — recovered API surface

> ArHub 路径配置 — 同时支持开发模式和桌面打包模式。

## Module-level names

- `API_PORT` (int)
- `CLAUDE_BIN` (str)
- `DB_PATH` (WindowsPath)
- `FRONTEND_DIST` (WindowsPath)
- `IS_DESKTOP` (bool)
- `PANDOC_BIN` (str)
- `PROJECT_ROOT` (WindowsPath)
- `RUNTIME_DRAWIO` (WindowsPath)
- `RUNTIME_NODE` (WindowsPath)
- `RUNTIME_PYTHON` (WindowsPath)
- `RUNTIME_TEXLIVE` (WindowsPath)
- `SKILLS_DIR` (WindowsPath)
- `TEMPLATES_DIR` (WindowsPath)
- `TOOLS_DIR` (WindowsPath)
- `WORKSPACES_DIR` (WindowsPath)
- `annotations` (_Feature)
- `os` (module)
- `platform` (module)
- `sys` (module)

## class `Path(PurePath)`

- `__init__(self, /, *args, **kwargs)` — Initialize self.  See help(type(self)) for accurate signature.
- `absolute(self)` — 
- `as_posix(self)` — 
- `as_uri(self)` — 
- `chmod(self, mode, *, follow_symlinks=True)` — 
- `cwd()` — 
- `exists(self)` — 
- `expanduser(self)` — 
- `glob(self, pattern)` — 
- `group(self)` — 
- `hardlink_to(self, target)` — 
- `home()` — 
- `is_absolute(self)` — 
- `is_block_device(self)` — 
- `is_char_device(self)` — 
- `is_dir(self)` — 
- `is_fifo(self)` — 
- `is_file(self)` — 
- `is_mount(self)` — 
- `is_relative_to(self, *other)` — 
- `is_reserved(self)` — 
- `is_socket(self)` — 
- `is_symlink(self)` — 
- `iterdir(self)` — 
- `joinpath(self, *args)` — 
- `lchmod(self, mode)` — 
- `link_to(self, target)` — 
- `lstat(self)` — 
- `match(self, path_pattern)` — 
- `mkdir(self, mode=511, parents=False, exist_ok=False)` — 
- `open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None)` — 
- `owner(self)` — 
- `read_bytes(self)` — 
- `read_text(self, encoding=None, errors=None)` — 
- `readlink(self)` — 
- `relative_to(self, *other)` — 
- `rename(self, target)` — 
- `replace(self, target)` — 
- `resolve(self, strict=False)` — 
- `rglob(self, pattern)` — 
- `rmdir(self)` — 
- `samefile(self, other_path)` — 
- `stat(self, *, follow_symlinks=True)` — 
- `symlink_to(self, target, target_is_directory=False)` — 
- `touch(self, mode=438, exist_ok=True)` — 
- `unlink(self, missing_ok=False)` — 
- `with_name(self, name)` — 
- `with_stem(self, stem)` — 
- `with_suffix(self, suffix)` — 
- `write_bytes(self, data)` — 
- `write_text(self, data, encoding=None, errors=None, newline=None)` — 
