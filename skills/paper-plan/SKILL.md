---
name: paper-plan
description: "Generate a structured paper outline from review conclusions and experiment results. Use when user says \"paper outline\", \"plan the paper\", or wants to create a paper plan before writing."
argument-hint: [topic-or-narrative-doc]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch, mcp__codex__codex, mcp__codex__codex-reply
---

# Paper Plan: From Review Conclusions to Paper Outline

Generate a structured outline from: **$ARGUMENTS**

## Constants

- **TARGET_VENUE = `ICLR`** — Override via Additional Parameters. Supported: ICLR, NeurIPS, ICML.
- **MAX_PAGES** — ICLR=9, NeurIPS=9, ICML=8. Override via Additional Parameters.
- **CUSTOM_REQUIREMENTS** — User's custom instructions, highest priority.
- **REVIEWER_SCRIPT** — External reviewer script

## Inputs

1. NARRATIVE_REPORT.md / STORY.md / AUTO_REVIEW.md / CLAIMS_FROM_RESULTS.md
2. Experiment results (JSON/CSV in `figures/`, `experiment_results.md`, `figures/experiment_data.json`)
3. IDEA_REPORT.md (if applicable)
4. FINAL_PROPOSAL.md (if applicable, from research-refine-pipeline)

If none exist, generate plan from $ARGUMENTS description.

## Orchestra-Guided Writing Overlay

Read `../shared-references/writing-principles.md` when framing contribution, Abstract, Introduction.
Read `../shared-references/venue-checklists.md` before freezing outline.

## ⛔⛔⛔ Output Contract (highest priority)

**Must produce `PAPER_PLAN.md` (≥ 1KB, complete outline)**.

⛔ **MUST run output verification before ending**:
```bash
[ -f PAPER_PLAN.md ] && SZ=$(wc -c < PAPER_PLAN.md) || SZ=0
[ "$SZ" -ge 1024 ] && echo "✅ PAPER_PLAN.md ($SZ)" \
    || echo "❌ PAPER_PLAN.md missing or too small — complete it before ending the step"
```

## Workflow

### Step 1: Extract Claims and Evidence

Build Claims-Evidence Matrix:
| Claim | Evidence | Status | Section |
|-------|----------|--------|---------|

Identify one-sentence contribution, 3-5 core claims, known weaknesses.

### Step 2: Determine Structure

Section count is flexible (5-8). Choose based on paper type:

**Empirical**: Intro → Related → Method → Experiments → Analysis → Conclusion
**Theory+Exp**: Intro → Related → Prelim → Experiments → Theory A → Theory B → Conclusion
**Method**: Intro → Related → Method → Experiments → Ablation → Conclusion

Front-load the contribution: title, abstract, intro, hero figure should make the claim clear.

### Step 3: Section-by-Section Planning

For each section: content summary, key claims, figure/table plan, page budget, key citations.

Abstract: what→why hard→how→evidence→strongest result (150-250 words).
Introduction: hook→gap→contribution→results preview→hero figure (1.5 pages).
Related Work: ≥1 full page, organized by category, synthesize not list.

### Step 4: Content-Driven Figure Planning (Exemplar + Audit + Benchmark)

#### Phase A: Exemplar Awareness

Before planning figures, **read the figure exemplars file** to calibrate expectations:

```bash
cat _utils/figure_exemplars.md 2>/dev/null || cat skills/shared-scripts/figure_exemplars.md
```

Find the section matching your venue (ICLR/NeurIPS/JMLR etc.) and review the figure/table density. Don't mechanically copy — understand "what density is normal for this paper length."

The ratios and counts above are reference points only. Claude should adapt based on the specific research.

#### Phase B: Section-by-Section Audit

For every subsection in the outline, answer three questions:

1. **What is the core conclusion/content?** (one sentence)
2. **Can the reader understand it from text alone?** Or does it need a figure/table?
   - Numerical comparison → table or bar chart
   - Trend over time → line plot
   - Structural relationships → architecture diagram or flowchart
   - Distribution → histogram/boxplot/heatmap
   - Algorithm → pseudocode or flowchart
   - Pure discussion (e.g., related work categorization) → no figure needed
3. **If needed, figure or table?**
   - Precise values (coefficients, accuracy) → table
   - Visual trends/comparisons → figure
   - Both → main results in table, supplementary visualization in figure

