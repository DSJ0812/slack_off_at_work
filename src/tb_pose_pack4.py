# -*- coding: utf-8 -*-
"""tb_pose_pack3.py — 摸肚子新动作铺素材（全 6 套）

修复项：
  1. 变胖：宽度归一 0.45 → 1.0（pose_cut3）
  2. 变暗：分部位色彩校准，红身对齐 (244,67,63)（pose_cut3）
  3. 泪珠：A/B/C_ill 也换成新动作（用户确认）

结构差异：
  · _Happy 有 tb1/tb2 两套随机变体 → 两套铺同样内容
  · _ill  是平铺结构（无 tb 子目录） → 直接铺

分段（沿用上次确认）：
  A_Start : f1,3,5,8 + f33,34,34,35,35,36  = 10 帧
  B_Loop  : f37~f65 均匀 8 帧              =  8 帧
  C_End   : f92~f100 均匀 6 帧             =  6 帧
时长：A 95,95,95,115×7 / B 100×8 / C 100×6
"""
import os, glob
import numpy as np
from PIL import Image

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "pose_cut3")
DST_ROOT = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet/dino/Touch_Body"
ARCH = os.path.join(TMP, "_archive_tbpose")

files = sorted(glob.glob(os.path.join(SRC, "t_*.png")))
print("可用帧:", len(files))

A_IDX = [0, 2, 4, 7, 32, 33, 34, 34, 35, 35]
B_IDX = [36, 40, 44, 48, 52, 56, 60, 64]
C_IDX = [91, 92, 93, 94, 96, 99]
print("A:", [i + 1 for i in A_IDX])
print("B:", [i + 1 for i in B_IDX])
print("C:", [i + 1 for i in C_IDX])

A_DUR = [95, 95, 95, 115, 115, 115, 115, 115, 115, 115]
B_DUR = [100] * 8
C_DUR = [100] * 6


def place(seg, idxs, durs, variant):
    """variant: 'tb1' / 'tb2' / '' (平铺)"""
    outdir = os.path.join(DST_ROOT, seg, variant) if variant else os.path.join(DST_ROOT, seg)
    os.makedirs(outdir, exist_ok=True)
    # 归档旧帧（os.replace，不用 os.remove —— safe-delete shim 会崩）
    for old in glob.glob(os.path.join(outdir, "_*.png")):
        a = os.path.join(ARCH, seg, variant or "_flat")
        os.makedirs(a, exist_ok=True)
        d = os.path.join(a, os.path.basename(old))
        if not os.path.exists(d):
            os.replace(old, d)
    for k, (ii, du) in enumerate(zip(idxs, durs)):
        im = Image.open(files[ii]).convert("RGBA")
        if im.size != (1000, 1000):
            im = im.resize((1000, 1000), Image.LANCZOS)
        im.save(os.path.join(outdir, "_%03d_%d.png" % (k, du)), optimize=True)
    print("  %-28s -> %d 帧" % (os.path.join(seg, variant or "(flat)"), len(idxs)))


# _Happy：tb1 / tb2 两套
for tb in ("tb1", "tb2"):
    place("A_Happy", A_IDX, A_DUR, tb)
    place("B_Happy", B_IDX, B_DUR, tb)
    place("C_Happy", C_IDX, C_DUR, tb)

# _ill：平铺结构
place("A_ill", A_IDX, A_DUR, "")
place("B_ill", B_IDX, B_DUR, "")
place("C_ill", C_IDX, C_DUR, "")

print("done")
