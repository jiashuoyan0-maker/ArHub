---
name: research-review
description: Get a deep critical review of research via external reviewer. Use when user says "review my research", "help me review", "get external review", or wants critical feedback on research ideas, papers, or experimental results.
argument-hint: [topic-or-scope]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, Agent
---

# Research Review via External Reviewer (xhigh reasoning)

Get a multi-round critical review of research work from an external LLM with maximum reasoning depth.

## Context: $ARGUMENTS

## Prerequisites

- **Reviewer Script** (optional but recommended): `reviewer_client.py` must be accessible via `$REVIEWER_SCRIPT` environment variable.
- This gives Claude Code access to the configured reviewer model for cross-model review.
- **If the reviewer script fails (e.g. API key not configured)**: This skill will perform the review using Claude's own critical analysis capabilities. Cross-model review via the reviewer script is preferred for objectivity, but not required.

## Workflow

### Step 1: Gather Research Context
Before calling the external reviewer, compile a comprehensive briefing:
1. Read project narrative documents (e.g., STORY.md, README.md, paper drafts)
2. Read any memory/notes files for key findings and experiment history
3. Identify: core claims, methodology, key results, known weaknesses

### Step 2: Initial Review (Round 1)
Send a detailed prompt to the external reviewer:

```bash
# 写入评审 prompt
cat << 'REVIEW_EOF' > _review_prompt.txt
[Full research context + specific questions]
Please act as a senior ML reviewer (NeurIPS/ICML level). Identify:
1. Logical gaps or unjustified claims
2. Missing experiments that would strengthen the story
3. Narrative weaknesses
4. Whether the contribution is sufficient for a top venue
Please be brutally honest.
REVIEW_EOF

# 调用外部评审模型
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _review_prompt.txt --thread-file _reviewer_thread.json
```

### Step 3: Iterative Dialogue (Rounds 2-N)
Use `reviewer_client.py` with the same `--thread-file` to continue the conversation (对话历史通过 `_reviewer_thread.json` 自动保存):

For each round:
1. **Respond** to criticisms with evidence/counterarguments
2. **Ask targeted follow-ups** on the most actionable points
3. **Request specific deliverables**: experiment designs, paper outlines, claims matrices

```bash
cat << 'REVIEW_EOF' > _review_prompt.txt
[follow-up content for this round]
REVIEW_EOF

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _review_prompt.txt --thread-file _reviewer_thread.json
```

Key follow-up patterns:
- "If we reframe X as Y, does that change your assessment?"
- "What's the minimum experiment to satisfy concern Z?"
- "Please design the minimal additional experiment package (highest acceptance lift per GPU week)"
- "Please write a mock NeurIPS/ICML review with scores"
- "Give me a results-to-claims matrix for possible experimental outcomes"

### Step 4: Convergence
Stop iterating when:
- Both sides agree on the core claims and their evidence requirements
- A concrete experiment plan is established
- The narrative structure is settled

### Step 5: Document Everything
Save the full interaction and conclusions to **`review_report.md`** in the project root:
- Round-by-round summary of criticisms and responses
- Final consensus on claims, narrative, and experiments
- Claims matrix (what claims are allowed under each possible outcome)
- Prioritized TODO list with estimated compute costs
- Paper outline if discussed

Update project memory/notes with key review conclusions.

## Key Rules

- **Large file handling**: For long output files (reports, reviews, etc.), ALWAYS use Bash heredoc (`cat << 'EOF' > file` and `cat << 'EOF' >> file`) to write in chunks instead of the Write tool. The Write tool may silently fail on large content due to output token limits, causing empty parameters. Do NOT use the Write tool for files longer than ~150 lines.
- Send comprehensive context in Round 1 — the external model cannot read your files
- Be honest about weaknesses — hiding them leads to worse feedback
- Push back on criticisms you disagree with, but accept valid ones
- Focus on ACTIONABLE feedback — "what experiment would fix this?"
- 对话历史通过 `_reviewer_thread.json` 自动保存，可随时恢复
- The review document should be self-contained (readable without the conversation)

## Prompt Templates

### For initial review:
"I'm going to present a complete ML research project for your critical review. Please act as a senior ML reviewer (NeurIPS/ICML level)..."

### For experiment design:
"Please design the minimal additional experiment package that gives the highest acceptance lift per GPU week. Our compute: [describe]. Be very specific about configurations."

### For paper structure:
"Please turn this into a concrete paper outline with section-by-section claims and figure plan."

### For claims matrix:
"Please give me a results-to-claims matrix: what claim is allowed under each possible outcome of experiments X and Y?"

### For mock review:
"Please write a mock NeurIPS review with: Summary, Strengths, Weaknesses, Questions for Authors, Score, Confidence, and What Would Move Toward Accept."
