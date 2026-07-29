---
name: comp-paper-zh-docx
description: "数模竞赛/统计建模中文论文撰写（Word docx 模式）。docx-mode counterpart of comp-paper-zh — keeps competition chapter structure but produces paper/main.md only."
argument-hint: [competition-type]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# 中文竞赛论文撰写（docx 模式）

按竞赛规范结构生成中文论文，输出 Markdown 供 Word 导出：**$ARGUMENTS**

> docx 专用版本。保留 `comp-paper-zh` 全部写作纪律（章节结构、子问题分章节、上游验证、图表嵌入、引用纪律、模板复制后指纹校验在此简化为 markdown 框架对齐），但产物只有 **`paper/main.md`** 一个文件。
>
> ⛔ **绝不产 `.tex` / `.cls` / `.sty` / `.bib`，绝不调用 LaTeX 命令。**

## Constants

- **COMPETITION** — `stats` = 统计建模, `huazhong` = 华中杯, `wuyi` = 五一杯, `mathorcup` = MathorCup, others = 数模竞赛 (cumcm/huawei/etc.)
- **MAX_PAGES** — Default 20。正文字符数 ≥ MAX_PAGES × 800
- **CUSTOM_REQUIREMENTS** — 最高优先级

## Inputs

1. PROBLEM_ANALYSIS.md, MODELING_REPORT.md, RESULTS.md
2. figures/ — `.png` / `.pdf` / `latex_includes.tex`（仅作图编号 caption 参考）
3. code/, figures/all_results.json, figures/problem_*_results.json

## Load shared rules

```bash
cat _utils/writing_rules.md 2>/dev/null || cat skills/shared-scripts/writing_rules.md
```

> shared rules 中关于 LaTeX 的部分（`\begin`、`\input`、`gbt7714`、`thebibliography`）在 docx 模式下不适用，但写作哲学全部适用：claims-evidence、章节深度、扩写策略、图表是论据、de-AI polish。

## ⛔⛔⛔ 完成铁律（最高优先级）

**主产物**：`paper/main.md`（**单文件**，UTF-8，含完整论文，≥ 5KB）

**禁止产**：
- `paper/main.tex`、`paper/sections/*.tex`、`paper/references.bib`
- 任何 `.cls` / `.sty` / `.aux`
- 任何 LaTeX 命令（`\begin`、`\input`、`\cite`、`\label`、`\ref`、`\section`、`\includegraphics`、`\bibitem`）

**结束前必跑产出验证**：
```bash
echo "=== 产出验证（必须全部 ✅）==="
PASS=true

[ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
[ "$SZ" -ge 5120 ] && echo "✅ paper/main.md ($SZ bytes)" || { echo "❌ paper/main.md 缺失或过小"; PASS=false; }

chars=$(wc -m < paper/main.md 2>/dev/null || echo 0)
est_pages=$((chars / 800))
target=${MAX_PAGES:-20}
echo "字符: $chars, 估算页数: ~$est_pages, 目标: ≥ $target"
[ "$est_pages" -lt "$((target * 80 / 100))" ] && echo "⚠ 低于目标 80%"

# LaTeX 残留检查
if grep -qE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter|subsection|bibitem|usepackage|documentclass)\{' paper/main.md; then
    echo "❌ paper/main.md 残留 LaTeX 命令："
    grep -nE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter|subsection|bibitem|usepackage|documentclass)\{' paper/main.md | head -5
    PASS=false
fi

ls paper/*.tex paper/sections/*.tex 2>/dev/null | head -1 | grep -q . && { echo "❌ 检测到 .tex 文件"; PASS=false; } || true

[ "$PASS" != true ] && echo "⛔ 验证失败 — 必须修复后重跑"
```


## docx-cn-engine markdown 约定（必须遵守）

后续 `docx-export` 步骤用 `tools/docx-cn-engine/md_to_docx.js` 把 main.md 转成 .docx：

### 1. 标题层级
- `# 论文标题` — 论文封面标题（**全文唯一**，居中加粗最大字号，引擎会按封面样式渲染）
- `## 摘要` / `## Abstract` — 触发居中摘要样式
- `## 1 问题重述` / `## 2 模型假设` — 一级章节
- `### 1.1 子章节` — 二级
- `#### 三级`

数模竞赛章节命名建议：
```
## 1 问题重述
## 2 模型假设
## 3 符号说明
## 4 问题一的建模与求解
## 5 问题二的建模与求解
## 6 问题三的建模与求解
## 7 灵敏度分析与模型检验
## 8 模型评价与推广
## 参考文献
## 附录 A：代码
```

统计建模用中文数字：「一、绪论」、「二、文献综述」...，按内容驱动设计 5-7 个中段章节。

### 2. 摘要
```markdown
## 摘要

[400-600 字（数模）/ 500-700 字（统计建模）。**必须按问题分段**：
- 第 1 段：背景概述
- 第 2-4 段：分别针对问题一/二/三（方法 + 数值结果）
- 第 5 段：模型评价]

**关键词**：关键词1；关键词2；关键词3；关键词4；关键词5
```

