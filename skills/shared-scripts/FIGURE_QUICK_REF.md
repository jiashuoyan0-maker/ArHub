# Figure Quick Reference (auto-extracted)
Read this BEFORE writing any figure script.

<selection_priority>
### Selection priority: match data shape, not visual novelty

Choose the figure type that best communicates your data, not the fanciest one available. The decision order is:

1. **First check the "By data shape" table below** — match your data characteristics to the recommended figure type
2. **If multiple options fit**, prefer the one your target audience (competition judges, reviewers) will instantly understand
3. **Use advanced recipes** (Lollipop, Dumbbell, Waterfall, SHAP, etc.) when they genuinely add information that basic charts cannot show — e.g., Waterfall shows incremental contribution, SHAP shows feature direction
4. **Use basic recipes** (grouped bar, line, scatter) when they are the clearest way to present the data — a well-made grouped bar chart is better than a confusing Bump chart

A paper needs visual variety — mix basic and advanced charts. A paper with ALL advanced charts looks like it's trying too hard. A paper with ALL bar charts looks monotonous. Balance is key.

**Hard rule**: do not use the same chart type more than 3 times in one paper. If you already have 3 bar charts, use an alternative for the next comparison. Same applies to lollipop charts or any other type.
</selection_priority>

### By data shape

| Data characteristic | Best figure type | Recipes file | Avoid |
|---|---|---|---|
| ≤3 methods × 1-2 metrics | Three-line table | — | Any chart — too few data points for a meaningful figure |
| 4+ methods × 1 metric | Lollipop Chart or Grouped Bar | advanced #1, basic #1 | — |
| A vs B (2 methods, multiple metrics) | Dumbbell Chart | advanced #2 | heatmap — 2 rows looks like a traffic light |
| A vs B vs C (3-5 methods, multiple metrics) | Grouped Bar Chart or Radar chart | basic #1, competition #5 | — |
| Methods × Metrics matrix (≤5×5) | Method Comparison Heatmap or Grouped Bar | advanced #16, basic #1 | — |
| Methods × Metrics (show trends across metrics) | Parallel Coordinates | advanced #17 | multiple separate charts |
| Methods × Metrics matrix (>5×5) | Heatmap with values | basic #5 | — |
| Methods × Datasets ranking | Bump Chart or Grouped Bar | advanced #4, basic #1 | — |
| Before/after comparison | Dumbbell Chart or Grouped Bar | advanced #2, basic #1 | — |
| Before/after (paired samples) | Paired Dot Plot | advanced #22 | grouped bar (hides individual variation) |
| Relative to baseline (±%) | Diverging Bar Chart | advanced #20 | grouped bar (doesn't show direction clearly) |
| Two-group mirror comparison | Back-to-Back Bar Chart | advanced #21 | — |
| Multi-model statistical comparison | Taylor Diagram | advanced #19 | separate RMSE/R²/StdDev bar charts |
| Distribution comparison (5-15 groups) | Ridgeline Plot | advanced #23 | multiple histograms (wastes space) |
| Distribution comparison (2-4 groups × categories) | Grouped Violin Plot | advanced #24 | box plot (hides distribution shape) |
| Module contribution (ablation) | Waterfall Chart | advanced #6 | bar chart |
| Time series (1-3 lines) | Line plot with CI band | basic #3 | — |
| Time series (4+ lines) | Small multiples (subplot grid) | basic #12 | spaghetti plot |
| Distribution (1 group) | Violin + strip | basic #11 | histogram |
| Distribution (2-5 groups) | Rain Cloud Plot | academic #4 | box plot |
| Proportion/composition | Donut Chart or Stacked Area | basic #6, #8 | pie chart |
| Correlation matrix | Heatmap + dendrogram | advanced #14 | plain heatmap |
| 2D scatter + relationship | Scatter + regression + R² | basic #4 | — |
| 2D joint distribution (large N) | Hexbin + marginal histograms | competition #24 | plain scatter (overplotting) |
| 2D joint distribution (small N, clusters) | KDE contour + marginal density | competition #25 | plain scatter |
| 2D relationship + distribution | Scatter + regression + marginal density | competition #26 | scatter without marginals |
| High-dim features | t-SNE/UMAP scatter | academic #2 | — |
| 3D clustering results (3 features) | 3D scatter + centroids | competition #27 | 2D scatter (loses dimension) |
| Multi-criteria evaluation | Radar chart | competition #5 | — |
| Feature importance | SHAP Summary Plot | advanced #7 | horizontal bar |
| Classification result | Confusion matrix | competition #10 | — |
| Binary classifier comparison | ROC + AUC | competition #11 | — |
| Probability reliability | Calibration Plot | advanced #11 | — |

