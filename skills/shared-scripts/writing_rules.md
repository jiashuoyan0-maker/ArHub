# Shared Writing Rules

Common rules for all paper-writing skills (paper-write, paper-write-zh, comp-paper-zh, comp-paper-en).
Read this file at the start of writing workflow via `cat _utils/writing_rules.md`.

<figure_text_interleaving>
## Figure-Text Interleaving

Every figure/table needs surrounding text. This is the single most important quality signal
that separates human-written papers from AI-generated ones.

### Pattern (Chinese example)

```latex
为了分析各子问题的求解精度，我们将模型预测值与实际值进行对比，结果如图\ref{fig:compare}所示。

\begin{figure}[H]
  \centering
  \includegraphics[width=0.9\textwidth]{../figures/fig_compare.pdf}
  \caption{模型预测值与实际值对比}
  \label{fig:compare}
\end{figure}

从图\ref{fig:compare}可以看出，模型在问题一中的预测误差最小（RMSE=0.023），
而问题三由于数据稀疏性，误差相对较大（RMSE=0.156）。这表明模型对密集数据的
拟合能力较强，但在稀疏场景下仍有改进空间。

进一步地，我们对模型的关键参数进行灵敏度分析，结果见表\ref{tab:sensitivity}。

\begin{table}[H]
  \centering
  \caption{关键参数灵敏度分析}
  \label{tab:sensitivity}
  \begin{tabular}{lcc}
    \toprule
    参数 & 变化范围 & 目标函数变化 \\
    \midrule
    $\alpha$ & 0.1--0.9 & $<5\%$ \\
    $\beta$  & 0.01--0.5 & $<3\%$ \\
    \bottomrule
  \end{tabular}
\end{table}

表\ref{tab:sensitivity}显示，当参数$\alpha$从0.1变化到0.9时，目标函数值变化幅度
不超过5\%，说明模型对该参数不敏感，具有较好的鲁棒性。
```

### Pattern (English example)

```latex
As shown in Figure~\ref{fig:main}, we compare our method against three baselines
across all evaluation metrics.

\begin{figure}[H]
  \centering
  \includegraphics[width=0.95\textwidth]{../figures/fig_main_results.pdf}
  \caption{Main results comparison across all datasets and metrics.}
  \label{fig:main}
\end{figure}

From Figure~\ref{fig:main}, our method achieves a 3.2\% improvement in F1 score
over the strongest baseline (TransformerXL). The gain is most pronounced on the
long-sequence subset (5.1\%), suggesting that our attention mechanism better captures
long-range dependencies. On shorter sequences, the improvement is marginal (0.8\%),
which aligns with our hypothesis that the benefit scales with sequence length.
```

### Rules

1. Before each figure/table: 1-2 sentences of lead-in text explaining WHY the reader should look at it (not just "如图所示" or "as shown in")
   - **⛔ 如果图/表很大（占半页以上），引导文字必须至少 3-5 句**，否则会出现一页只有一句话+大片空白的情况。在引导文字中加入方法说明、参数设置、数据来源等内容填充
2. After each figure/table: 3-5 sentences of analysis including:
   - Data interpretation: what the key numbers/trends are
   - Comparison: vs other methods/groups/expectations
   - Reasoning or conclusion: what this result means
3. **⛔ Between consecutive figures/tables: at least one full paragraph (≥5 lines of text)**. 绝对禁止两张图/表连续出现中间没有分析文字。每张图后面必须有 3-5 句话的分析段落，然后才能放下一张图
4. When figures need side-by-side display, use subfigure within one figure environment. ⛔ subfigure 注意事项：每个 subfigure 的 `\caption{}` 要短（3-5 个字），详细说明放在主 figure 的 `\caption{}` 或正文里。subfigure 宽度用 `0.48\textwidth`（两张并排）或 `0.32\textwidth`（三张并排），中间留 `\hfill` 间距。**⛔ 竞赛论文（数模/统计建模）例外：禁止使用 subfigure 并排。** 竞赛论文每张图必须独占一个 figure 环境，宽度 ≥ `0.85\textwidth`。并排图会导致图片缩小到半页宽，评委看不清细节。如需对比两张图，用两个独立 figure 环境，中间加过渡分析文字。
5. Per-page density: figures/tables ≤60% of page area, text ≥40%
6. If a section has 3+ figures, each must have ≥5 lines of text between them

### Anti-pattern (never do this)

```latex
\begin{figure}[H]...\end{figure}
\begin{figure}[H]...\end{figure}  % consecutive figures with no text between them
\begin{table}[H]...\end{table}    % still no analysis
```