统计建模需另写英文摘要（350-500 词），紧跟在中文摘要后：
```markdown
## Abstract

[英文翻译，覆盖相同结构与全部数值]

**Keywords**: keyword1; keyword2; keyword3
```

⛔ 摘要必须**先写正文再写摘要**（在 Workflow Step 5.6）—— 摘要里的数字必须从正文摘出，不能编。

### 3. 公式
- 行内：`$x^2 + y^2 = r^2$`
- 独立：`$$E = mc^2$$`
- 编号：在公式后另起一行 `(1)`，引擎自动右对齐
```markdown
模型可表示为：

$$\min_{\mathbf{x}} \sum_{i=1}^{n} c_i x_i \quad \text{s.t.} \quad \sum_i a_{ij} x_i \leq b_j \quad (1)$$

其中 $c_i$ 为第 $i$ 项成本系数。
```

⛔ **禁止 `\begin{equation}`、`\[...\]`、`\begin{align}`** —— 引擎不渲染。

### 4. 图片
```markdown
![图 1：技术路线图](figures/fig_roadmap.png)
```
- alt 文字 → 图注（居中加粗）
- 路径相对工作区根目录
- 优先 PNG（PDF 也支持但 Word 渲染不如 PNG）

### 5. 表格（三线表自动渲染）
```markdown
**表 1：问题一各算法对比**

| 算法 | 适应度 | 收敛代数 | 求解时间(s) |
|------|--------|----------|-------------|
| GA | 0.823 | 145 | 12.3 |
| PSO | 0.811 | 162 | 10.8 |
| 本文方法 | **0.917** | **88** | **9.4** |
```

⛔ 长表格（>15 行）：正文放摘要表（前 5 行 + 后 3 行 + 「⋮」省略），完整版放「## 附录 A：完整结果表」。

⛔ 如果 `figures/TABLE_*.md` 已存在（由 paper-figure 步骤产出），直接 `cat figures/TABLE_x.md` 嵌入对应章节。

### 6. 参考文献
```markdown
## 参考文献

[1] 作者. 标题[J]. 期刊, 年份, 卷(期): 页码.
[2] LeSage J P, Pace R K. Introduction to Spatial Econometrics[M]. CRC Press, 2009.
[3] Author A. Title[D]. 学校, 年份.
```

引擎检测到 `## 参考文献` / `## References` 后，下面以 `[N]` 开头的行自动套 hanging indent。

⛔ **正文引用用 `[1]`、`[1, 2]`、`[1-3]` 而不是 `\cite{}`**。
⛔ 引用编号必须按正文出现顺序排列（[1] 先于 [2] 先于 [3]），不能跳号。

## Workflow

### Step 0: 上游验证 + 续写检查

```bash
echo "=== 上游输出完整性检查 ==="
UPSTREAM_OK=true

# 1. 核心文件
for f in PROBLEM_ANALYSIS.md MODELING_REPORT.md RESULTS.md; do
    if [ -f "$f" ]; then
        sz=$(wc -c < "$f")
        echo "✅ $f ($sz 字符)"
        [ "$sz" -lt 500 ] && echo "  ⚠ 内容不完整"
    else
        echo "❌ $f 不存在！"; UPSTREAM_OK=false
    fi
done

# 2. 子问题覆盖度
PROB_COUNT=$(grep -c '问题[一二三四五六七八九十]' PROBLEM_ANALYSIS.md 2>/dev/null || echo 0)
MODEL_COUNT=$(grep -c '问题[一二三四五六七八九十]' MODELING_REPORT.md 2>/dev/null || echo 0)
RESULT_FILES=$(ls figures/problem_*_results.json 2>/dev/null | wc -l)
echo "子问题数: 分析=$PROB_COUNT, 建模=$MODEL_COUNT, 结果=$RESULT_FILES"

# 3. 图表
PNG_COUNT=$(ls figures/*.png 2>/dev/null | wc -l)
PDF_COUNT=$(ls figures/*.pdf 2>/dev/null | wc -l)
echo "可嵌入图: PNG=$PNG_COUNT, PDF=$PDF_COUNT"
[ -f figures/all_results.json ] && echo "✅ all_results.json" || echo "⚠ 无 all_results.json"

# 4. 续写检查
if [ -f paper/main.md ]; then
    cp paper/main.md "paper/main-backup-$(date +%s).md.bak"
    echo "已存在 main.md，备份后进入续写"
fi

echo "=== 上游检查完成 ==="
```

### Step 1: 图表清单与嵌入计划

```bash
echo "=== 可用 PNG/PDF ==="
ls -la figures/*.png figures/*.pdf 2>/dev/null

echo "=== 可用 TABLE_*.md (Word 模式专用) ==="
ls -la figures/TABLE_*.md 2>/dev/null

echo "=== latex_includes.tex（仅作图编号 caption 参考）==="
cat figures/latex_includes.tex 2>/dev/null
```

**⛔ MANDATORY: 写章节前先建立图表嵌入计划：**

