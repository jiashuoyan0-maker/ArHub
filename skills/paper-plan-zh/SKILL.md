---
name: paper-plan-zh
description: "Generate a structured Chinese paper outline. Use when user says \"中文大纲\", \"中文论文规划\", \"Chinese paper outline\", or wants to create a Chinese academic paper plan."
argument-hint: [topic]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# 中文论文大纲生成

根据课题生成结构化大纲：**$ARGUMENTS**

## 常量

- **PAPER_TYPE** — `bachelor`/`master`/`journal`。默认 `journal`。
- **MAX_PAGES** — 本科=25、硕士=55、期刊=15。
- **CUSTOM_REQUIREMENTS** — 用户自定义要求，优先级最高。
- **REVIEWER_SCRIPT** — 外部评审脚本

## 输入

1. NARRATIVE_REPORT.md / STORY.md / AUTO_REVIEW.md / IDEA_REPORT.md
2. user_data/ — 数据文件、参考资料

如果以上均不存在，要求用户用 3-5 句话描述核心贡献。

## ⛔⛔⛔ 完成铁律（最高优先级）

**本步骤必须产出 `PAPER_PLAN.md`（≥ 1KB，完整的论文大纲）**。

⛔ **结束前必跑产出验证**：
```bash
[ -f PAPER_PLAN.md ] && SZ=$(wc -c < PAPER_PLAN.md) || SZ=0
[ "$SZ" -ge 1024 ] && echo "✅ PAPER_PLAN.md ($SZ)" \
    || echo "❌ PAPER_PLAN.md 缺失或过小 — 必须补全后重新跑验证, 不要结束本步骤"
```

## 工作流程

### Step 0: 数据探索（最高优先级）

扫描 `user_data/` 中所有数据文件，用 pandas 分析：
- 列名、数据类型、缺失值、基本统计量
- 数据模式（时间序列？方法对比？相关性？）
- 能支撑哪些论点、可生成哪些图表

### Step 1: 提取论点与证据

结合数据分析结果，构建论点-证据矩阵：

| 论点 | 证据 | 状态 | 章节 |
|------|------|------|------|
| [论点1] | [实验A, 指标B] | 充分支持 | §3.2 |

### Step 2: 确定论文结构

根据 PAPER_TYPE 选择：

**本科（~30页）**：绪论→理论基础→方法→实验→总结
**硕士（~80页）**：绪论→相关工作→方法A→方法B→实验→总结
**期刊（~15页）**：引言→相关工作→方法→实验→讨论→结论

### Step 3: 逐章节详细规划

每章指定：核心内容、子节划分、关键论点、图表计划、预计页数、关键引用。

### Step 4: 图表计划（范例感知 + 逐节审查 + 对标自检）

#### 阶段 A：范例感知

在规划图表前，**必须先读取图表范例文件**，了解同类型优秀论文的图表分布：

```bash
cat _utils/figure_exemplars.md 2>/dev/null || cat skills/shared-scripts/figure_exemplars.md
```

根据 PAPER_TYPE（本科/硕士/期刊），找到对应的"学术论文"部分，参考其图表数量和比例。不要机械套用，而是理解"这个体量的论文，图表密度大概是什么水平"。

以上比例和数量仅供参考，Claude 根据具体课题内容自主调整。理论重的论文架构图会多一些，实验重的论文数据图会多一些，统计类论文表格会多一些——这都是合理的。关键是逐节审查时认真思考每个小节是否需要可视化辅助。

#### 阶段 B：逐节审查

对每个章节的每个小节，逐一回答三个问题：

1. **这一节的核心结论/内容是什么？**（一句话概括）
2. **读者只看文字能直观理解吗？**还是需要图或表来辅助理解？
   - 数值对比 → 需要表格或柱状图
   - 趋势变化 → 需要折线图
   - 空间/结构关系 → 需要架构图或流程图
   - 分布特征 → 需要直方图/箱线图/热力图
   - 算法流程 → 需要伪代码或流程图
   - 纯文字论述（如文献综述的分类讨论）→ 不需要图表
3. **如果需要，图更合适还是表更合适？**
   - 精确数值（回归系数、p 值、准确率）→ 表
   - 直观趋势/对比/分布 → 图
   - 两者都需要时，主结果用表，辅助可视化用图

将审查结果填入模板的"逐节审查结果"表格。

#### 阶段 C：对标自检

规划完成后，统计图表总数，和阶段 A 的同类型范例对比，填入模板的"对标自检"表格。

**如果任何项标注 ⚠️，必须回到阶段 B 的审查表，找出哪些小节遗漏了图表，补充规划。**

重点检查：
- 方法/理论章节是否有架构图或算法伪代码？
- 实验/实证章节的每个实验/分析是否有对应的图或表？
- 超过 5 页的章节是否至少有 1 个图表？
- 绪论和总结通常不需要图表（除非有 hero figure 或研究路线图）

### Step 5: 引用规划

按章节列出需要的引用。绝不编造 BibTeX，不确定的标记 `[待验证]`。

### Step 6: 交叉评审

Send outline to external reviewer for feedback:

```bash
mkdir -p _tmp
cat << 'REVIEW_EOF' > _tmp/_review_prompt.txt
请评审这份论文大纲。重点关注：
1. 故事线是否有说服力？（背景→空白→贡献→证据）
2. 论点-证据矩阵是否有缺口？
3. 图表规划是否足够支撑页数预算？
4. 结构是否有问题（缺失章节、顺序不当）？
5. 评分（1-10）和最需要改进的 3 个方面

## 论文大纲：
REVIEW_EOF
cat PAPER_PLAN.md >> _tmp/_review_prompt.txt
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
$PYTHON "$REVIEWER_SCRIPT" --prompt-file _tmp/_review_prompt.txt --thread-file _tmp/_reviewer_thread.json 2>&1 | tee _tmp/_outline_review.txt
```

脚本不可用则跳过。

### Step 7: 输出

保存到 `PAPER_PLAN.md`，**严格遵循 `templates/paper_plan_template.md` 的格式**。

## 关键规则

- 大文件用 Bash heredoc 分块写入
- 不生成作者信息
- 如实标注证据缺口
- 页数预算是硬性约束
- 论点-证据矩阵是骨架
- 所有输出使用中文
- ⛔ 主输出文件：`PAPER_PLAN.md`。不要在根目录写额外报告
- ⛔ Markdown 中的 LaTeX 公式：`$$` 块级公式单独成行且前后空行，行内用 `$...$`，多行环境用块级，避免 `\text{}` 包裹中文