### By problem domain (competition)

| Problem type | Recommended figures | Recipes |
|---|---|---|
| Optimization (GA/PSO/SA) | Convergence curve + 3D surface + Pareto front | comp #1, #6, #3 |
| Scheduling/routing | Gantt chart + Network path | comp #15, #16 |
| Classification/clustering | Confusion matrix + ROC + 3D cluster scatter | comp #10, #11, #13 |
| Regression/prediction | Prediction vs Actual with CI band + Error Rain Cloud + Multi-step decay + Model accuracy heatmap | empirical #12, #14, #16, #13 |
| Sensitivity analysis | Tornado chart + Contour + 3D surface | comp #2, #14, #6 |
| Spatial data | China province choropleth + Spatiotemporal matrix | comp #7, #18 |
| Multi-objective | 2D Pareto + 3D Pareto surface | comp #3, #19 |
| Factor decomposition | Waterfall chart | comp #20, advanced #6 |

### By problem domain (academic/empirical)

| Paper type | Recommended figures | Recipes |
|---|---|---|
| DID/causal inference | Parallel trends + Event study + Placebo | empirical #2, #3, #4 |
| Regression analysis | Forest plot + Heterogeneity forest + Marginal effects | empirical #1, #10, #15 |
| Prediction/forecasting | Prediction with CI band + Error Rain Cloud + Multi-step decay + Model heatmap | empirical #12, #14, #16, #13 |
| Deep learning | Training curves + Attention map + t-SNE | academic #3, #6, #2 |
| Model comparison | Grouped Bar + Method Comparison Heatmap + Radar | basic #1, advanced #16, comp #5 |
| Hyperparameter tuning | Sensitivity grid + 3D loss landscape | academic #7, #8 |
| Meta-analysis | Forest plot + Funnel plot | empirical #1, advanced #12 |
| Survival analysis | Kaplan-Meier curve | advanced #9 |
| Genomics/omics | Volcano plot + Cluster heatmap | advanced #10, #14 |
| Method agreement | Bland-Altman plot | advanced #8 |

### Anti-patterns (check before generating — but use judgment)

Not every "upgrade" is appropriate. Check this table, but choose based on clarity for your audience.

| ❌ If you were going to use... | ✅ Consider this instead | Why | When to upgrade |
|---|---|---|---|
| Single-metric bar chart for ranking | Lollipop Chart | Less visual noise for pure ranking | When showing 5+ items ranked by one metric |
| Horizontal bar for feature importance | SHAP Summary Plot | Shows direction + magnitude | When you have SHAP values available |
| Bar chart for ablation | Waterfall Chart | Shows incremental contribution | Always — waterfall is strictly better for ablation |
| Bar chart for before/after (2 groups) | Dumbbell Chart | Shows direction and magnitude of change | When comparing exactly 2 conditions |
| Plain box plot | Rain Cloud Plot | Distribution shape + box stats + raw data | When sample size > 20 and distribution shape matters |
| Pie chart | Donut Chart | More modern, less visual distortion | Always |
| Plain heatmap | Heatmap + dendrogram | Adds clustering structure | When row/column ordering matters |
| Stacked bar (non-temporal) | Sankey Diagram | Shows flow direction | When data represents flow/routing |
| RdYlGn colormap | coolwarm or YlOrRd | Red-yellow-green = traffic light | Always |

**Keep using grouped bar chart when:**
- Comparing 3-5 methods across 2-5 metrics (this is what grouped bar charts are designed for)
- Your audience is competition judges or non-specialist reviewers who expect familiar chart types
- The data has clear, discrete categories on the x-axis
- You already have too many advanced charts in the paper and need visual variety

**Keep using line chart when:**
- Showing trends over time or continuous x-axis
- Comparing convergence curves or training progress
</figure_selection_guide>
### ⛔ 颜色使用通用规则

**数据颜色**（柱子、线条、散点等）：必须用 `PALETTE[i]` 或 `PALETTE_LIGHT[i]`，不要硬编码 hex 颜色。
**语义颜色**（上升/下降/中性等）：用 `COLORS['up']`、`COLORS['down']`、`COLORS['neutral']`，不要硬编码 `#27ae60` 或 `#e74c3c`。
**装饰颜色**（网格线/文字/标注框）：用 `COLORS['grid']`、`COLORS['text']`、`COLORS['bg_box']`。
**渐变起点**：用 `_lighten(PALETTE[0], 0.6)` 而不是硬编码 `#b0c4de`。

这样切换配色方案（journal/soft/npg/colorblind）时，所有颜色自动跟随。

配方代码中的硬编码颜色是历史遗留，写新代码时用上述变量替代。

### 柱状图（Bar Chart）