| 图/表 | 文件 | 嵌入位置 | 中文 caption |
|-------|------|----------|--------------|
| 1 | figures/fig_roadmap.png | 1 问题重述末尾 | 图 1：技术路线图 |
| 2 | figures/fig_flow_q1.png | 4 问题一-模型建立 | 图 2：问题一求解流程 |
| 3 | figures/fig_results_q1.png | 4 问题一-结果分析 | 图 3：问题一各算法对比 |
| 表 1 | figures/TABLE_results_q1.md | 4 问题一-结果分析 | 表 1：问题一最优解对比 |

**规则：**
- ⛔ 中文论文 caption 必须是中文。`latex_includes.tex` 里的英文 caption 嵌入时翻译
- ⛔ 必须使用真实存在的文件（先 ls 再嵌入）。`figures/` 仅含 `latex_includes.tex` 占位时跳过图嵌入
- ⛔ DrawIO 图（fig_roadmap / fig_flow_q1/q2/q3 / fig_pipeline）必须嵌入：技术路线图→问题重述末尾；子问题流程图→对应子问题章节开头（先 2-3 句引导文字，再放图）
- ⛔ 所有 `figures/*.pdf` / `figures/*.png` 必须有归属，不能漏

### Step 1.5: 文献预检索

⛔ 写任何引用之前，先建立已验证的文献池：
```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp
# 根据论文主题搜索（按选题调整）
#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "整数规划 调度" --max 5
```

把搜索结果写到 `_tmp/_verified_refs.txt`，写正文时只引用池子里的论文。

### Step 2: 撰写论文（一次写到 paper/main.md）

写作顺序：
1. **先写正文**（问题重述 → 假设 → 符号 → 各子问题 → 灵敏度 → 评价）
2. **再写参考文献**
3. **最后写摘要**（必须最后写，这样数字可以从正文摘出）

总骨架（以国赛/华为杯/MathorCup 为例，一份完整 main.md）：

```markdown
# [论文标题]

## 摘要

[占位：Step 5 最后填写]

**关键词**：...

## 1 问题重述

[用自己的话重述，不抄题目原文。1-2 段背景 + 各子问题概述]

![图 1：技术路线图](figures/fig_roadmap.png)

如图 1 所示，本文针对... [≥ 5 行总体思路与各子问题之间关系的说明]

## 2 模型假设

为简化建模，本文做出以下假设：

（1）[假设内容]。该假设的合理性在于... [1-2 句]
（2）[假设内容]。... 
（3）...
（4）...
（5）...

⛔ 4-6 条，每条 1-2 句。不要写成长段落，不要超过 6 条。

## 3 符号说明

**表 1：主要符号说明**

| 符号 | 含义 | 单位 |
|------|------|------|
| $N$ | 总数量 | 个 |
| $x_i$ | 第 $i$ 个变量 | --- |
| ... | ... | ... |

⛔ 15-20 个符号以内，只列正文实际使用的核心变量。

## 4 问题一的建模与求解

### 4.1 问题分析

[1-2 段，分析问题特点、关键约束、采用的求解思路]

### 4.2 模型建立

![图 2：问题一求解流程](figures/fig_flow_q1.png)

如图 2 所示，本文将问题一... [≥ 5 行流程概述]

记 $x_i$ 为决策变量，则模型可表示为：

$$\min \sum_{i=1}^n c_i x_i \quad (1)$$

$$\text{s.t.} \quad \sum_i a_{ij} x_i \leq b_j, \quad j=1,\dots,m \quad (2)$$

[公式后必须有 ≥ 5 行说明：每个符号物理意义、约束条件含义、目标函数解释]

### 4.3 求解算法

[算法步骤说明 + 复杂度分析。可用「（1）...（2）...（3）...」行内编号]

### 4.4 结果分析

**表 2：问题一最优解**

| 算法 | 适应度 | 求解时间(s) |
|------|--------|-------------|
| GA | 0.823 | 12.3 |
| PSO | 0.811 | 10.8 |
| 本文方法 | **0.917** | **9.4** |

由表 2 可见，本文方法在适应度上比 GA 高 11.4%，求解时间比 PSO 减少 13.0%。... [≥ 2 段数值解读 + 原因分析]

![图 3：问题一各算法收敛曲线](figures/fig_results_q1.png)

图 3 显示... [≥ 5 行分析]

## 5 问题二的建模与求解

[同问题一结构]

## 6 问题三的建模与求解

[同问题一结构]

## 7 灵敏度分析与模型检验

[选 ≥ 2 个关键参数，每个参数的变化曲线 + 分析段落]

## 8 模型评价与推广

### 8.1 优点

[3-4 条优点，每条 1 段说明]

### 8.2 不足

[2-3 条不足，每条 1 段说明]

### 8.3 推广

[1-2 段推广到其他场景的可能性]

## 参考文献

[1] LeSage J P, Pace R K. Introduction to Spatial Econometrics[M]. CRC Press, 2009.
[2] ...

## 附录 A：代码

```python
# 代码片段或文件清单
```
```

### Step 3: 写作纪律（每章节都遵守）

