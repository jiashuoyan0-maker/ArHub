---
name: paper-write-docx
description: "Draft an English academic paper as Markdown for Word (docx) export. Use when params.output_format == 'docx'. Mirrors paper-write writing rules (ICLR/NeurIPS/ICML) but produces paper/main.md only."
argument-hint: [venue-or-section]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch, mcp__codex__codex, mcp__codex__codex-reply
---

# Paper Write — Markdown for Word (docx mode)

Draft an English academic paper as Markdown: **$ARGUMENTS**

> docx-mode counterpart of `paper-write`. Keeps all writing principles (claims-evidence, story arc, citation discipline, venue checklists) but produces **`paper/main.md`** only. The downstream `docx-export` step runs `tools/docx-cn-engine/md_to_docx.js` to convert it.
>
> ⛔ **NEVER produce `paper/main.tex` / `paper/sections/*.tex` / `.cls` / `.sty` / `.bib`. NEVER run XeLaTeX.**

## Constants

- **TARGET_VENUE = `ICLR`** — Supported: ICLR, NeurIPS, ICML. Override via Additional Parameters.
- **MAX_PAGES = 9** — Body length target ≥ MAX_PAGES (~800 words/page).
- **ANONYMOUS = true**
- **CUSTOM_REQUIREMENTS** — highest priority.
- **REVIEWER_SCRIPT** — external reviewer script.

## Inputs

1. PAPER_PLAN.md — outline with claims-evidence matrix, figure plan
2. NARRATIVE_REPORT.md — research narrative
3. experiment_results.md / RESULTS.md / figures/all_results.json
4. figures/ — `.png` / `.pdf` files
5. Verified reference pool

## Load shared rules

```bash
cat _utils/writing_rules.md 2>/dev/null || cat skills/shared-scripts/writing_rules.md
```

> The LaTeX-specific bits in shared rules don't apply here; the writing principles do.

## Orchestra References

- `../shared-references/writing-principles.md` — story framing, clarity
- `../shared-references/venue-checklists.md` — submission requirements
- `../shared-references/citation-discipline.md` — citation fallback

## ⛔⛔⛔ Output Contract (highest priority)

**Single artifact**: `paper/main.md` (UTF-8, complete paper, ≥ 5KB)

**Never produce**: `paper/main.tex`, `paper/sections/*.tex`, `paper/references.bib`, `.cls`, `.sty`, `.aux`, any LaTeX command (`\begin`, `\input`, `\cite`, `\section`, `\includegraphics`, ...).

**Mandatory verification before ending**:
```bash
echo "=== Output verification (must be all ✅) ==="
PASS=true

[ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
[ "$SZ" -ge 5120 ] && echo "✅ paper/main.md ($SZ bytes)" || { echo "❌ paper/main.md missing or too small ($SZ bytes)"; PASS=false; }

words=$(wc -w < paper/main.md 2>/dev/null || echo 0)
est_pages=$((words / 600))   # ~600 words/page for English
target_pages="${MAX_PAGES:-9}"
echo "words: $words, est pages: ~$est_pages, target: ≥ $target_pages"
[ "$est_pages" -lt "$((target_pages * 80 / 100))" ] && echo "⚠ below 80% target — expand thinnest sections"

# No LaTeX residue
if grep -qE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter|subsection)\{' paper/main.md; then
    echo "❌ LaTeX command residue in paper/main.md:"
    grep -nE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter|subsection)\{' paper/main.md | head -5
    PASS=false
fi

# No .tex
ls paper/*.tex paper/sections/*.tex 2>/dev/null | head -1 | grep -q . && { echo "❌ .tex files detected"; ls paper/*.tex paper/sections/*.tex 2>/dev/null; PASS=false; } || true

[ "$PASS" != true ] && echo "⛔ verification FAILED — fix and re-run before ending"
```

## docx-cn-engine markdown conventions

The downstream `docx-export` step uses `tools/docx-cn-engine/md_to_docx.js`. Follow these conventions:

### 1. Headings
- `# Paper Title` — paper title (unique, centered, largest)
- `## 1. Introduction` — top-level section
- `### 1.1 Subsection`
- `#### Sub-subsection`

