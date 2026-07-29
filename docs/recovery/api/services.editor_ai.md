# `services.editor_ai` — recovered API surface

> 编辑器 AI 助手 — 双角色系统：LaTeX 编辑助手 + Python 代码大师

## Module-level names

- `LATEX_SYSTEM_PROMPT` (str)
- `MARKDOWN_SYSTEM_PROMPT` (str)
- `PYTHON_SYSTEM_PROMPT` (str)
- `REPLY_FORMAT` (str)
- `log` (Logger)
- `logging` (module)

## Functions

- `ai_edit(message: 'str', current_file: 'str', current_content: 'str', workspace_files: 'list[str]', compile_log: 'str' = '', extra_context: 'str' = '', history: 'list' = None, role: 'str' = 'latex', chat_summary: 'str' = '') -> 'dict'` — 调用 LLM 修改文件内容，根据用户选择的角色切换 prompt
- `call_llm(agent: 'str', prompt: 'str', timeout: 'int' = 300) -> 'str'` — 调用 LLM API，从 settings 读取配置。
