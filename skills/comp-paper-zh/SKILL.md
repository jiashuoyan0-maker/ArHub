---
name: comp-paper-zh
description: "数学建模竞赛/统计建模中文论文撰写。按竞赛规范结构生成完整 LaTeX 论文。Use when user says \"写竞赛论文\", \"competition paper\", \"建模论文\"."
argument-hint: [competition-type]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Competition Paper Writing (Chinese)

Write a competition paper based on modeling results: **$ARGUMENTS**

## Constants

- **COMPETITION** — `stats` = 统计建模, `huazhong` = 华中杯, `wuyi` = 五一杯, `mathorcup` = MathorCup, others = 数模竞赛 (cumcm/huawei/etc.)
- **MAX_PAGES** — Default 20. Body pages (chapter 1 through conclusion) must be ≥ MAX_PAGES.
- **CUSTOM_REQUIREMENTS**

## Inputs

1. PROBLEM_ANALYSIS.md, MODELING_REPORT.md, RESULTS.md
2. figures/, code/

## Load shared rules

```bash
cat _utils/writing_rules.md 2>/dev/null || cat skills/shared-scripts/writing_rules.md
```

<paper_structure>
## Paper Structure by Competition Type

### 数模竞赛 (cumcm/huawei/mathorcup/huazhong/etc.)

Template: `templates/cumcm/main.tex` (国赛/华为杯), `templates/mathorcup/main.tex` (MathorCup), `templates/huazhong/main.tex` (华中杯), `templates/wuyi/main.tex` (五一杯)

**⛔ MathorCup 必须使用 `MathorCupmodeling.cls` 文档类**（模板文件夹已包含 cls）。使用 `\bianhao{}`、`\tihao{}`、`\timu{}` 设置队伍信息，`\keyword{}` 设置关键词。摘要用 `\begin{abstract}...\end{abstract}` 环境。参考文献用 `\begin{thebibliography}` 环境。

**⛔ 华中杯必须使用 `cumcmthesis` 文档类**（模板文件夹 `huazhong/` 已包含 cls + 字体）。华中杯模板使用 `\begin{abstract}...\keywords{}\end{abstract}` 环境写摘要（不是手动排版），参考文献用 `\begin{thebibliography}` 环境（不是 `\bibliography{}`）。

```
摘要（~1页，含关键词）
1 问题重述
2 模型假设
3 符号说明
4 问题一的建模与求解（each sub-problem gets its own chapter）
5 问题二的建模与求解
6 问题三的建模与求解
7 灵敏度分析与模型检验
8 模型评价与推广
参考文献
附录 A：代码
```

### 统计建模 (stats)

Template: `templates/stats/main.tex`

**Chapter structure is driven by research content, not fixed templates.**

Award-winning stats modeling papers vary wildly in structure — some organize by model, some by analysis step, some by research question. There is no "standard structure". Claude must design chapters autonomously based on the actual content in TOPIC_PLAN.md / MODELING_REPORT.md.

#### Fixed skeleton (must keep)

```
表格清单
插图清单
摘要（中英文，分页）
一、绪论/前言（研究背景 + 文献综述/研究现状 + 研究目标/内容）
  ↓
  [Middle chapters: content-driven, Claude designs autonomously, typically 3-5 chapters]
  ↓
N、结论与建议（结论 + 建议/展望 + 创新与不足）
参考文献
致谢
附录（代码）
```

#### Middle chapter design guide

After reading TOPIC_PLAN.md, design middle chapters following these principles:

**Principle 1: Chapter titles must be specific, not generic**
- ✗ "四、模型构建" → ✓ "四、基于 CNN 的水质预测模型构建与评价"
- ✗ "五、实证分析" → ✓ "五、生育意愿的影响因素——集成学习模型"

**Principle 2: Organize by research logic chain, not by textbook methodology**
- If the research has multiple sub-problems/models, each model can be its own chapter
- If the research uses a single method with deep analysis, organize by analysis steps

**Principle 3: Data and method chapters can be merged or separated**
- Simple data (one dataset) → merge into "数据与方法"
- Complex data (multi-source, heavy preprocessing) → separate chapter "数据描述与预处理"

#### Award-winning paper structure examples (reference only, do not copy)

**Example A — Classification + Path Analysis (fertility intention)**:
前言 → 模型构建 (introduce ensemble + Bayesian network) → 数据说明和预处理 → 探索性特征分析 → 生育意愿的影响因素 (ensemble results) → 生育意愿影响路径 (Bayesian network results) → 结论与建议

**Example B — Mixed Modeling (data factors & economic growth)**:
研究背景+文献 → 研究思路和模型介绍 → 理论分析 → 模型构建 (production function + regression + ARIMA, each a section) → 模型应用 (GDP prediction) → 总结与建议 → 创新与不足

**Example C — DEA Evaluation (economic sustainability)**:
绪论 → 文献综述 → 研究区域概况 → 评价指标体系构建 → 数据优化处理 (normalization + PCA) → DEA 模型建立及求解 → 结论及建议

**Example D — Deep Learning Prediction (water quality CNN)**:
绪论 → 模型构建思路与创新 → 数据描述及预处理 → 主成分分析 → CNN 模型构建与评价 (with model comparison) → 结论与展望

**Key observations**:
- No award-winning paper uses the "baseline regression → robustness → heterogeneity" causal inference structure (unless the topic IS causal inference)
- Chapter count varies from 5-7, determined by content
- "Model introduction / theoretical basis" can come before or after the data chapter
- "Innovation & limitations" can be inside the conclusion or a standalone chapter

#### Chapter design checklist (self-check before writing)

- [ ] Does every chapter title contain specific research content (not generic "模型构建")?
- [ ] Does the chapter order follow the research logic chain (reader can follow naturally)?
- [ ] Do core analysis chapters (model results) occupy 40-50% of the paper?
- [ ] Is there a dedicated data description / exploratory analysis chapter (reviewers value data understanding)?
- [ ] Does the conclusion include "innovation" and "limitations" (reviewer bonus points)?

Use Chinese numbering (一、二、三...) with sub-sections (一)(二)(三). Do not use 1、2、3 or 1.1、1.2 format.
Fixed sections that must be kept: 表格清单, 插图清单, 中英文摘要, 绪论, 结论, 参考文献, 致谢.
</paper_structure>

## ⛔⛔⛔ 完成铁律（最高优先级）

**根据 `params.output_format` 决定主产物**：

- **PDF 模式（默认）**：`paper/main.tex`（≥ 5KB）+ `paper/sections/*.tex` + `paper/references.bib`
- **docx 模式**：`paper/main.md`（单文件，≥ 5KB）。**禁止产 paper/main.tex**

⛔ **结束前必跑产出验证**：
```bash
MODE=$(grep -q "Word（.docx）" CLAUDE.md 2>/dev/null && echo docx || echo pdf)
echo "MODE: $MODE"
PASS=true
if [ "$MODE" = "docx" ]; then
    [ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
    [ "$SZ" -ge 5120 ] && echo "✅ paper/main.md ($SZ)" || { echo "❌ paper/main.md 缺失或过小"; PASS=false; }
else
    [ -f paper/main.tex ] && SZ=$(wc -c < paper/main.tex) || SZ=0
    [ "$SZ" -ge 5120 ] && echo "✅ paper/main.tex ($SZ)" || { echo "❌ paper/main.tex 缺失或过小"; PASS=false; }
    SECT_COUNT=$(ls paper/sections/*.tex 2>/dev/null | wc -l)
    [ "$SECT_COUNT" -ge 3 ] && echo "✅ sections ($SECT_COUNT)" || { echo "❌ 章节过少"; PASS=false; }
fi
[ "$PASS" != true ] && echo "⛔ 产出验证失败 — 必须补全后重新跑验证, 不要结束本步骤"
```

## Workflow

### Step 0: Backup + resume check + upstream validation