**⛔ 写作风格铁律：**
- **禁止用 markdown bullet（`-`、`*`）或编号列表（`1.`、`2.`）作为正文叙述。** 只在「输入清单 / 评价指标定义 / 软件依赖 / 模型假设条目」这种枚举性场景使用。正文叙述必须用连贯段落。
- **每段至少 3-5 句话。**
- **连续段落不能以相同句式开头。** 三段都「本文...」开头必须改。
- **图表是论据不是主语。** 段落不能以「图 X 展示了」「如图 X 所示」「由图 X 可知」开头。改成：先论点 → 图表作旁证（"如图 X 所示，..."以圆括号或独立短句出现）→ 推论。
- **元叙述泄露禁止。** 正文不能出现"参赛者"、"参赛队伍"、"RESULTS.md"、"figures/all_results.json"、"CLAUDE.md"等内部文件名。

**⛔ 数值来源规则：**
所有数值（适应度、最优解、求解时间、各项指标）必须来自 `figures/all_results.json` / `figures/problem_*_results.json` / `RESULTS.md`。写每个章节前：
```bash
[ -f figures/all_results.json ] && cat figures/all_results.json
[ -f RESULTS.md ] && cat RESULTS.md
```
原样复制数字，不要凭记忆估算或四舍五入。

**⛔ 图文并茂硬规则：**
- 每张图/表后面必须有 ≥ 5 行分析（数值解读 + 对比 + 原因），然后才能放下一张图
- 绝对禁止两张图连续出现中间没有分析段落
- 图片 alt 文字（caption）必须中文

**⛔ 长表格处理：**
- ≤ 15 行：直接放正文
- > 15 行：正文放摘要表（前 5 行 + 后 3 行 + 「⋮」省略）+ 末尾的「## 附录 A」放完整表
- caption 注明「（部分，完整结果见附录）」

每写完一章后检查字数：
```bash
chars=$(wc -m < paper/main.md)
echo "main.md: $chars 字符"
```

### Step 4: 引用整理

写完正文后整理引用编号：

```bash
# 提取正文所有 [N]
grep -oE '\[[0-9]+(-[0-9]+)?(, *[0-9]+)*\]' paper/main.md | sort -u > _tmp/_cited.txt
echo "正文引用编号:"
cat _tmp/_cited.txt

# 检查参考文献条目数
ref_count=$(awk '/^## 参考文献/,0' paper/main.md | grep -cE '^\[[0-9]+\]')
echo "参考文献条目: $ref_count"
```

⛔ 引用编号必须连续递增（[1], [2], [3], [4]... 按首次出现顺序），不能跳号、不能回退。
⛔ 多引用合并：编号相邻 → 用 `[1, 2, 3]`；编号不相邻或跨度大 → 分别写 `[1][5]`。
⛔ 数模 ≥ 10 篇，统计建模 ≥ 20 篇。

### Step 4.5: 用 scholar_fetch 验证文献（必跑）

⛔ **所有参考文献必须用 scholar_fetch.py 工具获取真实 BibTeX。禁止凭记忆编造。**

写正文时用**描述性 citation key**便于后续搜索：`作者姓_年份_主题关键词`。
- ✅ `wang_2023_供应链韧性` 
- ❌ `wang2023supply`（无法回搜）
- 不确定作者/年份 → `TODO__` 前缀：`TODO__整数规划_车辆调度`

写完正文后逐个验证：

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
mkdir -p _tmp

# 把每个引用的描述性 key 列到 _tmp/_topics.txt
while IFS= read -r key; do
    query=$(echo "$key" | sed 's/^TODO__//; s/_/ /g')
    echo "--- 搜索: $key (query: $query) ---"
    $PYTHON "$SCHOLAR_SCRIPT" bibtex "$query" --max 3
    sleep 0.5
done < _tmp/_topics.txt
```

处理每个搜索结果：
1. 检查 `match_label`：`"good"` → 直接用。`"partial"` → 核对标题。`"low"` → 重新搜索或用 WebSearch。
2. `match_score` < 0.3 说明可能搜错，不要盲目使用。
3. 把搜到的真实文献按 GB/T 7714 格式写入末尾的「## 参考文献」章节，顺序与正文 `[N]` **首次出现**顺序一致。

**兜底**：搜不到或 `match_label="low"`，用 WebSearch 在 Google Scholar / Semantic Scholar 网站手动核实标题+作者+年份。

### Step 4.6: Claims-Evidence 矩阵核对

写每个章节前重读 PROBLEM_ANALYSIS.md / MODELING_REPORT.md 中的 claims-evidence 矩阵：

```bash
grep -A 100 'Claims-Evidence\|claim.*evidence\|claim-evidence\|观点.*证据' PROBLEM_ANALYSIS.md MODELING_REPORT.md PAPER_PLAN.md 2>/dev/null | head -50
```

写作纪律：
- 论文中每个论断必须对应到规划中的某一行
- 不要添加规划外的新论断（如有新发现，先更新 MODELING_REPORT.md）
- 不要跳过规划中的论断（即使是负面结果也要如实报告）
- 每个论断的数值证据必须与 `figures/all_results.json` 一致

如果某个规划中的论断在数据中找不到证据，诚实写「初步结果提示 X，更严谨的验证留待未来工作」，不要编造证据。

### Step 5: De-AI polish

参见 `_utils/writing_rules.md` 的 `<de_ai_polish>`。重点：
- 删除「本文提出 / 我们提出」类套话开头
- 用具体动词替换「探索 / 研究 / 调查」
- 控制「本文 / 我们」频次
- 去掉 AI 写作痕迹（"值得注意的是" / "综上所述" 频繁出现）

### Step 5.5: 交叉评审（可选）

```bash
mkdir -p _tmp
cat << 'REVIEW_EOF' > _tmp/_review_prompt.txt
请评审这篇竞赛论文草稿。重点关注：
1. 子问题覆盖完整性（每个子问题是否给出明确数值结果？）
2. 论点-证据对齐（每个结论是否有数据支撑？）
3. 章节结构与竞赛规范一致性
4. 写作清晰度（是否有元叙述泄露 / 套话开头）
5. 评分 1-10 + 最需改进的 3 个方面