### 2. Abstract (engine auto-centers)
```markdown
## Abstract

[150-250 word abstract]

**Keywords**: kw1; kw2; kw3
```

### 3. Math
- Inline: `$x^2 + y^2 = r^2$`
- Display: `$$ \nabla_\theta L(\theta) = \mathbb{E}[\dots] \quad (1) $$`
- Number on right by appending `(1)`, `(2)` after `$$ ... $$`

⛔ **Never use** `\begin{equation}`, `\[...\]`, `\begin{align}` — engine doesn't render those.

### 4. Figures
```markdown
![Figure 1: Architecture overview.](figures/fig_arch.png)
```
- Alt text becomes the caption (centered, bold)
- Path relative to workspace root
- Prefer `.png`; `.pdf` works but Word renders PNG better

### 5. Tables (3-line academic style)
```markdown
**Table 1: Main results.**

| Method | Accuracy | F1 | Time(s) |
|--------|----------|----|---------|
| Baseline | 0.823 | 0.811 | 124 |
| Ours | **0.917** | **0.905** | 132 |
```

⛔ **Never use** `\begin{table}` or `\input{figures/TABLE_x.tex}`. If `figures/TABLE_*.md` exists, paste its content.

### 6. References
```markdown
## References

[1] LeSage J P, Pace R K. Introduction to Spatial Econometrics. CRC Press, 2009.
[2] Vaswani A, Shazeer N, Parmar N, et al. Attention is all you need. NeurIPS, 2017.
```

In-text citations use `[1]`, `[1, 2]`, `[1-3]` — **not** `\cite{key}`.

The engine detects `## References` and renders the following `[N] ...` lines with hanging indent.

## Workflow

### Step 0: Upstream check + resume

```bash
echo "=== Upstream check ==="
for f in PAPER_PLAN.md RESULTS.md NARRATIVE_REPORT.md experiment_results.md; do
    [ -f "$f" ] && echo "✅ $f ($(wc -c < $f) chars)" || echo "  $f not found"
done
[ -f figures/all_results.json ] && echo "✅ figures/all_results.json" || echo "⚠ no all_results.json"
PNG_COUNT=$(ls figures/*.png 2>/dev/null | wc -l)
PDF_COUNT=$(ls figures/*.pdf 2>/dev/null | wc -l)
echo "figures: PNG=$PNG_COUNT, PDF=$PDF_COUNT"

if [ -f paper/main.md ]; then
    cp paper/main.md "paper/main-backup-$(date +%s).md.bak"
    echo "Resume mode — backed up existing main.md"
fi
```

**⛔ Numbers come from data, not memory.** Before writing any results section:
```bash
[ -f figures/all_results.json ] && cat figures/all_results.json
[ -f RESULTS.md ] && cat RESULTS.md
```

**⛔ Claims-Evidence discipline**: re-read PAPER_PLAN.md claims-evidence matrix before each section. Every claim must be supported by data. If evidence is missing for a planned claim, write an honest "preliminary results suggest X, formal validation left to future work" instead of fabricating.

### Step 1: Figure inventory

```bash
ls -la figures/*.png figures/*.pdf 2>/dev/null
ls -la figures/TABLE_*.md 2>/dev/null
cat figures/latex_includes.tex 2>/dev/null  # reference only — DO NOT use the LaTeX commands
```

Build a mapping: figure ID → file → target section. Only embed figures whose files exist.

### Step 1.5: Pre-fetch verified reference pool

⛔ Build a verified pool **before** writing any `[N]` citations.

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp
# Search by topic:
#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "transformer attention" --max 5
```

Save the verified list to `_tmp/_verified_refs.txt` with one entry per line.

### Step 2: Write the paper

Order: **Method/core → Experiments → Introduction → Related Work → Conclusion → Abstract** (last).

Save everything in **`paper/main.md`** (single file). Suggested skeleton:

```markdown
# [Paper Title]

[Author placeholders]

## Abstract

[150-250 words]

**Keywords**: kw1; kw2; kw3

## 1. Introduction

[Hook → gap → contribution → results preview, ~1.5 pages]

## 2. Related Work

[Synthesize by category, not by paper, ~1-1.5 pages]

## 3. Method

### 3.1 Notation

