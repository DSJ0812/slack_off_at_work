# -*- coding: utf-8 -*-
"""doubao_seg.py — 分析豆包对齐帧，找出最佳切段点与循环点。

1. 逐帧算"与首帧(f0)的像素差" → 看出动作相位
2. 在可能的中段里，找首尾最接近的一对帧作为 B_Loop 的循环区间
3. 输出切段建议
"""
import os, glob
import numpy as np
from PIL import Image

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
CUT = os.path.join(TMP, "doubao_cut2")

fs = sorted(glob.glob(os.path.join(CUT, "a_*.png")))
N = len(fs)
print("frames:", N)


def arr(fp, sz=200):
    im = Image.open(fp).convert("RGBA").resize((sz, sz), Image.LANCZOS)
    return np.array(im).astype(float)


A = [arr(f) for f in fs]

# 与首帧差
d0 = [float(np.abs(A[i] - A[0]).mean()) for i in range(N)]
print("\n=== 与首帧 f0 的差异（每 3 帧）===")
for i in range(0, N, 3):
    bar = "#" * int(d0[i] / 2)
    print("  f%03d %6.1f %s" % (i, d0[i], bar))

# 在 [20, N-20] 里找 循环区间：固定长度 L 的窗口，首尾差最小
print("\n=== 候选循环窗口（长度 10~16，首尾差异最小）===")
best = []
for L in (10, 12, 14, 16):
    cands = []
    for s in range(20, N - 20 - L):
        e = s + L
        diff = float(np.abs(A[e] - A[s]).mean())
        cands.append((diff, s, e))
    cands.sort()
    b = cands[0]
    best.append((L, b))
    print("  L=%2d  最佳区间 f%03d~f%03d  首尾差=%.2f" % (L, b[1], b[2], b[0]))

# 与末帧相似度（找 A 段终点：动作开始）
print("\n=== 与末帧 f%d 相似度 ===" % (N - 1))
dN = [float(np.abs(A[i] - A[N - 1]).mean()) for i in range(N)]
for i in range(0, N, 6):
    print("  f%03d %6.1f" % (i, dN[i]))
