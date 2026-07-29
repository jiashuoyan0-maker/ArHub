---
name: comp-paper-en-docx
description: "Mathematical modeling competition paper in English (MCM/ICM/APMCM) — Word docx mode. docx-mode counterpart of comp-paper-en — keeps COMAP structure but produces paper/main.md only."
argument-hint: [competition-type]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Competition Paper Writing (English) — docx mode

Write an MCM/ICM/APMCM paper as Markdown for Word export: **$ARGUMENTS**

> docx-mode counterpart of `comp-paper-en`. Keeps COMAP/APMCM structure (Summary Sheet, Assumptions, Notations, sub-problem chapters, Sensitivity Analysis, Strengths & Weaknesses) but produces **`paper/main.md`** only.
>
> ⛔ **NEVER produce `.tex` / `.cls` / `.sty` / `.bib`. NEVER use LaTeX commands.**

## Constants

- **COMPETITION** — Default `mcm`
- **MAX_PAGES** — Default 25. Body ≥ MAX_PAGES (~600 words/page in English)
- **CUSTOM_REQUIREMENTS**

## Inputs

1. PROBLEM_ANALYSIS.md, MODELING_REPORT.md, RESULTS.md
2. figures/ — `.png` / `.pdf`
3. code/, figures/all_results.json, figures/problem_*_results.json

## Load shared rules

```bash
cat _utils/writing_rules.md 2>/dev/null || cat skills/shared-scripts/writing_rules.md
```

## MCM/ICM Paper Structure

```
Summary Sheet (1 page — most important page)
1. Introduction
2. Assumptions and Justifications
3. Notations
4. Model Design and Solution (per sub-problem)
5. Sensitivity Analysis
6. Model Evaluation (Strengths + Weaknesses)
7. Conclusions
References
Appendix A: Code
```

## ⛔⛔⛔ Output Contract (highest priority)

**Single artifact**: `paper/main.md` (UTF-8, ≥ 5KB)

**Never produce**: `.tex` / `.bib` / `.cls` / `.sty` / `.aux` / any LaTeX command.

**Mandatory verification**:
```bash
PASS=true
[ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
[ "$SZ" -ge 5120 ] && echo "✅ paper/main.md ($SZ)" || { echo "❌ paper/main.md missing"; PASS=false; }

words=$(wc -w < paper/main.md 2>/dev/null || echo 0)
est_pages=$((words / 600))
target_pages="${MAX_PAGES:-25}"
echo "words: $words, est pages: ~$est_pages, target: ≥ $target_pages"
[ "$est_pages" -lt "$((target_pages * 80 / 100))" ] && echo "⚠ below 80% target"

if grep -qE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter|subsection|bibitem|usepackage|documentclass)\{' paper/main.md; then
    echo "❌ LaTeX residue:"
    grep -nE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter|subsection|bibitem|usepackage|documentclass)\{' paper/main.md | head -5
    PASS=false
fi

ls paper/*.tex paper/sections/*.tex 2>/dev/null | head -1 | grep -q . && { echo "❌ .tex files detected"; PASS=false; } || true

[ "$PASS" != true ] && echo "⛔ verification FAILED"
```

## docx-cn-engine markdown conventions

(See paper-write-docx for the full reference.)

- `# Title` (unique, centered cover); `## Section`; `### Subsection`
- `## Summary Sheet` / `## Abstract` triggers centered abstract style
- `## References` triggers hanging-indent for `[N] ...` lines
- Math: `$inline$`, `$$display$$`, append ` (1)` for numbering
- Figures: `![Figure 1: caption](figures/fig.png)`
- Tables: markdown pipe tables (rendered as 3-line academic style)
- Citations: `[1]`, `[1, 2]`, `[1-3]` — never `\cite{}`

## Workflow

### Step 0: Upstream check + resume