**⛔ 上游输出完整性检查（写论文前必做）：**
```bash
echo "=== 上游输出完整性检查 ==="
UPSTREAM_OK=true

# 1. 核心文件是否存在
for f in PROBLEM_ANALYSIS.md MODELING_REPORT.md RESULTS.md; do
    if [ -f "$f" ]; then
        sz=$(wc -c < "$f")
        echo "✅ $f ($sz 字符)"
        [ "$sz" -lt 500 ] && echo "  ⚠ 文件过小，内容可能不完整"
    else
        echo "❌ $f 不存在！"
        UPSTREAM_OK=false
    fi
done

# 2. 子问题覆盖度：赛题分析 vs 建模报告 vs 代码结果
PROB_COUNT=$(grep -c '问题[一二三四五六七八九十]' PROBLEM_ANALYSIS.md 2>/dev/null || echo 0)
MODEL_COUNT=$(grep -c '问题[一二三四五六七八九十]' MODELING_REPORT.md 2>/dev/null || echo 0)
RESULT_FILES=$(ls figures/problem_*_results.json 2>/dev/null | wc -l)
echo "子问题数: 分析=$PROB_COUNT, 建模=$MODEL_COUNT, 代码结果=$RESULT_FILES"
[ "$MODEL_COUNT" -lt "$PROB_COUNT" ] && echo "⚠ 建模报告覆盖子问题数少于赛题分析"
[ "$RESULT_FILES" -lt "$PROB_COUNT" ] && echo "⚠ 代码结果文件数少于子问题数"

# 3. 图表文件是否存在
PDF_COUNT=$(ls figures/*.pdf 2>/dev/null | wc -l)
echo "PDF 图表: $PDF_COUNT 个"
[ "$PDF_COUNT" -eq 0 ] && echo "⚠ 没有 PDF 图表，论文将缺少图片"

# 4. all_results.json 是否存在
[ -f figures/all_results.json ] && echo "✅ all_results.json 存在" || echo "⚠ all_results.json 不存在，论文数值可能不准确"

# 5. latex_includes.tex 是否存在
[ -f figures/latex_includes.tex ] && echo "✅ latex_includes.tex 存在" || echo "⚠ latex_includes.tex 不存在，图表嵌入代码缺失"

echo "=== 上游检查完成 ==="
```

Back up existing `paper/`. Check for incomplete sections from previous runs:
```bash
echo "=== 断点续写检查 ==="
if [ -d "paper/sections" ]; then
    for f in paper/sections/*.tex; do
        [ -f "$f" ] || continue
        chars=$(wc -c < "$f")
        if [ "$chars" -lt 500 ]; then
            echo "⚠ 占位符: $(basename $f) ($chars 字符) — 需要续写"
        else
            echo "✅ 已完成: $(basename $f) ($chars 字符)"
        fi
    done
fi
```
Resume rules: only write placeholder sections (<500 chars or contains "待补充"/"placeholder"), skip completed ones (>2000 chars). Save each chapter immediately — do not accumulate in memory.

### Step 1: Copy template (based on COMPETITION type)

```bash
mkdir -p paper/sections
# Select template based on competition type — copy entire folder (tex + cls + fonts)
TMPL_BASE="_templates"
[ -d "$TMPL_BASE" ] || TMPL_BASE="templates"

if [ "$COMPETITION" = "stats" ] || echo "$ARGUMENTS" | grep -qi "统计建模\|stats"; then
    echo "Using stats template"
    cp "$TMPL_BASE/stats/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "apmcm_zh\|亚太.*中文\|亚太赛中文" || grep -qi "apmcm_zh\|亚太.*中文\|亚太赛中文" CLAUDE.md 2>/dev/null; then
    echo "Using APMCM (Chinese) template — based on CUMCM Chinese template"
    cp "$TMPL_BASE/cumcm/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "mathorcup\|MathorCup\|mathor" || grep -qi "mathorcup" CLAUDE.md 2>/dev/null; then
    echo "Using MathorCup template"
    cp "$TMPL_BASE/mathorcup/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "huazhong\|华中杯" || grep -qi "huazhong\|华中杯" CLAUDE.md 2>/dev/null; then
    echo "Using huazhong template"
    cp "$TMPL_BASE/huazhong/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "huawei\|华为杯" || grep -qi "huawei\|华为杯" CLAUDE.md 2>/dev/null; then
    echo "Using huawei template"
    cp "$TMPL_BASE/huawei/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "wuyi\|五一杯" || grep -qi "wuyi\|五一杯" CLAUDE.md 2>/dev/null; then
    echo "Using wuyi template"
    cp "$TMPL_BASE/wuyi/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "cumcm\|国赛" || grep -qi "cumcm\|国赛" CLAUDE.md 2>/dev/null; then
    echo "Using cumcm template"
    cp "$TMPL_BASE/cumcm/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "changsanjiao\|长三角" || grep -qi "changsanjiao\|长三角" CLAUDE.md 2>/dev/null; then
    echo "Using changsanjiao template"
    cp "$TMPL_BASE/changsanjiao/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "huashu\|华数杯" || grep -qi "huashu\|华数杯" CLAUDE.md 2>/dev/null; then
    echo "Using huashubei template"
    cp "$TMPL_BASE/huashubei/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "diangong\|电工杯" || grep -qi "diangong\|电工杯" CLAUDE.md 2>/dev/null; then
    echo "Using diangongbei template"
    cp "$TMPL_BASE/diangongbei/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "dongsansheng\|东三省\|辽宁" || grep -qi "dongsansheng\|东三省\|辽宁" CLAUDE.md 2>/dev/null; then
    echo "Using dongsansheng template"
    cp "$TMPL_BASE/dongsansheng/"* paper/ 2>/dev/null
elif echo "$ARGUMENTS" | grep -qi "shuwei\|数维杯" || grep -qi "shuwei\|数维杯" CLAUDE.md 2>/dev/null; then
    echo "Using shuweibei template"
    cp "$TMPL_BASE/shuweibei/"* paper/ 2>/dev/null
else
    echo "Using default template"
    cp "$TMPL_BASE/default/"* paper/ 2>/dev/null
fi
# Rename to main.tex if needed
[ -f paper/main.tex ] && echo "Template copied: $(wc -l < paper/main.tex) lines" || echo "ERROR: template not found!"
```

**⛔ 模板复制后立即验证（必须通过才能继续）：**
```bash
echo "=== 模板完整性验证 ==="
if [ ! -f paper/main.tex ]; then
    echo "❌ CRITICAL: paper/main.tex 不存在！模板复制失败"
else
    # 通用检查
    grep -q 'documentclass' paper/main.tex && echo "✅ documentclass 存在" || echo "❌ 缺少 documentclass"
    grep -q '\\input{sections/' paper/main.tex && echo "✅ sections input 存在" || echo "❌ 缺少 sections input"
    grep -q 'thebibliography\|bibliography{' paper/main.tex && echo "✅ 参考文献结构存在" || echo "❌ 缺少参考文献"
    grep -q 'appendices\|\\appendix' paper/main.tex && echo "✅ 附录结构存在" || echo "❌ 缺少附录"

    # ⛔ 模板指纹校验：对比 paper/main.tex 和模板原文，确认是复制的不是 Claude 自己写的
    TMPL_BASE="_templates"
    [ -d "$TMPL_BASE" ] || TMPL_BASE="templates"
    # 找到当前使用的模板原文
    TMPL_MAIN=""
    for d in "$TMPL_BASE"/*/; do
        [ -f "${d}main.tex" ] || continue
        # 用 documentclass 行匹配
        TMPL_CLS=$(grep 'documentclass' "${d}main.tex" 2>/dev/null | head -1)
        PAPER_CLS=$(grep 'documentclass' paper/main.tex 2>/dev/null | head -1)
        if [ "$TMPL_CLS" = "$PAPER_CLS" ]; then
            TMPL_MAIN="${d}main.tex"
            break
        fi
    done

    if [ -n "$TMPL_MAIN" ]; then
        echo "模板原文: $TMPL_MAIN"
        # 对比前 20 行（preamble 部分），如果差异超过 5 行说明被重写了
        DIFF_COUNT=$(diff <(head -20 "$TMPL_MAIN") <(head -20 paper/main.tex) 2>/dev/null | grep -c '^[<>]')
        if [ "$DIFF_COUNT" -gt 10 ]; then
            echo "❌ CRITICAL: paper/main.tex 的 preamble 和模板差异过大（$DIFF_COUNT 行不同）— 可能被重写了！"
            echo "⛔ 强制从模板重新复制..."
            cp paper/main.tex paper/main.tex.broken 2>/dev/null
            TMPL_DIR=$(dirname "$TMPL_MAIN")
            cp "$TMPL_DIR"/* paper/ 2>/dev/null
            echo "✅ 模板已重新复制（旧文件备份为 main.tex.broken）"
        else
            echo "✅ 模板指纹校验通过（preamble 差异 $DIFF_COUNT 行，在允许范围内）"
        fi
    else
        echo "⚠ 未找到匹配的模板原文，跳过指纹校验"
    fi
fi
```

