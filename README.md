# ArHub

[![Latest Release](https://img.shields.io/github/v/release/jiashuoyan0-maker/ArHub?label=Release)](https://github.com/jiashuoyan0-maker/ArHub/releases/latest)
[![Quality](https://github.com/jiashuoyan0-maker/ArHub/actions/workflows/quality.yml/badge.svg)](https://github.com/jiashuoyan0-maker/ArHub/actions/workflows/quality.yml)
[![CodeQL](https://github.com/jiashuoyan0-maker/ArHub/actions/workflows/codeql.yml/badge.svg)](https://github.com/jiashuoyan0-maker/ArHub/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<p align="center">
  <img src="assets/icon-1024.png" width="112" alt="ArHub icon">
</p>

<p align="center">
  <strong>把 Agent、文件、编辑器和工作流放回同一个任务现场。</strong><br>
  <strong>Bring agents, files, editors, and workflows into one focused workspace.</strong>
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> · <a href="#english">English</a> ·
  <a href="https://github.com/jiashuoyan0-maker/ArHub/releases/latest">Download</a>
</p>

![ArHub file tree, agent chat, and editor workspace](assets/screenshots/04-files-editor-agent.png)

## 简体中文

ArHub（AI Research Hub）是一个面向科研写作、数据分析和工程任务的桌面 Agent
工作台，基于 Electron、FastAPI、OpenAI-compatible 模型接口和可扩展 Skill
工作流构建。

ArHub 不把 Agent 限制在孤立的聊天框里。日常操作以对话为中心；当任务涉及文件、
代码或其他产物时，文件树、编辑器和预览会在当前工作区按需展开。执行步骤、检查点、
日志和产物会随任务持久化，方便继续运行、回看和审阅。

> [!NOTE]
> 本仓库由已安装应用的构建产物重建。后端、Agent、工作流、编辑器、状态层和文档
> 导出链路已经重写为可审查源码并可从源码运行；前端保留可运行的 `dist/` 产物与
> 恢复后的 `frontend-src/index.js`。原始 Vite 模块图仍未恢复；Windows 打包与
> 发布链已经使用可审查配置重新建立。

### 下载与安装

[前往 GitHub Releases 下载最新 Windows 安装包](https://github.com/jiashuoyan0-maker/ArHub/releases/latest)。

自 `v1.0.12` 起，Windows 稳定版只发布并推荐约 326 MiB 的 **Lite** 安装包。
Lite 保留桌面端、开放模型 Agent、基础文档处理和本机 Claude Code 接入；TeX、Draw.io、
Pandoc、Git、Node/Claude 与大型机器学习库不再随安装包内置。设置与工作区继续保存在
`%APPDATA%\ArHub`，覆盖更新不会清除用户数据。

安装器使用引导式安装：可以保留默认目录，也可以选择其他磁盘或目录。程序和
内置运行时随所选安装目录移动；模型设置、凭证、日志和工作区仍保存在 `%APPDATA%\ArHub`，升级
或卸载程序不会删除这些用户数据。完整路径规则见 [docs/PATHS.md](docs/PATHS.md)。

> [!IMPORTANT]
> ArHub 是个人维护的开源项目，Windows 安装器目前没有 Authenticode 代码签名。
> SmartScreen 可能显示“Windows 已保护你的电脑”或“未知发布者”。请只从本仓库的
> GitHub Releases 下载，并先核对 SHA-256；确认一致后，选择“更多信息” ->
> “仍要运行”。不要关闭 Microsoft Defender、SmartScreen 或其他系统级安全防护，
> 也不要从网盘或第三方镜像下载安装包。

```powershell
Get-FileHash .\ArHub-Setup-1.0.12-lite-x64.exe -Algorithm SHA256
```

将输出与同一 Release 中的 `SHA256SUMS.txt` 对应条目逐字核对。正式发布还包含
SHA-512 自动更新校验、CycloneDX SBOM、安装烟测报告和 GitHub 构建来源证明。

### 界面预览

#### Agent 与文档并排工作

Agent 对话是主工作区。打开文档后，Markdown/LaTeX 编辑器会在侧边展开，当前
文件会自动进入 Agent 上下文，不需要在聊天窗口、文件管理器和编辑器之间来回切换。
输入栏可以直接切换开放模型或本机 Claude Code、调整思考强度、添加附件，并在
Agent 运行时将发送操作切换为终止操作。

![ArHub Agent and Markdown editor](assets/screenshots/03-editor-agent-split.png)

#### 从单步任务到完整科研流水线

新建任务时可以选择 Idea 发现、实验桥接、自动审稿循环或完整流水线。模板负责定义
步骤与角色，参数仍由用户在启动前确认。

![ArHub research workflow templates](assets/screenshots/01-workflow-templates.png)

完整流水线可以继续设置输出格式、论文语言、论文类型和后续执行选项。运行状态、
检查点和产物按任务持久化，中断后可以从已有状态继续。

![ArHub full pipeline configuration](assets/screenshots/02-full-pipeline-config.png)

#### 每个 Agent 独立选择模型

执行者、审稿者和编辑器助手可以分别配置 Base URL、API Key 与 Model ID，适合用
不同模型承担执行、批判和写作任务。运行时、Provider 与思考强度也可以独立选择。
下图仅填写公开的官方 API 地址和演示模型名，所有 API Key 均为空。

![ArHub multi-agent model settings](assets/screenshots/05-model-settings-light.png)

#### 面向更多工具的开放扩展层

扩展中心通过 Manifest 注册 Agent Profile、提示命令与工具入口。内置的 Diagram Studio
和 Web Studio 可以把流程图、网页项目和研究写作放进同一个工作区；第三方 Manifest
默认只作为声明式数据加载，不会直接执行扩展代码。

![ArHub extension center](assets/screenshots/06-extension-center.png)

### 典型工作方式

1. 新建任务并选择工作流模板，或者从一个轻量 Agent 对话开始。
2. 为执行者、审稿者和编辑器助手选择 Provider、模型与思考强度，或切换到本机 Claude Code。
3. Agent 调用 Skill 执行检索、分析、代码、绘图或文档生成，并把结果写入任务工作区。
4. 在对话旁打开产物，检查文件差异，再决定应用、丢弃或撤销修改。
5. 在检查点暂停、恢复或重跑单个步骤，不必从头复制整段提示词。

### 主要能力

- 为执行者、审稿者和编辑器分别配置模型与 API。
- 运行带检查点、产物管理和断点恢复的多步骤 Skill 工作流。
- 在 Agent 对话旁动态展开文件树、编辑器、预览和上下文。
- 审阅 Agent 文件差异，支持应用、丢弃和撤销。
- 导出 Markdown 为 DOCX，并预览 PDF、DOCX、Markdown 和图片。
- 通过声明式 manifest 扩展 Agent profile 与命令入口。

### 模型配置

三个 Agent 均接受 OpenAI Chat Completions 兼容地址，包括：

- 服务根地址，例如 `https://api.deepseek.com`
- 带版本的兼容地址，例如 `https://open.bigmodel.cn/api/paas/v4`
- 完整的 `.../chat/completions` 地址

DeepSeek、GLM 和其他 OpenAI-compatible 服务共用同一连接层。模型 ID 必须填写为
账号实际开放的 ID，例如 `deepseek-chat`、服务商提供的 GLM 模型 ID 或 `gpt-4o`。
连接层遵循 `HTTP_PROXY`、`HTTPS_PROXY` 和 `NO_PROXY`。

内置 Agent 直接调用设置页中配置的模型接口，不依赖 Claude CLI。`ClaudeRunner`
仅保留为兼容类名，Agent 本身没有被替换。不同服务商对工具调用、视觉输入、上下文
长度和 token 参数的支持不同，连接测试通过不代表所有工作流能力完全一致。

API Key 只应保存在本机设置中。不要把 Key 写入仓库、截图、Issue 或日志。任何曾在
聊天或其他外部位置暴露的凭证都应在服务商控制台吊销并重新生成。

### 当前状态

| 组成部分 | 状态 | 说明 |
|---|---|---|
| Electron 主进程 | 可审查源码 | `main.js`、`preload.js`、`updater.js` |
| FastAPI 后端 | 可运行源码 | 70 条应用路由，支持隔离数据目录和工作区边界 |
| Agent 与工作流 | 可运行源码 | provider-neutral 工具循环、检查点、暂停恢复和持久状态 |
| 编辑器 | 可运行源码 | Markdown/LaTeX、文件树、Agent diff/apply/undo、图片与脚本工具 |
| DOCX 与提取 | 可运行源码 | Node 高保真引擎、python-docx fallback、PDF/DOCX 文本提取 |
| 前端 | 恢复产物 | Codex 式动态工作台、亮暗主题；尚无可复现的模块化前端构建 |
| Skills 与扩展 | 明文可审查 | Skill、模板和声明式 profile 不需要激活或解密 |
| Windows 安装包 | Lite 稳定版 | Lite runtime、NSIS、SBOM、校验和、自定义安装目录与 GitHub 发布工作流；官方产物当前未签名 |

### 从源码运行

建议使用 Windows、Python 3.11 和 Node.js 20+。FastAPI 会同时托管 `dist/` 前端，
无需单独启动前端开发服务器。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

$env:ARHUB_DATA_DIR = "$PWD\.arhub-data"
$env:ARHUB_API_PORT = "18088"
.\.venv\Scripts\python.exe -X utf8 -m uvicorn backend.main:app --host 127.0.0.1 --port 18088
```

启动后访问 [http://127.0.0.1:18088](http://127.0.0.1:18088)。DOCX 的 Python
fallback 随 `backend/requirements.txt` 安装。需要公式与复杂排版能力时，再安装
可选 Node 引擎依赖：

```powershell
npm --prefix tools\docx-cn-engine ci
```

### 开发与验证

```powershell
npm run check:js
npm run check:python
npm test
npm run audit:open-source
git diff --check
```

当前回归集包含 38 个 Python 测试和 26 个 Node 测试，覆盖模型 URL、LLM 请求、
Agent 工具循环、工作流状态、编辑器安全边界、diff/apply/undo、DOCX 导出和提取
队列。Windows 发布工作流还会完成安装、后端启动、前端加载、卸载和未签名状态检查。

本地构建未签名 Windows 安装器：

```powershell
npm ci
$env:ARHUB_RUNTIME_DIR = 'C:\path\to\verified\runtime'
npm run runtime:check
npm run package:win:unsigned
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke-test-installer.ps1 `
  -InstallerPath release\ArHub-Setup-1.0.11-lite-x64.exe -RequireUnsigned
```

### 数据与扩展

默认数据目录为 `%APPDATA%\ArHub`。源码开发和测试建议设置 `ARHUB_DATA_DIR` 使用
独立目录。数据库、日志、工作区、模型凭证和用户扩展均不进入公开仓库。

声明式扩展注册表只读取 JSON manifest，不导入或执行第三方代码。未来若开放可执行
扩展，需要先建立权限声明、隔离和撤销机制。

### 仓库结构

| 路径 | 内容 |
|---|---|
| `backend/` | FastAPI 路由、状态、Agent、工作流和导出服务 |
| `dist/` | 当前运行使用的前端产物 |
| `frontend-src/` | 从 bundle 恢复的可读 JSX 源码 |
| `skills/` | 科研写作、分析、绘图和工作流 Skills |
| `extensions/` | 声明式 Agent profile 与扩展 manifest |
| `templates/`、`tools/` | 模板、DOCX 引擎与辅助工具 |
| `tests/` | 后端和核心行为回归测试 |
| `docs/recovery/` | 历史恢复证据与旧 API 表面，不代表当前实现状态 |

### 已知限制

1. 原始前端模块和 Vite 配置未恢复，修改 UI 时必须同步
   `frontend-src/index.js` 与 `dist/`。
2. 安装包可以从已提交产物和锁定 runtime 重建，但前端尚不能从模块化源码独立重建。
3. 三个旧字节码 DOCX helper 的原始源码无法恢复，但已由新的 Node/Python 实现替代。
4. provider-neutral 不等于 provider-identical；模型能力差异仍需按服务商验证。
5. Windows 官方安装器当前未签名；下载者必须从官方 Release 获取并核对 SHA-256。

贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请按
[SECURITY.md](SECURITY.md) 处理，第三方许可见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

---

### Lite 安装包

自 `v1.0.12` 起，Stable Release 只发布 Lite：

- `Lite`（约 326 MiB）保留桌面端、FastAPI、开放模型 Agent、基础文档/表格处理，并可选择本机 Claude Code。
- 安装包不再内置 Node/Claude、Git、TeX、Draw.io、Pandoc 和大型机器学习库，降低下载、更新与维护成本。
- 设置与工作区保存在 `%APPDATA%\ArHub`；本机 Claude Code 使用用户已经安装并登录的 Claude Code，开放模型继续支持 DeepSeek、GLM 和 OpenAI-compatible API。

## English

ArHub (AI Research Hub) is a desktop agent workspace for research writing, data
analysis, and engineering tasks. It is built with Electron, FastAPI,
OpenAI-compatible model APIs, and extensible Skill workflows.

ArHub does not confine an agent to an isolated chat box. Conversation remains
the center of the workspace, while the file tree, editor, and previews open as
the task requires them. Steps, checkpoints, logs, and artifacts persist with
the task so work can be resumed, reviewed, and audited later.

> [!NOTE]
> This repository was reconstructed from the build artifacts of an installed
> application. The backend, agents, workflows, editor, state layer, and document
> export path have been rewritten as reviewable source code and can run from
> source. The frontend currently retains the working `dist/` artifacts and the
> recovered `frontend-src/index.js`. The original Vite module graph has not been
> recovered, while the Windows packaging and release pipeline has been rebuilt
> with reviewable configuration.

### Download and installation

[Download the latest Windows installer from GitHub Releases](https://github.com/jiashuoyan0-maker/ArHub/releases/latest).

Starting with `v1.0.12`, Windows stable releases ship only the recommended Lite
installer of approximately 326 MiB. Lite keeps the desktop app, open-model
agent, basic document processing, and local Claude Code integration. TeX,
Draw.io, Pandoc, Git, bundled Node/Claude, and large ML packages are no longer
included. Settings and workspaces remain under `%APPDATA%\ArHub` across updates.

The installer is assisted: users can keep the default destination or
choose another drive and directory. Application files and the bundled runtime
follow the selected destination, while model settings, credentials, logs, and workspaces remain in
`%APPDATA%\ArHub` and survive upgrades or uninstall. See
[docs/PATHS.md](docs/PATHS.md) for the complete policy.

> [!IMPORTANT]
> ArHub is an independently maintained open-source project. The Windows
> installer is currently distributed without an Authenticode code-signing
> certificate. SmartScreen may therefore display "Windows protected your PC"
> or "Unknown publisher." Download only from this repository's GitHub Releases
> page and verify the SHA-256 checksum first. After it matches, select
> "More info" -> "Run anyway." Do not disable Microsoft Defender, SmartScreen,
> or any other system-wide protection, and do not use third-party mirrors.

```powershell
Get-FileHash .\ArHub-Setup-1.0.12-lite-x64.exe -Algorithm SHA256
```

Compare the result character by character with the matching entry in
`SHA256SUMS.txt` from the same Release. Official releases also include SHA-512
update verification, CycloneDX SBOMs, an installer smoke-test report, and GitHub
build provenance attestations.

### Interface preview

#### Work with the agent and document side by side

The agent conversation is the main workspace. When a document is opened, the
Markdown/LaTeX editor expands alongside it and automatically places the current
file in the agent context. There is no need to keep switching among a chat,
file manager, and editor. The composer can switch between open models and local
Claude Code, set reasoning effort, attach files, and turn Send into Stop while
the agent is running.

![ArHub Agent and Markdown editor](assets/screenshots/03-editor-agent-split.png)

#### From a single task to a complete research pipeline

New tasks can start from Idea Discovery, Experiment Bridge, an automated review
loop, or the full pipeline. Templates define the steps and roles, while the
user confirms parameters before execution.

![ArHub research workflow templates](assets/screenshots/01-workflow-templates.png)

The full pipeline can also configure output format, paper language, paper type,
and follow-up execution options. Run state, checkpoints, and artifacts are
persisted per task and can be resumed after an interruption.

![ArHub full pipeline configuration](assets/screenshots/02-full-pipeline-config.png)

#### Choose a model for each agent

The executor, reviewer, and editor assistant can each use a separate Base URL,
API Key, and Model ID. This makes it possible to assign execution, critique,
and writing to different models. Runtime, provider, and reasoning effort are
configurable as well. The screenshot contains public API endpoints and example
model names only; every API key field is empty.

![ArHub multi-agent model settings](assets/screenshots/05-model-settings-light.png)

#### An open extension layer for more tools

The extension center registers agent profiles, prompt commands, and tool entry
points through manifests. Built-in Diagram Studio and Web Studio bring diagrams,
web projects, and research writing into one workspace. Third-party manifests are
loaded as declarative data and do not execute extension code by default.

![ArHub extension center](assets/screenshots/06-extension-center.png)

### Typical workflow

1. Create a task and select a workflow template, or begin with a lightweight agent chat.
2. Choose a provider, model, and reasoning effort for each agent, or switch to local Claude Code.
3. Let the agent call Skills for search, analysis, coding, plotting, or document generation.
4. Open artifacts beside the conversation, inspect file diffs, then apply, discard, or undo changes.
5. Pause, resume, or rerun an individual step from a checkpoint without rebuilding the prompt.

### Key capabilities

- Configure models and APIs independently for the executor, reviewer, and editor.
- Run multi-step Skill workflows with checkpoints, artifact management, and resume support.
- Open the file tree, editor, previews, and context dynamically beside the agent chat.
- Review agent-generated file diffs, with apply, discard, and undo actions.
- Export Markdown to DOCX and preview PDF, DOCX, Markdown, and image files.
- Extend agent profiles and command entry points through declarative manifests.

### Model configuration

All three agents accept OpenAI Chat Completions-compatible endpoints, including:

- A service root, such as `https://api.deepseek.com`
- A versioned compatibility endpoint, such as `https://open.bigmodel.cn/api/paas/v4`
- A complete `.../chat/completions` endpoint

DeepSeek, GLM, and other OpenAI-compatible providers use the same connection
layer. The Model ID must be one actually enabled for the account, such as
`deepseek-chat`, a GLM model ID supplied by the provider, or `gpt-4o`. The
connection layer respects `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY`.

The default open-model runtime calls the endpoints configured in Settings
directly. Users can also select a compatible local Claude Code installation;
ArHub detects the executable, streams its structured output, supports stop, and
passes the configured Claude effort level (`low` through `max`). Provider-aware
reasoning controls map to GLM thinking mode and OpenAI reasoning effort without
sending unsupported options to DeepSeek. Providers still differ in tool calling,
vision input, context length, and token parameter support, so a successful
connection test does not guarantee identical workflow capabilities.

### Lite installer

Stable Releases ship only Lite starting with `v1.0.12`:

- **Lite** keeps Electron, the FastAPI core, the open-model agent, and basic
  document/spreadsheet libraries. It expects a local Claude Code installation
  when that runtime is selected.
- Bundled Node/Claude, Git, TeX, Draw.io, Pandoc, and large optional ML packages
  are omitted to reduce download size and maintenance cost.
- Settings and workspaces remain under `%APPDATA%\ArHub` across updates.

API keys should be stored only in local settings. Never place keys in the
repository, screenshots, Issues, or logs. Revoke and regenerate any credential
that has previously been exposed in a chat or another external location.

### Project status

| Component | Status | Notes |
|---|---|---|
| Electron main process | Reviewable source | `main.js`, `preload.js`, and `updater.js` |
| FastAPI backend | Runnable source | 70 application routes with isolated data directories and workspace boundaries |
| Agents and workflows | Runnable source | Provider-neutral tool loop, checkpoints, pause/resume, and persistent state |
| Editor | Runnable source | Markdown/LaTeX, file tree, agent diff/apply/undo, image and script tools |
| DOCX and extraction | Runnable source | High-fidelity Node engine, python-docx fallback, and PDF/DOCX text extraction |
| Frontend | Recovered artifacts | Codex-style dynamic workspace and light/dark themes; no reproducible modular frontend build yet |
| Skills and extensions | Plain reviewable files | Skills, templates, and declarative profiles require no activation or decryption |
| Windows installer | Lite stable release | Lite runtime, NSIS, SBOMs, checksums, custom install paths, and GitHub release workflow; official artifacts are currently unsigned |

### Run from source

Windows, Python 3.11, and Node.js 20+ are recommended. FastAPI serves the
`dist/` frontend, so a separate frontend development server is not required.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

$env:ARHUB_DATA_DIR = "$PWD\.arhub-data"
$env:ARHUB_API_PORT = "18088"
.\.venv\Scripts\python.exe -X utf8 -m uvicorn backend.main:app --host 127.0.0.1 --port 18088
```

Open [http://127.0.0.1:18088](http://127.0.0.1:18088) after startup. The Python
DOCX fallback is installed through `backend/requirements.txt`. For equations
and complex layout, install the optional Node engine dependencies:

```powershell
npm --prefix tools\docx-cn-engine ci
```

### Development and verification

```powershell
npm run check:js
npm run check:python
npm test
npm run audit:open-source
git diff --check
```

The current regression suite contains 40 Python tests and 26 Node tests. It
covers model URLs, LLM requests, agent tool loops, workflow state, editor safety
boundaries, diff/apply/undo, DOCX export, and the extraction queue. The Windows
release workflow additionally verifies installation, backend startup, frontend
loading, uninstallation, and the expected unsigned state.

To build an unsigned Windows installer locally:

```powershell
npm ci
$env:ARHUB_RUNTIME_DIR = 'C:\path\to\verified\runtime'
npm run runtime:check
npm run package:win:lite
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke-test-installer.ps1 `
  -InstallerPath release\ArHub-Setup-1.0.12-lite-x64.exe -RequireUnsigned
```

### Data and extensions

The default data directory is `%APPDATA%\ArHub`. Source development and tests
should set `ARHUB_DATA_DIR` to an isolated directory. Databases, logs,
workspaces, model credentials, and user extensions are excluded from the public
repository.

The declarative extension registry reads JSON manifests only; it does not import
or execute third-party code. Executable extensions should not be introduced
until permission declarations, isolation, and revocation mechanisms exist.

### Repository layout

| Path | Contents |
|---|---|
| `backend/` | FastAPI routes, state, agents, workflows, and export services |
| `dist/` | Frontend artifacts used by the current application |
| `frontend-src/` | Readable JSX source recovered from the bundle |
| `skills/` | Skills for research writing, analysis, plotting, and workflows |
| `extensions/` | Declarative agent profiles and extension manifests |
| `templates/`, `tools/` | Templates, DOCX engine, and supporting tools |
| `tests/` | Backend and core behavior regression tests |
| `docs/recovery/` | Historical recovery evidence and legacy API surfaces, not current implementation status |

### Known limitations

1. The original frontend modules and Vite configuration have not been recovered;
   UI changes must update both `frontend-src/index.js` and `dist/`.
2. The installer can be rebuilt from committed artifacts and the locked runtime,
   but the frontend cannot yet be rebuilt independently from modular source.
3. The original source of three legacy bytecode DOCX helpers could not be
   recovered, but new Node/Python implementations have replaced them.
4. Provider-neutral does not mean provider-identical; model capabilities must
   still be verified per provider.
5. The official Windows installer is currently unsigned; download it only from
   the official Release and verify its SHA-256 checksum.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing. Report security
issues according to [SECURITY.md](SECURITY.md). Third-party license information
is available in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

ArHub-owned code is distributed under the [MIT License](LICENSE). Third-party
components remain subject to their respective licenses.

---

## 社区 / Community

欢迎在 [Linux DO 社区](https://linux.do/) 交流 ArHub 的使用体验、问题反馈和扩展想法。

Join the ArHub discussion on [Linux DO](https://linux.do/) to share feedback,
report issues, and exchange extension ideas.
