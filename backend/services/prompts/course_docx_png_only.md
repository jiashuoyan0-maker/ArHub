

## ⛔ 输出格式：仅 PNG（Word 导出工作流）
本工作流最终导出 Word 文档（.docx），Word **不能嵌入 PDF**，因此：
**所有图表只输出 PNG，不要输出 PDF**：
```python
from _utils.plot_utils import setup_style, save_fig; setup_style()
# ⛔ Word 模式：只用 .png 扩展名（save_fig 会自动 350 DPI 防中文糊）
save_fig(fig, 'figures/fig_xxx.png')
# ⛔ 不要再调用 save_fig(fig, 'xxx.pdf') 或 fig.savefig('xxx.pdf')
```
**对于 drawio/GPT Image/TikZ 等只有 PDF 的图，必须立刻转 PNG 并删除原 PDF**：
```bash
# 包含 fig_*.pdf 和 tikz_*.pdf（TikZ 几何/算法图编译产出，最容易被漏）
for pdf in figures/fig_*.pdf figures/tikz_*.pdf; do
    [ -f "$pdf" ] || continue
    bn=$(basename "$pdf" .pdf)
    png="figures/${bn}.png"
    if [ ! -f "$png" ]; then
        # DPI=350（含中文小字时；250 以下会糊）
        python3 -c "import fitz; doc=fitz.open('$pdf'); pix=doc[0].get_pixmap(matrix=fitz.Matrix(350/72, 350/72), alpha=False); pix.save('$png')" 2>/dev/null || \
        python3 -c "from pdf2image import convert_from_path; convert_from_path('$pdf', dpi=350)[0].save('$png','PNG')" 2>/dev/null || \
        echo "⚠ $pdf → PNG 转换失败"
    fi
    # 转完后删除 PDF（Word 不需要，避免冗余）
    [ -f "$png" ] && rm -f "$pdf"
done
```
**⛔ TikZ 多页 PDF（一个 tikz_diagrams.tex 画了多张图）**：先拆页再转 PNG：
```bash
for tpdf in figures/tikz_diagrams.pdf figures/tikz_*.pdf; do
    [ -f "$tpdf" ] || continue
    pages=$(python3 -c "import fitz; print(fitz.open('$tpdf').page_count)" 2>/dev/null || echo 1)
    bn=$(basename "$tpdf" .pdf)
    if [ "$pages" -gt 1 ]; then
        # 多页：每页转一张 PNG（tikz_diagrams_1.png, _2.png ...），供 main.md 分别引用
        python3 -c "import fitz; d=fitz.open('$tpdf'); [d[i].get_pixmap(matrix=fitz.Matrix(350/72,350/72),alpha=False).save(f'figures/${bn}_{i+1}.png') for i in range(d.page_count)]" 2>/dev/null && rm -f "$tpdf"
    fi
done
```
**核查清单**（写完所有图后必须跑）：
```bash
# 1. figures/ 不应有 fig_*.pdf / tikz_*.pdf 残留
remaining_pdf=$(find figures/ \( -name 'fig_*.pdf' -o -name 'tikz_*.pdf' \) 2>/dev/null | wc -l)
[ "$remaining_pdf" -gt 0 ] && echo "❌ 还残留 $remaining_pdf 个 PDF，需删除"
# 2. 每个 PNG 不应过小
for png in figures/fig_*.png figures/tikz_*.png; do
    [ -f "$png" ] || continue
    sz=$(wc -c < "$png" 2>/dev/null || stat -c%s "$png" 2>/dev/null)
    if [ "$sz" -lt 30000 ]; then
        echo "⚠ $(basename $png) 仅 ${sz} 字节，可能模糊（应 ≥ 50KB），建议提高 DPI 重新生成"
    fi
done
```
**任何 ❌ 或 ⚠ 都必须修复**（重新生成或转换）。
**⛔ 转 PNG 后，确保 paper/main.md 用 `![](figures/tikz_xxx.png)` 引用了每张 TikZ 图（几何示意图、算法流程图），不能因为转了 PNG 却没在正文引用而丢图。**