Read the copied template to understand its structure before writing:
```bash
cat paper/main.tex
```

**⛔ 你必须完整读取 main.tex 模板内容。后续写章节时，只修改 sections/*.tex 文件，不要重写 main.tex。**

Use the template as-is. Only modify:
- Replace bracket placeholders (`[论文标题]`, `[中文摘要内容]`, etc.) with actual content
- Replace `\input{sections/...}` filenames if your section files have different names
- Fill in the abstract and keywords

**⛔ CRITICAL TEMPLATE RULES (violation = broken PDF):**

1. **NEVER rewrite main.tex from scratch** — the template has 100+ lines of carefully tuned preamble (fonts, margins, section numbering, citation format). Writing from scratch will break fonts, margins, and formatting.

2. **NEVER replace `\listoftables`/`\listoffigures` with hand-written text lists** — the template uses LaTeX auto-generated lists. If you write "表1.xxx\n表2.yyy" manually, the list won't update when tables change.

3. **NEVER add a separate cover page for MathorCup** — MathorCup 官方格式没有独立封面。队伍编号表格+标题+摘要都在第一页。不要自己加 `\maketitle` 或写一个大标题封面。直接用模板里的格式：表格 → 分隔线 → 标题 → 摘要。

4. **NEVER change the cover page year/届数 format** — replace `[竞赛年份]` with the actual year (e.g., `2026`), `[届数]` with the actual number (e.g., `十二`).

5. **Verify after writing**: `diff paper/main.tex` against the template — only bracket placeholders and `\input` lines should differ.

6. **MathorCup 模板验证**：检查 main.tex 使用 `\documentclass{MathorCupmodeling}`，`\bianhao{}`/`\tihao{}`/`\timu{}` 已填写。

7. **华中杯模板验证**：检查 `\documentclass[withoutpreface,bwprint]{cumcmthesis}` 未被修改，摘要使用 `\begin{abstract}...\keywords{}\end{abstract}` 环境，参考文献使用 `\begin{thebibliography}{99}...\end{thebibliography}`，附录使用 `\begin{appendices}...\end{appendices}`，不要自己加 `\usepackage{geometry}`。

8. **五一杯模板验证**：检查承诺书页完整保留，摘要使用手动排版（`\noindent \textbf{关键词：}` 在上，`\noindent \textbf{摘\quad 要：}` 在下，不用 `\begin{abstract}` 环境），参考文献使用 `\begin{thebibliography}`，附录第一节是文件列表表格。**⛔ 五一杯额外检查**：(a) 不要加 `\usepackage{cite}`（和 natbib 冲突会导致编译错误），(b) 不要重复加载 `\usepackage{subcaption}` 和 `\usepackage{float}`（cls 已包含），(c) 不要加 `\maketitle`（五一杯用手写承诺书页，不用 cls 的 maketitle），(d) 不要删除 `withoutpreface` 选项。

The cover page uses `\fzxbsong` (方正小标宋) and `\fsgb` (仿宋GB2312) fonts with `\cline{2-2}` underlines in a tabular. These fonts have fallback definitions — if the .ttf files are not installed, they fall back to `\heiti` and `\fangsong`.

When replacing cover page placeholders, ONLY change the text inside `[...]` brackets. Do NOT touch `\cline{2-2}`, `\\`, `&`, or any LaTeX commands:
```latex
% Template has (和 cover station.tex 格式一致):
参赛学校：&[学校名称]\\\cline{2-2}
% Replace ONLY the bracket text:
参赛学校：&某某大学\\\cline{2-2}
% NEVER remove \cline{2-2} (creates underline) or & (column separator)
```

Do NOT modify:
- `\documentclass` line (font size, paper size)
- `\usepackage[...]{geometry}` (page margins)
- `\ctexset{section=...}` (chapter numbering format)
- `\pagestyle` / `\fancyhf` (header/footer)
- `\usepackage[...]{natbib}` or `\usepackage[...]{gbt7714}` (citation format)
- Cover page structure (封面布局)
- `\listoftables` / `\listoffigures` (表格与插图清单 — 自动生成，不要手写)
- Anything before `\begin{document}` (preamble)
- The cover page, abstract, TOC, and bibliography sections in main.tex — only replace placeholder text within them

Write all chapter content in separate `paper/sections/*.tex` files. The main.tex `\input{sections/...}` lines load them automatically. Do not paste chapter content directly into main.tex.

If you need to add packages, add them after the existing `\usepackage` block, before `\begin{document}`.

Do not write main.tex from scratch — the template handles fonts, spacing, margins, citation format, headers/footers.

Note: the stats template uses `natbib` with `[numbers, square, super]` format (superscript `[1]`), while the cumcm template uses `gbt7714` with superscript format. Use whichever the template provides. In body text, use `\cite{key}` — the `super` option automatically renders it as superscript.

Do not redefine LaTeX built-in commands (`\sin`, `\cos`, `\tanh`, `\log`, `\exp`, `\max`, `\min`, etc.) in math_commands.tex.

### Step 2: Abstracts

**⛔ CRITICAL: Do NOT write the abstract now.** Skip this step entirely. Write a placeholder `[摘要待正文完成后填写]` in the abstract section. The abstract MUST be written LAST (after Step 5) because it needs specific numerical results from all chapters. Writing it first = making up numbers.

Come back to fill the abstract in Step 5 (final check), after all body chapters are complete. At that point, read RESULTS.md and all section .tex files to extract the actual numbers.

<abstract_format>
The template uses manual typesetting for abstracts. Do not use two `\begin{abstract}` environments — ctexart shows "摘要" as title for both.

**⛔ 华中杯例外**：华中杯模板基于 `cumcmthesis` 文档类，使用 `\begin{abstract}...\keywords{}\end{abstract}` 环境。不要改成手动排版格式。正确写法：
```latex
\begin{abstract}
[中文摘要内容，400-600字]
\keywords{[关键词1]\quad [关键词2]\quad [关键词3]}
\end{abstract}
```

**⛔ 五一杯说明**：五一杯模板有承诺书页（第一页）和封面页（第二页）。**五一杯摘要使用手动排版（不用 `\begin{abstract}` 环境）**：关键词在上（`\noindent \textbf{关键词：}...`），摘要在下（`\noindent \textbf{摘\quad 要：}`）。这是五一杯官方格式，跟国赛/华中杯不同。承诺书页不要删除。

Correct format for cumcm/stats templates (already in template):
```latex
% === 中文摘要 ===
\begin{center}
{\zihao{3}\heiti 摘\hspace{2em}要}
\end{center}
\zihao{-4}\songti
[中文摘要内容，600-800字，写满一整页]
\noindent\textbf{关键词：}...

% === 英文摘要（新页）===
\newpage
\begin{center}
{\zihao{3}\bfseries Abstract}
\end{center}
[English abstract, 400-600 words, faithful translation]
\noindent\textbf{Keywords:} ...
```

**数模竞赛摘要**: 400-600 字, every sub-problem must have specific numerical results. **⛔ 必须按问题分段**：第1段背景概述，第2-4段分别针对问题一/二/三（方法+数值结果），第5段模型评价。每段用 LaTeX 空行分隔。五一杯虽然是手动排版摘要，分段规则同样适用。
**统计建模摘要**: 500-700 字, aim to fill most of one page but leave 3-4 lines margin at bottom — overflowing onto a second page looks worse than being slightly short. Content chain: 研究背景与意义 → 现有方法不足 → 本文方法 → 数据来源与处理 → 关键数值结果 → 应用价值与政策建议. English abstract: 350-500 words, same structure and all numerical results, also fit on one page.
</abstract_format>

### Step 3: Figure inventory + mandatory embedding plan

Before writing any chapter, build a complete inventory of available figures:

```bash
echo "=== Available PDF figures ==="
ls -la figures/*.pdf 2>/dev/null || echo "No PDF figures found"
echo ""
echo "=== Available table files (PDF模式: .tex / Word模式: .md) ==="
ls -la figures/TABLE_*.tex figures/TABLE_*.md 2>/dev/null || echo "No TABLE files found"
echo ""
echo "=== latex_includes.tex content (figure→PDF mapping) ==="
cat figures/latex_includes.tex 2>/dev/null || echo "No latex_includes.tex"
echo ""
echo "=== TikZ 几何/算法/架构图 ==="
# TikZ 由 paper-figure-drawio 生成为 figures/tikz_diagrams.tex → 编译成 figures/tikz_diagrams.pdf（多图则 tikz_*.pdf / tikz_diagrams_N.pdf）
# 它们的 \includegraphics 图块已写进 latex_includes.tex，按 latex_includes.tex 嵌入即可。
ls figures/tikz_*.pdf 2>/dev/null && echo "→ 有 TikZ 图，必须嵌入" || echo "No TikZ diagrams"
```

**⛔ MANDATORY: Build a FIGURE EMBEDDING PLAN before writing any chapter:**
```
FIGURE EMBEDDING PLAN:
1. fig_desc_stats.pdf → 第三章 描述性统计 → caption: "图X 核心变量描述性统计分布"
2. fig_model_comparison.pdf → 第四章 模型对比 → caption: "图X 模型性能对比雷达图"
3. TABLE_regression.tex(PDF模式) / TABLE_regression.md(Word模式) → 第四章 回归分析 → caption: "表X 回归分析结果"
4. tikz_diagrams.pdf (几何/算法/架构 TikZ, from latex_includes.tex) → 对应章节 → caption: "图X 弦长递推几何关系示意"
```
> 表格按输出模式选格式：PDF 模式 `\input{figures/TABLE_*.tex}`；Word/docx 模式 `cat figures/TABLE_*.md`。figures/ 里有几个 TABLE 文件就嵌入几个，一张不漏。

**Rules:**
- **⛔ 图表 caption 必须是中文**（中文论文）。如果 `latex_includes.tex` 里的 caption 是英文，嵌入时必须翻译成中文
- **⛔ 必须使用 `latex_includes.tex` 里的 figure 代码块**，不要自己写 `\includegraphics`。直接复制整个 `\begin{figure}...\end{figure}` 块，只改 caption 为中文
- **⛔ TikZ 图必须嵌入**：`latex_includes.tex` 里每个引用 `tikz_diagrams.pdf` / `tikz_*.pdf` 的 `\begin{figure}...\end{figure}` 块都要复制到对应章节，一张都不能漏
- **⛔ 图片路径必须是 `../figures/xxx.pdf`**（因为 sections/ 在 paper/ 下面）
- Only embed figures whose PDF files actually exist — do not create figure environments for PDFs that don't exist

**⛔⛔⛔ DrawIO 图嵌入规则（最容易被遗漏，必须逐条检查）：**

DrawIO 图（技术路线图、求解流程图、Pipeline 图等）的 `\begin{figure}...\end{figure}` 代码块在 `latex_includes.tex` 的**末尾部分**（由 paper-figure-drawio 步骤追加）。你必须把它们嵌入到正确的章节：

| DrawIO 图类型 | 嵌入位置 | 章节文件 |
|--------------|---------|---------|
| 技术路线图 (fig_roadmap) | 问题重述章节末尾 | `1_restatement.tex` 或 `1_introduction.tex` |
| 子问题求解流程图 (fig_flow_q1/q2/q3) | 对应子问题的"模型建立"小节开头，先写 2-3 句引导文字（概述本问题的求解思路和主要步骤），再放流程图 | `5_problem1.tex`、`6_problem2.tex` 等 |
| 数据处理 Pipeline (fig_pipeline) | 数据预处理章节 | 数据处理相关章节 |
| TikZ 几何/算法图 (tikz_diagrams.pdf) | 几何示意图→对应子问题章节开头；算法流程图→模型建立小节 | 对应子问题/模型章节 |

**写完所有章节后，必须运行以下检查确认 DrawIO/TikZ 图全部嵌入：**
```bash
echo "=== DrawIO/TikZ 嵌入检查 ==="
for pdf in figures/fig_roadmap.pdf figures/fig_flow_*.pdf figures/fig_pipeline*.pdf figures/fig_framework*.pdf; do
    [ -f "$pdf" ] || continue
    bn=$(basename "$pdf")
    if grep -rq "$bn" paper/sections/*.tex paper/main.tex 2>/dev/null; then
        echo "✅ $bn 已嵌入"
    else
        echo "❌ $bn 未嵌入 — 必须立即修复！"
    fi
done
# ⛔ TikZ 图检查（按 PDF 文件名核对，最可靠）
for tpdf in figures/tikz_diagrams.pdf figures/tikz_diagrams_*.pdf figures/tikz_*.pdf; do
    [ -f "$tpdf" ] || continue
    tbn=$(basename "$tpdf")
    if grep -rq "$tbn" paper/sections/*.tex paper/main.tex 2>/dev/null; then
        echo "✅ TikZ $tbn 已嵌入"
    else
        echo "❌ TikZ $tbn 未嵌入 — 必须立即修复！"
    fi
done
```
**如果有任何 ❌，必须立即修复后再继续写下一章。不要等到最后才修复。**

Also scan `figures/*.tex` for all `\begin{figure}` / `\begin{table}` blocks with their `\label{}`. After writing, verify all are embedded:
```bash
grep -oh '\\label{[^}]*}' figures/*.tex 2>/dev/null | sort -u > _tmp/all_fig_labels.txt
grep -oh '\\label{[^}]*}' paper/sections/*.tex paper/main.tex 2>/dev/null | sort -u > _tmp/embedded_labels.txt
comm -23 _tmp/all_fig_labels.txt _tmp/embedded_labels.txt  # should be empty
```

TikZ 图通过 `latex_includes.tex` 里的 `\includegraphics{tikz_diagrams.pdf}` 图块嵌入（不要用 `\input`）。按图的内容映射到章节：
- 技术路线图/研究框架图/问题关系图 → 问题重述章节末尾（`1_restatement.tex`），不要放到后面的子问题章节
- 各子问题求解流程图/几何示意图 → 对应子问题章节开头（`4_problem1.tex`、`5_problem2.tex`、`6_problem3.tex` 等）
- 模型架构图 → 对应模型章节

### Step 3.5: 文献预检索（写正文之前必须完成）

**⛔ 在写任何 \cite{} 之前，必须先建立已验证的文献池。**

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp
# 根据论文主题搜索真实论文，建立引用池
# 示例（根据实际选题调整）：
#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "你的核心方法关键词" --max 5
#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "你的研究领域关键词" --max 5
```

搜索后创建 `_tmp/_verified_refs.txt`，写正文时只引用池子里的论文。需要新引用时先搜索验证再加入池子。

**兜底**：如果 `scholar_fetch.py` 搜不到或 `match_label="low"`，用 WebSearch 在 Google Scholar / Semantic Scholar 网站上搜索，手动核实标题+作者+年份后再加入池子。

### Step 4: Write each chapter

**⛔ CRITICAL: ALL numerical results in the paper MUST come from `figures/*.json` or `RESULTS.md`.** Before writing any result chapter, run:
```bash
cat figures/all_results.json
cat RESULTS.md
```
Copy the exact numbers from JSON into the LaTeX text. Do NOT round differently, do NOT estimate, do NOT make up numbers that "look reasonable". If a number is not in the JSON, it cannot appear in the paper.

**⛔ 数模竞赛（cumcm/huawei/mathorcup）必须严格按模板的章节顺序写：**
```
1_restatement.tex  — 问题重述（用自己的话重述，不是抄题目）
2_assumptions.tex  — 模型假设（5-7 条，每条有内容+合理性说明）
3_symbols.tex      — 符号说明（⛔ 见下方格式规则）
4_problem1.tex     — 问题一的建模与求解
5_problem2.tex     — 问题二的建模与求解
6_problem3.tex     — 问题三的建模与求解
7_sensitivity.tex  — 灵敏度分析与模型检验
8_evaluation.tex   — 模型评价与推广
A_code.tex         — 附录：代码
```
**⛔ 模型假设必须在符号说明之前。** 不要合并成一个章节，不要调换顺序。文件名必须和模板 `\input{sections/...}` 一致。

**⛔ 模型假设数量控制**：4-5 条，不要超过 6 条。每条假设 1-2 句话（假设内容 + 合理性说明），不要写成长段落。假设太多说明问题没简化好。

**⛔ 符号说明表格控制**：15-20 个变量以内。只列正文中实际使用的核心变量，不要把所有中间变量都列进去。

**⛔ 分页规则（所有章节通用）：**
- **不要在 section 文件内部加 `\newpage`、`\clearpage` 或 `\nopagebreak`** — 让 LaTeX 自动分页，手动干预容易产生空白页
- main.tex 里只在摘要后和目录后用分页，正文章节之间不要加
- compile_utils.sh 会自动移除 section 文件里的 `\newpage`/`\clearpage`/`\nopagebreak`
- **例外**：符号说明文件（compile_utils.sh 会自动转成 longtable 支持跨页）

**⛔ 符号说明表格格式（必须用 longtable，不要用 table+tabular）：**
- 符号说明必须用 `longtable` 环境，不要用 `\begin{table}...\begin{tabular}`
- longtable 天然支持跨页，标题永远在表格开头，不会出现标题和表格分离的问题
- 不需要 `\centering`（longtable 自带居中）
- 不需要引导文字（"本文所用主要符号..."），标题直接紧跟表格
- compile_utils.sh 会自动把 table+tabular 转成 longtable（兜底），但最好从源头写对
- 正确写法：
```latex
\section{符号说明}
\begin{longtable}{clc}
\caption{主要符号说明}\label{tab:symbols} \\
\toprule
符号 & 含义 & 单位 \\
\midrule
\endfirsthead
\toprule
符号 & 含义 & 单位 \\
\midrule
\endhead
$N$ & 总数量 & 个 \\
$x_i$ & 第$i$个变量 & --- \\
... \\
\bottomrule
\end{longtable}
```
符号 & 含义 & 单位 \\
\midrule
$T(t)$ & 温度 & $^\circ$C \\
$v$ & 速度 & cm/min \\
\bottomrule
\end{tabular}
\end{table}
```
- 符号控制在 15-20 个以内，表格控制在半页以内

**⛔ 写每个章节前，先读 MODELING_REPORT.md 和 RESULTS.md 对应部分的内容。** 不要凭记忆写——数值结果、公式推导、算法步骤都必须从这些文档中提取。

Read RESULTS.md for exact numbers — ensure paper numbers match computation results.

**⛔ 图文数值一致性规则：** 描述图表内容时（如"从图X可以看出，模型A的RMSE为0.023"），数值必须从 `figures/*.json` 或 `RESULTS.md` 中读取，不要凭记忆编写。写完后用 `bash _utils/writing_check.sh paper/` 检查一致性。

**⛔ 长表格处理规则（>12 行的数据表格）：**

正文中**禁止**直接放超过 12 行的表格（调度方案、完整数据列表、逐步迭代结果等）。处理方式：

1. **正文：只放缩略版**（前 3 行 + 后 3 行 + 中间 `$\vdots$` 省略），底部注明"完整结果见附录 X"
2. **附录：放完整表格**（用 longtable 环境，允许跨页）

示例（正文缩略版）：
```latex
\begin{table}[H]
\centering
\caption{问题一调度方案（部分）}
\begin{tabular}{cccc}
\toprule
任务 & 设备 & 开始时间 & 结束时间 \\
\midrule
1 & A & 0 & 5 \\
2 & B & 2 & 8 \\
3 & A & 5 & 12 \\
\multicolumn{4}{c}{$\vdots$} \\
28 & C & 45 & 52 \\
29 & A & 48 & 55 \\
30 & B & 50 & 58 \\
\bottomrule
\end{tabular}
\label{tab:q1_schedule_short}
\footnotesize 注：完整调度方案（30 条记录）见附录 B。
\end{table}
```

**判断标准：** 如果 `figures/TABLE_*.tex` 文件超过 12 行数据行，必须自动生成缩略版 + 附录完整版。不要把 100+ 行的 longtable 直接嵌入正文章节。

Follow the interleaving, embedding, and LaTeX rules from `_utils/writing_rules.md`.

**⛔ 图文并茂硬规则（每个章节都必须遵守）：**
- 所有 `\begin{figure}` 必须用 `[H]`，不要用 `[htbp]`
- 每张图/表后面必须有 ≥5 行分析文字（数值解读+对比+结论），然后才能放下一张图
- 绝对禁止两张图连续出现中间没有分析段落
- 图片用 `\includegraphics[width=0.85\textwidth,height=0.38\textheight,keepaspectratio]`
- **⛔ 禁止使用 subfigure/subcaption 并排图片。** 每张图必须独占一个 `\begin{figure}[H]...\end{figure}` 环境，宽度 ≥ `0.85\textwidth`。不要用 `\begin{subfigure}{0.48\textwidth}` 把两张图缩成半页宽——这会导致图片太小看不清。如果确实需要对比两张图，分成两个独立的 figure 环境，中间加 2-3 句过渡分析文字
- **⛔ 图片宽度下限：** `width` 参数不得小于 `0.8\textwidth`。任何 `width=0.5\textwidth`、`width=0.48\textwidth`、`width=0.45\textwidth` 都是错误的，必须改为 `0.85\textwidth` 或 `0.9\textwidth`

**⛔ 超长表格处理规则（>15 行的结果表格必须遵守）：**

如果某个结果表格超过 15 行数据（如调度方案、路径规划、逐日预测值等），**不要把完整表格放在正文里**——会占好几页，挤压正文空间。正确做法：

1. **正文放摘要表**：只展示前 5 行 + 后 3 行 + 汇总统计（均值/最优/总计），caption 标注"（部分，完整结果见附录表 X）"
2. **附录放完整表**：在 `sections/A_code.tex`（或新建 `sections/A_tables.tex`）里放完整表格

```latex
% === 正文中的摘要表 ===
\begin{table}[H]
\centering
\caption{问题一调度方案（部分，完整结果见附录表\ref{tab:full_schedule}）}
\begin{tabular}{cccc}
\toprule
车间 & 设备 & 开始时间 & 结束时间 \\
\midrule
1 & A-1 & 0 & 1200 \\
1 & A-2 & 1200 & 2400 \\
\multicolumn{4}{c}{$\vdots$} \\
3 & C-4 & 8400 & 9600 \\
3 & C-5 & 9600 & 10800 \\
\midrule
\multicolumn{2}{c}{总计} & \multicolumn{2}{c}{Makespan = 10800s} \\
\bottomrule
\end{tabular}
\end{table}

% === 附录中的完整表 ===
% 在 A_code.tex 或 A_tables.tex 中：
\section{完整结果表格}
\begin{table}[H]
\centering
\caption{问题一完整调度方案}\label{tab:full_schedule}
\begin{longtable}{cccc}
% ... 完整数据 ...
\end{longtable}
\end{table}
```

**判断标准：** 写表格前先数数据行数。≤15 行直接放正文，>15 行用摘要+附录方案。compile_utils.sh 也会自动检测并截断超长表格，但最好在写的时候就处理好。

After each chapter, check character count:
```bash
chars=$(wc -c < "paper/sections/当前章节.tex")
echo "当前章节: $chars 字符 (~$(echo "scale=1; $chars/900" | bc) 页)"
# Chinese LaTeX ≈ 800-1000 chars per page
# If chapter expected 5 pages but only 2000 chars (~2.5 pages), expand immediately
```

<exemplar_depth>
#### Writing depth reference

**国赛一等奖 (25-30 pages, 3 sub-problems)**:
- 问题重述+分析 (2-3p): restate in own words, extract core problems — not copying the problem statement
- 模型假设+符号说明 (2p): 5-7 assumptions (each with content + justification, not too many not too few), one complete symbol table with 15-25 variables (符号/含义/单位 three columns, do not split into multiple tables)
- Each sub-problem (5-7p): model formulation (2p, with derivation and physical meaning) + solution method (1.5p, with algorithm steps) + results with table+figure (1p) + analysis (0.5-1.5p, numerical meaning + comparison with expectations + reasoning)
- 灵敏度分析 (2-3p): ≥2 key parameters, each with variation curve plot + analysis paragraph
- 模型评价 (2p): 3-4 strengths + 2-3 weaknesses + generalization directions. Pure text discussion, no figures or tables needed

**华为杯一等奖 (40-50 pages)**: deeper derivations, more thorough analysis per sub-problem (8-10p each), 灵敏度分析 (4-5p), 模型评价 (3p, pure text, no figures) with comparison to other methods

**统计建模获奖 (35-40 pages)** — chapter structure is content-driven, page allocation reference:

- 绪论/前言 (4-8p): research background + literature review (grouped by 3-4 themes, 3-5 papers per theme with detailed discussion) + research objectives
- 数据描述与预处理 (6-8p): data source + variable description table + descriptive statistics table + exploratory analysis (distribution / trend / cross-tabulation plots)
- 模型/方法 chapters (6-10p): theoretical basis + formula derivation + parameter settings + implementation details (adjust by actual number of models)
- Core results analysis (10-16p): the most important part of the paper — every result needs 2-3 paragraphs of interpretation, not just "as shown in Table X"
- 结论与建议 (3-5p): conclusions + recommendations + innovation points + limitations and future work

Common traits of award-winning papers:
- Solid exploratory analysis (cross-tabulation, group comparisons, rich visualization)
- Core analysis chapters occupy 40-50% of total pages, every numerical result has deep interpretation
- Specific chapter titles ("基于集成学习的生育意愿影响因素分析" not "模型构建")
- Include "innovation & limitations" discussion (reviewer bonus points)

| Type | Pages | Characters | References |
|------|-------|-----------|------------|
| 数模国赛 (30p limit) | 25-30 | 18000-25000 | ≥10 |
| 华为杯 | 40-50 | 30000-40000 | ≥15 |
| MathorCup | 35-40 | 25000-35000 | ≥10 |
| 华中杯 | 25-30 | 18000-25000 | ≥10 |
| 五一杯 | 25-30 | 18000-25000 | ≥10 |
| 统计建模 | 35-40 | 25000-35000 | ≥20 |
</exemplar_depth>

<figure_usage_principles>
#### Figure/table usage by competition type

**统计建模**: Figures first, tables second. Figure/table selection is driven by the actual analysis methods used — regression uses forest plots + regression tables, prediction uses prediction comparison plots + accuracy tables, classification uses confusion matrices + ROC, evaluation uses radar charts + ranking tables. Every analysis step should have a corresponding figure or table.

**数模竞赛**: "字不如表，表不如图". Every sub-problem must have independent result display (table + figure). Comprehensive comparison figures are additional supplements. Reviewers value information density and aesthetics.

Do not force figures where they are not needed (pure literature review, theoretical derivation). Claude decides figure count and placement based on content needs.
</figure_usage_principles>

<stats_figure_placement>
#### Stats modeling paper figure placement rules

Figure/table selection is driven by research content, not fixed type templates. Below are figures mapped to analysis methods:

**Data description stage** (almost all papers need these):
- Descriptive statistics table (required), data distribution plots / boxplots, correlation heatmap, time series trend plots

**Model results stage** (select based on actual methods used):
- Regression: regression result table + coefficient forest plot
- Prediction: prediction comparison plot (actual vs predicted) + model accuracy table (MAE/RMSE/R²) + error distribution plot
- Classification: confusion matrix + ROC curve + model comparison table (Accuracy/F1/AUC)
- Clustering: cluster scatter plot / t-SNE + silhouette score table
- Evaluation: comprehensive score ranking table + radar chart
- Causal inference: baseline regression table + robustness check table + heterogeneity comparison plot

**Model interpretation / diagnostics stage** (select as needed):
- Feature importance / SHAP plot, residual diagnostics, sensitivity analysis plot, ablation table

**Principle**: Core result figures/tables go in the body text. Appendix only for code and very long auxiliary tables.
</stats_figure_placement>

<chapter_writing_points>
#### Chapter writing points (universal, adapt to research logic)

**⛔ 写作风格铁律（所有章节都必须遵守）：**
- **禁止在正文中使用 `\begin{itemize}` 或 `\begin{enumerate}` 列表。** 黑点/编号列表是最明显的 AI 写作痕迹。必须用连贯的段落叙述。
  - 需要列举时用行内编号："（1）...（2）...（3）..."或"首先...其次...最后..."
  - 例外：模型假设列表（可用编号）、附录
- **每段至少 3-5 句话。** 不要写只有 1-2 句的短段落。
- **连续段落不能以相同句式开头。** 如连续三段都以"本文..."开头，必须改。
- **图表是论据不是主语。** 段落不能以"图X展示了"、"如图X所示"、"由图X可知"开头。图表引用用括号旁注 `（图X）` 融入论证链条：先论点 → 图表作旁证 → 推论。详见 `_utils/writing_rules.md` 的"图表是论据"规则。
- **禁止元叙述和内部指令泄露。** 正文中不能出现"参赛者"、"参赛队伍"、"RESULTS.md"、"figures/*.json"、"CLAUDE.md"等内部文件名或工作流术语。用"本文"代替"我们团队"，论文是独立学术文档。

**绪论/前言** (all papers):
- Research background (why this problem matters) → Literature review / research status (what others did, what gaps remain) → Research objectives / content / contributions → Paper structure overview
- Literature review organized by theme (≥15 citations), not chronologically listed

**数据与预处理** (almost all papers need this):
- Data source → Sample description (time range / sample size / variable count) → Variable definition / coding table → Missing value / outlier handling → Exploratory analysis (distribution plots / trend plots / cross-tabulation)
- Exploratory analysis is a key capability demonstration for reviewers — do not skip

**模型/方法 chapters** (organize by actual research content):
- Each model/method: theoretical basis (1-2 paragraphs) → mathematical formulas → parameter setting rationale → implementation details
- Multiple models: can introduce all models first then show results (Example B style), or give each model its own chapter with results (Example A style)

**结果分析 chapters** (core, should occupy 40-50% of paper):
- Every result must have: numerical presentation (table/figure) → interpretation (2-3 paragraphs, not just "as shown in Table X") → comparison with expectations / other methods → reasoning
- Multi-model comparison: horizontal comparison table + rationale for selecting the best model

**结论与建议**:
- Main conclusions (echo research objectives) → Policy / application recommendations (specific and actionable) → Innovation points → Limitations and future work
- "Innovation & limitations" can be inside the conclusion or a standalone chapter (Example B style)
</chapter_writing_points>

**Expansion strategies** when content is thin (not padding — substantive content):
- Formula listed without derivation → add step-by-step derivation with physical meaning explanation
- Result with only "如表所示" → add 2-3 paragraphs of interpretation (numerical meaning, comparison with expectations, reasoning, comparison with other methods)
- Assumptions as bare list → add justification for each assumption
- Algorithm as pseudocode only → add explanation of key steps, complexity analysis, convergence discussion
- Literature review only lists papers → add method summary for each and connection to this work

### Step 5: References

Follow the `<references_workflow>` in `_utils/writing_rules.md`.
Stats papers: ≥20 references. The stats template uses `natbib` with `[numbers, square, super]` — use `\cite{key}` in body text (auto-superscript) + `\bibliography{references}` + `\bibliographystyle{plainnat}`. The cumcm template uses `gbt7714` — only need `\bibliography{references}`. The huazhong template uses `\begin{thebibliography}{99}...\end{thebibliography}` — manually add `\bibitem` entries (do not use `\bibliography{}`). The wuyi template uses `gbt7714-numerical` — use `\bibliography{references}` (same as cumcm).

**⛔ 使用 scholar_fetch.py 工具获取所有参考文献的 BibTeX。禁止凭记忆编造 BibTeX。**

**⛔ 引用编号必须按正文出现顺序排列（1, 2, 3, 4...），不能跳着来。** 使用 `\begin{thebibliography}` 的模板：`\bibitem` 的排列顺序必须跟正文中 `\cite{}` 首次出现的顺序一致。使用 `\bibliography{references}` 的模板：BibTeX 会自动按引用顺序编号（gbt7714-numerical / plainnat 都支持）。写完所有章节后，检查引用编号是否连续递增，如果不是，调整 `\bibitem` 顺序或 `.bib` 文件中的条目顺序。

**⛔⛔ 正文中引用编号必须全局递增出现（严格，不可违反）：**

写正文时每个引用编号必须比之前所有已出现的编号大（即首次引用必须按 [1], [2], [3], [4]... 顺序）：
- ✅ 正确：全文第一个引用 [1]，第二个 [2]，第三个 [3]...
- ❌ 错误：正文中先出现 [3]，然后出现 [8]，又回到 [1] — 引用编号跳跃
- ❌ 错误：前文已出现 [5]，后文再出现新引用为 [3] — 编号回退

**如何保证递增：**
- 所有引用的 key 在 .bib 文件或 thebibliography 环境中的排列顺序 = 它们在正文中首次出现的顺序
- 如果写作时发现某处需要一个新引用，它的编号会自动是当前已用编号的最大值+1
- 写完所有章节后，逐段扫描正文，确认引用编号 [N] 严格递增（只允许重复已出现的编号）

**⛔ 引用格式规则（中文竞赛论文必须上标）：**
- 必须用上标引用样式：`\bibliographystyle{gbt7714-numerical}` 或 natbib 的 `super` 选项
- 如果模板用的是 `plain/plainnat/unsrt`（非上标），正文中必须用 `\upcite{}` 或 `\textsuperscript{\cite{}}` 而不是 `\cite{}`
- 禁止：非上标样式 + 直接 `\cite{}` → 引用会显示为 `[1]` 而非上标 `¹`

**⛔ 多引用合并规则（合并必须按编号升序）：**

同一处引用多篇文献时：
- ✅ 正确：`方法A\cite{a,b,c}` — 一个 \cite 命令，多个 key 用逗号分隔，**且 a,b,c 对应的编号必须升序**（如 [1,2,5]）
- ✅ 正确：`方法A\cite{a}\cite{b}` — 如果 a,b 编号不相邻（如 [3] 和 [7]），也可以分开写
- ❌ 错误：`方法A\cite{a}\cite{b}\cite{c}` — 多个连续 \cite 且编号相邻，必须合并成 `\cite{a,b,c}`
- ❌ 错误：`方法A\cite{c,a,b}` — 编号顺序错乱（如 [5,1,2]），必须改成 `\cite{a,b,c}`（[1,2,5]）
- ❌ 错误：`方法A\cite{a,b}` 但 a=[3]、b=[1] — 编号降序，必须改成 `\cite{b,a}`（[1,3]）

**合并的判定规则（严格）：**
1. 多引用里的 key 必须按其编号升序排列 → 如 [1,2,5] 对应 `\cite{key_of_1, key_of_2, key_of_5}`
2. 如果两个引用编号不相邻（中间差 > 1），建议合并为一个 `\cite{}` 保持整洁
3. 如果不能保证升序，**宁愿分开写** `\cite{a}\cite{b}` 也不要错序合并
4. 写作时难以预知最终编号，可先按 key 的出现逻辑合并，编译后用 compile_check.sh 检查并调整

**⛔ 引用写法规则：写正文时，citation key 必须包含描述性关键词，格式为 `作者姓_年份_主题关键词`。**
例如：`\cite{wang_2023_supply_chain_resilience}` 而不是 `\cite{wang2023supply}`。
不确定作者/年份时用 `TODO__` 前缀：`\cite{TODO__digital_economy_spatial_spillover}`。

```bash
# Step 5a: 收集所有引用 key
grep -roh '\\cite[tp]*{[^}]*}' paper/sections/*.tex paper/main.tex 2>/dev/null \
  | grep -oP '\{[^}]+\}' | tr -d '{}' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u > _tmp/_cited_keys.txt
echo "引用 key 数量: $(wc -l < _tmp/_cited_keys.txt)"

# Step 5b: 逐个搜索并获取 BibTeX（用描述性关键词搜索）
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
while IFS= read -r key; do
    query=$(echo "$key" | sed 's/^TODO__//; s/_/ /g')
    echo "--- 获取: $key (搜索: $query) ---"
    $PYTHON "$SCHOLAR_SCRIPT" bibtex "$query" --max 3
    sleep 0.5
done < _tmp/_cited_keys.txt
```

处理每个搜索结果：
1. 检查 `match_label`：`"good"` → 直接使用。`"partial"` → 核实标题。`"low"` → 很可能搜错了，换关键词或用 WebSearch。
2. `match_score` < 0.3 说明大概率不是目标论文，不要盲目使用。
3. 将 .tex 中的 citation key 替换为 BibTeX 条目中的实际 key。
4. `bibtex_source=auto` 的条目加 `% [VERIFY]`。`match_label="low"` 的加 `% [LOW_MATCH]`。

### Step 5.5: De-AI polish

See `<de_ai_polish>` in `_utils/writing_rules.md`.

### Step 5.6: Write abstract NOW (after all chapters are complete)

**⛔ MANDATORY: NOW write the abstract.** Read RESULTS.md and all section .tex files. Extract the actual numerical results from each sub-problem. The abstract must contain ONLY numbers that appear in the body text — do NOT invent or round differently.

**⛔ 统计建模必须写中英文两个摘要**：先写中文摘要（500-700字），然后将中文摘要忠实翻译为英文摘要（350-500 words），所有数值结果、方法名称、结论必须一一对应。数模竞赛（国赛/五一杯/MathorCup/华中杯等）只写中文摘要。

For math modeling competitions: each sub-problem must have its specific result in the abstract (e.g., "问题一采用XX算法，最优解为YY，空间利用率达ZZ%")。

Read `_utils/writing_rules.md` for abstract format rules (分段、首行缩进、长度).

### Step 6: Final verification

```bash
bash _utils/writing_check.sh paper/ 2>/dev/null || bash skills/shared-scripts/writing_check.sh paper/
```

Also check:
```bash
source .env_skill 2>/dev/null || true  # 加载 MAX_PAGES 等数值参数
echo "=== 各章节字符数 ==="
total=0
for f in paper/sections/*.tex; do
    chars=$(wc -c < "$f")
    total=$((total + chars))
    echo "  $(basename $f): $chars 字符 (~$(echo "scale=1; $chars/900" | bc) 页)"
done
echo "  总计: $total 字符 (~$(echo "scale=1; $total/900" | bc) 页)"
echo "  目标: ≥ MAX_PAGES × 800 = $((MAX_PAGES * 800)) 字符"
```
- Total chars ≥ MAX_PAGES × 800 (expand thinnest chapters if not)
- Any sub-problem chapter <3500 chars (~4 pages) needs expansion
- All figures/*.pdf and TABLE files (PDF模式 .tex / Word模式 .md) referenced in sections/正文
- No template bracket placeholders remaining (`[论文标题]`, `[中文摘要内容]`, etc.)

**⛔ Constraint consistency check (MUST do before finishing):**
Read PROBLEM_ANALYSIS.md (or the original problem statement in user_data/) and check every numerical result in the paper against the problem's constraints:
```
=== 论文-题目约束一致性检查 ===
1. 读取题目中的所有约束条件（容量、预算、时间窗、数量限制等）
2. 逐个检查论文正文中的结果是否满足这些约束
3. 例如：题目说"车辆载重上限 6000kg"，论文写"装载 7344kg" → 矛盾，必须修正
4. 例如：题目说"30 个省份"，论文分析了 28 个 → 不完整，必须补充
5. 摘要中的数字是否与正文一致？
6. 不同章节引用同一个结果时数字是否一致？（如问题一的最优解在摘要、正文、结论中出现 3 次，必须完全相同）
```
如果发现矛盾，修改论文正文（不是修改约束）。如果是代码结果本身违反约束，说明代码有 bug，需要回到 comp-code 修复。

**⛔ Page count pre-check (MUST pass before finishing — do NOT leave this to compile step):**
```bash
source .env_skill 2>/dev/null || true  # 加载 MAX_PAGES 等数值参数
echo "=== 页数预检 ==="
total_chars=0
for f in paper/sections/*.tex; do
    [ -f "$f" ] || continue
    chars=$(wc -c < "$f")
    total_chars=$((total_chars + chars))
done
est_pages=$((total_chars / 900))
echo "总字符: $total_chars, 估算页数: ~$est_pages 页, 目标: ≥ ${MAX_PAGES:-30} 页"
if [ -n "$MAX_PAGES" ] && [ "$est_pages" -lt "$((MAX_PAGES * 80 / 100))" ]; then
    echo "⛔ CRITICAL: 页数严重不足 ($est_pages < 80% of $MAX_PAGES)"
    echo "必须扩充最薄的章节后再结束"
fi
```
If estimated pages < 80% of MAX_PAGES, you MUST expand the thinnest 2-3 chapters before finishing. Read MODELING_REPORT.md and RESULTS.md for additional content to add (more derivation, more result analysis, more parameter discussion).

**Figure embedding verification (must pass before finishing)**:
```bash
echo "=== 图表嵌入检查 ==="
missing=0
for pdf in figures/*.pdf; do
    [ -f "$pdf" ] || continue
    bn=$(basename "$pdf")
    if ! grep -rq "$bn" paper/sections/*.tex paper/main.tex 2>/dev/null; then
        echo "MISSING: $bn 未嵌入任何章节"
        missing=$((missing + 1))
    fi
done
for fig_tex in figures/*.tex; do
    [ -f "$fig_tex" ] || continue
    for lbl in $(grep -oh '\\label{[^}]*}' "$fig_tex" 2>/dev/null); do
        if ! grep -rq "$lbl" paper/sections/*.tex paper/main.tex 2>/dev/null; then
            echo "MISSING: $lbl (from $(basename $fig_tex)) 未嵌入"
            missing=$((missing + 1))
        fi
    done
done
echo "缺失: $missing"
```
If any figures are missing, go back and embed them into the appropriate sections before finishing. **⛔ Do NOT proceed to Step 7 until missing = 0.** Repeat the check after each fix.

**⛔ 模板完整性自检（写完所有章节后必须检查 main.tex 没有被破坏）：**
```bash
echo "=== main.tex 模板完整性检查 ==="
TMPL_OK=0
TMPL_FAIL=0

# 通用检查（所有模板）
grep -q 'documentclass' paper/main.tex && { echo "✅ documentclass"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少 documentclass"; TMPL_FAIL=$((TMPL_FAIL+1)); }
grep -q '\\input{sections/' paper/main.tex && { echo "✅ sections input"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少 sections input"; TMPL_FAIL=$((TMPL_FAIL+1)); }
grep -q 'thebibliography\|bibliography{' paper/main.tex && { echo "✅ 参考文献"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少参考文献"; TMPL_FAIL=$((TMPL_FAIL+1)); }
grep -q 'appendices\|\\\\appendix' paper/main.tex && { echo "✅ 附录"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少附录"; TMPL_FAIL=$((TMPL_FAIL+1)); }
grep -q 'superscript\|\\@cite\|setcitestyle.*super' paper/main.tex && { echo "✅ 上标引用"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少上标引用定义"; TMPL_FAIL=$((TMPL_FAIL+1)); }

# 五一杯特有检查
if grep -qi 'wuyi\|五一杯' CLAUDE.md 2>/dev/null; then
    grep -q '承诺书' paper/main.tex && { echo "✅ 五一杯承诺书页"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 五一杯缺少承诺书页"; TMPL_FAIL=$((TMPL_FAIL+1)); }
    grep -q 'image2' paper/main.tex && { echo "✅ 五一杯封面logo"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 五一杯缺少封面logo"; TMPL_FAIL=$((TMPL_FAIL+1)); }
    grep -q '关键词' paper/main.tex && { echo "✅ 五一杯关键词"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 五一杯缺少关键词"; TMPL_FAIL=$((TMPL_FAIL+1)); }
fi

# MathorCup 特有检查
if grep -qi 'mathorcup' CLAUDE.md 2>/dev/null; then
    grep -q 'MathorCupmodeling' paper/main.tex && { echo "✅ MathorCup cls"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ MathorCup 未使用正确 cls"; TMPL_FAIL=$((TMPL_FAIL+1)); }
    grep -q '\\bianhao\|\\tihao\|\\timu' paper/main.tex && { echo "✅ MathorCup 队伍信息"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ MathorCup 缺少队伍信息"; TMPL_FAIL=$((TMPL_FAIL+1)); }
fi

# 华中杯特有检查
if grep -qi 'huazhong\|华中杯' CLAUDE.md 2>/dev/null; then
    grep -q 'cumcmthesis' paper/main.tex && { echo "✅ 华中杯 cls"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 华中杯未使用 cumcmthesis"; TMPL_FAIL=$((TMPL_FAIL+1)); }
fi

echo ""
echo "模板检查: $TMPL_OK 通过, $TMPL_FAIL 失败"
[ "$TMPL_FAIL" -gt 0 ] && echo "⛔ 必须修复所有失败项！可能是 main.tex 被意外重写了，请从模板重新复制并只替换占位符。"
```

### Step 7: Output

数模竞赛: sections/ numbered by sub-problem (4_problem1.tex, 5_problem2.tex...)
统计建模: sections/ by academic structure (1_introduction.tex, 2_data_method.tex...)

## Key Rules

- Use templates from `templates/`, do not write main.tex from scratch
- Chinese/English abstracts: manual typesetting, not two `\begin{abstract}` environments
- Citation format: use whichever the template provides (stats: natbib `[1]`, cumcm: gbt7714 superscript, huazhong: thebibliography manual entries, wuyi: gbt7714-numerical)
- No `\hypersetup{colorlinks=true}` — conflicts with hidelinks
- Body pages ≥ MAX_PAGES (can exceed, must not fall short)
- No team info — use placeholders
- Tables: three-line style (booktabs)
- Primary output: `paper/` directory, temp files: `_tmp/`
- ⛔ **本步骤只写论文 .tex 文件，不要重新生成图表 PDF、不要修改 code/*.py、不要重新运行分析代码。** 图表和数据已由前序步骤（paper-figure / comp-code）生成完毕，直接引用即可
- Large files: Bash heredoc
- ⛔ **Bash heredoc 必须用带引号的 `'EOF'`（防止 `\\` 被转义）：**
  - ✅ 正确：`cat << 'EOF' > paper/sections/4_problem1.tex`（引号内 `\\` 原样保留）
  - ❌ 错误：`cat << EOF > paper/sections/4_problem1.tex`（无引号，`\\` 变成 `\`，导致表格 `Misplaced \noalign` 错误）
  - 这是表格编译失败的最常见原因——40+ 处 `\\` 全部变成 `\`，编译器只报第一个错就停了