### 3.2 Formulation

$$ \mathcal{L}(\theta) = \mathbb{E}_{x \sim \mathcal{D}} [\ell(f_\theta(x), y)] \quad (1) $$

### 3.3 Algorithm

![Figure 1: Method overview.](figures/fig_arch.png)

As shown in Figure 1, ... [≥ 5 lines analysis]

## 4. Experiments

### 4.1 Setup

### 4.2 Main results

**Table 1: Comparison with baselines.**

| Method | Acc | F1 |
|--------|-----|-----|
| ... | ... | ... |

Table 1 shows ... [numerical interpretation + comparison + reasoning, ≥ 2 paragraphs]

![Figure 2: Ablation.](figures/fig_ablation.png)

Figure 2 reveals ... [≥ 5 lines]

### 4.3 Ablation

### 4.4 Discussion

## 5. Conclusion

[Rephrase contributions + limitations + future work, ~0.5 page]

## References

[1] LeSage J P, Pace R K. Introduction to Spatial Econometrics. CRC Press, 2009.
[2] Vaswani A, et al. Attention is all you need. NeurIPS 2017.
```

**⛔ Style discipline:**
- No bullet/enumerated lists for narrative prose. Use "(1) ... (2) ..." inline numbering or transitional phrases ("First, ...; second, ...").
- Each paragraph 3-5 sentences minimum.
- Consecutive paragraphs cannot start with the same syntactic pattern.
- Every figure/table needs ≥ 5 lines of analysis after it before the next visual.

After each section:
```bash
words=$(wc -w < paper/main.md)
echo "running word count: $words"
```

<exemplar_depth>
#### Writing depth by venue

**ICLR/NeurIPS/ICML (9 pages main body, ~5400-6300 words for body)**:
- Abstract (0.3p, 150-250 words): what → why hard → how → evidence → strongest result. Self-contained
- Introduction (1.5p): hook → gap → contributions → results preview → hero figure. Front-load the contribution
- Related Work (1-1.5p): organize by category, synthesize not list. Each category: 3-5 papers with method summary + positioning vs this work
- Method (2-2.5p): notation → formulation → algorithm. Every formula has intuition explanation. Key derivation steps not skipped
- Experiments (3-4p): setup → main results table → comparison plots → ablation table → analysis. Every result has 1-2 paragraphs of interpretation (not just "our method outperforms")
- Conclusion (0.5p): rephrase contributions + limitations + future work

**JMLR/TPAMI journal (15-20 pages, ~9000-12000 words)**:
- Introduction (2-3p): more thorough literature positioning
- Related Work (2-3p): comprehensive survey by sub-topic
- Method (4-6p): full derivations, proofs, complexity analysis
- Experiments (6-8p): multiple datasets, extensive ablations, qualitative analysis, failure cases
- Conclusion (1p): detailed limitations and future directions
</exemplar_depth>

**Expansion strategies** (not padding — substantive content):
- Formula listed without derivation → add step-by-step derivation with intuition
- Result only says "Table X shows" → add 1-2 paragraphs (what numbers mean, comparison, reasoning)
- Related work only lists papers → add method summaries and positioning vs this work
- Algorithm only has pseudocode → add explanation of key steps and complexity analysis

#### Section guidelines (per-section minimums)
- Abstract: what → why hard → how → evidence → strongest result. Self-contained. 150-250 words.
- Introduction: hook → gap → contributions → results preview. 1.5 pages. Front-load contribution.
- Related Work: ≥ 1 full page. Organize by category, synthesize not list.
- Method: notation → formulation → algorithm. 1.5-2 pages.
- Experiments: setup → main results → ablations. 2.5-3 pages. Every claim needs evidence.
- Conclusion: rephrase contributions + limitations + future work. 0.5 pages.

#### Per-section minimum figures/citations
- Introduction: ≥ 1 figure (hero figure recommended) + ≥ 3 citations
- Related Work: ≥ 3 citations per category
- Method: ≥ 1 figure (architecture/algorithm) + ≥ 2 citations
- Experiments: ≥ 3 figures/tables + ≥ 3 citations
- Conclusion: ≥ 1 citation

### Step 3: Reference numbering

After writing prose:
```bash
grep -oE '\[[0-9]+(-[0-9]+)?(, *[0-9]+)*\]' paper/main.md | sort -u > _tmp/_cited.txt
ref_count=$(awk '/^## References/,0' paper/main.md | grep -cE '^\[[0-9]+\]')
echo "Cited tokens vs reference entries: $(wc -l < _tmp/_cited.txt) vs $ref_count"
```

Make every `[N]` in body match an entry in `## References`. No gaps.

