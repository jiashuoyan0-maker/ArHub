# `services.state_store` — recovered API surface

> SQLite 状态持久化

## Module-level names

- `DB_PATH` (WindowsPath)
- `Dict` (_SpecialGenericAlias)
- `List` (_SpecialGenericAlias)
- `Optional` (_SpecialForm)
- `aiosqlite` (module)
- `asyncio` (module)
- `json` (module)
- `log` (Logger)
- `logging` (module)

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

## class `datetime(date)`

datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])

The year, month and day arguments are required. tzinfo may be None, or an
instance of a tzinfo subclass. The remaining arguments may be ints.

- `__init__(self, /, *args, **kwargs)` — Initialize self.  See help(type(self)) for accurate signature.
- `astimezone()` — tz -> convert to local time in new timezone tz
- `combine()` — date, time -> datetime with same date and time fields
- `ctime()` — Return ctime() style string.
- `date()` — Return date object with same year, month and day.
- `dst()` — Return self.tzinfo.dst(self).
- `fromisocalendar()` — int, int, int -> Construct a date from the ISO year, week number and weekday.
- `fromisoformat()` — string -> datetime from a string in most ISO 8601 formats
- `fromordinal()` — int -> date corresponding to a proleptic Gregorian ordinal.
- `fromtimestamp()` — timestamp[, tz] -> tz's local time from POSIX timestamp.
- `isocalendar()` — Return a named tuple containing ISO year, week number, and weekday.
- `isoformat()` — [sep] -> string in ISO 8601 format, YYYY-MM-DDT[HH[:MM[:SS[.mmm[uuu]]]]][+HH:MM].
- `isoweekday()` — Return the day of the week represented by the date.
- `now(tz=None)` — Returns new datetime object representing current time local to tz.
- `replace()` — Return datetime with new specified fields.
- `strftime()` — format -> strftime() style string.
- `strptime()` — string, format -> new datetime parsed from a string (like time.strptime()).
- `time()` — Return time object with same time but with tzinfo=None.
- `timestamp()` — Return POSIX timestamp as float.
- `timetuple()` — Return time tuple, compatible with time.localtime().
- `timetz()` — Return time object with same time and tzinfo.
- `today()` — Current date or datetime:  same as self.__class__.fromtimestamp(time.time()).
- `toordinal()` — Return proleptic Gregorian ordinal.  January 1 of year 1 is day 1.
- `tzname()` — Return self.tzinfo.tzname(self).
- `utcfromtimestamp()` — Construct a naive UTC datetime from a POSIX timestamp.
- `utcnow()` — Return a new datetime representing UTC day and time.
- `utcoffset()` — Return self.tzinfo.utcoffset(self).
- `utctimetuple()` — Return UTC time tuple, compatible with time.localtime().
- `weekday()` — Return the day of the week represented by the date.

## Functions

- `create_workflow(db: 'aiosqlite.Connection', wf: 'dict') -> 'None'` — 
- `export_workflow_data(wf_id: 'str') -> 'Optional[Dict]'` — 导出工作流的完整 DB 数据（workflow + steps + logs），返回 dict 或 None。
- `get_all_settings() -> 'Dict[str, str]'` — 
- `get_db() -> 'aiosqlite.Connection'` — 
- `get_setting(key: 'str', default: 'str' = '') -> 'str'` — 
- `get_workflow(db: 'aiosqlite.Connection', wf_id: 'str') -> 'Optional[Dict]'` — 
- `get_workflows_to_resume() -> 'list[str]'` — 返回需要恢复的工作流 ID 列表，调用后清空。
- `import_workflow_data(data: 'Dict', new_id: 'str', workspace_dir: 'str') -> 'None'` — 从导出的 manifest 数据导入工作流到 DB。
- `init_db()` — 
- `list_workflows(db: 'aiosqlite.Connection') -> 'list[dict]'` — 
- `save_settings(data: 'Dict[str, str]') -> 'None'` — 
- `update_workflow(db: 'aiosqlite.Connection', wf_id: 'str', **fields) -> 'None'` — 更新工作流字段，带重试逻辑应对并发锁竞争。
