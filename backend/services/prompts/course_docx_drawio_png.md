

## ⛔ DrawIO 架构图：仅导出 PNG（Word 模式不要 PDF）+ 自动裁白边
本工作流最终导出 Word，**只需要 PNG**，不要 PDF：
```bash
DRAWIO=$(command -v draw.io 2>/dev/null || echo 'D:/项目/Auto-claude-code-research-in-sleep-main/desktop/runtime/draw.io/draw.io.exe')
for d in figures/*.drawio; do
    [ -f "$d" ] || continue
    bn=$(basename "$d" .drawio)
    # ⛔ scale 4 约 384 DPI；防中文糊；只导 PNG
    "$DRAWIO" --export --format png --crop --scale 4 --transparent --output "figures/${bn}.png" "$d" 2>/dev/null || true
    # 如果 PNG 导出失败或文件过小，临时导 PDF 再用 350 DPI 转 PNG（之后立即删 PDF）
    if [ ! -f "figures/${bn}.png" ] || [ $(stat -c%s "figures/${bn}.png" 2>/dev/null || wc -c < "figures/${bn}.png") -lt 30000 ]; then
        "$DRAWIO" --export --format pdf --crop --output "figures/${bn}.pdf" "$d" 2>/dev/null || true
        if [ -f "figures/${bn}.pdf" ]; then
            python3 -c "import fitz; doc=fitz.open('figures/${bn}.pdf'); pix=doc[0].get_pixmap(matrix=fitz.Matrix(350/72, 350/72), alpha=False); pix.save('figures/${bn}.png')" 2>/dev/null || \
            python3 -c "from pdf2image import convert_from_path; convert_from_path('figures/${bn}.pdf', dpi=350)[0].save('figures/${bn}.png','PNG')" 2>/dev/null || \
            echo "⚠ ${bn}.png 转换失败"
            # ⛔ 转完后立即删 PDF（Word 模式不需要）
            [ -f "figures/${bn}.png" ] && rm -f "figures/${bn}.pdf"
        fi
    fi
done

# ⛔ 第二步：所有 PNG 自动裁白边（消除 drawio --crop 失效或 PDF 边距导致的空白）
# 这一步必须做：Word 嵌入图片不会自动裁，外圈白边 = Word 里图周围一圈巨大空白
python3 << 'PY'
import os, glob
try:
    from PIL import Image, ImageChops
except ImportError:
    print("⚠ PIL 未安装，跳过裁白边")
    raise SystemExit(0)

def trim(im, bg_threshold=240):
    """裁掉图片四周的白色/接近白色的边。bg_threshold=240 容忍轻微抗锯齿灰边。"""
    # 转 RGB（PNG 可能是 RGBA，先合成白底再裁）
    if im.mode in ('RGBA', 'LA'):
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != 'RGB':
        im = im.convert('RGB')
    # 制造一个全白参考图，与原图 difference
    bg_ref = Image.new('RGB', im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg_ref)
    # 把 < threshold 的差异视为白边
    bbox_data = diff.point(lambda x: 0 if x < (255 - bg_threshold) else 255)
    bbox = bbox_data.getbbox()
    if bbox is None:
        return im  # 全白图
    # 加 20px padding，避免裁得太紧贴边
    pad = 20
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(im.size[0], x1 + pad)
    y1 = min(im.size[1], y1 + pad)
    return im.crop((x0, y0, x1, y1))

trimmed = 0
for png in glob.glob('figures/fig_*.png'):
    try:
        im = Image.open(png)
        orig_w, orig_h = im.size
        cropped = trim(im)
        new_w, new_h = cropped.size
        # 只在裁掉超过 5% 时保存（避免无意义的细微差异）
        if (orig_w - new_w) / orig_w > 0.05 or (orig_h - new_h) / orig_h > 0.05:
            cropped.save(png, 'PNG', optimize=True)
            print(f"  ✂ 裁白边: {os.path.basename(png)} {orig_w}x{orig_h} → {new_w}x{new_h}")
            trimmed += 1
    except Exception as e:
        print(f"  ⚠ {png} 裁边失败: {e}")
print(f"完成：{trimmed} 张图被裁掉了多余白边")
PY

# 清理：删除遗留的 fig_*.pdf（Word 模式不需要）
find figures/ -name 'fig_*.pdf' -delete 2>/dev/null || true
```
**清晰度自检**：每张 PNG 应 ≥ 50KB；如有 < 30KB 的 PNG，重新用更高 scale 导出。
导出完成后必须 `ls -la figures/*.png` 验证每张架构图都有清晰 PNG，且 `ls figures/fig_*.pdf` 应无文件。
