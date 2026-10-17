# -*- coding: utf-8 -*-
import os, glob
from PIL import Image, ImageDraw
VUP = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet/vup"
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"

picks = [
    ("摸身体A tb2", "Touch_Body/A_Happy/tb2"),
    ("摸身体A tb1", "Touch_Body/A_Happy/tb1"),
    ("摸身体B 循环", "Touch_Body/B_Happy/tb1"),
    ("捏 A", "Pinch/Happy/A"),
    ("捏 B", "Pinch/Happy/B"),
    ("捏 C", "Pinch/Happy/C"),
]
cell = 240
out = Image.new("RGB", (len(picks) * 250 + 8, cell + 34), (255, 255, 255))
d0 = ImageDraw.Draw(out)
for i, (lab, rel) in enumerate(picks):
    fs = sorted(glob.glob(os.path.join(VUP, rel, "*.png")))
    if not fs:
        d0.text((i * 250 + 6, 10), "无 " + rel, fill=(200, 0, 0)); continue
    im = Image.open(fs[len(fs) // 2]).convert("RGBA")
    bg = Image.new("RGB", (cell, cell), (250, 250, 252))
    t = im.resize((cell, cell), Image.LANCZOS)
    bg.paste(t, (0, 0), t)
    out.paste(bg, (i * 250 + 4, 28))
    d0.text((i * 250 + 4, 8), "%s (%d帧)" % (lab, len(fs)), fill=(0, 0, 0))
out.save(os.path.join(TMP, "ref_body_pinch.png"))
print("saved ref_body_pinch.png")
