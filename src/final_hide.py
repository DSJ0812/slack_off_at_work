# -*- coding: utf-8 -*-
import os, glob
from PIL import Image, ImageDraw
FR  = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/dino_anim3/frames"
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
LB, RB = (438,0,1000,1000), (0,0,562,1000)
H = 300

def pick(clip, idx, box):
    fs = sorted(glob.glob(os.path.join(FR, clip, "*.png")))
    im = Image.open(fs[idx]).convert("RGBA").crop(box)
    w = max(1, int(im.width*H/im.height))
    im = im.resize((w, H), Image.LANCZOS)
    bg = Image.new("RGB", (w, H), (248,250,252))
    bg.paste(im, (0,0), im)
    return bg

cols = [
    ("贴左 · 躺好", "HideLA", -1, LB),
    ("贴左 · 躲着", "HideLB",  1, LB),
    ("贴左 · 探头", "HideLRB", 2, LB),
    ("贴右 · 躺好", "HideRA", -1, RB),
    ("贴右 · 躲着", "HideRB",  1, RB),
    ("贴右 · 探头", "HideRRB", 2, RB),
]
CW = 200
out = Image.new("RGB", (len(cols)*CW+8, H+40), (255,255,255))
d0 = ImageDraw.Draw(out)
for i,(lab, clip, idx, box) in enumerate(cols):
    bg = pick(clip, idx, box)
    x = i*CW + (CW-bg.width)//2
    out.paste(bg, (x, 32))
    d0.text((i*CW+6, 8), lab, fill=(0,0,0))
    d0.line([(i*CW, 28), (i*CW, H+36)], fill=(225,225,228), width=1)
out.save(os.path.join(TMP, "final_hide.png"))
print("saved final_hide.png", out.size)
