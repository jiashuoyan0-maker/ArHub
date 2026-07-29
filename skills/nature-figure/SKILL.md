---
name: nature-figure
description: "Generate publication-ready matplotlib figures matching Nature journal standards. Use when user says 'Nature figure', 'Nature style plot', or needs high-impact journal figures with Nature typography, color systems, and SVG/PDF export."
argument-hint: [figure-plan-or-data-path]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, mcp__codex__codex, mcp__codex__codex-reply
---

# Nature Figure: Publication-Quality Figures for Nature/High-Impact Journals

Generate Nature-style figures from: **$ARGUMENTS**

## Constants

- **FIG_DIR = `figures/`**
- **PRIMARY_FORMAT = `pdf`** (LaTeX embedding, vector)
- **DPI = 300**
- **CUSTOM_REQUIREMENTS** — User-specified requirements, highest priority.

## Mandatory rcParams (apply at top of EVERY script)

```python
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['svg.fonttype'] = 'none'          # editable text in SVG/PDF
plt.rcParams['font.size'] = 16                 # 24 for large bar panels
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.linewidth'] = 2.5           # 3 for big bars, 2 for compact
plt.rcParams['legend.frameon'] = False
```

### Integration with plot_utils.py

Try `setup_style(palette='nature')` first. If unavailable, use inline rcParams above as fallback:

```python
import os, sys, shutil
os.makedirs('_utils', exist_ok=True)
for src in ['plot_utils.py']:
    for search in ['skills/shared-scripts', '../skills/shared-scripts']:
        p = os.path.join(search, src)
        if os.path.isfile(p):
            shutil.copy2(p, f'_utils/{src}')
            break
sys.path.insert(0, '.')
try:
    from _utils.plot_utils import setup_style, save_fig, PALETTE
    setup_style(palette='nature')
except (ImportError, TypeError):
    # Fallback: apply Nature rcParams directly
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    plt.rcParams['svg.fonttype'] = 'none'
    plt.rcParams['font.size'] = 16
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.linewidth'] = 2.5
    plt.rcParams['legend.frameon'] = False
```

## Nature Color Palette

```python
PALETTE_NATURE = {
    "blue_main":      "#0F4D92",   # deep blue — hero method
    "blue_secondary": "#3775BA",   # medium blue
    "green_1": "#DDF3DE",          # light positive
    "green_2": "#AADCA9",          # mid positive
    "green_3": "#8BCF8B",          # strong positive
    "red_1":   "#F6CFCB",          # light baseline
    "red_2":   "#E9A6A1",          # mid baseline
    "red_strong": "#B64342",       # strong baseline/negative
    "neutral_light": "#CFCECE",
    "neutral_mid":   "#767676",
    "neutral_dark":  "#4D4D4D",
    "neutral_black": "#272727",
    "gold":   "#FFD700",
    "teal":   "#42949E",
    "violet": "#9A4D8E",
}

# For unified-family figures (NMI-style dense pages)
PALETTE_NMI_PASTEL = {
    "baseline_dark": "#484878",
    "baseline_mid":  "#7884B4",
    "baseline_soft": "#B4C0E4",
    "ours_tiny":  "#E4E4F0",
    "ours_base":  "#E4CCD8",
    "ours_large": "#F0C0CC",
    "delta_up":   "#2E9E44",
    "delta_down": "#E53935",
}
```

Semantic rules:
- Blue = proposed/hero method
- Green = positive variants/improvements
- Red/pink = baselines/contrast
- Neutral grays = reference/background
- Use NMI pastel when comparing method families on dense pages

## Default Operating Stance

1. **Classify** the figure into one of 5 Nature page archetypes (see below)
2. **Hero panel** concept: one dominant panel + subordinate evidence panels
3. **Direct labels** over legends when categories are spatially fixed
4. **White background** for plots; black only for microscopy/imaging plates
5. **One restrained palette** per figure: neutral + signal + accent families
6. **Panel labels**: small bold lowercase (a, b, c) near top-left edge

## 5 Nature Page Archetypes

| Archetype | Layout | When to use |
|-----------|--------|-------------|
| Schematic-led composite | Wide story panel + smaller quant panels below | Method explanation + validation |
| Dark image plate | Black tiles with fluorescent channels | Microscopy, imaging, volume rendering |
| Clinical triptych | Top longitudinal, middle forest, bottom summary | Clinical/longitudinal studies |
| Dense categorical | Grid of equal panels, unified palette | Multi-metric comparisons |
| Asymmetric hero | One dominant panel spanning grid cells + small supports | Single key result + context |