Record results in a "Section Audit" table in the output.

#### Phase C: Benchmark Check

After planning, count total figures+tables and compare with Phase A exemplars:

| Item | Exemplar Reference | This Paper | Status |
|------|-------------------|-----------|--------|
| Data figures (PDF) | [ref] | [actual] | ✅/⚠️ |
| Tables (LaTeX) | [ref] | [actual] | ✅/⚠️ |
| TikZ diagrams (architecture/roadmap) | [ref] | [actual] | ✅/⚠️/❌ |
| Algorithm pseudocode | [ref] | [actual] | ✅/⚠️ |
| Total | [ref] | [actual] | ✅/⚠️ |
| Density (pages/element) | [ref] | [actual] | ✅/⚠️ |

**If any item is ⚠️, go back to Phase B audit table and add missing figures/tables.**

Key checks:
- Method section has architecture diagram or pseudocode?
- Every experiment in experiments section has a figure or table?
- Any section > 3 pages with no visual element?
- Introduction has a hero figure?

#### ⛔ Phase D: TikZ 架构图规划检查

参考 `figure_exemplars.md` 中的"TikZ 架构图分布规律"和"各论文类型 TikZ 图参考建议"表，根据论文类型和内容自主决定是否需要 TikZ 图。

**位置一：绪论/引言 — 技术路线图或研究框架图**
- 硕士论文（CS/AI）：研究框架图（问题→方法→实验→结论的宏观流程）
- 硕士论文（经管/统计）：研究路线图（问题→文献→假设→数据→实证→结论）
- 本科论文：技术路线图（简化版研究框架）
- 期刊论文（ICLR/NeurIPS 等）：可选，方法复杂时建议有

**位置二：方法/模型章节 — 模型架构图或理论框架图**
- CS/AI 方向：整体模型架构图（输入→模块→输出），复杂模块可额外画细节图
- 经管/统计方向：理论模型框架图（变量关系路径图，标注假设 H1/H2/H3）

**规划原则：参考范例自主决定，决定了就必须写进 Figure Plan。后续图表生成和编译检查都以 Figure Plan 为准。**

在 Figure Plan 表格中，TikZ 图应标注位置和类型：

```markdown
| ID | Type | Description | Location | Priority |
|----|------|-------------|----------|----------|
| TikZ-1 | 技术路线图/研究框架图 | 整体研究逻辑链路 | 绪论/Introduction | 必须/推荐 |
| TikZ-2 | 模型架构图/理论框架图 | 核心方法的内部结构 | 方法/Method | 必须/推荐 |
```

**⚠️ 如果 Figure Plan 中 TikZ 图数量为 0，对照"各论文类型 TikZ 图参考建议"表确认是否合理。如果范例建议有但规划中没有，标注理由。**

### Step 5: Citation Scaffolding

Per-section citation plan. Never generate BibTeX from memory. Flag uncertain with `[VERIFY]`.

### Step 6: Cross-Review

Send outline to external reviewer for feedback:

```bash
mkdir -p _tmp
cat << 'REVIEW_EOF' > _tmp/_review_prompt.txt
Please review this paper outline. Focus on:
1. Is the story arc compelling? (hook → gap → contribution → evidence)
2. Does the Claims-Evidence Matrix have gaps?
3. Is the figure plan sufficient for the page budget?
4. Are there structural issues (missing sections, wrong ordering)?
5. Score (1-10) and top 3 improvements needed.

## Paper Outline:
REVIEW_EOF
cat PAPER_PLAN.md >> _tmp/_review_prompt.txt
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_outline_review.txt
```

If reviewer script unavailable, skip this step.

### Step 7: Output

Save to `PAPER_PLAN.md` with: title, one-sentence contribution, Claims-Evidence Matrix, section structure, figure plan, citation plan, reviewer feedback.

## Key Rules

- Large files: use Bash heredoc
- No author information
- Honest about evidence gaps
- MAX_PAGES = main body to Conclusion (refs/appendix excluded)
- Claims-Evidence Matrix is the backbone
- Front-load the story
- Section count is flexible (5-8)
- ⛔ Main output: `PAPER_PLAN.md`. Don't write extra reports to root
- ⛔ LaTeX in Markdown: `$$` block formulas on own line with blank lines before/after, inline `$...$`, multi-line environments (aligned/cases) must be block-level, avoid `\text{}` with CJK