Also never write just: "如表所示，我们的方法表现最好" / "As shown in Table X, our method outperforms all baselines." — this is empty analysis. Explain WHERE it's better, by HOW MUCH, and WHY.

### ⛔ 图表是论据，不是主语（Figure as Evidence, Not Subject）

获奖论文的图文衔接是论点驱动的：先有论点，图表作为旁证嵌入论证链条，最后给出推论。去掉图表引用，句子的逻辑依然完整。

**禁止模式**（AI 典型痕迹 — 图表做主语，段落变流水账）：
```
图3展示了三种算法的收敛曲线。从图中可以看出，遗传算法收敛最快。
图4给出了灵敏度分析的结果。由图可知，参数α对结果影响最大。
表5列出了各模型的评价指标。从表中可以看出，模型A表现最优。
```

**正确写法**（论点驱动 — 图表是括号里的旁证）：
```
算法选择的关键在于收敛效率与解质量的平衡。在相同迭代次数下，
遗传算法在第15代即趋于稳定，而模拟退火需要约40次迭代才能达到
相近精度（图3）。考虑到竞赛时间约束，本文最终采用遗传算法求解。

为验证模型的鲁棒性，对关键参数α进行了±20%的扰动。当α从0.8
变化到1.2时，目标函数值波动不超过3.7%（图4），表明模型对参数
扰动不敏感，具有良好的实用价值。
```

**核心原则**：
- 段落不能以"图X展示了"、"如图X所示"、"由图X可知"、"从图X可以看出"开头
- 图表引用优先用括号旁注形式 `（图X）` 或 `（见表X）`，融入句子中间或末尾
- 连续两段不能用相同方式引用图表（如连续两段都以"...（图X）"结尾也不行）
- 每个图表的分析段落必须包含：数值解读 + 对比/原因分析 + 结论推断，三者缺一不可
</figure_text_interleaving>

<figure_embedding>
## Figure Embedding

- Copy each figure/table block into the corresponding section file individually
- Do not use `\input{../figures/latex_includes.tex}` (dumps all figures into one section)
- Do not use pgfplots to draw from CSV (path/column/encoding issues are common)
- Image paths: `../figures/xxx.pdf` (relative to paper/ directory)
- **⛔ 图片宽度规则**：单张图 `width=0.9\textwidth`（默认），双栏并排 `width=0.48\textwidth`。不要用 `width=0.5\textwidth` 或更小的值——图会显得很小。如果图本身是宽幅的（如时序图、热力图），用 `width=0.95\textwidth`。
- **⛔ 图片高度规则**：单张图不能超过页面高度的 70%（约 18cm）。如果数据条目多（如 20+ 个类别的柱状图），必须限制 figsize 高度或分成多张子图。Python 生成时 `figsize=(width, height)` 的 height 不要超过 8（英寸）。超长的横向柱状图（30+ 条目）改用 `figsize=(7, 6)` + 缩小字号，或者只展示 Top 15/20。
- Float specifier: 用 `[H]`（需要 `\usepackage{float}`），图片紧跟在对应文字后面，不浮动。配合 `\includegraphics` 的 `height=0.38\textheight,keepaspectratio` 限高，防止图太高撑爆页面。⛔ 不要用 `[htbp]`——会导致图浮动，图和文字分离，多张图堆在一起
- Figure/table captions: keep short (one line, ≤15 Chinese characters or ≤10 English words). Detailed descriptions go in the body text before/after the figure, not in the caption. Example: `\caption{残差诊断四联图}` not `\caption{Wiener 过程模型残差诊断。(a) Q-Q 图检验正态性;(b) 残差 vs 拟合值检验同方差性;(c) 残差直方图与标准正态分布对比;(d) 残差 vs 时间检验独立性。}`
- **⛔ Caption 分隔符必须是空格，不能是冒号。** 中文论文的图表标题格式是"图 1 xxx"而不是"图 1: xxx"。在 preamble 中必须有 `\captionsetup{labelsep=quad}` 或 `\captionsetup{labelsep=space}`。如果模板已有此设置则不要重复添加。如果 Claude 自己写 main.tex，必须在 `\usepackage{caption}` 后加 `\captionsetup{labelsep=quad}`
- Wide tables (≥6 columns or multiple `p{}` columns): wrap with `\resizebox{\textwidth}{!}{...}`
- Narrow tables (≤4 columns): do not use `\resizebox` — it stretches text to full width, font becomes huge, table fills entire page
- Medium tables (5 columns): use `\resizebox` only if the table actually overflows margins; when in doubt, skip it
- Safest universal approach for any table: use `\begin{tabular*}{\textwidth}` or `\small\begin{tabular}` instead of `\resizebox` — this constrains width without distorting font size
- If a table is too tall (>12 rows), it MUST be truncated in body text — show first 3 rows + `$\vdots$` + last 3 rows, full table goes to appendix
- **⛔ 超过 12 行的结果表必须截断展示**：正文只放前 3 行 + `\midrule` + `$\vdots$` 省略行 + 后 3 行，完整表放附录。示例：
  ```latex
  \begin{table}[H]
  \centering\small
  \caption{7月1--7日各品类补货与定价策略（部分，完整结果见附录表A-1）}
  \begin{tabular}{llcccc}
  \toprule
  品类 & 日期 & 补货量(kg) & 加成率 & 零售价(元/kg) & 预期收益(元) \\
  \midrule
  花叶类 & 7月1日 & 174.1 & 0.600 & 8.53 & 160.94 \\
  花叶类 & 7月2日 & 177.3 & 0.600 & 8.53 & 163.88 \\
  花叶类 & 7月3日 & 164.2 & 0.600 & 8.53 & 151.80 \\
  \multicolumn{6}{c}{$\vdots$} \\
  辣椒类 & 7月5日 & 53.4 & 0.700 & 21.03 & 284.34 \\
  辣椒类 & 7月6日 & 53.3 & 0.700 & 21.03 & 283.87 \\
  辣椒类 & 7月7日 & 52.8 & 0.700 & 21.03 & 281.20 \\
  \bottomrule
  \end{tabular}
  \end{table}
  ```
  正文用截断表 + 文字总结关键发现，附录放完整表（用 `longtable` 跨页）。
