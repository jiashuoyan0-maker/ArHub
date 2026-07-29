# `services.extract_worker` — recovered API surface

> 异步文本提取 worker.

## Module-level names

- `Callable` (_CallableType)
- `ExtractFn` (_CallableGenericAlias)
- `Optional` (_SpecialForm)
- `annotations` (_Feature)
- `asyncio` (module)
- `json` (module)
- `log` (Logger)
- `logging` (module)
- `time` (module)

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

## Functions

- `get_status(dir_: 'Path') -> 'dict'` — 读取目录的提取状态. 给 API endpoint 用.
- `mark_pending(dir_: 'Path', name: 'str') -> 'None'` — 上传完成时调用, 标记为待提取.
- `schedule_extract(upload_dir: 'Path', name: 'str', extract_fn: 'ExtractFn') -> 'None'` — 提交一个文件到提取队列. 立即返回, 任务在后台跑.