## Layout Rules

- Hero panel gets visual hierarchy; support panels validate, not compete
- Panel labels: `ax.set_title('a', loc='left', pad=3, fontsize=14, fontweight='bold')`
- Tight gutters; increase spacing when dark/light modalities touch
- Prefer shared legend strip above a row over per-panel legends
- Dynamic y-axis: tighten to data range, never fixed 0–100 for narrow bands
- figsize guidance: journal-width composite (7.0–7.4, 5.5–7.8); bar panels (28–45, 6–12)

## Export Policy

**根据工作流模式选择输出格式（查看 CLAUDE.md 末尾的格式指令）：**

```python
import os
os.makedirs('./figures/', exist_ok=True)
fig.tight_layout(pad=0.5)

# 默认（LaTeX 模式）— 只输出 PDF（矢量、给 \includegraphics 用）
fig.savefig('./figures/name.pdf', dpi=300, bbox_inches='tight')

# Word 模式（CLAUDE.md 含「⛔ 输出格式：仅 PNG」时）— 只输出 PNG（350 DPI）
# fig.savefig('./figures/name.png', dpi=350, bbox_inches='tight', facecolor='white')

plt.close(fig)
```

- **LaTeX 模式：只输出 PDF**（不要同时存 PNG，避免冗余）
- **Word 模式：只输出 PNG**（DPI 350 防中文糊；不要存 PDF，Word 不能嵌 PDF）
- 总是 `bbox_inches='tight'` + `plt.close(fig)`
- 检查 CLAUDE.md 末尾决定用哪种格式

## Workflow

### Step 1: Read data + classify figure type

Read PAPER_PLAN.md and data files. For each figure, classify into archetype and choose palette.

### Step 2: Read references + Generate scripts

**⛔ 必须在写任何绑图脚本之前，先读取以下参考文件：**

```bash
# 必读：配色方案和 helper 函数
cat _references/api.md

# 必读：根据图表类型选择对应教程
cat _references/tutorials.md

# 按需读取（多面板/复杂布局时）
cat _references/common-patterns.md

# 按需读取（需要了解 Nature 真实页面风格时）
cat _references/nature-2026-observations.md

# 按需读取（雷达图/3D/特殊图表时）
cat _references/chart-types.md
```

One script per figure. Each starts with Nature rcParams setup (`setup_style(palette='nature')` or inline rcParams). Follow the patterns from `_references/tutorials.md` as starting point.

### Step 3: Execute and validate

Run each script. Verify PDF output exists in `figures/`. Check:
- No `plt.title()` (captions in LaTeX only)
- Font ≥ 9pt final size
- Grayscale-distinguishable
- Panel labels present for multi-panel figures
- Colors from Nature palette, not matplotlib defaults

### Step 4: Generate latex_includes.tex

Include all figures with `[H]` float specifier and English captions.

## Related Files

| File | Open when |
|------|-----------|
| [references/api.md](references/api.md) | Palette constants, helper function signatures, validation rules |
| [references/design-theory.md](references/design-theory.md) | Typography, color theory, layout rationale |
| [references/chart-types.md](references/chart-types.md) | Radar, 3D sphere, fill_between, scatter patterns |
| [references/common-patterns.md](references/common-patterns.md) | Ultra-wide panels, legend-only axes, print-safe bars |
| [references/nature-2026-observations.md](references/nature-2026-observations.md) | Real Nature page archetypes from 2026 issues |
| [references/tutorials.md](references/tutorials.md) | End-to-end walkthroughs: bars, trends, heatmaps |
| `_utils/plot_utils.py` | Shared plotting infrastructure |

## Key Rules

- ⛔ Never use `svg.fonttype = 'path'` — breaks text editability
- ⛔ No `plt.title()` — captions belong in LaTeX
- ⛔ No matplotlib default colors — always use Nature palette
- ⛔ No grid lines by default — sparse y-ticks guide the eye
- Active voice in axis labels; concise legend entries
- For ablation: single color with varying alpha (0.2–1.0)
- Error bars: `elinewidth=2, capthick=2, capsize=10`
- Heatmap text contrast: white on dark cells, black on light cells
