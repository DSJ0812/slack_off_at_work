# -*- coding: utf-8 -*-
import os, glob
from PIL import Image, ImageDraw
DINO = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet/dino"
TMP  = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
LEFT_BOX  = (438, 0, 1000, 1000)   # 贴左可见区（素材系）
RIGHT_BOX = (0,   0, 562,  1000)   # 贴右可见区（素材系）

def midframe(rel):
    fs = sorted(glob.glob(os.path.join(DINO, rel, "*.png")))
    if not fs: return None, rel, 0
    return Image.open(fs[len(fs)//2]).convert("RGBA"), rel, len(fs)

rows = [
    ("贴左-Main躺下",  "SideHide_Left_Main/Nomal/A",  LEFT_BOX),
    ("贴左-Main躲着",  "SideHide_Left_Main/Nomal/B_1", LEFT_BOX),
    ("贴左-Rise探头",  "SideHide_Left_Rise/Nomal/B",  LEFT_BOX),
    ("贴右-Main躺下",  "SideHide_Right_Main/Nomal/A",  RIGHT_BOX),
    ("贴右-Main躲着",  "SideHide_Right_Main/Nomal/B_1", RIGHT_BOX),
    ("贴右-Rise探头",  "SideHide_Right_Rise/Nomal/B",  RIGHT_BOX),
]
cell_h = 240
cols = 3
out = Image.new("RGB", (cols*260+8, len(rows)*(cell_h+26)+8), (255,255,255))
d0 = ImageDraw.Draw(out)
for r,(lab, rel, box) in enumerate(rows):
    fs = sorted(glob.glob(os.path.join(DINO, rel, "*.png")))
    if not fs:
        d0.text((8, r*(cell_h+26)+8), "%s  【无文件 %s】" % (lab, rel), fill=(200,0,0)); continue
    picks = [fs[0], fs[len(fs)//2], fs[-1]]
    for c, fp in enumerate(picks):
        im = Image.open(fp).convert("RGBA").crop(box)
        w = max(1, int(im.width * cell_h / im.height))
        im = im.resize((w, cell_h), Image.LANCZOS)
        bg = Image.new("RGB", (w, cell_h), (250,250,252))
        bg.paste(im, (0,0), im)
        out.paste(bg, (c*260+4, r*(cell_h+26)+22))
    d0.text((6, r*(cell_h+26)+6), "%s  [%s] 共%d帧  首/中/末" % (lab, rel.split('/')[-1], len(fs)), fill=(0,0,0))
out.save(os.path.join(TMP, "dino_hide_now.png"))
print("saved dino_hide_now.png")