- **⛔ 超参数/配置表格规则**：如果不同模型的参数数量差异很大（如线性回归 2 个参数 vs LSTM 9 个参数），**不要用一个大表**——拆成每个模型一个小表，或者用 `longtable` 跨页。否则表格会超出页面底部被截断。
- **⛔ 表格高度预估**：每行约 0.5cm，一页最多放 ~40 行。如果表格总行数（含 multirow 展开后的实际行数）> 35 行，必须用 `longtable` 或拆分。
- **⛔ 表格不能被页面截断**：编译后必须检查每个表格是否完整显示。如果表格底部被切掉，改用 `longtable` 环境（需要 `\usepackage{longtable}`）或拆分成多个小表。
- TikZ code: paste directly into section files, do not copy `\usepackage` lines
- TikZ node text: do not use bare backslash with Chinese (`\归一化` → `\\归一化` or `/归一化`)
- No emoji or special Unicode in LaTeX source
- Never create empty figure environments: every `\begin{figure}...\end{figure}` must contain either `\includegraphics{../figures/xxx.pdf}` or a `tikzpicture`. If the PDF file doesn't exist yet, skip the figure entirely rather than writing an empty shell with just a caption

### TikZ geometry/algorithm/architecture figures

TikZ figures are generated by paper-figure-drawio as `figures/tikz_diagrams.tex`, compiled to `figures/tikz_diagrams.pdf` (multiple figures → `tikz_diagrams_N.pdf` / `tikz_*.pdf`). Their `\includegraphics` figure blocks are already appended to `figures/latex_includes.tex`. (Legacy name `tikz_architecture_examples.tex` is also accepted.)

To embed: copy each `\begin{figure}...\end{figure}` block that references a `tikz_*.pdf` from `latex_includes.tex` directly into the appropriate section (not via `\input`). **Every `tikz_*.pdf` must be embedded — none may be dropped.** Map by caption/content:
- 技术路线图/研究框架图/问题关系图 → introduction/problem analysis chapter
- 模型架构图/求解流程图/几何示意图 → method/model chapter (geometry → the relevant sub-problem section)
- Others → judge by caption

### Python 图表防遮挡规则（Anti-Overlap）

生成 matplotlib/seaborn 图表时，必须检查以下遮挡问题：

