---
name: paper-write-nature
description: "Draft a Nature-style LaTeX paper with hourglass structure, reader-first logic, and publication-quality English. Use when user says 'Nature paper', 'Nature writing', 'SCI writing', or needs high-impact journal manuscript drafting."
argument-hint: [venue-or-section]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch, mcp__codex__codex, mcp__codex__codex-reply
---

# Nature-Style Paper Writing

Draft a Nature-quality LaTeX paper based on: **$ARGUMENTS**

## Constants

- **TARGET_VENUE = `Nature`** — Override via Additional Parameters. Supported: Nature, Nature Methods, Nature Machine Intelligence, Communications journals.
- **MAX_PAGES** — Nature Article: ~5 pages main text + Methods. Override via Additional Parameters.
- **ANONYMOUS = false** — Nature uses non-anonymous submission.
- **DBLP_BIBTEX = true** — Fetch real BibTeX from DBLP/CrossRef. Never fabricate.
- **CUSTOM_REQUIREMENTS** — Highest priority.
- **REVIEWER_SCRIPT** — External reviewer script.

## Inputs

1. PAPER_PLAN.md — outline with claims-evidence matrix, figure plan
2. RESULTS.md — structured experiment results
3. figures/ — SVGs/PDFs + latex_includes.tex
4. Existing .bib file (or will create)

If no PAPER_PLAN.md, generate minimal outline from available docs.

## Core Architecture

### 1. Identify Paper Type First

Before writing, determine the paper type:

- **Research paper**: why the phenomenon matters → what was done → what was found → what it means
- **Methods paper**: does the method work → is it reproducible → is it better under fair comparison
- **Hypothesis-based**: establish or rule out a causal explanation
- **Algorithmic/device**: propose procedure/tool/system → show reliable and advantageous performance

Do not use one narrative logic for all paper types.

### 2. Reader-First Writing Order

Write for the reader's cognitive sequence:
1. Is this relevant to me? (Introduction hook)
2. What is new here? (Contribution statement)
3. Do I trust it? (Results + Methods)
4. Can I reuse it? (Methods detail + Data Availability)
5. What does it mean? (Discussion + boundaries)

### 3. Productive Writing Order

For research articles, write in this order:
1. **Results** — anchor everything in evidence
2. **Introduction** — frame the gap now that you know the findings
3. **Title** — crystallize the contribution
4. **Discussion** — interpret and bound
5. **Materials and Methods** — reproducibility
6. **Abstract** — mini-paper summary last

### 4. Hourglass Structure

- **Introduction**: open broadly → narrow to specific gap → state question/hypothesis
- **Discussion/Conclusion**: widen again → connect findings to literature → explain how gap was filled

### 5. Paragraph Architecture: Claim-Evidence-Boundary

Every paragraph follows:
- **Claim**: one controlling idea (topic sentence)
- **Evidence**: data, comparison, explanation, literature support
- **Boundary**: limitation, scope, or transition to next claim

## Section Responsibilities

### Title
- ≤ 75 characters including spaces (Nature guideline)
- Searchable, specific, restrained, defensible
- Pattern: `[Core entity] in/through/by [mechanism or context]`
- No vague hooks, no unverified "first"

### Abstract (150–200 words)
Mini-paper structure: context/problem → gap → approach → key result with numbers → implication

### Introduction (~600–800 words for Nature)
- Hook: why the topic matters broadly
- Known: what is established
- Gap: what remains unresolved
- Aim: what this study asks/does
- Value: brief indication of approach and significance
- Do NOT summarize Results or Conclusion here
- Short paragraphs OK (Nature style allows 3–4 sentence paragraphs)

### Results
- Past tense: report what was observed
- Orient reader to figure/table → state main observation → quantitative detail → patterns
- Results = what happened, NOT what it means
- Each result paragraph tied to a specific figure or table
- Active voice preferred: "We observed..." not "It was observed that..."

### Discussion
- Restate main finding → plausible explanations → compare with earlier work → limitations → implications → future work
- Short rule: Results = what we observed; Discussion = how we understand it and when it may fail
- Three-part close: contribution → key evidence → implication with boundary

### Materials and Methods
- Specific, complete, transparent, reproducible
- Another group must determine: ethical conformity, materials/conditions, key parameters, data processing, statistical tests, software versions
- Never: "under standard conditions", "using routine methods", "data were analyzed statistically"

### Data Availability Statement
Generate using Nature data policy principles:
- Map each dataset to access route: public repository, controlled access, within supplement, reused source, third-party restricted
- Prefer DOI/accession numbers over personal websites
- Pattern: "The [data type] generated in this study have been deposited in [repository] under accession code [XXX]. Source data are provided with this paper."
- Flag "available upon request" as weak unless legally/ethically required

## Failure Mode Diagnosis

Before editing any section, diagnose the main problem in priority order:

1. **Paper type** — wrong narrative logic for this paper type?
2. **Section job** — section not fulfilling its rhetorical responsibility?
3. **Paragraph logic** — claim without evidence? evidence without claim? missing boundary?
4. **Sentence polish** — clutter, passive voice, overclaim?

Fix from top down. Do not polish sentences while reasoning is broken.

## Nature-Specific Style Rules

