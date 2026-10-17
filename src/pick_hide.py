# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
src = Image.open(os.path.join(TMP, "dino_base.png")).convert("RGBA")
S = 0.86
BOX = (438, 0, 1000, 1000)

def make(dx, rot=-90):
    t = src.resize((2000, 2000), Image.LANCZOS)
    a = 1.0 / S
    t = t.transform((2000, 2000), Image.AFFINE,
                    (a, 0, 1000 - a * 1000, 0, a, 1860 - a * 1860), resample=Image.BICUBIC)
    t = t.rotate(rot, center=(1000, 1000), resample=Image.BICUBIC)
    t = t.transform((2000, 2000), Image.AFFINE, (1, 0, -dx, 0, 1, 0), resample=Image.BICUBIC)
    return t.resize((1000, 1000), Image.LANCZOS).crop(BOX)

cands = [
    ("当前 dx-360", -360),
    ("选1 躲着 -240", -240),
    ("选1 探头 +100", 100),
    ("选2 躲着 0", 0),
    ("选2 探头 +200", 200),
]
ch = 280
out = Image.new("RGB", (len(cands) * 215 + 8, ch + 34), (255, 255, 255))
d0 = ImageDraw.Draw(out)
for i, (lab, dx) in enumerate(cands):
    im = make(dx)
    w = max(1, int(im.width * ch / im.height))
    im = im.resize((w, ch), Image.LANCZOS)
    bg = Image.new("RGB", (w, ch), (250, 250, 252))
    bg.paste(im, (0, 0), im)
    out.paste(bg, (i * 215 + 4, 28))
    d0.text((i * 215 + 4, 8), lab, fill=(0, 0, 0))
out.save(os.path.join(TMP, "pick_hide.png"))
print("saved", out.size)