**⛔ 强制规则（违反会导致图表不可用）：**
1. **任何 `ax.text()` 标注超过 3 个时，必须改用 `smart_labels()`** — 不允许手动逐个 `ax.text()`，因为无法保证不重叠
2. **任何 `ax.legend()` 必须改用 `auto_legend(ax)`** — 自动选择不遮挡数据的位置
3. **PCA biplot / 散点标注 / 特征重要性图** — 标签必须用 `smart_labels()`，这类图标签密集，手动偏移必定重叠
4. **⛔ 子图标注 (a)(b)(c)(d) 必须用 `ax.set_title()` 而不是 `ax.text(transAxes)`：**
   ```python
   # ✅ 正确：紧贴子图顶部，不受 aspect ratio 影响
   ax.set_title('(a)', fontsize=12, fontweight='bold', loc='left', pad=3)
   
   # ❌ 错误：set_aspect('equal') 时标注会远离子图
   ax.text(-0.08, 1.05, '(a)', transform=ax.transAxes, fontsize=12, fontweight='bold')
   ```
   原因：`transAxes` 坐标相对于 axes 逻辑区域，但 `set_aspect('equal')` 或 `constrained_layout` 会让实际绘图区域缩小，导致 `y=1.05` 看起来离图很远。`set_title(loc='left', pad=3)` 自动贴着实际渲染的 axes 边框。

**⛔ 通用防遮挡规则（所有图表都必须遵守）：**
- **多条线终点标注**：如果 ≥3 条线的终点 y 值差距 < y 轴范围的 5%，必须用 `smart_labels()` 而不是手动 `ax.text()`
- **柱状图 + 折线叠加（双轴图）**：折线数值标注放在折线上方（不是柱子上方），柱子的数值标注放在柱子内部或顶部。两者不要在同一个 y 位置。**⛔ 参考线/基准线的标注框必须放在图的边缘（左上角/右上角），绝对不要放在柱子和折线的交叉区域 — 这是最常见的遮挡场景。** 用 `transform=ax.transAxes` 固定在图的角落位置。
- **图例位置**：如果图例和数据重叠，用 `bbox_to_anchor` 把图例放到图外（上方或右侧）
- **标注框不能超出图表边界**：所有 `ax.text()` 和 `ax.annotate()` 的位置必须在 xlim/ylim 范围内。如果标注在边缘，用 `clip_on=False` + 加大 `pad_inches`
- **等高线图/3D 曲面图标注规则**：最优点标注（星号+文字框）如果在图的边缘（靠近轴），标注文字必须偏向图内侧，不要朝外（会遮挡坐标轴刻度）。用 `textcoords='offset points'` 控制偏移方向：靠右边缘的点偏左标注 `(-60, 20)`，靠上边缘的点偏下标注 `(20, -40)`。同时加大 `pad_inches=0.3` 防止裁切
- **数值标注间距**：相邻标注的 y 间距至少为字号高度的 1.5 倍。如果做不到，只标注关键点（最大/最小/首尾）

**检查清单：**
4. 参考线标注不能和数值标签重叠 — **⛔ 参考线/基准线/阈值线的文字标注必须放在图的边缘（角落），用 `transform=ax.transAxes` 定位到 (0.02, 0.98) 或 (0.98, 0.02) 等角落位置。绝对不要用 `ax.text(x_data, y_data, ...)` 把标注放在数据区域中间。**
5. 密集数据（>15 个标签）时 — 只标注关键点（最大/最小/首尾），不要每个点都标
6. 棒棒糖图/森林图 — 值域窄时（如 0.03-0.13），标签偏移量必须按值域比例计算。**数值标签必须用 `smart_labels()` 而不是手动 `ax.text()`**，因为数据点密集时固定偏移必定重叠。如果最大值的标签超出 xlim，必须加大 `xlim` 右边界（`ax.set_xlim(min_val - margin, max_val + margin)`，margin 至少为值域的 15%）。
7. 环形图 — 小扇区（<5%）的标签必须用外部连线，不能放在扇区内
8. 双轴图 — 柱状图用 `alpha=0.6` 半透明避免遮挡折线
9. **多 axes 布局（聚类热力图、边际直方图等）** — 树状图/边际图和主图之间至少留 0.05 的间距。`fig.add_axes([left, bottom, width, height])` 时，相邻 axes 的边界不能紧贴。树状图右边界和热力图左边界之间至少 0.04，标签区域额外预留 0.03。推荐用 `fig.add_gridspec()` 代替手动 `add_axes()`，自动处理间距。

