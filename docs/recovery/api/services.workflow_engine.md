# `services.workflow_engine` — recovered API surface

> 工作流 DAG 编排引擎 — 逐步调用子 Skill，支持暂停/恢复 [v3-drawio-slim]

## Module-level names

- `Dict` (_SpecialGenericAlias)
- `List` (_SpecialGenericAlias)
- `Optional` (_SpecialForm)
- `SKILLS_DIR` (WindowsPath)
- `TEMPLATES` (dict)
- `TOOLS_DIR` (WindowsPath)
- `Tuple` (_TupleType)
- `WORKSPACES_DIR` (WindowsPath)
- `asyncio` (module)
- `claude_runner` (ClaudeRunner)
- `json` (module)
- `log` (Logger)
- `logging` (module)
- `uuid` (module)

## class `Any(object)`

- `__init__(self, /, *args, **kwargs)` — Initialize self.  See help(type(self)) for accurate signature.

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

## class `StepDef(object)`

StepDef(skill_name: 'str', display_name: 'str', output_files: 'List[str]' = <factory>, primary_output: 'Optional[str]' = None, has_checkpoint: 'bool' = False, checkpoint_type: 'Optional[str]' = None)

- `__init__(self, skill_name: 'str', display_name: 'str', output_files: 'List[str]' = <factory>, primary_output: 'Optional[str]' = None, has_checkpoint: 'bool' = False, checkpoint_type: 'Optional[str]' = None) -> None` — Initialize self.  See help(type(self)) for accurate signature.

## class `StepStatus(str, Enum)`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

