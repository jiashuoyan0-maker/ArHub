# `services.skill_crypto` — recovered API surface

> Utility module for skill file I/O operations.

## Module-level names

- `Optional` (_SpecialForm)
- `hashlib` (module)
- `json` (module)
- `os` (module)

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

- `clear_decrypt_key() -> 'None'` — 清除内存中的解密密钥。
- `decrypt_bytes(data: 'bytes', key: 'bytes') -> 'bytes'` — AES-256-GCM 解密。输入 nonce(12) + tag+ciphertext。
- `decrypt_dk_from_transport(encrypted_dk_hex: 'str', license_key: 'str') -> 'str'` — 客户端调用：用 license_key 解密服务端下发的 dk，返回 hex 字符串。
- `decrypt_file(src: 'Path', key: 'bytes') -> 'bytes'` — 解密 .enc 文件，返回明文 bytes。
- `decrypt_skill_file_to_memory(enc_path: 'Path', license_key: 'Optional[str]' = None) -> 'Optional[bytes]'` — 解密单个 .enc 文件到内存。密钥从内存缓存获取。
- `decrypt_skill_md(skills_dir: 'Path', skill_name: 'str', license_key: 'Optional[str]' = None) -> 'Optional[str]'` — 解密并读取指定 skill 的 SKILL.md 内容。
- `decrypt_skills_to_workspace(skills_dir: 'Path', workspace_utils: 'Path', sub_dir: 'str' = 'shared-scripts', license_key: 'Optional[str]' = None) -> 'bool'` — 将加密的 skills 子目录解密到工作区。
- `encrypt_bytes(plaintext: 'bytes', key: 'bytes') -> 'bytes'` — AES-256-GCM 加密。返回 nonce(12) + tag+ciphertext。
- `encrypt_dk_for_transport(master_key_hex: 'str', license_key: 'str') -> 'str'` — 服务端调用：用 license_key 加密 master_key_hex，返回 hex 字符串。
- `encrypt_file(src: 'Path', dst: 'Path', key: 'bytes') -> 'None'` — 加密单个文件，写入 .enc 文件。
- `encrypt_skills_dir(skills_dir: 'Path', output_dir: 'Path', master_key: 'str' = '') -> 'dict'` — 将 skills_dir 下所有文件加密到 output_dir。
- `get_decrypt_key() -> 'Optional[bytes]'` — 获取缓存的解密密钥。
- `is_encrypted_skills(skills_dir: 'Path') -> 'bool'` — 检查 skills 目录是否是加密的。
- `set_decrypt_key(dk_hex: 'str') -> 'None'` — 设置解密密钥（从服务端获取后调用）。