**⛔ 热力图数字必须可读**：`sns.heatmap()` 的 `annot=True` 默认用黑色文字，深色格子上完全看不清。必须加 `annot_kws` 或用自适应文字颜色：
```python
# 方法：用 seaborn 内置的自适应（推荐）
sns.heatmap(data, annot=True, fmt='.2f', cmap='YlOrRd',
            linewidths=0.5, linecolor='white',
            annot_kws={'fontsize': 9, 'fontweight': 'bold'})
# 手动设置阈值：深色格子用白字，浅色格子用黑字
from matplotlib.colors import Normalize
norm = Normalize(vmin=data.min().min(), vmax=data.max().max())
for text in ax.texts:
    val = float(text.get_text())
    text.set_color('white' if norm(val) > 0.6 else 'black')
```
不要只用 `annot=True` 就完事——必须确保所有格子上的数字都清晰可读。
10. **聚类热力图 + 树状图** — **⛔ 必须严格按照 advanced #14 配方的 `fig.add_axes()` 布局代码，不要用 gridspec 自己发挥。** 只保留顶部树状图，不用左侧树状图（会遮挡 y 轴标签）。树状图高度占比不超过 15%（`add_axes([0.22, 0.85, 0.56, 0.12])`）。热力图左边界 `_left` 必须 ≥ 0.22（给 y 轴标签+左侧色条留足空间）。如果有左侧分组色条，色条放在 `_left - 0.05` 处（宽度 0.025），色条和热力图之间至少留 0.025 的间距给 y 轴标签。**⛔ 禁止让色条和 y 轴标签区域重叠 — 这是最常见的遮挡 bug。**
11. **帕累托图** — **⛔ 必须用 basic #9 配方的竖向布局（竖向柱状图 + 右轴累积折线），不要用横向柱状图 + twiny() 自己发挥。** 关键技巧：左轴 ylim 设为数据最大值的 2.5 倍，右轴 ylim 设为 `(-65, 110)`，这样柱子在下半部分、折线在上半部分，互不遮挡。

工具函数（在 `_utils/plot_utils.py` 中）：
- `smart_labels(ax, xs, ys, texts, ...)` — 自动推开重叠标签（基于 adjustText 库）
- `auto_legend(ax, ...)` — 自动选择不遮挡数据的图例位置
- `check_legend_overlap(ax)` — 返回最佳图例位置字符串
</figure_embedding>

<latex_constraints>
## LaTeX Constraints

- Line breaks: use `\\` (double backslash), not `\[` (that starts display math mode)
- Title spacing: `\\[0.5em]`, not `\[0.5em]`
- Table row endings: `\\` (double backslash), not `\` (single backslash — causes compile failure)
- Do not redefine built-in math operators (`\sin`, `\cos`, `\tanh`, `\log`, `\exp`, `\max`, `\min`, etc.)
- `math_commands.tex`: only define paper-specific new commands, never override existing ones
- Avoid `\begin{itemize}` in body text (bullet-point lists read as AI-generated). Use `\begin{enumerate}` or flowing prose instead. Itemize is acceptable only in appendices
- **⛔ 正文中禁止使用 `\begin{itemize}` 和 `\begin{enumerate}` 列表。** 黑点/编号列表是最典型的 AI 写作痕迹。学术论文正文必须用连贯的段落叙述。例外：模型假设（可用编号）、附录、算法步骤描述。
  - ❌ 错误：`\begin{itemize} \item 牛市：2023年7月至... \item 震荡市：2024年4月至... \end{itemize}`
  - ✅ 正确：将每个要点展开为完整段落，用"首先...其次...此外..."等过渡词连接，或用"（1）...（2）...（3）..."行内编号
- **⛔ 正文中禁止出现元叙述和内部指令。** 以下内容绝对不能出现在论文正文中：
  - "参赛者"、"参赛队伍"、"我们团队" → 用"本文"代替
  - "RESULTS.md"、"figures/*.json"、"CLAUDE.md"、"MODELING_REPORT.md" 等文件名 → 这些是内部工作文件，不是论文内容
  - "数据驱动"、"可解释建模"等原则性描述如果是从 SKILL 指令中复制的，不要原样写入正文
  - "竞赛特征"、"竞赛要求" → 论文是独立的学术文档，不要提及竞赛本身的规则或要求
  - 任何看起来像是"给 AI 的指令"而不是"给读者的分析"的内容
- No `\hypersetup{colorlinks=true}` — conflicts with `hidelinks`, causes blue citation links
- Citation format: use venue-appropriate package (gbt7714 for Chinese papers with superscript `[1]`, natbib for English ML venues with `Author, Year`)
- Do not use `\usepackage{natbib}` in Chinese academic papers (thesis/journal) — it produces `[Author, Year]` instead of `[1]`. Exception: the stats competition template intentionally uses natbib with `[numbers, square]` which correctly produces `[1]` format
- **⛔ 引用格式规则（中文论文）：**
  - 每个 `\cite{}` 只引用一篇文献：`\cite{wang2020}` ✅，`\cite{wang2020,li2021,zhang2022}` ❌
  - 引用编号必须按出现顺序递增：正文中先出现的文献编号小，后出现的编号大。不要出现 `[3]` 在 `[1]` 前面的情况
  - 如果需要同时引用多篇，分开写：`王某\cite{wang2020}、李某\cite{li2021}和张某\cite{zhang2022}分别研究了...`
  - 不要在一句话末尾堆砌引用：`...具有重要意义\cite{a,b,c,d,e}` ❌ → 每篇文献对应具体的观点或贡献
- **⛔ 模型假设用 `\needspace{20\baselineskip}`，符号说明用 `\needspace{15\baselineskip}`**——compile_utils.sh 自动处理：
  - 模型假设（`2_assumptions.tex`）：注入 `\needspace{20\baselineskip}`，当前页剩余空间够放 5 条假设就不换页，不够才换
  - 符号说明（`3_symbols.tex`）：注入 `\needspace{15\baselineskip}`，确保标题和表格在同一页
  - 不要手动加 `\clearpage` 或 `\needspace`，compile_utils.sh 会自动处理
- **⛔ 封面信息不要用 tabular + `\cline`。** 封面的学校、队员、指导老师等信息用 `\makebox` 或 `\underline{\hspace{}}` 排版，不要用 tabular 表格。`\cline{2-2}` 在封面上会被渲染成文本 "cline2-2"。正确做法：
  ```latex
  参赛学校：\underline{\makebox[8cm][c]{[学校名称]}} \\[0.8em]
  参赛队员：\underline{\makebox[8cm][c]{[队员姓名]}} \\[0.8em]
  ```
- **⛔ 引号统一用中文全角引号 `"..."` 和 `'...'`（中文论文）：**
  - ✅ 正确（中文论文）：`"重要发现"`（全角双引号 U+201C/U+201D，xeCJK 自动渲染为对称弯引号）
  - ✅ 正确（中文论文）：`'方法'`（全角单引号 U+2018/U+2019）
  - ❌ 错误（中文论文）：`` ``重要发现'' ``（LaTeX 风格反引号 + 单引号，在中文环境下会显示成两个堆叠的反引号）
  - ❌ 错误：`"重要发现"`（ASCII 直引号 `"...""`，LaTeX 渲染为右右引号 `""`）
  - **英文论文例外**：英文环境用 LaTeX 风格 `` ``important'' ``（西文字体下渲染为对称弯引号），不要用全角引号
  - 如果不小心写错，compile_utils.sh / comp-compile-zh 会在编译前自动统一为全角引号
