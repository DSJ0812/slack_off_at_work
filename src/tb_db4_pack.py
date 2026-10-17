# -*- coding: utf-8 -*-
"""tb_pose_pack3.py — 摸肚子新动作铺素材（全 6 套）

修复项：
  1. 变胖：宽度归一 0.45 → 1.0（db4_cut）
  2. 变暗：分部位色彩校准，红身对齐 (244,67,63)（db4_cut）
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
SRC = os.path.join(TMP, "db4_cut")
DST_ROOT = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet/dino/Touch_Body"
ARCH = os.path.join(TMP, "_archive_tbpose")

files = sorted(glob.glob(os.path.join(SRC, "t_*.png")))
print("可用帧:", len(files))

A_IDX = [0, 2, 4, 7, 13, 14, 15, 16, 16]
B_IDX = [17, 24, 31, 38, 45, 52, 59, 66, 73, 80]
C_IDX = [82, 85, 88, 91, 94, 96]
print("A:", [i + 1 for i in A_IDX])
print("B:", [i + 1 for i in B_IDX])
print("C:", [i + 1 for i in C_IDX])

A_DUR = [110, 110, 110, 110, 90, 90, 90, 90, 90]
B_DUR = [85] * 10
C_DUR = [90, 90, 90, 90, 110, 130]


def arch_dir(seg, variant):
    """每次运行用新编号子目录，避免同名跳过导致旧帧残留在素材目录"""
    base = os.path.join(ARCH, seg, variant or "_flat")
    n = 1
    while os.path.exists(os.path.join(base, "run_%03d" % n)):
        n += 1
    d = os.path.join(base, "run_%03d" % n)
    os.makedirs(d, exist_ok=True)
    return d


def place(seg, idxs, durs, variant):
    """variant: 'tb1' / 'tb2' / '' (平铺)"""
    outdir = os.path.join(DST_ROOT, seg, variant) if variant else os.path.join(DST_ROOT, seg)
    os.makedirs(outdir, exist_ok=True)
    # 归档旧帧（os.replace，不用 os.remove —— safe-delete shim 会崩）
    # 无条件全部移走，否则同名旧帧会残留造成新旧混存
    olds = glob.glob(os.path.join(outdir, "_*.png"))
    if olds:
        a = arch_dir(seg, variant)
        for old in olds:
            os.replace(old, os.path.join(a, os.path.basename(old)))
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