⛔ Numbering must be strictly increasing by first appearance: [1] before [2] before [3]. No regression.
⛔ Multi-cite merging: `[1, 2, 3]` requires ascending order; non-adjacent IDs can be split `[1] [5]`.

### Step 3.5: Build verified BibTeX entries (citation discipline)

⛔ **Use scholar_fetch.py for ALL reference retrieval. NEVER fabricate BibTeX from memory.**

While drafting, use **descriptive citation keys** so you can search them later: `LastName_Year_topic_keywords`.
- ✅ `wang_2023_supply_chain_resilience` 
- ❌ `wang2023supply` (impossible to re-search)
- If author/year unknown, use `TODO__` prefix: `TODO__digital_economy_spatial_spillover`

When all draft text is done, search and verify each citation:

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp

# Collect citation keys / topic descriptors (you maintained while writing)
# For each, search scholar_fetch:
while IFS= read -r key; do
    query=$(echo "$key" | sed 's/^TODO__//; s/_/ /g')
    echo "--- Fetching: $key (query: $query) ---"
    $PYTHON "$SCHOLAR_SCRIPT" bibtex "$query" --max 3
    sleep 0.5
done < _tmp/_topics.txt
```

For each search result:
1. **Check `match_label`**: `"good"` → use; `"partial"` → verify title matches; `"low"` → likely wrong paper, retry with better keywords or use WebSearch.
2. **Check `match_score`**: < 0.3 → don't blindly trust.
3. Format the BibTeX result as a `[N] LastName F M, ... Title. Venue, Year.` line under `## References`.
4. If `bibtex_source=auto`, add `<!-- VERIFY -->` comment in the source markdown next to the citation.

⛔ References must include ≥ 30 entries for journal venues, ≥ 20 for conferences (rules of thumb).

### Step 4: De-AI polish

See `<de_ai_polish>` in writing_rules.md. Key:
- Drop "this paper proposes / we propose" boilerplate openings
- Replace "explore / investigate" with concrete verbs
- Cap "we" frequency

### Step 5: Cross-review

```bash
mkdir -p _tmp
cat << 'EOF' > _tmp/_review_prompt.txt
Review this academic paper draft. Focus on:
1. Logic flow and argument structure
2. Claim-evidence alignment
3. Clarity and concision
4. Missing/weak sections
5. Score (1-10) + top-3 improvements

## Paper:
EOF
cat paper/main.md >> _tmp/_review_prompt.txt
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_cross_review.txt
```

Skip if reviewer script unavailable.

### Step 5.5: Reverse outline test

Extract topic sentences from each paragraph → read them in sequence → check claim coverage → fix gaps.

```bash
# Extract first sentence of every paragraph (paragraphs separated by blank line)
awk 'BEGIN{RS=""} {print substr($0, 1, index($0,"\n")?index($0,"\n")-1:length($0)) }' paper/main.md \
  | grep -v '^#' | grep -v '^!' | grep -v '^|' | head -50
```

Reading just topic sentences should still tell the paper's story. If gaps exist (claim made but evidence missing, or evidence presented but claim not stated), fix them.

### Step 6: Final verification

Run the full output-contract verification block (top of this SKILL). Any ⛔ → go back, fix, re-verify.

## Key Rules (docx mode)

- **Single artifact**: `paper/main.md`
- **Never produce**: `.tex` / `.bib` / `.cls` / `.sty` / `.aux`
- **No LaTeX commands** in body
- **Math**: `$...$` / `$$...$$`
- **Figures**: `![alt](path)`
- **Tables**: markdown pipe tables
- **Citations**: `[N]`, references inline in `## References` section
- Body length ≥ MAX_PAGES × 600 words
- Numbers from data files, not memory
- Backup before overwrite
