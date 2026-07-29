

## ⛔ 表格输出格式：仅 Markdown 三线表（.md）
本工作流最终导出 Word，**所有结果表格必须输出为 `.md`，不要再生成 `.tex`**：

**为什么这条铁律重要**：写作步骤会直接 `cat figures/TABLE_xxx.md >> paper/main.md`，完全跳过「从 JSON 抠数字到 Markdown 表格」这一步，从源头杜绝 AI 编造/记错表格数字。

**调用 stats_utils 时按 .md 后缀输出**：
```python
from _utils.stats_utils import regression_table, descriptive_table, correlation_table
# ⛔ Word 模式：表格全部输出 .md（Markdown 三线表）
regression_table(results, ['OLS', 'Logit'],
                 output='figures/TABLE_regression.md',
                 caption='回归结果')
descriptive_table(df, output='figures/TABLE_descriptive.md',
                  caption='描述性统计')
```

**手写表格时使用以下 Markdown 三线表标准格式**：
```markdown
**表 1：模型性能对比**

| 模型 | RMSE | MAE | R² |
|---|---|---|---|
| LSTM | 0.023 | 0.018 | 0.94 |
| Transformer | 0.019 | 0.015 | 0.96 |

> 注：所有指标基于测试集；最优值已加粗。

<!-- label: tab:model_perf -->
```

**表格生成铁律**：
- ⛔ **禁止**生成 `figures/TABLE_*.tex`（Word 模式根本不读 .tex 文件）
- ⛔ **禁止**写 `\begin{table}` / `\begin{tabular}` / `\toprule` / `\midrule` / `\bottomrule`
- ✅ 生成 `figures/TABLE_*.md`：每个表格一个文件，文件名见名知意（TABLE_regression.md / TABLE_descriptive.md / TABLE_model_perf.md...）
- ✅ 表格里的所有数值**必须**从 `figures/all_results.json` / `figures/*.json` / `RESULTS.md` 读取，禁止凭记忆填
- ✅ 表头单独一行 `| h1 | h2 |`，**接下来必须有分隔行** `|---|---|`
- ✅ 每行 `|` 数量必须一致（列数对齐）
- ✅ 单元格里的 `|` 必须转义为 `\|`
- ✅ 表注用 `> 注：xxx`（引用块）

**核查清单**（生成完所有表格后必须跑）：
```bash
echo '=== 表格格式核查 ==='
# 1. figures/ 不应有 TABLE_*.tex
tex_count=$(ls figures/TABLE_*.tex 2>/dev/null | wc -l)
[ "$tex_count" -gt 0 ] && echo "❌ 还残留 $tex_count 个 .tex 表格，必须删除并改用 .md"
# 2. .md 表格列数对齐 + 必有分隔行
for md in figures/TABLE_*.md; do
    [ -f "$md" ] || continue
    if ! grep -qE '^\|[\s\-:|]+\|\s*$' "$md"; then
        echo "❌ $(basename $md) 缺少分隔行 |---|---| ，Word 不会渲染成表格"
    fi
done
echo '=== 表格生成完成 ==='
ls -1 figures/TABLE_*.md 2>/dev/null
```
**任何 ❌ 都必须修复**（删除 .tex / 补全分隔行 / 重新生成）。
