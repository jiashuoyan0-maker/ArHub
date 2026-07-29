# 源码恢复记录

原始仓库丢失后，ArHub 从本机已安装的未打包 `resources\app` 构建产物重建。
本文件记录来源与证据边界；它不是当前功能缺口清单。

## 初始恢复

### 明文内容

以下内容可直接从安装产物取回：

- Electron 主进程：`main.js`、`preload.js`、`updater.js`
- 后端入口、配置、数据库 schema、requirements 和部分工具
- 模板、扩展 manifest、DOCX 工具、样式 profile 与图标资源
- Skills 明文资源

恢复阶段使用的固定代理、CLI wrapper 和补丁注入模块只服务于旧安装版诊断。
provider-neutral 源码完成后，这些模块已从公开运行时删除。

### Cython 模块

原安装包中 18 个 Python 模块被编译为原生机器码，无法自动还原为原始源码。
通过运行时导入和反射恢复了初始 57 条 HTTP 路由、Pydantic 字段、函数签名和
docstring，并保存到 `docs/recovery/api/`。最初生成的 API stub 只用于确定
重写边界，不等同于原实现。

## 当前重写状态

初始 stub 已由新的可维护实现替换。当前 `backend.main` 可导入 70 条应用路由，
并已覆盖：

- SQLite 状态、设置、工作流导入导出和检查点
- OpenAI-compatible LLM 请求与 provider URL 规范化
- provider-neutral Agent 工具循环和本地文件边界
- 工作流状态机、暂停恢复、心跳与 WebSocket 输出
- Artifact 上传、浏览、编辑、提取和安全路径解析
- Markdown/LaTeX 编辑器、Agent diff/apply/discard/undo 与历史记录
- DOCX Node 引擎、python-docx fallback、预览和下载
- 扩展 manifest 注册表与兼容激活端点

`ClaudeRunner` 名称只为兼容既有调用方，当前实现不要求 Claude CLI。
`docs/recovery/api/` 保留历史签名供考证，不保证与新实现逐项相同。

## 前端

原 Vite bundle 没有 sourcemap：

- `dist/` 保留当前可运行产物。
- `frontend-src/index.js` 是反混淆和 JSX 还原后的可读单文件源码。
- Codex 式动态工作台、ArHub 品牌、亮暗主题和开放 profile 层直接维护在恢复
  源码及附加资源中。

原始模块目录和 Vite 构建配置仍未恢复，这是当前主要源码可维护性缺口。

## DOCX 字节码边界

旧安装中三个 DOCX helper 只剩 `.pyc`，原始实现不可恢复且字节码不入库。
公开运行时已用 `backend/services/docx_exporter.py`、Node DOCX 引擎和
python-docx fallback 替代这些功能，因此源码运行不依赖旧字节码。

## 有意排除

- 备份、缓存、`__pycache__` 和恢复期临时文件
- 用户数据库、日志、许可证文件和模型凭证
- `.pyd`、`.pyc`、`.exe`、`.dll`、证书与签名
- 无再分发许可的商业字体
- 安装 runtime 与本机绝对路径

## 剩余工程工作

1. 将恢复前端拆分为可复现构建的模块。
2. 建立锁定依赖的 Electron/Python runtime 与安装包流程。
3. 生成 SBOM，自动检查第三方许可并建立代码签名。
4. 扩大 provider、文档格式和 Windows 干净环境测试矩阵。
