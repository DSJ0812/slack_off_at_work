# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw
VUP = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet/vup"
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"

def tile(im, cell, xline=None, box=None):
    bg = Image.new("RGBA", (cell, cell), (250, 250, 252, 255))
    if box:
        im = im.crop(box)
    t = im.resize((cell, cell), Image.LANCZOS)
    bg.alpha_composite(t)
    d = ImageDraw.Draw(bg)
    if xline is not None:
        xx = int(xline * cell / 1000.0)
        d.line([(xx, 0), (xx, cell)], fill=(230, 50, 50, 255), width=4)
    return bg

rows = [
    ("SideHide_Left_Main", [("Nomal/A/A_000_125.png","A0"),("Nomal/A/A_004_125.png","A4"),
                            ("Nomal/A/A_008_125.png","A8"),("Nomal/B_2/B2_003_125.png","B2"),
                            ("Nomal/C/C_004_125.png","C4")]),
]
cell = 260
for sub, items in rows:
    out = Image.new("RGBA", (cell*len(items), cell*2+40), (255,255,255,255))
    d0 = ImageDraw.Draw(out)
    for i,(rel,lab) in enumerate(items):
        p = os.path.join(VUP, sub, rel)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        # 上排：完整素材 + 可见区红线（素材系 438）
        out.alpha_composite(tile(im, cell, xline=438), (i*cell, 20))
        # 下排：裁出可见区（素材 438~1000）
        out.alpha_composite(tile(im, cell, box=(438,0,1000,1000)), (i*cell, cell+40))
        d0.text((i*cell+4, 4), "%s 上=全图+红线 下=可见区" % lab, fill=(0,0,0,255))
    out.convert("RGB").save(os.path.join(TMP, "ref_%s.png" % sub))
    print("saved ref_%s.png" % sub)

# 单独放大原版 A_008 与 C_004
for rel, name in [("Nomal/A/A_008_125.png","A8"), ("Nomal/C/C_004_125.png","C4"),
                  ("Nomal/B_2/B2_003_125.png","B2")]:
    im = Image.open(os.path.join(VUP, "SideHide_Left_Main", rel)).convert("RGBA")
    bg = Image.new("RGB", (500,500), (250,250,252))
    bg.paste(im.resize((500,500), Image.LANCZOS), (0,0), im.resize((500,500), Image.LANCZOS))
    bg.save(os.path.join(TMP, "ref_big_%s.png" % name))
print("done")