## 论文正文：
REVIEW_EOF
cat paper/main.md >> _tmp/_review_prompt.txt
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_cross_review.txt
```

如评审脚本不可用则跳过。

### Step 5.6: 最后写摘要

⛔ **MANDATORY: 现在才写摘要。** 之前是占位符。

读 RESULTS.md / figures/all_results.json / 已写完的各子问题章节，把每个子问题的具体数值结果摘出来填进摘要：

```markdown
## 摘要

[第 1 段] 本文针对... 的问题，建立了... 模型... [背景与思路概述]

[第 2 段] 针对问题一，本文采用... 算法，最优解为... 适应度达到 0.917，求解时间 9.4 秒。... [问题一具体方法+数值]

[第 3 段] 针对问题二，本文构建... 模型... [问题二具体方法+数值]

[第 4 段] 针对问题三，本文... [问题三具体方法+数值]

[第 5 段] 灵敏度分析表明... 模型评价显示... [模型评价+推广]

**关键词**：关键词1；关键词2；关键词3；关键词4；关键词5
```

⛔ 摘要 400-600 字（数模）/ 500-700 字（统计建模），按问题分段，每段用 markdown 空行分隔。

⛔ 统计建模额外写英文摘要（350-500 词），结构和数值与中文一一对应。

### Step 6: 最终验证

```bash
echo "=== 最终验证 ==="

# 1. 主产物
[ -f paper/main.md ] && SZ=$(wc -c < paper/main.md) || SZ=0
echo "paper/main.md: $SZ bytes"

# 2. 字符数与页数估算
chars=$(wc -m < paper/main.md)
est_pages=$((chars / 800))
target=${MAX_PAGES:-20}
echo "字符: $chars, 估算页数: ~$est_pages, 目标: ≥ $target"
if [ "$est_pages" -lt "$((target * 80 / 100))" ]; then
    echo "⛔ 页数严重不足，必须扩充最薄章节后再结束"
fi

# 3. 顶级章节数
sec_count=$(grep -cE '^## ' paper/main.md)
echo "顶级章节数: $sec_count"

# 4. 子问题覆盖度
for n in 一 二 三; do
    if grep -qE "^## [0-9]+ 问题${n}" paper/main.md; then
        echo "✅ 问题${n}章节存在"
    else
        echo "⚠ 问题${n}章节缺失"
    fi
done

