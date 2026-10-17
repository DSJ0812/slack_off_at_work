# -*- coding: utf-8 -*-
"""tb_pose_pack.py v2 — 英雄pose版切段铺素材（含修正）"""
import os, glob
import numpy as np
from PIL import Image

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "pose_cut")
DST_ROOT = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet/dino/Touch_Body"
ARCH = os.path.join(TMP, "_archive_tbpose")

files = sorted(glob.glob(os.path.join(SRC, "t_*.png")))
print("可用帧:", len(files))

# A段：简化起手（站姿稳定 f1~f8 共 4 帧 + 起手 f33~f36 共 6 帧）
A_IDX = [0, 2, 4, 7, 32, 33, 34, 35, 35, 35]   # 末 3 帧重复=起手定格
A_IDX = [0, 2, 4, 7, 32, 33, 34, 34, 35, 35]
# B段：f37~f65 有动作区 8 帧
B_IDX = [36, 40, 44, 48, 52, 56, 60, 64]
# C段：f92~f100 均匀 6 帧
C_IDX = [91, 92, 93, 94, 96, 99]

print("A:", [i+1 for i in A_IDX])
print("B:", [i+1 for i in B_IDX])
print("C:", [i+1 for i in C_IDX])

A_DUR = [95,95,95,115,115,115,115,115,115,115]
B_DUR = [100]*8
C_DUR = [100]*6

def place(seg, idxs, durs):
    for tb in ("tb1","tb2"):
        outdir = os.path.join(DST_ROOT, seg, tb)
        os.makedirs(outdir, exist_ok=True)
        for old in glob.glob(os.path.join(outdir, "_*.png")):
            a = os.path.join(ARCH, seg, tb); os.makedirs(a, exist_ok=True)
            d = os.path.join(a, os.path.basename(old))
            if not os.path.exists(d): os.replace(old, d)
        for k,(ii,du) in enumerate(zip(idxs,durs)):
            im = Image.open(files[ii]).convert("RGBA")
            if im.size != (1000,1000): im = im.resize((1000,1000), Image.LANCZOS)
            im.save(os.path.join(outdir, "_%03d_%d.png" % (k,du)), optimize=True)
        print("  %s/%s -> %d 帧" % (seg, tb, len(idxs)))

place("A_Happy", A_IDX, A_DUR)
place("B_Happy", B_IDX, B_DUR)
place("C_Happy", C_IDX, C_DUR)
print("done")
