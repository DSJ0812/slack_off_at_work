# -*- coding: utf-8 -*-
"""make_pinch_sheet.py — 把 Pinch A/B/C 三段的最新渲染拼成一张总览图（给用户看）。

输出 probe_pinch_v3.png：
  第1行 PinchA 10 帧（瞪眼 → 忍痛 → 被拽歪）
  第2行 PinchB  6 帧（甩头挣扎）
  第3行 PinchC 16 帧（松手甩头 → 缩小 → 喷火 → 收火）
"""
import os
from PIL import Image, ImageDraw

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
FR = os.path.join(TMP, "dino_anim3", "frames")
OUT = os.path.join(TMP, "probe_pinch_v3.png")


def load(nm):
    d = os.path.join(FR, nm)
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith(".png") and os.path.getsize(os.path.join(d, f)) > 0]


ROWS = [
    ("PinchA  10帧 · 瞪眼惊吓 → 眯眼忍痛 → 头被拽歪", "PinchA"),
    ("PinchB   6帧 · 按住不放，被拎着左右甩头挣扎", "PinchB"),
    ("PinchC  16帧 · 松手甩头回弹 → 缩小让位 → 喷火 → 收火", "PinchC"),
]
BOX = (90, 10, 910, 990)          # 完整角色（含平移余量）
CH = 230
CW = int(CH * (BOX[2] - BOX[0]) / (BOX[3] - BOX[1]))
COLS = 16
LBL = 26
sheet = Image.new("RGB", (CW * COLS, (CH + LBL) * len(ROWS)), (255, 255, 255))
ds = ImageDraw.Draw(sheet)
for r, (label, nm) in enumerate(ROWS):
    y0 = r * (CH + LBL)
    ds.rectangle([0, y0, CW * COLS, y0 + LBL], fill=(232, 238, 245))
    ds.text((8, y0 + 7), label, fill=(24, 34, 48))
    fs = load(nm)
    for c, fp in enumerate(fs):
        im = Image.open(fp).convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        sheet.paste(bg.crop(BOX).convert("RGB").resize((CW, CH), Image.LANCZOS),
                    (c * CW, y0 + LBL))
        ds.rectangle([c * CW, y0 + LBL, c * CW + CW, y0 + LBL + CH],
                     outline=(205, 212, 222))
        ds.text((c * CW + 4, y0 + LBL + 2), str(c), fill=(200, 40, 40))
sheet.save(OUT)
print("SHEET ->", OUT, sheet.size)
