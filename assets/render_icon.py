from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


SCALE = 3
SIZE = 1024
W = H = SIZE * SCALE
HERE = Path(__file__).resolve().parent
OUT = HERE / "icon-1024.png"
PREVIEW = HERE / "icon-preview-64.png"
ICO = HERE.parent / "icon.ico"


def rgb(hex_color: str) -> np.ndarray:
    value = hex_color.lstrip("#")
    return np.array([int(value[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def mix(a: np.ndarray, b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return a * (1.0 - t[..., None]) + b * t[..., None]


def over(base: np.ndarray, color: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    return base * (1.0 - alpha[..., None]) + color * alpha[..., None]


# Build the colour field at 3x, then downsample for clean app-icon edges.
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
x /= SCALE
y /= SCALE
t = np.clip((x + y) / (2.0 * SIZE), 0.0, 1.0)
left = rgb("#48C6FF")
middle = rgb("#6C63F5")
right = rgb("#FF5FA2")
first = np.clip(t / 0.44, 0.0, 1.0)
second = np.clip((t - 0.44) / 0.56, 0.0, 1.0)
field = np.where((t <= 0.44)[..., None], mix(left, middle, first), mix(middle, right, second))

cyan_distance = np.sqrt(((x - 235.0) / 560.0) ** 2 + ((y - 228.0) / 560.0) ** 2)
cyan_alpha = np.clip(1.0 - cyan_distance, 0.0, 1.0) ** 1.55 * 0.62
field = over(field, rgb("#C4F7FF"), cyan_alpha)

coral_distance = np.sqrt(((x - 820.0) / 620.0) ** 2 + ((y - 790.0) / 620.0) ** 2)
coral_alpha = np.clip(1.0 - coral_distance, 0.0, 1.0) ** 1.45 * 0.68
field = over(field, rgb("#FF9A9E"), coral_alpha)

sheen_axis = np.clip((0.75 * x + 0.45 * y) / 720.0, 0.0, 1.0)
sheen_alpha = np.clip(1.0 - sheen_axis, 0.0, 1.0) ** 2.0 * 0.20
field = over(field, rgb("#FFFFFF"), sheen_alpha)
field = np.clip(field, 0, 255).astype(np.uint8)
field_image = Image.fromarray(field, "RGB").convert("RGBA")

box = tuple(v * SCALE for v in (48, 48, 976, 976))
radius = 218 * SCALE
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)

canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
icon_shadow = mask.filter(ImageFilter.GaussianBlur(22 * SCALE))
shadow_layer = Image.new("RGBA", (W, H), (35, 22, 91, 0))
shadow_alpha = icon_shadow.point(lambda value: int(value * 0.23))
offset_alpha = Image.new("L", (W, H), 0)
offset_alpha.paste(shadow_alpha, (0, 18 * SCALE))
shadow_layer.putalpha(offset_alpha)
canvas.alpha_composite(shadow_layer)

field_image.putalpha(mask)
canvas.alpha_composite(field_image)

# A single white hub mark: centre + three endpoints, no orbit, particles or lettering.
glyph_mask = Image.new("L", (W, H), 0)
g = ImageDraw.Draw(glyph_mask)
line_width = 58 * SCALE
g.line([(512 * SCALE, 508 * SCALE), (512 * SCALE, 329 * SCALE)], fill=255, width=line_width)
g.line([(486 * SCALE, 532 * SCALE), (348 * SCALE, 673 * SCALE)], fill=255, width=line_width)
g.line([(538 * SCALE, 532 * SCALE), (676 * SCALE, 673 * SCALE)], fill=255, width=line_width)
for cx, cy, r in ((512, 303, 70), (320, 704, 70), (704, 704, 70), (512, 532, 86)):
    g.ellipse(((cx - r) * SCALE, (cy - r) * SCALE, (cx + r) * SCALE, (cy + r) * SCALE), fill=255)

glyph_shadow = glyph_mask.filter(ImageFilter.GaussianBlur(14 * SCALE))
glyph_shadow = glyph_shadow.point(lambda value: int(value * 0.28))
glyph_shadow_offset = Image.new("L", (W, H), 0)
glyph_shadow_offset.paste(glyph_shadow, (0, 13 * SCALE))
glyph_shadow_layer = Image.new("RGBA", (W, H), (51, 34, 122, 0))
glyph_shadow_layer.putalpha(glyph_shadow_offset)
canvas.alpha_composite(glyph_shadow_layer)

glyph_layer = Image.new("RGBA", (W, H), (255, 255, 255, 0))
glyph_layer.putalpha(glyph_mask)
canvas.alpha_composite(glyph_layer)

border = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(border).rounded_rectangle(
    tuple(v * SCALE for v in (50, 50, 974, 974)),
    radius=216 * SCALE,
    outline=(255, 255, 255, 88),
    width=3 * SCALE,
)
canvas.alpha_composite(border)

final = canvas.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
final.save(OUT, optimize=True)
final.resize((64, 64), Image.Resampling.LANCZOS).save(PREVIEW, optimize=True)
final.save(
    ICO,
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(OUT)
print(PREVIEW)
print(ICO)
