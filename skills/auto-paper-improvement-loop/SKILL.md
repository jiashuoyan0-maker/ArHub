---
name: auto-paper-improvement-loop
description: "Autonomously improve a generated paper via external reviewer model review → implement fixes → recompile, for 2 rounds. Use when user says \"改论文\", \"improve paper\", \"论文润色循环\", \"auto improve\", or wants to iteratively polish a generated paper."
argument-hint: [paper-directory]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Auto Paper Improvement Loop: Review → Fix → Recompile

Autonomously improve the paper at: **$ARGUMENTS**

## Context

Runs after `/paper-write` + `/paper-compile`. Iterates on writing quality (not research).

## Constants

- **MAX_ROUNDS = 2** — Round 1 catches structural issues, Round 2 catches presentation issues.
- **REVIEWER_SCRIPT** — External reviewer script. Thread via `_reviewer_thread.json`.
- **HUMAN_CHECKPOINT = false** — When true, pause after each review for user input.
- **LATEX_ENGINE** — Auto-detect: ctex/xelatex in main.tex → xelatex, otherwise pdflatex.
- **CUSTOM_REQUIREMENTS** — Highest priority.

## State Persistence

Writes `PAPER_IMPROVEMENT_STATE.json` after each round for crash recovery:
```json
{"current_round": 1, "last_score": 6, "status": "in_progress", "timestamp": "..."}
```
On startup: if exists + in_progress + <24h → resume. Otherwise start fresh.

## Workflow

### Step 0: Preserve Original
```bash
cp paper/main.pdf paper/main_round0_original.pdf
```

### Step 1: Collect Paper Text
Concatenate all `paper/sections/*.tex` for review.

### Step 2: Round 1 Review

Send the full paper text to the external reviewer via `reviewer_client.py`:

```bash
mkdir -p _tmp
cat << 'REVIEW_EOF' > _tmp/_review_prompt.txt
You are reviewing an academic paper. Please provide a detailed, structured review.

## Full Paper Text:
REVIEW_EOF
cat _tmp/_paper_full_text.tex >> _tmp/_review_prompt.txt
cat << 'REVIEW_EOF' >> _tmp/_review_prompt.txt

## Review Instructions
Please act as a senior reviewer. Provide:
1. **Overall Score** (1-10, where 6 = weak accept, 7 = accept)
2. **Summary** (2-3 sentences)
3. **Strengths** (3-5 bullet points)
4. **Weaknesses** (categorized as CRITICAL / MAJOR / MINOR, each with specific location and actionable fix)
   - Check for "figure-as-subject" AI pattern: paragraphs starting with "图X展示了"/"As shown in Figure X" — flag as MAJOR if ≥3 occurrences
5. **Verdict**: "Accept" / "Almost" / "Reject"
6. **Actionable Fixes** (ordered by priority, each with exact section and what to change)
REVIEW_EOF
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_round1_review.txt
```

If the reviewer script fails (API key not configured or network error), perform the review using self-analysis — act as a senior reviewer, score honestly, and proceed to Step 3. Cross-model review is preferred for objectivity but not required.

### Step 2b: Human Checkpoint (if enabled)
Present score + weaknesses. Wait for "go" / custom instructions / "skip N" / "stop".
Non-interactive mode: auto-proceed.

### Step 3: Implement Round 1 Fixes

Priority: CRITICAL → MAJOR → MINOR.

Common fix patterns:
| Issue | Fix |
|-------|-----|
| Assumption-model mismatch | Rewrite assumption, add bridging proposition |
| Overclaims | Soften: "validate"→"demonstrate relevance" |
| Missing metrics | Add quantitative table with caveats |
| Notation confusion | Rename globally, add Notation paragraph |
| Figure-as-subject writing | Rewrite: move figure ref to parenthetical, lead with analysis point |
| Missing references | Add to bib, cite appropriately |

### Step 4: Recompile Round 1

Auto-detect engine. Manual 4-step: engine→bibtex→engine→engine. Save `main_round1.pdf`.

### Step 5-6: Round 2 Review + Fixes

Same process. Use same `_tmp/_reviewer_thread.json` for context continuity (multi-turn dialogue is automatic):

```bash
cat << 'REVIEW_EOF' > _tmp/_review_prompt.txt
Since your last review, we have implemented the following fixes:
[list the fixes from Step 3]

Please re-review the updated paper. Focus on:
1. Were the CRITICAL/MAJOR issues adequately addressed?
2. Any new issues introduced by the fixes?
3. Updated score and verdict.

## Updated Paper Text:
REVIEW_EOF
cat _tmp/_paper_full_text.tex >> _tmp/_review_prompt.txt
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_round2_review.txt
```

If reviewer unavailable, use self-analysis for Round 2 as well.

### Step 7: Recompile Round 2

Save `main_round2.pdf`.

### Step 8: Format Check

Check overfull hbox (>10pt → fix), page count vs limit, underfull warnings.

### Step 9: Document Results

Create `paper/PAPER_IMPROVEMENT_LOG.md`：

```markdown
# Paper Improvement Log

## Score Progression

| Round | Score | Verdict | Key Changes |
|-------|-------|---------|-------------|
| Round 0 (original) | X/10 | No/Almost/Yes | Baseline |
| Round 1 | Y/10 | No/Almost/Yes | [summary of fixes] |
| Round 2 | Z/10 | No/Almost/Yes | [summary of fixes] |

## Round 1 Review & Fixes

### Review (full text)
[Complete raw review text, verbatim]

### Fixes Implemented
1. [Fix description + which files changed]
2. [Fix description]

## Round 2 Review & Fixes

### Review (full text)
[Complete raw review text, verbatim]

### Fixes Implemented
1. [Fix description]
2. [Fix description]

## PDFs
| File | Size | Description |
|------|------|-------------|
| main_round0_original.pdf | X KB | Before improvement |
| main_round1.pdf | X KB | After round 1 |
| main_round2.pdf | X KB | After round 2 (final) |
| main.pdf | X KB | = round2 |
```

## Output

```
paper/
├── main_round0_original.pdf
├── main_round1.pdf
├── main_round2.pdf (final)
├── main.pdf (= round2)
└── PAPER_IMPROVEMENT_LOG.md
```

## Key Rules

- Preserve all PDF versions
- Save full raw review text (don't truncate)
- Same thread file for Round 2 (context continuity)
- Always recompile after fixes
- Don't fabricate experimental results
- Soften overclaims rather than adding unsupported claims
- Global consistency when renaming notation (all files)
- ⛔ Main output: `paper/main.pdf` + `paper/PAPER_IMPROVEMENT_LOG.md`. Don't write extra reports (e.g. AUTO_PAPER_IMPROVEMENT_REPORT.md, AUTO_PAPER_IMPROVEMENT_FINAL_REPORT.md) to root
- ⛔ Temp files (`_review_prompt.txt`, `_paper_full_text.tex`, `_round1_review.txt` etc.) go to `_tmp/`
- Large files: Bash heredoc
