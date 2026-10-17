# -*- coding: utf-8 -*-
"""doubao_pack.py — 把豆包对齐帧按 A/B/C 三段铺进 VPet 素材目录。

切段（基于 doubao_seg.py 的相位分析）：
  A_Start : f06 ~ f13   （8 帧）站立 → 被拽 → 瞪眼
  B_Loop  : f22 ~ f34   （13 帧）挣扎循环（首尾差 0.94，几乎完美闭合）
  C_End   : f78 ~ f96   （19 帧）松手回正 → 站立

目标目录：mod/0000_core/pet/dino/Pinch/Nomal/{A,B,C}
★ 用 os.link 硬链接铺（省空间）；清理旧帧用 os.replace 归档（绝不 os.remove）
"""
import os, glob, shutil

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
CUT = os.path.join(TMP, "doubao_cut2")
VPET = r"D:/softapp/VPet_dino/VPet"
DST = os.path.join(VPET, "mod", "0000_core", "pet", "dino", "Pinch", "Nomal")
STALE = os.path.join(TMP, "stale_doubao")

SEGS = [
    ("A", list(range(6, 14)), 90),      # 8 帧 @90ms
    ("B", list(range(22, 35)), 110),    # 13 帧 @110ms
    ("C", list(range(78, 97)), 90),     # 19 帧 @90ms
]

# Pinch 的三种心情状态都要铺（否则切到 Happy/PoorCondition 时还是旧代码版）
STATES = ["Nomal", "Happy", "PoorCondition"]

# 额外目录：原版存在但状态名不是"心情段"的（Happy/B_2），也铺 B 段
EXTRA = [("Happy/B_2", range(22, 35), 110)]

os.makedirs(STALE, exist_ok=True)
print("目标根:", os.path.dirname(DST))

total_links = 0
total_stale = 0
for st in STATES:
    for seg, idxs, dur in SEGS:
        d = os.path.join(os.path.dirname(DST), st, seg)
        os.makedirs(d, exist_ok=True)
        want = set()
        for k, i in enumerate(idxs):
            src = os.path.join(CUT, "a_%03d.png" % i)
            assert os.path.exists(src), src
            name = "_%03d_%d.png" % (k, dur)
            dst = os.path.join(d, name)
            want.add(name)
            if os.path.exists(dst):
                os.replace(dst, os.path.join(STALE, "%s_%s_%s_old" % (st, seg, name)))
            os.link(src, dst)
            total_links += 1
        for f in os.listdir(d):
            if f.lower().endswith(".png") and f not in want:
                os.replace(os.path.join(d, f), os.path.join(STALE, "%s_%s_%s" % (st, seg, f)))
                total_stale += 1

# 额外目录
for rel, idxs, dur in EXTRA:
    d = os.path.join(os.path.dirname(DST), rel)
    if not os.path.isdir(d):
        print("  跳过不存在目录:", rel)
        continue
    want = set()
    for k, i in enumerate(idxs):
        src = os.path.join(CUT, "a_%03d.png" % i)
        name = "_%03d_%d.png" % (k, dur)
        dst = os.path.join(d, name)
        want.add(name)
        if os.path.exists(dst):
            os.replace(dst, os.path.join(STALE, "x_%s_%s_old" % (rel.replace("/", "_"), name)))
        os.link(src, dst)
        total_links += 1
    for f in os.listdir(d):
        if f.lower().endswith(".png") and f not in want:
            os.replace(os.path.join(d, f), os.path.join(STALE, "x_%s_%s" % (rel.replace("/", "_"), f)))
            total_stale += 1
    print("  额外 %s: %d 帧" % (rel, len(idxs)))

print("链接 %d 个, 归档旧帧 %d 个" % (total_links, total_stale))

for st in STATES:
    for seg, idxs, dur in SEGS:
        d = os.path.join(os.path.dirname(DST), st, seg)
        fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
        print("  %-14s %s: %d 文件" % (st, seg, len(fs)))