</latex_constraints>

<page_filling>
## Page Filling (Chinese thesis/competition papers)

Every page should be filled. Half-empty pages are a basic formatting failure in Chinese theses and competition papers.

- Last page of each chapter: text fills at least 2/3 of the page. If only a few lines remain, expand the chapter content
- Figures should not occupy a page alone — text must appear above or below
- **⛔ 所有图使用 `keepaspectratio` + `height` 双约束**，LaTeX 自动处理高图缩放，不需要在 DrawIO 层面限制图的高度
- Do not use `\clearpage` or `\newpage` between chapters (except for abstract/TOC pages). Let LaTeX flow naturally
- If a chapter ends with empty space, add a "本章小结" paragraph (2-3 sentences summarizing the chapter and previewing the next)
</page_filling>

<abstract_requirements>
## Abstract Requirements

### Chinese papers (thesis/competition)
- Chinese abstract: 500-700 characters. Aim to fill most of one page but leave 3-4 lines margin at the bottom — overflowing onto a second page looks worse than being slightly short
- Content chain: 研究背景与意义 → 现有方法的不足 → 本文提出的方法 → 数据来源与处理 → 关键发现（must have specific numbers like 精度、R²、p值） → 应用价值
- English abstract: 350-500 words, faithful translation of Chinese abstract. Same principle — fit on one page with a small margin, do not overflow
- Use manual typesetting for abstracts (not `\begin{abstract}` twice — ctexart shows "摘要" as title for both)
- The abstract is the soul of the paper — reviewers read it first. It must be thorough, never just 2-3 paragraphs

**⛔ 论文标题规则：**
- 标题不能太简单笼统（如"车辆路径规划问题研究"）。必须体现具体的研究方法和创新点
- 不要用副标题（不要用"——"分隔的两段式标题），一句话说清楚
- 数模竞赛标题格式：一句话包含 `研究对象 + 核心方法/模型 + 研究视角`。例如：
  - ✗ "物流配送优化" → ✓ "基于改进遗传算法的冷链物流多目标配送路径优化研究"
  - ✗ "疫情传播模型" → ✓ "考虑人口流动与疫苗接种的新冠疫情 SEIR 改进传播模型"
  - ✗ "机器人竞技策略" → ✓ "基于多目标动力学建模与博弈决策的人形机器人竞技策略优化研究"
  - ✗ "数据分析" → ✓ "基于多期双重差分与空间杜宾模型的数据要素市场化配置效应研究"
