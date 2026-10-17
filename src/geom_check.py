# -*- coding: utf-8 -*-
import os, glob, time
import numpy as np
from PIL import Image, ImageDraw
DINO = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet/dino"
TMP  = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"

print("=== VPet cache 状态 ===")
cache = r"D:/softapp/VPet_dino/VPet/cache"
cf = [os.path.join(cache, f) for f in os.listdir(cache)]
cf.sort(key=lambda p: os.path.getmtime(p), reverse=True)
print("最新 cache:", time.strftime("%m-%d %H:%M:%S", time.localtime(os.path.getmtime(cf[0]))), "| 共", len(cf), "个")

def analyze(rel, idx):
    fs = sorted(glob.glob(os.path.join(DINO, rel, "*.png")))
    if not fs:
        print("  NO FILE", rel); return None
    im = Image.open(fs[idx]).convert("RGBA")
    a = np.array(im); al = a[:, :, 3]
    cols = np.where(al.max(axis=0) > 10)[0]
    rows = np.where(al.max(axis=1) > 10)[0]
    print("  %-42s n=%d  x[%d,%d]  y[%d,%d]" % (rel.split('/')[-2]+"/"+rel.split('/')[-1], len(fs),
          cols.min(), cols.max(), rows.min(), rows.max()))
    return im

print("=== 素材内容范围（素材系 1000，横躺后） ===")
imL  = analyze("SideHide_Left_Main/Nomal/B_1", 1)
imLA = analyze("SideHide_Left_Main/Nomal/A", -1)
imR  = analyze("SideHide_Right_Main/Nomal/B_1", 1)

def annot(im, box, path, label):
    bg = Image.new("RGB", (620, 640), (250, 250, 252))
    t = im.resize((600, 600), Image.LANCZOS)
    bg.paste(t, (10, 10), t)
    d = ImageDraw.Draw(bg)
    for xx in box:
        px = 10 + int(xx * 600 / 1000)
        d.line([(px, 10), (px, 610)], fill=(230, 50, 50), width=4)
    d.text((10, 616), label, fill=(0, 0, 0))
    bg.save(path); print("  saved", path)

if imL:  annot(imL,  (438, 1000), os.path.join(TMP, "look_LB.png"), "贴左 HideLB  红线=可见区 [438,1000]")
if imR:  annot(imR,  (0, 562),    os.path.join(TMP, "look_RB.png"), "贴右 HideRB  红线=可见区 [0,562]")
if imLA: annot(imLA, (438, 1000), os.path.join(TMP, "look_LA.png"), "贴左 HideLA末帧 红线=可见区 [438,1000]")