# 5. 图嵌入检查
echo "--- 图嵌入检查 ---"
missing_img=0
for img in figures/*.png figures/*.pdf; do
    [ -f "$img" ] || continue
    bn=$(basename "$img")
    [ "$bn" = "latex_includes.tex" ] && continue
    if ! grep -q "$bn" paper/main.md; then
        echo "⚠ 未嵌入: $bn"
        missing_img=$((missing_img + 1))
    fi
done
echo "未嵌入图: $missing_img"
[ "$missing_img" -gt 0 ] && echo "⛔ 必须把缺失的图嵌入到对应章节"

# 6. 引用编号检查
max_cited=$(grep -oE '\[[0-9]+\]' paper/main.md | grep -v '^## ' | tr -d '[]' | sort -n | tail -1)
ref_lines=$(awk '/^## 参考文献/,0' paper/main.md | grep -cE '^\[[0-9]+\]')
echo "正文最大引用编号: ${max_cited:-0}, 参考文献条目: $ref_lines"
[ -n "$max_cited" ] && [ "$ref_lines" -lt "$max_cited" ] && echo "⛔ 参考文献条目少于正文引用编号"

# 7. LaTeX 残留检查
if grep -qE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter)\{' paper/main.md; then
    echo "⛔ LaTeX 残留："
    grep -nE '\\(begin|end|input|cite|ref|label|includegraphics|section|chapter)\{' paper/main.md | head -5
fi

# 8. .tex 残留检查
ls paper/*.tex paper/sections/*.tex 2>/dev/null | head -1 | grep -q . && echo "⛔ 检测到 .tex" || echo "✅ 无 .tex"

# 9. 摘要是否真写了（不是占位符）
if grep -A 3 '^## 摘要' paper/main.md | grep -qE '占位|placeholder|待|TODO'; then
    echo "⛔ 摘要还是占位符，必须填写"
fi
```

如果任何 ⛔ 出现，回到对应步骤修复。

## 统计建模专属：章节设计指南（仅 stats 类型适用）

数模竞赛章节固定（问题重述 → 假设 → 符号 → 各子问题 → 灵敏度 → 评价），但**统计建模章节由内容驱动**，没有固定模板。看 `MODELING_REPORT.md` / `TOPIC_PLAN.md` 后自主设计 5-7 个中段章节。

### 固定骨架（必须保留）

```
摘要（中英文，分页）
一、绪论/前言（研究背景 + 文献综述 + 研究目标）
  ↓
  [中段章节：内容驱动，3-5 章]
  ↓
N、结论与建议（结论 + 建议 + 创新与不足）
参考文献
致谢
附录（代码）
```

### 中段章节设计原则

**原则 1：章节标题必须具体，不要泛化**
- ✗ 「四、模型构建」 → ✓ 「四、基于 CNN 的水质预测模型构建与评价」
- ✗ 「五、实证分析」 → ✓ 「五、生育意愿的影响因素 — 集成学习模型」

**原则 2：按研究逻辑链组织，不按教科书方法论**
- 多子问题/多模型 → 每个模型一章
- 单方法深入分析 → 按分析步骤组织

**原则 3：数据与方法可合并或拆分**
- 数据简单（一个数据集）→ 合并「数据与方法」
- 数据复杂（多源、重预处理）→ 单独「数据描述与预处理」

### 4 个获奖论文结构示例（参考，不要照抄）

**示例 A — 分类 + 路径分析（生育意愿）**：
前言 → 模型构建（集成 + Bayesian Network） → 数据与预处理 → 探索性特征分析 → 影响因素（集成结果） → 影响路径（贝叶斯网络结果） → 结论

**示例 B — 混合建模（数据要素与经济增长）**：
研究背景+文献 → 研究思路 → 理论分析 → 模型构建（生产函数 + 回归 + ARIMA，每个一节） → 模型应用（GDP 预测） → 总结建议 → 创新与不足

**示例 C — DEA 评价（经济可持续性）**：
绪论 → 文献综述 → 研究区域概况 → 评价指标体系 → 数据优化处理（标准化 + PCA） → DEA 模型建立 → 结论建议

**示例 D — 深度学习预测（CNN 水质）**：
绪论 → 模型构建思路与创新 → 数据描述 → 主成分分析 → CNN 模型构建（含模型对比） → 结论展望

**关键观察**：
- 没有任何获奖论文用「基线回归 → 稳健性 → 异质性」结构（除非主题就是因果推断）
- 章节数 5-7，由内容决定
- 「模型介绍/理论基础」可在数据章节前或后
- 「创新与不足」可在结论里或单独一章

### 章节设计自查（写之前必跑）

- [ ] 每章标题是否含具体研究内容（不是「模型构建」这种泛化）？
- [ ] 章节顺序是否符合研究逻辑链？
- [ ] 核心分析章节（模型结果）是否占 40-50%？
- [ ] 是否有数据描述/探索性分析专章？
- [ ] 结论是否含「创新」「不足」？

中文数字章节（一、二、三...），子节用（一）（二）（三）。**不要**用 1、2、3 或 1.1、1.2。

## 写作深度参考（按竞赛类型）

| 类型 | 页数 | 字符数（markdown） | 文献数 |
|------|------|--------------------|--------|
| 数模国赛 (30p) | 25-30 | 18000-25000 | ≥ 10 |
| 华为杯 | 40-50 | 30000-40000 | ≥ 15 |
| MathorCup | 35-40 | 25000-35000 | ≥ 10 |
| 华中杯 | 25-30 | 18000-25000 | ≥ 10 |
| 五一杯 | 25-30 | 18000-25000 | ≥ 10 |
| 统计建模 | 35-40 | 25000-35000 | ≥ 20 |

### 数模竞赛各章字数（参考，1 字 ≈ 1 字符）

- 问题重述+分析：2-3 页（用自己话重述，不抄题目）
- 模型假设+符号说明：2 页（5-7 假设，每条含理由；15-25 符号一表）
- 每个子问题：5-7 页（建模 2p + 求解 1.5p + 结果表+图 1p + 分析 0.5-1.5p）
- 灵敏度分析：2-3 页（≥ 2 个关键参数，每个变化曲线 + 分析段）
- 模型评价：2 页（3-4 优点 + 2-3 不足 + 推广，纯文字无图）

### 统计建模各章字数（参考）

- 绪论/前言：4-8 页（背景 + 文献综述按 3-4 主题分组每组 3-5 篇 + 研究目标）
- 数据描述与预处理：6-8 页（数据源 + 变量表 + 描述统计 + 探索性分析）
- 模型/方法章节：6-10 页（理论基础 + 公式推导 + 参数 + 实现）
- 核心结果分析：10-16 页（**最重要**，每个结果 2-3 段解读）
- 结论建议：3-5 页

### 获奖论文共性

- 扎实的探索性分析（交叉表 + 分组对比 + 丰富可视化）
- 核心分析章节占 40-50%，每个数值结果有深度解读
- 章节标题具体（「基于集成学习的生育意愿影响因素分析」而非「模型构建」）
- 含「创新与不足」讨论（评审加分项）

### 图表使用原则

**统计建模**：图先于表。图表选择由实际方法决定 — 回归用 forest plot + 系数表；预测用预测对比图 + 准确率表；分类用混淆矩阵 + ROC；评价用雷达图 + 排名表。每个分析步骤必有对应图/表。

**数模竞赛**：「字不如表，表不如图」。每个子问题必有独立结果展示（表 + 图）。

不强求图表（纯文献综述、纯理论推导可不放图）。

## 引用规则（中文竞赛论文必须遵守）

### 上标格式

中文竞赛论文**必须用上标引用**：正文用 `[1]`（自动渲染为上标 ¹），不要用 `[1]` 平排显示。

### 编号递增（严格，不可违反）

写正文时每个引用编号必须比之前所有已出现的编号大：
- ✅ 正确：全文第一个引用 `[1]`，第二个 `[2]`，第三个 `[3]`...
- ❌ 错误：先出现 `[3]`，后出现 `[8]`，又回到 `[1]` — 编号跳跃
- ❌ 错误：前文 `[5]`，后文新引用为 `[3]` — 编号回退

### 多引用合并规则

同一处引用多篇文献时：
- ✅ 正确：`方法A [1, 2, 3]` — 编号升序
- ✅ 正确：`方法A [1] [5]` — 编号不相邻可分开
- ❌ 错误：`方法A [1] [2] [3]` — 连续相邻应合并为 `[1, 2, 3]`
- ❌ 错误：`方法A [3, 1, 2]` — 顺序错乱
- ❌ 错误：`方法A [3, 1]` — 编号降序

合并判定规则（严格）：
1. 多引用里编号必须升序
2. 编号不相邻（差 > 1）建议合并保持整洁
3. 不能保证升序，宁愿分开写也不要错序合并

### 数模 ≥ 10 篇，统计建模 ≥ 20 篇

## 长表格处理（>15 行结果表必须遵守）

如果某个结果表（调度方案、路径规划、逐日预测等）超过 15 行数据，**不要**完整放正文，会挤压正文空间。

正确做法：

1. **正文摘要表**：前 5 行 + 后 3 行 + 「⋮」省略 + 汇总统计（均值/最优/总计）。caption 注「（部分，完整结果见附录表 X）」。
2. **附录完整表**：在「## 附录 A」放完整表格。

```markdown
**表 N：问题一调度方案（部分，完整结果见附录表 X）**

| 任务 | 设备 | 开始 | 结束 |
|------|------|------|------|
| 1 | A | 0 | 5 |
| 2 | B | 2 | 8 |
| 3 | A | 5 | 12 |
| ⋮ | ⋮ | ⋮ | ⋮ |
| 28 | C | 45 | 52 |
| 29 | A | 48 | 55 |
| 30 | B | 50 | 58 |

注：完整调度方案（30 条）见附录表 X。Makespan = 58。
```

判断标准：表格行数 > 15 → 用摘要 + 附录方案。

## 数模竞赛章节铁律（写之前必读）

**⛔ 数模竞赛严格按章节顺序：**
```
## 1 问题重述（用自己的话，不抄题目原文）
## 2 模型假设（5-7 条，每条含内容 + 合理性说明）
## 3 符号说明（15-20 个核心变量，三线表）
## 4 问题一的建模与求解
## 5 问题二的建模与求解
## 6 问题三的建模与求解
## 7 灵敏度分析与模型检验
## 8 模型评价与推广
## 参考文献
## 附录 A：代码
```

**⛔ 模型假设数量控制**：4-5 条，不超过 6 条。每条 1-2 句话（假设内容 + 合理性说明），不写长段落。假设太多说明问题没简化好。

**⛔ 符号说明表格控制**：15-20 个变量以内。只列正文实际使用的核心变量，不要把所有中间变量都列进去。

**⛔ MathorCup 必须用 `MathorCupmodeling` 模板的章节命名**（队伍编号 + 题号 + 题目放在文档开头，不要单独封面页）。markdown 用对应一级标题表达即可，docx 引擎会按 profile 渲染。

**⛔ 华中杯特殊**：参考文献用编号 `[1]`，docx 引擎会按 profile 渲染。

## 图文一致性规则（写每章前必读）

**⛔ 图文数值一致性规则**：描述图表内容时（如"从图 X 可以看出，模型 A 的 RMSE 为 0.023"），数值必须从 `figures/*.json` / `RESULTS.md` 读取，不要凭记忆。

**⛔ 图片大小**：markdown 图片自动按页面宽度渲染（docx 引擎处理），写作时不需要手动指定尺寸。但描述图表前后必须有 ≥ 5 行分析文字（数值解读 + 对比 + 结论）。

## 约束一致性检查（写完正文必跑）

读 PROBLEM_ANALYSIS.md 检查每个数值结果是否满足题目约束：

```
=== 论文-题目约束一致性检查 ===
1. 读取题目里所有约束（容量、预算、时间窗、数量限制等）
2. 逐个检查论文正文中的结果是否满足这些约束
   例：题目说"车辆载重上限 6000kg"，论文写"装载 7344kg" → 矛盾，必须修
   例：题目说"30 个省份"，论文分析了 28 个 → 不完整，必须补
3. 摘要中的数字与正文一致？
4. 同一结果在多处出现时数字完全相同？
   （如问题一最优解在摘要、正文、结论 3 次出现，必须完全相同）
```

如果发现矛盾，**修改论文**而不是改约束。如果代码结果本身违反约束，回到 comp-code 修复。

## 各章节写作要点（通用，适配研究逻辑）

**⛔ 写作风格铁律（所有章节都遵守）：**
- **禁止用 markdown bullet/编号列表作为正文叙述。** bullet 仅用于「输入清单 / 评价指标定义 / 软件依赖 / 模型假设条目」。正文叙述必须连贯段落。
  - 列举用「（1）...（2）...（3）...」行内编号或「首先...其次...最后...」过渡词
- **每段至少 3-5 句话。** 不写 1-2 句的短段落。
- **连续段落不能以相同句式开头。** 三段都「本文...」开头必须改。
- **图表是论据不是主语。** 段落不能以「图 X 展示了」「如图 X 所示」「由图 X 可知」开头。先论点 → 图表作旁证（"如图 X 所示，..."以圆括号或独立短句出现）→ 推论。
- **禁止元叙述泄露。** 正文不能出现"参赛者"、"参赛队伍"、"RESULTS.md"、"figures/all_results.json"、"CLAUDE.md"等内部文件名或工作流术语。

### 绪论/前言（所有论文）
- 研究背景（问题为什么重要）→ 文献综述 / 研究现状（别人做了什么，差距在哪）→ 研究目标 / 内容 / 贡献 → 论文结构
- 文献综述按主题分组（≥ 15 引用），不要按时间顺序罗列

### 数据与预处理（几乎所有论文都要）
- 数据源 → 样本描述（时间范围 / 样本量 / 变量数）→ 变量定义 / 编码表 → 缺失值 / 异常值处理 → 探索性分析（分布图 / 趋势图 / 交叉表）
- 探索性分析是给评审看能力的关键，不要跳过

### 模型/方法章节（按实际研究内容组织）
- 每个模型/方法：理论基础（1-2 段）→ 数学公式 → 参数设定依据 → 实现细节
- 多模型：可以先介绍所有模型再展示结果（示例 B 风格），或每个模型一章带结果（示例 A 风格）

### 结果分析章节（核心，占 40-50%）
- 每个结果必须有：数值呈现（表/图）→ 解读（2-3 段，不只是「如表所示」）→ 与预期/其他方法对比 → 原因分析
- 多模型对比：横向对比表 + 选最优模型的理由

### 结论与建议
- 主要结论（呼应研究目标）→ 政策/应用建议（具体可执行）→ 创新点 → 不足与未来工作
- 「创新与不足」可在结论里或单独一章（示例 B 风格）

## 扩写策略（实质内容，不是注水）

- 公式列出但没推导 → 加分步推导 + 物理意义
- 结果只「如表所示」 → 加 2-3 段（数值含义 + 与预期对比 + 原因 + 与其他方法对比）
- 假设光秃秃列表 → 每条加合理性说明
- 算法只伪代码 → 加关键步骤说明 + 复杂度 + 收敛性讨论
- 文献综述只罗列 → 每篇加方法摘要 + 与本工作的联系

## Key Rules（docx 模式专属）

- **唯一主产物**：`paper/main.md`
- **绝不产**：`.tex` / `.bib` / `.cls` / `.sty` / `.aux`
- **公式**：`$...$` / `$$...$$`，禁止 `\begin{equation}` / `\[...\]` / `\begin{align}`
- **图嵌入**：`![中文 caption](path)`，禁止 `\includegraphics`
- **表格**：markdown pipe table，禁止 `\begin{table}` / `\input{TABLE_x.tex}`
- **引用**：`[N]`，禁止 `\cite{}`
- **参考文献**：以文本形式直接写在 `## 参考文献` 章节，禁止 `\bibitem` / `.bib`
- 数模摘要按问题分段（4-5 段，每段对应一个子问题）
- 中文 caption（不要英文）
- 正文字符数 ≥ MAX_PAGES × 800
- 数值必须来自 `figures/all_results.json` / `figures/problem_*_results.json` / `RESULTS.md`，禁止编造
- 长表格 (>15 行) 用「正文摘要 + 附录完整版」
- 引用编号按首次出现顺序，不跳号不回退
- 备份现有 `paper/main.md` 后再覆盖
