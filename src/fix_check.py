# -*- coding: utf-8 -*-
import os, math
from PIL import Image, ImageDraw
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
src = Image.open(os.path.join(TMP, "dino_base.png")).convert("RGBA")
S = 0.86
LB, RB = (438, 0, 1000, 1000), (0, 0, 562, 1000)

def make(rot, dx, dy, wob):
    t = src.resize((2000, 2000), Image.LANCZOS)
    a = 1.0 / S
    t = t.transform((2000, 2000), Image.AFFINE,
                    (a, 0, 1000 - a * 1000, 0, a, 1860 - a * 1860), resample=Image.BICUBIC)
    t = t.rotate(rot + wob, center=(1000, 1000), resample=Image.BICUBIC)
    t = t.transform((2000, 2000), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BICUBIC)
    return t.resize((1000, 1000), Image.LANCZOS)

def strip(rot, dxp, box, path):
    dy_sign = 1.0 if rot > 0 else -1.0
    tiles, labs = [], []
    for i in range(6):
        s = math.sin(i / 6.0 * 2 * math.pi)
        im = make(rot, dxp, 120.0 * dy_sign * s, 6.0 * s).crop(box)
        w = max(1, int(im.width * 200 / im.height))
        im = im.resize((w, 200), Image.LANCZOS)
        bg = Image.new("RGB", (w, 200), (250, 250, 252)); bg.paste(im, (0, 0), im)
        tiles.append(bg); labs.append("s=%.2f" % s)
    out = Image.new("RGB", (len(tiles) * 145 + 8, 232), (255, 255, 255))
    d0 = ImageDraw.Draw(out)
    for i, t in enumerate(tiles):
        out.paste(t, (i * 145 + 4, 26))
        d0.text((i * 145 + 4, 6), labs[i], fill=(0, 0, 0))
    out.save(path); print("saved", path)

strip(-90,  200, LB, os.path.join(TMP, "fix_L.png"))
strip( 90, -200, RB, os.path.join(TMP, "fix_R.png"))
