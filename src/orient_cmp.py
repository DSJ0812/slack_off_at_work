# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
src = Image.open(os.path.join(TMP, "dino_base.png")).convert("RGBA")
S = 0.86
LEFT_BOX  = (438, 0, 1000, 1000)
RIGHT_BOX = (0, 0, 562, 1000)

def make(rot, dx, box):
    t = src.resize((2000, 2000), Image.LANCZOS)
    a = 1.0 / S
    t = t.transform((2000, 2000), Image.AFFINE,
                    (a, 0, 1000 - a * 1000, 0, a, 1860 - a * 1860), resample=Image.BICUBIC)
    t = t.rotate(rot, center=(1000, 1000), resample=Image.BICUBIC)
    t = t.transform((2000, 2000), Image.AFFINE, (1, 0, -dx, 0, 1, 0), resample=Image.BICUBIC)
    return t.resize((1000, 1000), Image.LANCZOS).crop(box)

def board(cands, box, path):
    ch = 300
    out = Image.new("RGB", (len(cands) * 250 + 8, ch + 34), (255, 255, 255))
    d0 = ImageDraw.Draw(out)
    for i, (lab, rot, dx) in enumerate(cands):
        im = make(rot, dx, box)
        w = max(1, int(im.width * ch / im.height))
        im = im.resize((w, ch), Image.LANCZOS)
        bg = Image.new("RGB", (w, ch), (250, 250, 252))
        bg.paste(im, (0, 0), im)
        out.paste(bg, (i * 250 + 4, 28))
        d0.text((i * 250 + 4, 8), lab, fill=(0, 0, 0))
    out.save(path)
    print("saved", path)

# 贴左：可见区在素材右半边
board([
    ("1  rot+90 dx800 (当前)", 90, 800),
    ("2  rot-90 dx0", -90, 0),
    ("3  rot-90 dx-400", -90, -400),
    ("4  rot-90 dx-800", -90, -800),
], LEFT_BOX, os.path.join(TMP, "orient_L.png"))

# 贴右：可见区在素材左半边
board([
    ("1  rot-90 dx-800 (当前)", -90, -800),
    ("2  rot+90 dx0", 90, 0),
    ("3  rot+90 dx400", 90, 400),
    ("4  rot+90 dx800", 90, 800),
], RIGHT_BOX, os.path.join(TMP, "orient_R.png"))
