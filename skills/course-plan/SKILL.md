---
name: course-plan
description: "课程论文大纲规划。读取用户主题、上传资料，产出大纲、数据分析规划、图表规划，为后续数据分析和正文撰写做准备。Use when starting a course paper workflow."
argument-hint: [paper-topic]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent
---

# 课程论文大纲规划

为以下主题规划课程论文：**$ARGUMENTS**

## 常量

- **SUBJECT_DOMAIN** — 学科领域（cs / humanities / economics / engineering）
- **WORD_COUNT_TARGET** — 目标字数（默认 8000）
- **SKIP_FIGURES** — 是否跳过图表生成（true/false，默认 false；从 CLAUDE.md 中的 `skip_figures` 参数读取）
- **CUSTOM_REQUIREMENTS** — 用户自定义要求

## 输入

1. 论文主题（$ARGUMENTS）
2. 用户上传的参考资料（`user_data/`，可选）
3. 用户提供的大纲草稿（如果存在 `OUTLINE.md`）

## ⛔ 数据存在性 Gate（最重要）

**先做这一步**，决定整个规划走"有图表"还是"无图表"分支：

```bash
echo "=== 数据存在性检查 ==="
DATA_FILES=""
for f in user_data/*.csv user_data/*.json user_data/*.xlsx user_data/*.xls user_data/*.tsv user_data/*.txt; do
    [ -f "$f" ] || continue
    # 排除提取文本类（_extracted.txt 是从 PDF 提取的描述文本，不是数据）
    case "$(basename "$f")" in
        *_extracted.txt) continue ;;
    esac
    DATA_FILES="$DATA_FILES $f"
done

# 检查 SKIP_FIGURES 标志（CLAUDE.md 顶部参数区中的 skip_figures: true）
SKIP_FIGURES=$(grep -E '^- skip_figures:\s*[Tt]rue' CLAUDE.md 2>/dev/null | head -1)

echo "数据文件: ${DATA_FILES:-（无）}"
echo "用户跳过图表: ${SKIP_FIGURES:-否}"
```

**两类硬规则：**

1. **如果 `SKIP_FIGURES=true`（用户在前端关闭了图表）**：
   - 强制走「无图表分支」
   - `PAPER_PLAN.md` 中**禁止规划任何 fig_/TABLE_**，只规划文字结构

2. **如果 `SKIP_FIGURES=false`（用户开启图表）**：
   - 走「有图表分支」
   - **有数据 → 按真实数据规划具体图表**
   - **没数据 → 仍然规划完整图表清单**，并明确标注「**基于仿真/示例数据**」（paper-analysis 步骤会按规划生成仿真数据）
   - **绝不许因为 user_data/ 为空就跳过图表规划** — 用户已经明确开启图表，仿真数据是合理选择

**关键原则：** 是否规划图表只看 `skip_figures` 这一个开关，不看是否有数据。没数据就用仿真数据，但图表规划必须照常做。

## 硬约束

1. **本步骤只规划，不写正文。** 正文由 `course-paper` 完成。
2. 必须产出 `OUTLINE.md` 和 `PAPER_PLAN.md`（即使无图表也要有 PAPER_PLAN.md，明确写「无图表」）。
3. 老师上传的要求文档（`user_data/*_extracted.txt`）优先级高于学科默认结构。
4. **图表规划只许基于真实数据**：禁止凭空编造"将绘制某图"。
5. 文献关键词清单要写进 `OUTLINE.md` 末尾。

## ⛔⛔⛔ 完成铁律（最高优先级）

**本步骤必须产出 `OUTLINE.md`（≥ 800 字节，完整的论文大纲）**。

⛔ **结束前必跑产出验证**：
```bash
[ -f OUTLINE.md ] && SZ=$(wc -c < OUTLINE.md) || SZ=0
[ "$SZ" -ge 800 ] && echo "✅ OUTLINE.md ($SZ)" \
    || echo "❌ OUTLINE.md 缺失或过小 — 必须补全后重新跑验证, 不要结束本步骤"
```

## 工作流程

### Step 1: 输入梳理

```bash
echo "=== 检查用户上传资料 ==="
ls user_data/ 2>/dev/null || echo "无用户上传文件"

# 列出所有提取文本（PDF/DOCX 已被后端提取）
for f in user_data/*_extracted.txt user_data/*.txt; do
    [ -f "$f" ] && { echo "--- $f ---"; head -c 800 "$f"; echo; }
done

# 检测用户上传的格式模板（.docx）
TEMPLATE_DOCX=$(find user_data -maxdepth 1 -name "*.docx" 2>/dev/null | head -1)
if [ -n "$TEMPLATE_DOCX" ]; then
    echo "检测到用户上传的 docx 模板: $TEMPLATE_DOCX"
    echo "（docx-export 步骤会自动提取该模板的字体/字号/页边距并应用到导出 Word）"
    # 同时检查模板对应的提取文本（如 xxx_extracted.txt），用于了解模板的章节结构
    TEMPLATE_TXT="${TEMPLATE_DOCX%.docx}_extracted.txt"
    [ -f "$TEMPLATE_TXT" ] && { echo "模板内容预览:"; head -c 500 "$TEMPLATE_TXT"; echo; }
fi

# 用户上传的图片：复制到 figures/ 供后续撰写直接引用
mkdir -p figures
USER_IMAGES=""
for f in user_data/*.png user_data/*.jpg user_data/*.jpeg; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    cp "$f" "figures/$bn"
    echo "复制用户图片到 figures/: $bn"
    USER_IMAGES="$USER_IMAGES figures/$bn"
done
```

