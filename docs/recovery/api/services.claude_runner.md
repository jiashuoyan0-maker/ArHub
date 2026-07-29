# `services.claude_runner` — recovered API surface

> Claude Code CLI 子进程管理

## Module-level names

- `Awaitable` (_SpecialGenericAlias)
- `CLAUDE_BIN` (str)
- `Callable` (_CallableType)
- `Dict` (_SpecialGenericAlias)
- `IS_DESKTOP` (bool)
- `List` (_SpecialGenericAlias)
- `Optional` (_SpecialForm)
- `REVIEWER_SCRIPT` (str)
- `RUNTIME_DRAWIO` (WindowsPath)
- `RUNTIME_PYTHON` (WindowsPath)
- `RUNTIME_TEXLIVE` (WindowsPath)
- `SCHOLAR_SCRIPT` (str)
- `SKILLS_DIR` (WindowsPath)
- `TOOLS_DIR` (WindowsPath)
- `Union` (_SpecialForm)
- `asyncio` (module)
- `claude_runner` (ClaudeRunner)
- `hashlib` (module)
- `json` (module)
- `log` (Logger)
- `logging` (module)
- `os` (module)
- `platform` (module)
- `re` (module)
- `shutil` (module)

## class `ClaudeRunner(object)`

- `__init__(self)` — 
- `cancel(self, workflow_id_prefix: 'str') -> 'bool'` — 取消匹配前缀的所有进程。
- `is_running(self, workflow_id: 'str') -> 'bool'` — 
- `run_skill(self, skill_name: 'str', arguments: 'str', cwd: 'Union[str, Path]', workflow_id: 'str', on_output: 'Optional[Callable[[str], Awaitable[None]]]' = None, extra_params: 'Optional[Dict]' = None, workspace_files: 'Optional[List[str]]' = None, context_summary: 'Optional[str]' = None, inactivity_timeout: 'int' = 2400, resume_session_id: 'Optional[str]' = None) -> 'Dict'` — 通过 claude -p 执行一个 skill，流式读取输出。

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
