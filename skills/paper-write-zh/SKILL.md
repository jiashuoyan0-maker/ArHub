---
name: paper-write-zh
description: "Draft a Chinese academic paper in LaTeX using XeLaTeX + ctex. Use when user says \"写中文论文\", \"中文LaTeX\", \"Chinese paper writing\", or wants to generate Chinese LaTeX content."
argument-hint: [topic]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Chinese Paper LaTeX Writing

Draft a Chinese LaTeX paper section by section: **$ARGUMENTS**

## Constants

- **PAPER_TYPE** — `bachelor`/`master`/`journal`. Default `journal`.
- **MAX_PAGES** — bachelor=25, master=55, journal=15. Body pages must be ≥ MAX_PAGES.
- **CUSTOM_REQUIREMENTS** — Highest priority.
- **REVIEWER_SCRIPT** — External reviewer script `reviewer_client.py`

## Inputs

1. **PAPER_PLAN.md** — outline with data analysis summary
2. **NARRATIVE_REPORT.md** — research narrative
3. **figures/** — PDFs + `latex_includes*.tex` + `tikz_diagrams.tex`（TikZ，编译为 `tikz_diagrams.pdf`）
4. **user_data/** — user materials (.cls/.docx templates, data files)

If `user_data/` has CSV/JSON, read exact values with pandas before writing experiment chapters.

## Load shared rules

```bash
cat _utils/writing_rules.md 2>/dev/null || cat skills/shared-scripts/writing_rules.md
```

## Template selection

Priority: user `.cls` > user `.docx` > built-in template

Built-in templates in `templates/`:
- `bachelor_main.tex` — 本科毕业论文 (ctexart)
- `master_main.tex` — 硕士学位论文 (ctexbook)
- `journal_main.tex` — 期刊论文 (ctexart, two-column)

Copy template to `paper/main.tex`, replace all bracket placeholders with actual content.
Template handles fonts, spacing, margins, gbt7714, headers/footers — do not write main.tex from scratch.

**⛔ CRITICAL TEMPLATE RULES:**
1. **NEVER rewrite main.tex from scratch** — the template has carefully tuned preamble
2. **NEVER replace `\listoftables`/`\listoffigures` with hand-written text** — use auto-generated lists
3. Only replace bracket placeholders (`[论文标题]`, `[作者]`, etc.) with actual content
4. Only modify `\input{sections/...}` lines to match actual section filenames

<abstract_format>
### Abstract format

The template uses manual typesetting for abstracts (`\begin{center}{\heiti 摘要}\end{center}` + `\begin{center}{\bfseries Abstract}\end{center}`). Do not use two `\begin{abstract}` environments — ctexart's abstract title is fixed as "摘要", so the English abstract would also show a Chinese title.

Chinese abstract: 500-700 characters. Aim to fill most of one page but leave 3-4 lines margin at the bottom — overflowing onto a second page looks worse than being slightly short. Content chain: 研究背景与意义 → 现有方法不足 → 本文方法 → 数据来源与处理 → 关键数值结果（精度、R²、p值等）→ 应用价值与建议.

English abstract: 350-500 words, faithful translation covering the same structure and all numerical results. Same principle — fit on one page, do not overflow.
</abstract_format>

## ⛔⛔⛔ 完成铁律（最高优先级，违反则本步骤失败）

**根据 `params.output_format` 决定主产物路径**：

- **PDF 模式（默认）**：必须产出 `paper/main.tex`（基于模板，≥ 5KB）+ `paper/sections/*.tex`（每章节 ≥ 500 字符）+ `paper/references.bib`
- **docx 模式（用户选 Word 输出）**：必须产出 `paper/main.md`（**单文件**，含完整论文，≥ 5KB）。**禁止产 paper/main.tex**

⛔ **如何识别当前模式**：
```bash
grep -q "Word（.docx）" CLAUDE.md && echo "MODE=docx" || echo "MODE=pdf"
```

⛔ **结束前必跑产出验证**（步骤的最后一步，绝不省略）：
```bash
echo "=== 产出验证（必须全部 ✅）==="
MODE=$(grep -q "Word（.docx）" CLAUDE.md 2>/dev/null && echo docx || echo pdf)
echo "MODE: $MODE"
PASS=true
if [ "$MODE" = "docx" ]; then
    [ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
    if [ "$SZ" -ge 5120 ]; then echo "✅ paper/main.md ($SZ bytes)"; else echo "❌ paper/main.md 缺失或过小 ($SZ bytes)"; PASS=false; fi
else
    [ -f paper/main.tex ] && SZ=$(wc -c < paper/main.tex) || SZ=0
    if [ "$SZ" -ge 5120 ]; then echo "✅ paper/main.tex ($SZ bytes)"; else echo "❌ paper/main.tex 缺失或过小 ($SZ bytes)"; PASS=false; fi
    SECT_COUNT=$(ls paper/sections/*.tex 2>/dev/null | wc -l)
    if [ "$SECT_COUNT" -ge 3 ]; then echo "✅ paper/sections/*.tex ($SECT_COUNT 个章节)"; else echo "❌ paper/sections/ 章节过少 ($SECT_COUNT)"; PASS=false; fi
fi
[ "$PASS" != true ] && echo "⛔ 产出验证失败 — 必须补全后重新跑验证, 不要结束本步骤"
```

**如果验证失败,继续补全产出而不是退出**。

## Workflow

### Step 0: Backup + resume check + 上游验证

**⛔ 上游输出完整性检查（写论文前必做）：**
```bash
echo "=== 上游输出完整性检查 ==="
UPSTREAM_OK=true

# 1. 核心文件是否存在
for f in PAPER_PLAN.md RESULTS.md; do
    if [ -f "$f" ]; then
        sz=$(wc -c < "$f")
        echo "✅ $f ($sz 字符)"
        [ "$sz" -lt 500 ] && { echo "  ⚠ 文件过小，内容可能不完整"; UPSTREAM_OK=false; }
    else
        echo "⚠ $f 不存在（将使用最小大纲兜底）"
    fi
done

# 2. 实验数据文件
[ -f figures/all_results.json ] && echo "✅ figures/all_results.json" || echo "⚠ 无 all_results.json，数值可能不准确"
[ -f experiment_results.md ] && echo "✅ experiment_results.md" || echo "  （无 experiment_results.md，将依赖 RESULTS.md）"

# 3. 图表文件
PDF_COUNT=$(ls figures/*.pdf 2>/dev/null | wc -l)
echo "PDF 图表: $PDF_COUNT 张"
[ "$PDF_COUNT" -eq 0 ] && echo "⚠ 无 PDF 图表，论文将缺少图片"

# 4. latex_includes.tex
[ -f figures/latex_includes.tex ] && echo "✅ figures/latex_includes.tex" || echo "⚠ 无 latex_includes.tex，图表嵌入代码缺失"

echo "=== 上游检查完成 ==="
$UPSTREAM_OK || echo "⚠ 部分上游文件不完整，继续执行但结果可能欠佳"
```

Back up existing `paper/` to `paper-backup-{timestamp}/`. Check for incomplete sections:
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
Resume: only write placeholder sections (<500 chars or contains "待补充"/"placeholder"), skip completed ones (>2000 chars). See `<resume_strategy>` in writing_rules.md for full details.

**⛔ 数值来源规则（全文遵守）：**
所有论文中的数值（精度、RMSE、R²、p-value、系数、训练时间等）必须来自 `figures/all_results.json` 或 `RESULTS.md`。写任何含数值的章节之前先：
```bash
[ -f figures/all_results.json ] && cat figures/all_results.json
[ -f RESULTS.md ] && cat RESULTS.md
```
从中复制数字原样填入论文。不要凭记忆估算、四舍五入或编造数值。最终的 quality gate 会做数值一致性检查，编造的数字会被发现。

**⛔ Claims-Evidence 对照（必须严格遵循规划）：**

写每个章节前，先重读 PAPER_PLAN.md 中的 claims-evidence 矩阵：
```bash
grep -A 100 'Claims-Evidence\|claim.*evidence\|claim-evidence\|观点.*证据' PAPER_PLAN.md 2>/dev/null | head -30
```

写作纪律：
- 论文中的每个论断必须对应到规划中的某一行
- 不要添加规划外的新论断（如有新发现，先更新 PAPER_PLAN.md）
- 不要跳过规划中的论断（即使是负面结果也要如实报告）
- 每个论断的数值证据必须与 `figures/all_results.json` 一致

如果某个规划中的论断在数据中找不到证据，诚实写"初步结果提示 X，更严谨的验证留待未来工作"，不要编造证据。

### Step 1: Initialize

Create `paper/`, copy template to `main.tex`, generate `math_commands.tex` (paper-specific commands only — do not redefine `\sin`, `\cos`, `\log`, etc.).

### Step 2: Figure inventory

Before writing any section, build a complete inventory of available figures. This prevents empty figure environments (caption without image).

```bash
echo "=== Available PDF figures ==="
ls -la figures/*.pdf 2>/dev/null || echo "No PDF figures found"
echo ""
echo "=== Available table files (PDF模式: .tex / Word模式: .md) ==="
ls -la figures/TABLE_*.tex figures/TABLE_*.md 2>/dev/null || echo "No TABLE files found"
echo ""
echo "=== TikZ 几何/算法/架构图 ==="
# TikZ 图由 paper-figure-drawio 生成为 figures/tikz_diagrams.tex → 编译成 figures/tikz_diagrams.pdf
# （历史命名可能是 tikz_architecture_examples.tex，一并兼容）。TikZ 的 PDF 已被写进 latex_includes.tex。
ls -la figures/tikz_*.pdf figures/tikz_*.tex 2>/dev/null || echo "No TikZ diagrams"
grep -l 'tikz_' figures/latex_includes.tex >/dev/null 2>&1 && echo "→ TikZ 已在 latex_includes.tex 中，按其图块嵌入对应章节" || true
echo ""
echo "=== latex_includes.tex content (figure→PDF mapping) ==="
cat figures/latex_includes.tex 2>/dev/null || echo "No latex_includes.tex"
```

From the output above, build a mapping table: figure label → PDF filename → target section. Only embed figures whose PDF files actually exist — do not create figure environments for PDFs that don't exist (this causes empty figures with just a caption and no image).

**⛔ TikZ 图（如 `figures/tikz_diagrams.pdf` / `figures/tikz_*.pdf`）必须嵌入论文。** 它们已在 `latex_includes.tex` 中有对应 `\includegraphics` 图块，按几何/算法/架构图的章节归属嵌入（几何示意图→对应子问题章节，算法流程图→模型建立章节）。**禁止漏掉任何 `tikz_*.pdf`。**

**⛔ 中文论文的图表 caption 必须是中文。** 如果 `latex_includes.tex` 里的 caption 是英文，嵌入时必须翻译成中文。例如：`\caption{Model Performance Comparison}` → `\caption{模型性能对比}`。

Also scan `figures/*.tex` for all `\begin{figure}` / `\begin{table}` blocks with their `\label{}`. After writing, verify all embedded:
```bash
grep -oh '\\label{[^}]*}' figures/*.tex 2>/dev/null | sort -u > _all_fig_labels.txt
grep -oh '\\label{[^}]*}' paper/sections/*.tex paper/main.tex 2>/dev/null | sort -u > _embedded_labels.txt
comm -23 _all_fig_labels.txt _embedded_labels.txt  # should be empty
```

### Step 2.5: 文献预检索（写正文之前必须完成）

**⛔ 在写任何 \cite{} 之前，必须先建立已验证的文献池。**

目的：先搜索到真实存在的论文，写正文时只引用池子里的论文，避免编造不存在的文献。

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp

# 根据论文的关键主题领域搜索真实论文
# （根据你的具体选题调整搜索词）
# 示例：
#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "空间杜宾模型 数字经济" --max 5
#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "算力基础设施 区域发展" --max 5
```

搜索后，创建 `_tmp/_verified_refs.txt`，每行一篇已验证论文：
```
key: lesage_2009_spatial | title: Introduction to Spatial Econometrics | authors: LeSage, Pace | year: 2009 | match: good
```

**写正文时只能引用这个池子里的论文。** 如果需要引用池子外的论文，先搜索验证后再加入池子。

**兜底**：如果 `scholar_fetch.py` 搜不到或 `match_label="low"`，用 WebSearch 在 Google Scholar / Semantic Scholar 网站上搜索，手动核实标题+作者+年份后再加入池子。

### Step 3: Write each section

Writing order: method/core → experiments → introduction → related work → conclusion.
Save each section immediately. If approaching output limit, create `% [PLACEHOLDER]` files for remaining sections.

**⛔ 写实验/结果章节前，必须先读 experiment_results.md / RESULTS.md / figures/*.json 获取精确数值。** 不要凭记忆编造结果——所有数值（精度、R²、p 值、系数等）必须从数据文件中提取。

**⛔ 写作风格铁律：**
- **禁止在正文中使用 `\begin{itemize}` 或 `\begin{enumerate}`。** 用连贯段落叙述，需要列举时用"（1）...（2）...（3）..."行内编号或"首先...其次..."过渡词。
- **每段至少 3-5 句话，不要写 1-2 句的短段落。**
- **连续段落不能以相同句式开头。**

Follow all rules from `_utils/writing_rules.md` (interleaving, embedding, LaTeX constraints, page filling, resume strategy).

**⛔ 图文并茂硬规则（每个章节都必须遵守）：**
- 所有 `\begin{figure}` 必须用 `[H]`，不要用 `[htbp]`
- 每张图/表后面必须有 ≥5 行分析文字（数值解读+对比+结论），然后才能放下一张图
- 绝对禁止两张图连续出现中间没有分析段落
- 图片用 `\includegraphics[width=0.85\textwidth,height=0.38\textheight,keepaspectratio]`

After each section, check chars:
```bash
chars=$(wc -c < "paper/sections/当前章节.tex")
echo "当前章节: $chars 字符"
# Chinese LaTeX ≈ 800-1000 chars/page
# If chapter page budget in PAPER_PLAN.md is 5 pages but only 2000 chars (~2.5 pages), expand immediately
```

<exemplar_depth>
#### Writing depth by paper type

**本科毕业论文 (30 pages, 5 chapters)**:
- 绪论 (5-6p): 研究背景 1-2 段 + 国内外研究现状按 2-3 个方向分类综述 + 研究内容与方法 + 论文结构
- 理论基础 (5-6p): 核心概念定义 + 相关理论介绍 + 技术路线说明, each concept in full paragraphs (not one-sentence mentions)
- 方法/系统设计 (8-10p): 整体架构 + 各模块详细设计 + 关键算法/公式 + 实现细节
- 实验/测试 (6-8p): 实验环境 + 数据集 + 评价指标 + 主要结果表 + 对比图 + 结果分析 (1-2 paragraphs per result)
- 总结与展望 (2-3p): 工作总结 + 不足之处 + 未来改进方向

**硕士论文 — CS/AI (80 pages, 6 chapters)**:
- 绪论 (8-10p): 研究背景 2-3 段详细论述 + 国内外研究现状按子领域分 3-4 类每类 3-5 篇详细讨论 + 研究内容与创新点
- 相关工作 (12-14p): 按子领域分组, each sub-field has overview paragraph + representative methods detailed + connection to this work
- 方法 (18-20p): each core concept in full paragraphs (definition → formula → intuition → connection to this work), derivation steps not skipped
- 实现 (10-12p): 系统架构 + 数据流 + 超参数配置 + 工程优化细节
- 实验 (20-24p): every result has 2-3 paragraphs of interpretation (数值分析 + 原因分析 + 与其他方法对比), not just "如表所示我们更好"
- 总结 (4-6p): 改述贡献 + 局限性 + 未来工作

**硕士论文 — 经管/统计 (80 pages)**:
- 绪论 (6-8p): research background + significance + literature review + research gap + contributions
- 文献综述 (12-14p): grouped by 3-4 themes, 5-8 papers per theme with detailed discussion
- 理论与方法 (10-16p): theoretical framework / model specification (adapt by research type: causal inference writes hypotheses + variables + model; prediction writes model selection + parameters; evaluation writes indicator system + weighting method)
- 数据与描述性分析 (10-16p): data source + sample description + variable definition table + descriptive stats + exploratory analysis
- 核心分析 (20-24p): organized by research content (causal: regression + robustness + heterogeneity; prediction: model comparison + error analysis; evaluation: comprehensive scoring + dimensional analysis), every result has 2-3 paragraphs of interpretation
- 结论 (6p): main findings + policy recommendations + limitations + future directions

**期刊论文 (15 pages, 5-6 sections)**:
- Introduction (1.5p): hook → gap → contribution → results preview
- Related Work (1-1.5p): by category, synthesize not list
- Method (2-2.5p): notation → formulation → algorithm, compact but complete
- Experiments (3-4p): setup → main results → ablation → analysis
- Conclusion (0.5p): rephrase contributions + limitations

| Type | Pages | Characters | References |
|------|-------|-----------|------------|
| 本科 (30p) | 25-30 | 10000-15000 | ≥20 |
| 硕士 (80p) | 50-60 | 30000-50000 | ≥50 |
| 期刊 (15p) | 12-15 | 6000-8000 | ≥30 |
</exemplar_depth>

#### Per-section minimum figures/citations
- 绪论: ≥1 figure + ≥3 citations
- 相关工作: ≥1 figure/table + ≥3 citations
- 方法: ≥2 figures + ≥2 citations
- 实验: ≥3 figures/tables + ≥3 citations
- 结论: ≥1 citation

Core result tables (主结果对比表, 消融实验表) and key analysis figures belong in the body, not appendix. Appendix only: code, very long auxiliary tables, extra experiment details.

**Expansion strategies** (not padding — substantive content):
- Formula without derivation → add step-by-step derivation with physical meaning
- Result with only "如表所示" → add 2-3 paragraphs (数值含义 + 与预期对比 + 原因分析 + 与其他方法对比)
- Literature review only lists papers → add method summary for each + connection to this work
- Algorithm as pseudocode only → add explanation, complexity analysis, convergence discussion

#### Figure usage principle

"字不如表，表不如图" — but figures only where data needs visualization (data description, experiment results). Do not force figures into pure literature review or theoretical derivation. Claude decides figure count and placement based on content needs.

### Step 4: Build references

Follow the `<references_workflow>` in `_utils/writing_rules.md`.
gbt7714 package handles bibliographystyle — only need `\bibliography{references}`.
Verify references.bib is non-empty before proceeding to next step.

**⛔ 使用 scholar_fetch.py 工具获取所有参考文献的 BibTeX。禁止凭记忆编造 BibTeX。**

**⛔ 引用写法规则：写正文时，citation key 必须包含描述性关键词，格式为 `作者姓_年份_主题关键词`。**
例如：`\cite{wang_2023_supply_chain_resilience}` 而不是 `\cite{wang2023supply}`。
这样搜索时能用关键词找到正确的论文。如果不确定作者/年份，用 `TODO__` 前缀：`\cite{TODO__digital_economy_spatial_spillover}`。

```bash
# Step 4a: 收集所有引用 key 并提取搜索关键词
grep -roh '\\cite[tp]*{[^}]*}' paper/sections/*.tex paper/main.tex 2>/dev/null \
  | grep -oP '\{[^}]+\}' | tr -d '{}' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u > _tmp/_cited_keys.txt
echo "引用 key 数量: $(wc -l < _tmp/_cited_keys.txt)"
cat _tmp/_cited_keys.txt

# Step 4b: 逐个搜索并获取 BibTeX（用描述性关键词搜索）
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
while IFS= read -r key; do
    # 将 citation key 转为搜索词：去掉 TODO__ 前缀，下划线替换为空格
    query=$(echo "$key" | sed 's/^TODO__//; s/_/ /g')
    echo "--- 获取: $key (搜索: $query) ---"
    $PYTHON "$SCHOLAR_SCRIPT" bibtex "$query" --max 3
    sleep 0.5
done < _tmp/_cited_keys.txt
```

处理每个搜索结果：
1. **检查 `match_label`**：`"good"` → 直接使用。`"partial"` → 核实标题是否匹配你的引用意图。`"low"` → 很可能搜错了，换更好的关键词重新搜索或用 WebSearch。
2. **检查 `match_score`**：分数 < 0.3 说明搜索结果大概率不是你想引用的论文，不要盲目使用。
3. 选择正确的论文，将其 `bibtex` 字段复制到 `paper/references.bib`。
4. 将 .tex 文件中的 citation key 替换为 BibTeX 条目中的实际 key。
5. 如果 `bibtex_source=auto`，在条目上方加 `% [VERIFY]`。
6. 如果 `match_label="low"` 且找不到更好的结果，加 `% [LOW_MATCH - 请核实是否为目标论文]`，并用 WebSearch 兜底。

### Step 5: De-AI polish

See `<de_ai_polish>` in `_utils/writing_rules.md`.

### Step 6: Cross-review

Send draft to external reviewer for feedback:

```bash
mkdir -p _tmp
cat << 'REVIEW_EOF' > _tmp/_review_prompt.txt
请评审这篇中文学术论文草稿。重点关注：
1. 逻辑流畅性和论证结构
2. 论点-证据对齐（每个论点是否有数据支撑？）
3. 写作清晰度和简洁性
4. 缺失内容或薄弱章节
5. 评分（1-10）和最需要改进的 3 个方面

## 论文各章节：
REVIEW_EOF
for f in paper/sections/*.tex; do
    [ -f "$f" ] && echo "### $(basename $f)" >> _tmp/_review_prompt.txt && cat "$f" >> _tmp/_review_prompt.txt
done
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_cross_review.txt
```

If reviewer script unavailable, skip this step.

### Step 7: Final verification

```bash
bash _utils/writing_check.sh paper/ 2>/dev/null || bash skills/shared-scripts/writing_check.sh paper/
```

Also verify:
```bash
source .env_skill 2>/dev/null || true  # 加载 MAX_PAGES 等数值参数
echo "=== 各章节字符数 ==="
total=0
for f in paper/sections/*.tex; do
    chars=$(wc -c < "$f")
    total=$((total + chars))
    echo "  $(basename $f): $chars 字符"
done
echo "  总计: $total 字符"
echo "  目标: ≥ ${MAX_PAGES:-30} × 800 = $((${MAX_PAGES:-30} * 800)) 字符"
```
- Total chars ≥ MAX_PAGES × 800 (expand thinnest sections if not)
- references.bib exists and non-empty
- No template bracket placeholders remaining
- All figures/*.pdf referenced in sections
- No `\input{../figures/...}` in section files

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
If any figures are missing, go back and embed them into the appropriate sections before finishing. **⛔ Do NOT finish until missing = 0.**

**⛔ Page count pre-check (MUST pass before finishing):**
```bash
source .env_skill 2>/dev/null || true  # 加载 MAX_PAGES 等数值参数
total=0
for f in paper/sections/*.tex; do
    [ -f "$f" ] || continue
    chars=$(wc -c < "$f")
    total=$((total + chars))
done
est_pages=$((total / 900))
echo "总字符: $total, 估算页数: ~$est_pages, 目标: ≥ ${MAX_PAGES:-30}"
if [ -n "$MAX_PAGES" ] && [ "$est_pages" -lt "$((MAX_PAGES * 80 / 100))" ]; then
    echo "⛔ 页数低于目标 80%，建议扩充最薄章节"
fi
```
If estimated pages < 80% of MAX_PAGES, expand the thinnest chapters before finishing.

## Key Rules

- Use templates, do not write main.tex from scratch
- XeLaTeX compilation required
- Citation format: gbt7714 (superscript `[1]`), not natbib
- No `\hypersetup{colorlinks=true}` — conflicts with hidelinks
- Body pages ≥ MAX_PAGES
- No real author info — use placeholders
- Primary output: `paper/` directory, temp files: `_tmp/`
- ⛔ **本步骤只写论文 .tex 文件，不要重新生成图表 PDF、不要修改 code/*.py、不要重新运行分析代码。** 图表和数据已由前序步骤生成完毕，直接引用即可
- Large files: Bash heredoc
- Backup before overwrite
