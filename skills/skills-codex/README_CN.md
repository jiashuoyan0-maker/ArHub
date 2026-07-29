# skills-codex 说明

## 1. 这个包是什么

这是一个面向 **Codex** 的技能包目录，当前版本已经与主线 `skills/` 对齐：

- 保留与 `.claude/skills` **同名** 的完整技能集
- 同步包含主线新增的 `experiment-bridge`、`grant-proposal`、`paper-illustration`

数量对比：

- `.claude/skills` 当前技能数：`31`
- 本包技能数：`31`
- 与 `.claude/skills`：一一对应，无额外私有技能

本包路径结构是：

```text
skills/skills-codex/
  <skill-name>/
    SKILL.md
    ...
```

## 2. 和 Claude 版本相比做了哪些变动

### 2.1 范围控制

本包没有把当前 `~/.codex/skills` 里的所有内容都打进去，而是只保留：

- 主线 `skills/` 中已有的同名技能
- 这些技能所需的最小资源目录

因此，本包 **不包含**：

- `doc`
- `pdf`
- `.system/*`

### 2.2 保持 Claude 风格的打包方式

为了尽量贴近 `.claude` 的单文件风格：

- 大部分技能只保留 `SKILL.md`
- 只有确实依赖本地资源的技能保留附属目录

当前保留附属目录的有：

- `paper-write/templates/`
- `comm-lit-review/references/`

### 2.3 `paper-write` 做了资源补强

相比 `.claude/skills/paper-write`，本包里的 `paper-write` 不只保留原来的模板 `.tex`，还补入了实际编译需要的样式资源：

- `iclr2026_conference.sty`
- `iclr2026_conference.bst`
- `icml2025.sty`
- `neurips_2025.sty`

这意味着它比原始 `.claude` 版本更完整，更接近“可直接用于生成论文模板”的状态。

### 2.4 `comm-lit-review`

这是保留在主线同步集里的领域强化技能，定位是：

- 通信 / 无线 / NTN / 卫星 / Wi-Fi / 传输控制 / 资源分配等方向的文献检索
- 默认按通信领域口径做信息检索，而不是走通用文献检索逻辑

它的核心增强点：

- 数据库分层：`IEEE Xplore -> ScienceDirect -> ACM Digital Library -> 全网补充`
- venue 分层：`顶会/top期刊 -> 主流强 venue -> 更广的正式 venue`
- 默认是 **软约束**
- 如果用户明确说 `only top venues` / `top journals only` / `top conferences only`，则切到 **硬约束**

### 2.5 MCP 逻辑的处理方式

这部分和 `.claude` 版本相比，最需要单独说明。

本包对 `MCP` 逻辑的处理分成两类：

#### A. Claude 专属的控制型 MCP 逻辑

这类逻辑指的是旧技能里如果存在：

- `mcp__codex__...`
- `threadId`
- `codex-reply`
- `USER_REQUEST`

这一类 **面向旧会话编排/回帖机制** 的写法，在迁移到新的 Codex 技能体系时不应继续保留。

这次整理后的技能包，目标就是：

- 不依赖 `.claude` 专属线程编排
- 不依赖旧的 `mcp__codex__` 调用约定
- 让技能在新的 Codex 技能语义下直接工作

也就是说，**旧 Claude 专属的控制型 MCP 逻辑不属于这个包的一部分**。

#### B. 外部服务型 MCP 逻辑

有些技能仍然可能在 `SKILL.md` 中提到外部 MCP 服务，例如：

- `research-lit` 里的 `Zotero / Obsidian MCP`
- `auto-review-loop-llm` 里的 `llm-chat MCP`
- `auto-review-loop-minimax` 里的 `minimax-chat MCP`

这类 MCP 不是旧 Claude 会话编排逻辑，而是**外部能力接入**。它们在本包中仍然保留为技能说明的一部分，但：

- 本包只迁移技能文件
- **不会**帮你迁移这些 MCP server 的实际配置
- 新环境里如果没有对应 MCP server，这些能力就会降级或跳过

因此可以把这次迁移理解成：

- **去掉旧 Claude 专属的控制型 MCP 依赖**
- **保留外部服务型 MCP 的可选入口说明**

## 3. 哪些技能是单文件，哪些不是

本包里绝大多数技能都按单文件方式整理，只包含：

- `SKILL.md`

只有这两个不是单文件：

- `paper-write`
- `comm-lit-review`

原因：

- `paper-write` 依赖 `templates/`
- `comm-lit-review` 依赖 `references/`

## 4. 如何在新的 Codex 里安装

### 4.1 基本安装

在新环境里，把本目录下的技能复制到 `~/.codex/skills/` 即可：

```bash
mkdir -p ~/.codex/skills
cp -a skills/skills-codex/* ~/.codex/skills/
```

如果你当前就在仓库根目录，也可以用绝对路径：

```bash
mkdir -p ~/.codex/skills
cp -a /path/to/Auto-claude-code-research-in-sleep/skills/skills-codex/* ~/.codex/skills/
```

### 4.2 安装后建议

安装完成后，建议：

1. 启动一个新的 Codex 会话
2. 检查技能列表里是否能看到新增的 `comm-lit-review`
3. 抽样验证一个单文件技能和一个带资源技能

例如：

- 单文件技能：`research-lit`
- 带资源技能：`paper-write` 或 `comm-lit-review`

### 4.3 验证方式

如果目标环境中带有 Codex 的 system skills，可以用：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/comm-lit-review
```

如果输出：

```text
Skill is valid!
```

说明目录结构至少是合法的。

## 5. 安装时需要知道的边界

### 5.1 本包只处理技能文件，不处理环境

本包不包含这些内容：

- Python 依赖
- LaTeX / Poppler / GPU / SSH / conda 环境
- MCP 配置
- API Key / 环境变量

也就是说，本包解决的是 **技能文件迁移**，不是 **运行环境迁移**。

如果目标环境需要继续使用外部 MCP 能力，还需要你单独恢复或重建相应配置，例如：

- Zotero MCP
- Obsidian MCP
- llm-chat MCP
- minimax-chat MCP

### 5.2 `.system` 不在本包里

本包没有包含：

- `~/.codex/skills/.system/openai-docs`
- `~/.codex/skills/.system/skill-creator`
- `~/.codex/skills/.system/skill-installer`

默认假设新的 Codex 环境本身已经带有这些系统技能，或者不依赖它们。

## 6. 当前包的用途

这个包适合：

- 从 `.claude` 风格技能迁移到 Codex
- 保留与主线 `skills/` 一致的技能集合
- 在 Codex 环境中直接使用与 Claude 侧对齐的工作流

如果后面你还想继续精简或扩展，可以基于这个目录继续做白名单管理。