```bash
echo "=== Upstream check ==="
for f in PROBLEM_ANALYSIS.md MODELING_REPORT.md RESULTS.md; do
    [ -f "$f" ] && echo "✅ $f ($(wc -c < $f) chars)" || echo "❌ $f missing"
done
[ -f figures/all_results.json ] && echo "✅ figures/all_results.json" || true
PNG_COUNT=$(ls figures/*.png 2>/dev/null | wc -l)
PDF_COUNT=$(ls figures/*.pdf 2>/dev/null | wc -l)
echo "figures: PNG=$PNG_COUNT, PDF=$PDF_COUNT"

if [ -f paper/main.md ]; then
    cp paper/main.md "paper/main-backup-$(date +%s).md.bak"
    echo "Resume mode — backup created"
fi
```

### Step 1: Figure inventory + embedding plan

```bash
ls -la figures/*.png figures/*.pdf 2>/dev/null
ls -la figures/TABLE_*.md 2>/dev/null
cat figures/latex_includes.tex 2>/dev/null  # caption reference only
```

⛔ Build figure embedding plan before writing:
| ID | File | Section | Caption |
|----|------|---------|---------|
| Fig 1 | figures/fig_roadmap.png | 1. Introduction | Figure 1: Solution roadmap |
| Fig 2 | figures/fig_flow_q1.png | 4.1 Sub-problem 1 | Figure 2: Sub-problem 1 algorithm flow |
| ... | ... | ... | ... |

⛔ Only embed figures whose files exist. ⛔ DrawIO figures (roadmap/flow) MUST be embedded into proper sections.

### Step 1.5: Pre-fetch verified reference pool

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp
# Search by topic, save verified entries to _tmp/_verified_refs.txt
```

### Step 2: Write the paper

Order: Body chapters first → References → Summary Sheet last.

Skeleton (one `paper/main.md`):

```markdown
# [Paper Title]

## Summary Sheet

[Placeholder — write LAST in Step 5.6, after all chapters complete and numerical results known]

**Keywords**: ...

## 1. Introduction

### 1.1 Problem Background

[2-3 paragraphs of real-world context, references to prior work]

### 1.2 Restatement of the Problem

[Restate in own words, NOT copy the problem statement]

### 1.3 Our Approach

![Figure 1: Solution roadmap.](figures/fig_roadmap.png)

As shown in Figure 1, our approach... [≥ 5 lines]

## 2. Assumptions and Justifications

We make the following assumptions:

(1) [Assumption]. This assumption is justified because... [1-2 sentences]
(2) ...
(3) ...
(4) ...
(5) ...

⛔ 4-6 assumptions. Each 1-2 sentences (assumption + justification).

## 3. Notations

**Table 1: Key Notations**

| Symbol | Meaning | Unit |
|--------|---------|------|
| $N$ | Total quantity | items |
| $x_i$ | Decision variable for item $i$ | --- |
| ... | ... | ... |

⛔ 15-20 symbols max — only those actually used in body.

## 4. Sub-Problem 1

### 4.1 Problem Analysis

[1-2 paragraphs]

### 4.2 Model Formulation

![Figure 2: Sub-problem 1 algorithm flow.](figures/fig_flow_q1.png)

Figure 2 illustrates... [≥ 5 lines]

We formulate the model as:

$$\min \sum_{i=1}^n c_i x_i \quad (1)$$

$$\text{s.t.} \quad \sum_i a_{ij} x_i \leq b_j, \quad j=1,\dots,m \quad (2)$$