- `__init__(self, *args, **kwds)` — Initialize self.  See help(type(self)) for accurate signature.
- `capitalize(self, /)` — Return a capitalized version of the string.
- `casefold(self, /)` — Return a version of the string suitable for caseless comparisons.
- `center(self, width, fillchar=' ', /)` — Return a centered string of length width.
- `count()` — S.count(sub[, start[, end]]) -> int
- `encode(self, /, encoding='utf-8', errors='strict')` — Encode the string using the codec registered for encoding.
- `endswith()` — S.endswith(suffix[, start[, end]]) -> bool
- `expandtabs(self, /, tabsize=8)` — Return a copy where all tab characters are expanded using spaces.
- `find()` — S.find(sub[, start[, end]]) -> int
- `format()` — S.format(*args, **kwargs) -> str
- `format_map()` — S.format_map(mapping) -> str
- `index()` — S.index(sub[, start[, end]]) -> int
- `isalnum(self, /)` — Return True if the string is an alpha-numeric string, False otherwise.
- `isalpha(self, /)` — Return True if the string is an alphabetic string, False otherwise.
- `isascii(self, /)` — Return True if all characters in the string are ASCII, False otherwise.
- `isdecimal(self, /)` — Return True if the string is a decimal string, False otherwise.
- `isdigit(self, /)` — Return True if the string is a digit string, False otherwise.
- `isidentifier(self, /)` — Return True if the string is a valid Python identifier, False otherwise.
- `islower(self, /)` — Return True if the string is a lowercase string, False otherwise.
- `isnumeric(self, /)` — Return True if the string is a numeric string, False otherwise.
- `isprintable(self, /)` — Return True if the string is printable, False otherwise.
- `isspace(self, /)` — Return True if the string is a whitespace string, False otherwise.
- `istitle(self, /)` — Return True if the string is a title-cased string, False otherwise.
- `isupper(self, /)` — Return True if the string is an uppercase string, False otherwise.
- `join(self, iterable, /)` — Concatenate any number of strings.
- `ljust(self, width, fillchar=' ', /)` — Return a left-justified string of length width.
- `lower(self, /)` — Return a copy of the string converted to lowercase.
- `lstrip(self, chars=None, /)` — Return a copy of the string with leading whitespace removed.
- `maketrans(x, y=<unrepresentable>, z=<unrepresentable>, /)` — Return a translation table usable for str.translate().
- `partition(self, sep, /)` — Partition the string into three parts using the given separator.
- `removeprefix(self, prefix, /)` — Return a str with the given prefix string removed if present.
- `removesuffix(self, suffix, /)` — Return a str with the given suffix string removed if present.
- `replace(self, old, new, count=-1, /)` — Return a copy with all occurrences of substring old replaced by new.
- `rfind()` — S.rfind(sub[, start[, end]]) -> int
- `rindex()` — S.rindex(sub[, start[, end]]) -> int
- `rjust(self, width, fillchar=' ', /)` — Return a right-justified string of length width.
- `rpartition(self, sep, /)` — Partition the string into three parts using the given separator.
- `rsplit(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `rstrip(self, chars=None, /)` — Return a copy of the string with trailing whitespace removed.
- `split(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `splitlines(self, /, keepends=False)` — Return a list of the lines in the string, breaking at line boundaries.
- `startswith()` — S.startswith(prefix[, start[, end]]) -> bool
- `strip(self, chars=None, /)` — Return a copy of the string with leading and trailing whitespace removed.
- `swapcase(self, /)` — Convert uppercase characters to lowercase and lowercase characters to uppercase.
- `title(self, /)` — Return a version of the string where each word is titlecased.
- `translate(self, table, /)` — Replace each character in the string using the given translation table.
- `upper(self, /)` — Return a copy of the string converted to uppercase.
- `zfill(self, width, /)` — Pad a numeric string with zeros on the left, to fill a field of the given width.

## class `TemplateDef(object)`

TemplateDef(pipeline_skill: 'str', display_name: 'str', sub_steps: 'List[StepDef]')

- `__init__(self, pipeline_skill: 'str', display_name: 'str', sub_steps: 'List[StepDef]') -> None` — Initialize self.  See help(type(self)) for accurate signature.

## class `TemplateType(str, Enum)`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

- `__init__(self, *args, **kwds)` — Initialize self.  See help(type(self)) for accurate signature.
- `capitalize(self, /)` — Return a capitalized version of the string.
- `casefold(self, /)` — Return a version of the string suitable for caseless comparisons.
- `center(self, width, fillchar=' ', /)` — Return a centered string of length width.
- `count()` — S.count(sub[, start[, end]]) -> int
- `encode(self, /, encoding='utf-8', errors='strict')` — Encode the string using the codec registered for encoding.
- `endswith()` — S.endswith(suffix[, start[, end]]) -> bool
- `expandtabs(self, /, tabsize=8)` — Return a copy where all tab characters are expanded using spaces.
- `find()` — S.find(sub[, start[, end]]) -> int
- `format()` — S.format(*args, **kwargs) -> str
- `format_map()` — S.format_map(mapping) -> str
- `index()` — S.index(sub[, start[, end]]) -> int
- `isalnum(self, /)` — Return True if the string is an alpha-numeric string, False otherwise.
- `isalpha(self, /)` — Return True if the string is an alphabetic string, False otherwise.
- `isascii(self, /)` — Return True if all characters in the string are ASCII, False otherwise.
- `isdecimal(self, /)` — Return True if the string is a decimal string, False otherwise.
- `isdigit(self, /)` — Return True if the string is a digit string, False otherwise.
- `isidentifier(self, /)` — Return True if the string is a valid Python identifier, False otherwise.
- `islower(self, /)` — Return True if the string is a lowercase string, False otherwise.
- `isnumeric(self, /)` — Return True if the string is a numeric string, False otherwise.
- `isprintable(self, /)` — Return True if the string is printable, False otherwise.
- `isspace(self, /)` — Return True if the string is a whitespace string, False otherwise.
- `istitle(self, /)` — Return True if the string is a title-cased string, False otherwise.
- `isupper(self, /)` — Return True if the string is an uppercase string, False otherwise.
- `join(self, iterable, /)` — Concatenate any number of strings.
- `ljust(self, width, fillchar=' ', /)` — Return a left-justified string of length width.
- `lower(self, /)` — Return a copy of the string converted to lowercase.
- `lstrip(self, chars=None, /)` — Return a copy of the string with leading whitespace removed.
- `maketrans(x, y=<unrepresentable>, z=<unrepresentable>, /)` — Return a translation table usable for str.translate().
- `partition(self, sep, /)` — Partition the string into three parts using the given separator.
- `removeprefix(self, prefix, /)` — Return a str with the given prefix string removed if present.
- `removesuffix(self, suffix, /)` — Return a str with the given suffix string removed if present.
- `replace(self, old, new, count=-1, /)` — Return a copy with all occurrences of substring old replaced by new.
- `rfind()` — S.rfind(sub[, start[, end]]) -> int
- `rindex()` — S.rindex(sub[, start[, end]]) -> int
- `rjust(self, width, fillchar=' ', /)` — Return a right-justified string of length width.
- `rpartition(self, sep, /)` — Partition the string into three parts using the given separator.
- `rsplit(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `rstrip(self, chars=None, /)` — Return a copy of the string with trailing whitespace removed.
- `split(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `splitlines(self, /, keepends=False)` — Return a list of the lines in the string, breaking at line boundaries.
- `startswith()` — S.startswith(prefix[, start[, end]]) -> bool
- `strip(self, chars=None, /)` — Return a copy of the string with leading and trailing whitespace removed.
- `swapcase(self, /)` — Convert uppercase characters to lowercase and lowercase characters to uppercase.
- `title(self, /)` — Return a version of the string where each word is titlecased.
- `translate(self, table, /)` — Replace each character in the string using the given translation table.
- `upper(self, /)` — Return a copy of the string converted to uppercase.
- `zfill(self, width, /)` — Pad a numeric string with zeros on the left, to fill a field of the given width.

## class `WorkflowStatus(str, Enum)`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

- `__init__(self, *args, **kwds)` — Initialize self.  See help(type(self)) for accurate signature.
- `capitalize(self, /)` — Return a capitalized version of the string.
- `casefold(self, /)` — Return a version of the string suitable for caseless comparisons.
- `center(self, width, fillchar=' ', /)` — Return a centered string of length width.
- `count()` — S.count(sub[, start[, end]]) -> int
- `encode(self, /, encoding='utf-8', errors='strict')` — Encode the string using the codec registered for encoding.
- `endswith()` — S.endswith(suffix[, start[, end]]) -> bool
- `expandtabs(self, /, tabsize=8)` — Return a copy where all tab characters are expanded using spaces.
- `find()` — S.find(sub[, start[, end]]) -> int
- `format()` — S.format(*args, **kwargs) -> str
- `format_map()` — S.format_map(mapping) -> str
- `index()` — S.index(sub[, start[, end]]) -> int
- `isalnum(self, /)` — Return True if the string is an alpha-numeric string, False otherwise.
- `isalpha(self, /)` — Return True if the string is an alphabetic string, False otherwise.
- `isascii(self, /)` — Return True if all characters in the string are ASCII, False otherwise.
- `isdecimal(self, /)` — Return True if the string is a decimal string, False otherwise.
- `isdigit(self, /)` — Return True if the string is a digit string, False otherwise.
- `isidentifier(self, /)` — Return True if the string is a valid Python identifier, False otherwise.
- `islower(self, /)` — Return True if the string is a lowercase string, False otherwise.
- `isnumeric(self, /)` — Return True if the string is a numeric string, False otherwise.
- `isprintable(self, /)` — Return True if the string is printable, False otherwise.
- `isspace(self, /)` — Return True if the string is a whitespace string, False otherwise.
- `istitle(self, /)` — Return True if the string is a title-cased string, False otherwise.
- `isupper(self, /)` — Return True if the string is an uppercase string, False otherwise.
- `join(self, iterable, /)` — Concatenate any number of strings.
- `ljust(self, width, fillchar=' ', /)` — Return a left-justified string of length width.
- `lower(self, /)` — Return a copy of the string converted to lowercase.
- `lstrip(self, chars=None, /)` — Return a copy of the string with leading whitespace removed.
- `maketrans(x, y=<unrepresentable>, z=<unrepresentable>, /)` — Return a translation table usable for str.translate().
- `partition(self, sep, /)` — Partition the string into three parts using the given separator.
- `removeprefix(self, prefix, /)` — Return a str with the given prefix string removed if present.
- `removesuffix(self, suffix, /)` — Return a str with the given suffix string removed if present.
- `replace(self, old, new, count=-1, /)` — Return a copy with all occurrences of substring old replaced by new.
- `rfind()` — S.rfind(sub[, start[, end]]) -> int
- `rindex()` — S.rindex(sub[, start[, end]]) -> int
- `rjust(self, width, fillchar=' ', /)` — Return a right-justified string of length width.
- `rpartition(self, sep, /)` — Partition the string into three parts using the given separator.
- `rsplit(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `rstrip(self, chars=None, /)` — Return a copy of the string with trailing whitespace removed.
- `split(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `splitlines(self, /, keepends=False)` — Return a list of the lines in the string, breaking at line boundaries.
- `startswith()` — S.startswith(prefix[, start[, end]]) -> bool
- `strip(self, chars=None, /)` — Return a copy of the string with leading and trailing whitespace removed.
- `swapcase(self, /)` — Convert uppercase characters to lowercase and lowercase characters to uppercase.
- `title(self, /)` — Return a version of the string where each word is titlecased.
- `translate(self, table, /)` — Replace each character in the string using the given translation table.
- `upper(self, /)` — Return a copy of the string converted to uppercase.
- `zfill(self, width, /)` — Pad a numeric string with zeros on the left, to fill a field of the given width.

## Functions

- `create_new_workflow(template: 'str', title: 'str', params: 'dict', enable_checkpoints: 'bool' = False) -> 'str'` — 
- `create_workflow(db: 'aiosqlite.Connection', wf: 'dict') -> 'None'` — 
- `dataclass(cls=None, /, *, init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False, match_args=True, kw_only=False, slots=False, weakref_slot=False)` — 
- `field(*, default=<dataclasses._MISSING_TYPE object at 0x000001A32AC6E490>, default_factory=<dataclasses._MISSING_TYPE object at 0x000001A32AC6E490>, init=True, repr=True, hash=None, compare=True, metadata=None, kw_only=<dataclasses._MISSING_TYPE object at 0x000001A32AC6E490>)` — 
- `get_db() -> 'aiosqlite.Connection'` — 
- `load_prompt(name: 'str', **vars: 'Any') -> 'str'` — 加载并渲染一个 prompt 模板。
- `resolve_checkpoint(workflow_id: 'str', response: 'dict')` — 
- `run_single_step(workflow_id: 'str', skill_name: 'str')` — 单独执行工作流中的单个步骤。
- `run_workflow(workflow_id: 'str')` — 逐步执行子步骤。支持从暂停处恢复（跳过已完成步骤）。
- `set_broadcast(fn)` — 
- `update_workflow(db: 'aiosqlite.Connection', wf_id: 'str', **fields) -> 'None'` — 更新工作流字段，带重试逻辑应对并发锁竞争。
- `wait_checkpoint(workflow_id: 'str', timeout: 'int' = 600) -> 'dict'` — 等待用户确认检查点，超时则自动确认继续。