- 标题应在建模求解/数据分析完成后，根据实际使用的方法和发现来拟定，不要在规划阶段就定死
- 标题长度：中文 15-30 字，简洁有力，不要超过 35 字

**⛔ 摘要页排版规则（中文论文）：**
- 摘要必须在封面之后、目录之前。不要在摘要前放 `\listoffigures`（插图目录）或 `\listoftables`（表格目录）
- 正确的页面顺序：封面 → 摘要（中文）→ 摘要（英文）→ 目录 → 正文。`\listoffigures` 和 `\listoftables` 如果需要，放在目录之后、正文之前

**⛔ 防空白页规则：**
- **不要在正文章节之间加 `\newpage`、`\clearpage` 或 `\nopagebreak`** — 让 LaTeX 自动分页。`\nopagebreak` 会把标题和大表格绑死，放不下就整块推到下一页产生空白页
- 只在摘要后和目录后用分页
- 参考文献和附录前不要加 `\newpage`
- 关键词必须用 `\textbf{关键词：}` 加粗标注，与摘要正文之间空一行
- 摘要页推荐用 `\begin{abstract}` 环境（ctexart 自带），不要用普通 `\section*{摘要}` + 段落文本
- **⛔ 摘要必须有首行缩进（2 字符）。** ctexart 的 `\begin{abstract}` 环境自动有缩进。如果用自定义排版，必须确保 `\parindent=2em`。绝对不要在摘要中使用 `\noindent`
- **⛔ 摘要必须分段，不要写成一整段。** 按论文类型分段：

  **数模竞赛（cumcm/huawei/mathorcup/apmcm）：**
  - 第 1 段：研究背景与问题概述（2-3 句）
  - 第 2 段：针对问题一，方法+模型+关键数值结果
  - 第 3 段：针对问题二，方法+模型+关键数值结果
  - 第 4 段：针对问题三，方法+模型+关键数值结果
  - 第 5 段：模型推广、灵敏度分析、优缺点（1-2 句）
  - 每个子问题必须单独成段，不能把所有问题挤在一段里

  **统计建模/学术论文：**
  - 第 1 段：研究背景与问题（2-3 句）
  - 第 2 段：研究方法与数据（3-4 句）
  - 第 3 段：关键发现与数值结果（3-5 句，必须有具体数字）
  - 第 4 段：研究意义与政策建议（1-2 句）
- 每段之间用 LaTeX 空行分隔（不要用 `\\` 或 `\vspace`）
- 摘要示例结构：
  ```latex
  \begin{abstract}
  在...背景下，...面临...问题。本文以...为研究对象，...

  研究采用...方法，构建了...模型。数据来源于...，样本包含...

  实证结果表明：第一，...（系数 0.042，p < 0.01）；第二，...；第三，...。
  稳健性检验（...）验证了结论的可靠性。

  本文的研究为...提供了实证依据，对...具有重要的政策启示。

  \textbf{关键词：}关键词1；关键词2；关键词3；关键词4；关键词5
  \end{abstract}
  ```

### Competition papers (数模竞赛)
- Chinese abstract: 400-600 characters, every sub-problem must have specific numerical results
- Summary Sheet (MCM/ICM): 300-400 words, self-contained with specific numbers, one full page

### English papers (ML venues)
- 150-250 words, self-contained
- Structure: what → why hard → how → evidence → strongest result
</abstract_requirements>

<resume_strategy>
## Resume / Breakpoint Strategy

Writing can be interrupted by timeout. Use these strategies to enable seamless resume:

1. Write in priority order: method/core chapters → experiments → introduction → related work → conclusion (core content first, auxiliary later)
2. Save each chapter immediately after writing — do not accumulate multiple chapters in memory
3. If approaching output limit, create placeholder files for remaining chapters:
```latex
% [PLACEHOLDER] This chapter needs continuation
% Expected content: [brief description of what this chapter should contain]
\section{Chapter Title}
Content to be added in continuation pass.
```
4. Before writing, always check for existing sections:
   - Placeholder sections (<500 chars or contains "PLACEHOLDER"/"待补充") → write these
   - Completed sections (>2000 chars) → skip, do not overwrite
   - This enables automatic resume after timeout/retry