提取要点：
- 老师对格式的要求（字体/字号/行距/页边距/字数）
- 老师对章节结构、参考文献数量的要求
- 用户已上传的数据文件清单（决定是否规划图表）
- 用户已上传的图片（已复制到 figures/，可直接在大纲中规划"嵌入这些图"）

### Step 2: 生成大纲（OUTLINE.md）

按学科领域生成大纲（结构借鉴 lunwen-skill chapter-patterns）。

每章必须给出：**预期字数 / 核心论点 3-5 条 / 关键术语 / 是否引图**。

**计算机科学（cs）：**
```
摘要 + 关键词
1. 引言（15%）
2. 相关工作 / 技术综述（20%）
3. 方法 / 系统设计（30%）
4. 实验与分析（25%，仅在有数据时存在；否则改为「案例分析」或「方法对比」）
5. 结论与展望（10%）
参考文献
```

**人文社科（humanities）：**
```
摘要 + 关键词
1. 引言
2. 文献综述
3. 研究方法（思辨型可省略）
4. 分析与讨论（核心章节，思辨型在此展开）
5. 结论
参考文献
```

**经济管理（economics）：**
```
摘要 + 关键词
1. 引言
2. 理论基础与文献综述
3. 研究假设与模型构建
4. 实证分析（有数据则放图表；无数据则改为「案例剖析」）
5. 结论与建议
参考文献
```

**工程技术（engineering）：**
```
摘要 + 关键词
1. 引言
2. 技术方案设计
3. 实现与测试（有数据则放图表）
4. 结果分析与优化
5. 结论
参考文献
```

`OUTLINE.md` 写作要点：
- 标题用 `## 第N章`，子节用 `### N.1`、`### N.2`
- 每章用一个 markdown 子表标注：字数/论点/术语/引图
- 末尾必须有「文献调研关键词」清单
- 末尾必须有「Claims-Evidence Matrix」（每个核心论点对应的证据来源）

**Claims-Evidence Matrix 模板：**
```markdown
## Claims-Evidence Matrix

| Claim（核心论点） | Evidence（证据来源） | Section（落点章节） | Status（待定/已支撑） |
|------------------|--------------------|-------------------|-------------------|
| [本文方法 X 优于 baseline] | fig_main_result（如有数据） / 文献 [1] [2] | 第 4 章 | 待定 |
| [Y 的提升源于 Z 机制] | fig_ablation / 文献 [3] | 第 4.3 节 | 待定 |
```

如果是无数据论文，Evidence 全部用文献支撑（不写 fig_）。

### Step 3: 数据分析与图表规划（PAPER_PLAN.md）

**分支 A — 有图表（SKIP_FIGURES=false，无论是否有数据）：**

如果有真实数据：
```markdown
# 课程论文：数据分析与图表规划

## 数据资产
- user_data/xxx.csv（N 行，K 列）— 字段：[列名 1] / [列名 2] / ...
- user_data/yyy.json — 含字段 [...]
- 用户已上传的图片（已复制到 figures/）：fig_user_*.png（N 张）

## 分析任务（由 paper-analysis 步骤执行，使用真实数据）
1. 描述性统计 → figures/all_results.json 中保存均值/方差等
2. 主要分析（根据论文主题）：相关性/回归/聚类/时序预测...
3. 验证性分析：稳健性/敏感性

## 图表规划（CHECKLIST，paper-figure 步骤按此清单执行）
- [ ] fig_desc_stats — 描述性统计（直方图/箱线图） — 数据来源 figures/all_results.json[describe] — 落点 §4
- [ ] fig_main_result — 主要结果对比 — 数据来源 figures/all_results.json[main] — 落点 §4
- [ ] fig_xxx — ...
- [ ] TABLE_desc — 描述性统计表 — 落点 §4
- [ ] TABLE_main — 主要结果表 — 落点 §4

## 输出文件命名规范
所有 fig_ 同时输出 PDF 和 PNG（PNG 用于 Word 导出）：
- figures/fig_xxx.pdf
- figures/fig_xxx.png
表格：figures/TABLE_xxx.md（⛔ 课程论文是 Word 输出，表格用 Markdown 三线表 .md，**不是 .tex**）
```

