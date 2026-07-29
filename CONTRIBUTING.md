# Contributing to ArHub

ArHub 已完成核心后端重构，当前贡献重点是提高可维护性、兼容性和可复现发布
能力。不要把安装目录中的 runtime、二进制文件或用户数据直接提交到仓库。

## 提交前

1. 先阅读当前实现和测试；`docs/recovery/api/` 是历史 API 证据，不是当前
   代码的唯一规范。
2. 保留 `%APPDATA%\ArHub`、`arhub.*` 和 `arhub.core` 的兼容迁移，
   除非变更同时提供迁移逻辑。
3. 不提交 API Key、激活信息、数据库、日志、证书、签名或绝对用户路径。
4. 新配置必须提供无真实凭证的示例，并默认关闭非必要外部网络行为。
5. 修改模型协议时，至少覆盖根地址、版本地址和完整 endpoint 三种 URL。
6. `ClaudeRunner` 是历史兼容类名；新实现必须保持 provider-neutral，不得
   重新引入固定模型服务商。
7. UI 变更必须同步可读的 `frontend-src/index.js` 和当前 `dist/` 产物，
   并验证亮色、暗色及窄窗口布局。

## 优先贡献方向

- 将恢复后的单文件前端拆分为可构建的模块和 Vite 工程。
- 建立可复现 Electron/Python runtime、SBOM、签名和安装包流水线。
- 扩大 DeepSeek、GLM 和其他 OpenAI-compatible 服务的工具调用测试矩阵。
- 为文件系统、工作流恢复、文档导出和扩展权限增加边界测试。
- 在保持声明式安全边界的前提下设计开放扩展 API。

## 本地检查

```powershell
npm run check:js
npm run check:python
npm test
npm run audit:open-source
git diff --check
```

提交说明应写清行为变化、验证方式和剩余限制。涉及 UI 的变更应附亮色与暗色
验证结果；涉及 provider 的变更不得包含真实 API Key。

