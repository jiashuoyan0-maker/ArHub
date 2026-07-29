# `services.llm_client` — recovered API surface

> 直接调用 OpenAI 兼容 LLM API — 使用原生 http.client（参考用户代码）

## Module-level names

- `AGENT_KEYS` (dict)
- `Dict` (_SpecialGenericAlias)
- `ENV_MAPPING` (dict)
- `http` (module)
- `json` (module)
- `log` (Logger)
- `logging` (module)
- `socket` (module)
- `ssl` (module)

## Functions

- `call_llm(agent: 'str', prompt: 'str', timeout: 'int' = 300) -> 'str'` — 调用 LLM API，从 settings 读取配置。
- `describe_image(image_path: 'str', context: 'str' = '') -> 'str'` — 用 vision LLM 描述图片内容。用于赛题图片识别。
- `get_all_settings() -> 'Dict[str, str]'` — 
- `get_env_for_subprocess() -> 'Dict[str, str]'` — 从 settings 构建子进程环境变量
- `test_connection(agent: 'str') -> 'Dict'` — 测试 API 连通性
- `urlparse(url, scheme='', allow_fragments=True)` — 