**如果没真实数据但用户开启了图表**（用仿真数据）：
```markdown
# 课程论文：数据分析与图表规划

## 数据资产
**用户未提供数据文件，将使用仿真/示例数据**（paper-analysis 步骤负责生成）。

## 仿真数据规划（paper-analysis 步骤参考）
基于论文主题「[主题]」，构造合理的仿真数据集：
- 数据规模：N=500 samples × K=8 features（视主题调整）
- 字段定义：
  - id (int): 样本编号
  - feature_1 (float): [含义]，分布假设 N(μ=0, σ=1)
  - feature_2 (categorical): [含义]，取值 {A, B, C}
  - target (float): [因变量]，由 feature_1 + 噪声 生成
- 数据生成方式：基于上述分布用 numpy/pandas 模拟
- 保持学术诚信：在论文中明确注明「数据为仿真生成」

## 分析任务（基于仿真数据）
1. 描述性统计
2. 主要分析（根据论文主题）
3. 验证性分析

## 图表规划（CHECKLIST，正常规划，标注基于仿真数据）
- [ ] fig_desc_stats — 描述性统计（仿真数据）— 落点 §4
- [ ] fig_main_result — 主要结果对比（仿真数据）— 落点 §4
- [ ] TABLE_desc — 描述性统计表 — 落点 §4
- [ ] TABLE_main — 主要结果表 — 落点 §4

## 输出文件命名规范
所有 fig_ 同时输出 PDF 和 PNG（PNG 用于 Word 导出）：
- figures/fig_xxx.pdf
- figures/fig_xxx.png
```

**分支 B — 无图表（SKIP_FIGURES=true，用户显式关闭）：**

```markdown
# 课程论文：图表规划

## 数据资产
（无 — 用户未上传数据文件，且未提供图片）

## 分析任务
（无）

## 图表规划
**本论文不规划任何 fig_ 或 TABLE_。**
- 后续 paper-analysis 与 paper-figure 步骤将被跳过
- 正文以叙述、引用文献、概念框架为主
- 如果某章想要"对比表"或"概念矩阵"，使用 Markdown 表格语法直接写在正文中（不算 figures/ 中的产物）

## 撰写注意
- 写作时不许说"如图 X 所示"或"详见 fig_xxx"
- 所有论点用文献引用支撑（[1] [2] 形式）
```

⛔ 写完 PAPER_PLAN.md 后必须自检：

```bash
echo "=== PAPER_PLAN 自检 ==="
SKIP=$(grep -ciE '^\*\*本论文不规划任何' PAPER_PLAN.md)
HAS_FIG=$(grep -cE '^- \[ \] fig_|TABLE_' PAPER_PLAN.md)
SKIP_FIGURES_FLAG=$(grep -ciE '^- skip_figures:\s*[Tt]rue' CLAUDE.md 2>/dev/null)

if [ "$SKIP" -ge 1 ] && [ "$HAS_FIG" -ge 1 ]; then
    echo "❌ 自检失败：标记了'不规划图表'但又列了 fig_/TABLE_，请删除规划项"
    exit 1
fi
if [ "$SKIP_FIGURES_FLAG" -ge 1 ] && [ "$HAS_FIG" -ge 1 ]; then
    echo "❌ 自检失败：用户已禁用图表（skip_figures=true）但 PAPER_PLAN 中列了 fig_，必须改为'无图表分支'"
    exit 1
fi
if [ "$SKIP_FIGURES_FLAG" -eq 0 ] && [ "$HAS_FIG" -eq 0 ] && [ "$SKIP" -eq 0 ]; then
    echo "❌ 自检失败：用户启用了图表但 PAPER_PLAN 中没列任何 fig_，必须规划完整图表清单（无数据时用仿真数据）"
    exit 1
fi
echo "✅ PAPER_PLAN.md 一致性 OK"
```

### Step 4: 文献关键词清单

在 `OUTLINE.md` 末尾追加：
```markdown
## 文献调研关键词
- 核心：[关键词1]、[关键词2]
- 扩展：[关键词3]、[关键词4]
- 时间范围：近 5 年优先
```

## 输出文件

- `OUTLINE.md` — 论文大纲（章节结构 + 字数分配 + 核心论点 + Claims-Evidence Matrix + 文献关键词）
- `PAPER_PLAN.md` — 数据分析与图表规划（有图表 / 无图表两种分支）

## 关键规则

1. **不写正文，只规划。** 正文交给 course-paper。
2. **是否规划图表只看 `skip_figures` 开关：**
   - 用户开启图表（默认）→ 必须规划完整图表清单
     - 有数据 → 用真实数据规划
     - 没数据 → **用仿真数据规划，不允许跳过图表**
   - 用户关闭图表 → 走「无图表分支」
3. **Claims-Evidence Matrix 必须存在**，是后续撰写质量的基准。
4. **PAPER_PLAN.md 一致性自检** 必须通过。
5. **用户上传图片自动复制到 figures/**，可在大纲中规划"§3.1 引用 fig_user_xxx.png"。
6. **学术诚信**：使用仿真数据时必须在 PAPER_PLAN 和后续论文正文中明确注明。