[≥ 5 lines explaining each symbol's meaning]

### 4.3 Solution Algorithm

[Algorithm steps + complexity analysis]

### 4.4 Results

**Table 2: Comparison of algorithms for Sub-problem 1**

| Algorithm | Fitness | Time(s) |
|-----------|---------|---------|
| GA | 0.823 | 12.3 |
| PSO | 0.811 | 10.8 |
| Ours | **0.917** | **9.4** |

Table 2 shows that our method... [≥ 2 paragraphs of analysis]

![Figure 3: Convergence curves.](figures/fig_results_q1.png)

Figure 3 reveals... [≥ 5 lines]

## 5. Sub-Problem 2

[Same structure]

## 6. Sub-Problem 3

[Same structure]

## 7. Sensitivity Analysis

[≥ 2 key parameters, each with variation curve + analysis]

## 8. Model Evaluation

### 8.1 Strengths

[3-4 strengths, each one paragraph]

### 8.2 Weaknesses

[2-3 weaknesses]

### 8.3 Future Work

[1-2 paragraphs]

## 9. Conclusions

[Summary + main contributions + practical implications]

## References

[1] LeSage J P, Pace R K. Introduction to Spatial Econometrics. CRC Press, 2009.
[2] Vaswani A, et al. Attention is all you need. NeurIPS 2017.

## Appendix A: Code

```python
# Code listings or file inventory
```
```

### Step 3: Writing discipline

**⛔ Style rules:**
- No bullet/enumerated lists for narrative prose. Use "(1) ... (2) ..." inline numbering or transitional phrases ("First, ...; second, ..."). Bullets/enumerations OK for input checklists, evaluation metrics definitions, software dependencies, model assumptions.
- Each paragraph 3-5 sentences minimum.
- Consecutive paragraphs cannot start with the same syntactic pattern.
- Figures/tables are evidence, not subjects. Don't open paragraphs with "Figure X shows" — instead: state claim → reference figure parenthetically (Figure X) → derive insight.

**⛔ Numbers from data only:**
```bash
[ -f figures/all_results.json ] && cat figures/all_results.json
[ -f RESULTS.md ] && cat RESULTS.md
```
Copy exact numbers from data files. No memory-based estimation.

**⛔ Figure-text discipline:**
- Each figure/table needs ≥ 5 lines of analysis (numerical interpretation + comparison + reasoning) before the next visual
- Never two consecutive visuals without analysis paragraph between

**⛔ Long tables (>15 rows):**
- ≤15 rows: in body
- >15 rows: body shows summary (first 5 + last 3 + "⋮"), full table in `## Appendix A`
- Caption notes "(partial; see Appendix for full table)"

After each section:
```bash
words=$(wc -w < paper/main.md)
echo "running word count: $words"
```

<exemplar_depth>
#### Writing depth reference

**MCM/ICM Outstanding Paper (~25 pages, ~15000 words total)**:
- Summary Sheet (1p, 300-400 words): self-contained with specific numerical results. Structure: problem statement (1-2 sentences) → method (2-3 sentences) → key results (3-4 sentences with numbers) → conclusion (1-2 sentences)
- Introduction (2p, ~1200 words): problem context + literature + approach overview
- Assumptions (0.5p): each assumption with justification (not just a bullet list)
- Notations (0.5p): 15-20 symbols max, three-line markdown table
- Each sub-problem (4-5p, ~2400-3000 words): model formulation (1.5p with derivation) + solution method (1p with algorithm) + results table+figure+numbers (1p) + analysis (0.5-1p interpretation + comparison)
- Sensitivity Analysis (2-3p, ~1200-1800 words): ≥ 2 key parameters, each with variation plot + analysis paragraph
- Model Evaluation (1.5p): 3-5 strengths + 2-3 weaknesses (**honest**, not token weaknesses like "limited by time") + generalization discussion
- References + Appendix (3-4p)

**APMCM First Prize (25-30 pages)**: similar but can be longer, 5-6 pages per sub-problem with more detailed analysis.
</exemplar_depth>

**Expansion strategies** (not padding — substantive content):
- Formula without derivation → add step-by-step derivation with physical meaning
- Result with only "Table X shows" → add 2-3 paragraphs (what numbers mean, comparison with expectations, why this result makes sense)
- Algorithm as pseudocode only → add explanation of key steps, complexity analysis, convergence discussion

**Summary Sheet** is the most important page — invest the most effort here. Must be self-contained, one page, ≥ 300 words, with quantitative results.

**Each sub-problem chapter**: model formulation → solution method → results (table + figure + numbers) → result analysis (2-3 paragraphs of interpretation)

**Sensitivity Analysis**: parameter sensitivity + robustness + error analysis

**Model Evaluation**: Strengths 3-5 points + Weaknesses 2-3 points (honest) — do not write token weaknesses like "limited by time"

### Step 4: Reference numbering

```bash
grep -oE '\[[0-9]+(-[0-9]+)?(, *[0-9]+)*\]' paper/main.md | sort -u > _tmp/_cited.txt
ref_count=$(awk '/^## References/,0' paper/main.md | grep -cE '^\[[0-9]+\]')
echo "Cited tokens vs reference entries: $(wc -l < _tmp/_cited.txt) vs $ref_count"
```

⛔ Numbering must be strictly increasing by first appearance ([1] before [2] before [3]). No gaps.
⛔ MCM/ICM ≥ 10 references; APMCM ≥ 10.

### Step 4.5: Verify references with scholar_fetch (mandatory)

⛔ **All references MUST be fetched via scholar_fetch.py. NEVER fabricate BibTeX from memory.**

Use **descriptive citation keys** while drafting: `LastName_Year_topic_keywords`.
- ✅ `cordeau_2007_vrp_branch_cut`
- ❌ `cordeau2007vrp` (impossible to re-search)
- Author/year unknown → `TODO__` prefix: `TODO__integer_programming_scheduling`

After drafting, verify each citation:

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp
# Place descriptive keys in _tmp/_topics.txt (one per line)
while IFS= read -r key; do
    query=$(echo "$key" | sed 's/^TODO__//; s/_/ /g')
    echo "--- Fetching: $key (query: $query) ---"
    $PYTHON "$SCHOLAR_SCRIPT" bibtex "$query" --max 3
    sleep 0.5
done < _tmp/_topics.txt
```

For each result:
1. **Check `match_label`**: `"good"` → use; `"partial"` → verify title; `"low"` → retry or use WebSearch.
2. **Check `match_score`**: < 0.3 → don't blindly trust.
3. Format result as `[N] Author A, Author B. Title. Venue, Year, vol(issue): pages.` under `## References`.
4. References order in `## References` MUST match first-appearance order in body.

**Fallback**: If `scholar_fetch.py` fails or `match_label="low"`, use WebSearch on Google Scholar / Semantic Scholar to verify title + authors + year manually.

### Step 4.6: Claims-Evidence Matrix Verification

Before each chapter, re-read the claims-evidence matrix in `PROBLEM_ANALYSIS.md` / `MODELING_REPORT.md` / `PAPER_PLAN.md`:

```bash
grep -A 100 'Claims-Evidence\|claim.*evidence\|claim-evidence' PROBLEM_ANALYSIS.md MODELING_REPORT.md PAPER_PLAN.md 2>/dev/null | head -50
```

Discipline:
- Every claim in the paper must map to a row in the planning doc
- Don't add claims outside the plan (if a new finding appears, update MODELING_REPORT.md first)
- Don't skip planned claims (even negative results must be reported honestly)
- Every numerical claim must match `figures/all_results.json` exactly

If a planned claim has no data evidence, write "preliminary results suggest X, formal validation left to future work" instead of fabricating evidence.

### Step 5: De-AI polish

See `<de_ai_polish>` in writing_rules.md. Key:
- Drop "this paper proposes / we propose" boilerplate
- Replace "explore / investigate" with concrete verbs
- Cap "we" frequency

### Step 5.5: Cross-review (optional)

```bash
mkdir -p _tmp
cat << 'EOF' > _tmp/_review_prompt.txt
Review this MCM/ICM/APMCM paper draft. Focus on:
1. Sub-problem coverage (does each sub-problem have explicit numerical results?)
2. Claim-evidence alignment (every conclusion supported by data?)
3. Chapter structure vs MCM/ICM standard
4. Writing clarity (any meta-narrative leaks / boilerplate openings?)
5. Score (1-10) + top-3 improvements

## Paper:
EOF
cat paper/main.md >> _tmp/_review_prompt.txt
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_cross_review.txt
```

Skip if reviewer script unavailable.

### Step 5.6: Write Summary Sheet LAST

⛔ NOW write the Summary Sheet (replace the placeholder from Step 2).

The Summary Sheet is the most important page. Read RESULTS.md and all body chapters to extract specific numerical results for each sub-problem.

```markdown
## Summary Sheet

[1-page summary covering:
- Background and problem context (1 short paragraph)
- Approach/methodology summary (1 paragraph)
- Sub-problem 1: method + key result with specific number (1 paragraph)
- Sub-problem 2: method + key result with specific number (1 paragraph)
- Sub-problem 3: method + key result with specific number (1 paragraph)
- Model evaluation: strengths + weaknesses (1 short paragraph)]

**Keywords**: keyword1; keyword2; keyword3; keyword4; keyword5
```

⛔ Each sub-problem must have its specific result in the Summary Sheet (e.g., "For Sub-problem 1, we apply genetic algorithm achieving fitness 0.917 with 9.4s solve time"). Numbers must match body text exactly.

### Step 6: Final verification

```bash
echo "=== Final verification ==="

[ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
echo "paper/main.md: $SZ bytes"

words=$(wc -w < paper/main.md)
est_pages=$((words / 600))
target=${MAX_PAGES:-25}
echo "words: $words, est pages: ~$est_pages, target: ≥ $target"
[ "$est_pages" -lt "$((target * 80 / 100))" ] && echo "⛔ MUST expand thinnest sections"

# Sub-problem coverage
for n in 1 2 3; do
    if grep -qE "^## [0-9]+\. Sub-Problem ${n}|^## [0-9]+\. Problem ${n}" paper/main.md; then
        echo "✅ Sub-Problem ${n} present"
    else
        echo "⚠ Sub-Problem ${n} missing"
    fi
done

# Figure embedding
missing_img=0
for img in figures/*.png figures/*.pdf; do
    [ -f "$img" ] || continue
    bn=$(basename "$img")
    [ "$bn" = "latex_includes.tex" ] && continue
    if ! grep -q "$bn" paper/main.md; then
        echo "⚠ unembedded: $bn"
        missing_img=$((missing_img + 1))
    fi
done
[ "$missing_img" -gt 0 ] && echo "⛔ embed missing figures"

# Citation continuity
max_cited=$(grep -oE '\[[0-9]+\]' paper/main.md | grep -v '^## ' | tr -d '[]' | sort -n | tail -1)
ref_lines=$(awk '/^## References/,0' paper/main.md | grep -cE '^\[[0-9]+\]')
echo "max cited: ${max_cited:-0}, refs: $ref_lines"
[ -n "$max_cited" ] && [ "$ref_lines" -lt "$max_cited" ] && echo "⛔ refs less than cited"

# LaTeX residue
if grep -qE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter)\{' paper/main.md; then
    echo "⛔ LaTeX residue:"
    grep -nE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter)\{' paper/main.md | head -5
fi

# .tex residue
ls paper/*.tex paper/sections/*.tex 2>/dev/null | head -1 | grep -q . && echo "⛔ .tex files detected" || echo "✅ no .tex"

# Summary Sheet not placeholder
if grep -A 3 '^## Summary Sheet' paper/main.md | grep -qiE 'placeholder|TODO'; then
    echo "⛔ Summary Sheet still placeholder — must fill in"
fi
```

If any ⛔ appears, fix and re-run verification.

### Step 7: Compliance check (MCM/ICM specific)

Before submitting, verify against contest rules:

- [ ] **Summary Sheet present** with quantitative results for every sub-problem
- [ ] **Team Control Number** placeholder visible (where required)
- [ ] **No author names / affiliations** anywhere in body (anonymous submission)
- [ ] **Page count** within limit (MCM/ICM ≤ 25; APMCM may extend; check current year's rules)
- [ ] **APMCM submission**: commitment letter is submitted separately, NOT bundled into the PDF/docx
- [ ] **Code appendix included** (complete runnable code, not snippets)
- [ ] **Figure paths reference** `figures/*.png` (not absolute paths)
- [ ] **Numbers in Summary Sheet** match numbers in body text exactly
- [ ] **Constraint consistency**: every numerical result satisfies problem constraints (load capacity, time window, count limits etc.)

If any box is ❌, fix before submission.

## Key Rules (docx mode)

- **Single artifact**: `paper/main.md`
- **Never**: `.tex` / `.bib` / `.cls` / `.sty` / `.aux`
- **Math**: `$...$` / `$$...$$`
- **Figures**: `![alt](path)`
- **Tables**: markdown pipe tables
- **Citations**: `[N]`
- Summary Sheet structure: each sub-problem with specific number
- Body length ≥ MAX_PAGES × 600 words
- Numbers from `figures/*.json` / `RESULTS.md`
- Long tables (>15 rows): summary in body + full in Appendix
- Citations strictly increasing by first appearance
- Backup before overwrite