### Sentence control
- Each sentence ≤ 30 words
- One core subject-verb proposition per sentence
- Split overloaded sentences rather than polishing cosmetically
- Active voice preferred: "We show..." not "It is shown that..."

### Paragraph control
- Short paragraphs OK (3–5 sentences typical for Nature)
- Each paragraph: one controlling idea + support
- Thematic linking, not repetitive "This suggests..." openings

### De-AI Polish Rules

Remove or replace these AI-typical words:
- "delve" → "examine", "investigate"
- "pivotal" → "important", "central"
- "landscape" → "field", "area"
- "multifaceted" → "complex"
- "underscores" → "shows", "highlights"
- "leveraging" → "using"
- "novel" (overused) → "new", or remove if claim is clear from context
- "groundbreaking" → remove or use specific evidence
- "paradigm shift" → describe the actual change
- "in conclusion" → just state the conclusion directly

### Hedging (Academic Phrasebank patterns)
- "These results suggest that..."
- "A possible explanation is that..."
- "This discrepancy may reflect..."
- "To our knowledge, this is the first..."
- "Further work is needed to determine whether..."

### Transitions
- Contrast: "However,", "By contrast,", "Nevertheless,"
- Addition: "Moreover,", "Furthermore,", "In addition,"
- Cause: "Consequently,", "As a result,", "Therefore,"
- Concession: "Although...,", "Despite...,", "Notwithstanding,"

### Limitations acknowledgment
- "These results should be interpreted with caution because..."
- "A limitation of this study is that..."
- "The generalizability of these findings is limited by..."

## ⛔⛔⛔ Output Contract (highest priority)

**Mandatory output depends on `params.output_format`**:

- **PDF mode**: `paper/main.tex` (≥ 5KB) + `paper/sections/*.tex` + `paper/references.bib`
- **docx mode**: `paper/main.md` (single file, ≥ 5KB). Do NOT create `paper/main.tex`

⛔ **MUST run output verification before ending the step**:
```bash
MODE=$(grep -q "Word（.docx）\|docx mode" CLAUDE.md 2>/dev/null && echo docx || echo pdf)
PASS=true
if [ "$MODE" = "docx" ]; then
    [ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
    [ "$SZ" -ge 5120 ] && echo "✅ paper/main.md ($SZ)" || { echo "❌ paper/main.md missing"; PASS=false; }
else
    [ -f paper/main.tex ] && SZ=$(wc -c < paper/main.tex) || SZ=0
    [ "$SZ" -ge 5120 ] && echo "✅ paper/main.tex ($SZ)" || { echo "❌ paper/main.tex missing"; PASS=false; }
fi
[ "$PASS" != true ] && echo "⛔ Output verification FAILED — must complete before ending"
```

**If verification fails, complete the missing files instead of exiting**.

## Workflow

### Step 1: Read inputs and plan

Read PAPER_PLAN.md, RESULTS.md, figures/. Identify paper type and writing order.

### Step 2: Draft Results first

Write Results section anchored to figures and data. Each paragraph: orient → observe → quantify → pattern.

### Step 3: Draft Introduction

Frame the gap now that findings are known. Hourglass: broad → narrow → specific aim.

### Step 4: Draft Title

Crystallize contribution in ≤ 75 characters.

### Step 5: Draft Discussion

Interpret findings, compare with literature, acknowledge limitations, state implications.

### Step 6: Draft Methods

Complete, reproducible, specific. Include statistical tests, software versions, parameters.

### Step 7: Draft Abstract

150–200 words. Context → gap → approach → key result → implication.

### Step 8: Data Availability + Author Contributions

Generate Data Availability statement. Add Author Contributions template.

### Step 9: Self-review

Run failure mode diagnosis on each section. Check:
- [ ] Hourglass structure intact
- [ ] Each paragraph has claim-evidence-boundary
- [ ] No AI-typical language remaining
- [ ] Active voice dominant
- [ ] Sentences ≤ 30 words
- [ ] Title ≤ 75 characters
- [ ] Abstract 150–200 words
- [ ] No fabricated references
- [ ] Hedging appropriate (no overclaim)
- [ ] Data Availability complete

### Step 10: Compile

Save to `paper/main.tex` with proper Nature formatting. Generate `paper/references.bib`.

## Related Files

| File | Open when |
|------|-----------|
| [references/section-moves.md](references/section-moves.md) | Section-specific move patterns and phrase families |
| [references/style-guardrails.md](references/style-guardrails.md) | Academic style checks, hedging, transitions |
| `shared-scripts/writing_rules.md` | General LaTeX writing rules |
| `shared-scripts/compile_check.sh` | Compilation verification |

## Key Rules

- ⛔ Never fabricate references — use DBLP/CrossRef or flag with [VERIFY]
- ⛔ Never upgrade association to causation
- ⛔ Never let AI draft the core scientific argument from scratch
- ⛔ No `plt.title()` in figures — captions in LaTeX only
- Language serves argument — do not polish sentences while reasoning is broken
- Write with empathy for the reader: relevance → novelty → trust → reuse → meaning
- If the draft is structurally rough, reconstruct logic first, prose second
- Nature allows short paragraphs — do not pad for length
- Direct claims with evidence, not hedged-to-meaninglessness