</resume_strategy>

<de_ai_polish>
## De-AI Polish

Remove these AI writing artifacts before finalizing:

### Structural AI patterns (most obvious — fix first)
- **⛔ `\begin{itemize}` / `\begin{enumerate}` in body text** — the #1 AI writing tell. Convert every bullet list to flowing paragraphs. Use "首先...其次...最后..." or "（1）...（2）...（3）..." inline numbering instead.
- **⛔ 每段只有 1-2 句话** — AI 喜欢写很多短段落。合并相关的短段落为 3-5 句的完整段落。
- **⛔ 连续段落以相同句式开头** — 如连续三段都以"本文..."开头，改为不同的开头方式。

### Chinese
- 具有重要的理论意义和实践价值
- 深入探讨、创新性地、值得注意的是
- Excessive use of 综上所述 to start paragraphs
- Consecutive paragraphs starting with 本文
- 空洞修饰语 — replace with specific numbers and facts
- "如表X所示" 后面没有分析 — 必须跟 2-3 句解读

### English
- delve, pivotal, landscape, tapestry, underscore, noteworthy
- "It is worth noting that", "Importantly,", "Notably,"
- Significance inflation, formulaic transitions, generic conclusions
- Consecutive paragraphs starting the same way
</de_ai_polish>

<references_workflow>
## References Generation Workflow

references.bib is a hard prerequisite for compilation. Without it, the PDF will have no references and will be judged as unqualified. Generate it during the writing phase, never skip.

### Collection
```bash
mkdir -p _tmp
grep -roh '\\cite[tp]*{[^}]*}' paper/sections/*.tex paper/main.tex 2>/dev/null \
  | grep -oP '\{[^}]+\}' | tr -d '{}' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u > _tmp/_cited_keys.txt
echo "Cited keys: $(wc -l < _tmp/_cited_keys.txt)"
cat _tmp/_cited_keys.txt
```

### Generation

**⛔ 优先使用 scholar_fetch.py 工具（环境变量 `$SCHOLAR_SCRIPT`）自动获取 BibTeX。**

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
# 对每个引用 key，用 scholar_fetch.py 搜索并获取 BibTeX
while IFS= read -r key; do
    echo "--- Fetching: $key ---"
    $PYTHON "$SCHOLAR_SCRIPT" bibtex "$key" --max 2
    sleep 0.5
done < _tmp/_cited_keys.txt
```

从每个结果的 JSON 输出中选择正确的论文，将其 `bibtex` 字段复制到 `paper/references.bib`。

**Fallback（scholar_fetch.py 搜不到时）：**
1. 用 WebSearch 搜索论文标题 + 第一作者
2. 从 DBLP/CrossRef 手动获取 BibTeX：
   - DBLP: `curl -s "https://dblp.org/search/publ/api?q=TITLE+AUTHOR&format=json&h=3"` → `curl -s "https://dblp.org/rec/{key}.bib"`
   - CrossRef: `curl -sLH "Accept: application/x-bibtex" "https://doi.org/{doi}"`
3. 如果都找不到，手动生成条目但标记 `note = {[VERIFY] Citation needs manual verification}`
4. 保存到 `paper/references.bib`
5. 禁止凭记忆编造 — 找不到就标记 `[VERIFY]`

### Verification
```bash
[ -f paper/references.bib ] && echo "OK: references.bib exists" || echo "CRITICAL: references.bib missing!"
bib_count=$(grep -c '^@' paper/references.bib 2>/dev/null || echo 0)
cited_count=$(wc -l < _tmp/_cited_keys.txt 2>/dev/null || echo 0)
echo "Bib entries: $bib_count, Cited keys: $cited_count"
[ "$bib_count" -eq 0 ] && echo "CRITICAL: references.bib is empty! Must generate entries."
[ "$bib_count" -lt "$cited_count" ] && echo "WARNING: fewer bib entries than cited keys"
```

If references.bib is empty or missing, do not proceed to the next step.
</references_workflow>

<output_conventions>
## Output Conventions

- Primary output: `paper/` directory
- Temp files: `_tmp/` directory
- Do not write extra reports to root (no PAPER_WRITING_REPORT.md, COMPILE_REPORT.md, PAPER_COMPLETION_SUMMARY.md, etc.)
- Large files: use Bash heredoc (`cat << 'EOF' > file`)
- No real author/team info — use placeholders
- Tables: three-line style (booktabs)
- Backup existing `paper/` before overwriting
</output_conventions>
