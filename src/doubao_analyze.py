# -*- coding: utf-8 -*-
"""doubao_analyze.py — 分析豆包视频帧的抠图难度 + 逐帧 bbox（对齐用）。

输出：
  1. 每帧背景色采样（确认是否纯白）
  2. 每帧角色 bbox（看位置漂移有多大 —— 决定要不要逐帧对齐）
  3. 抠图难度评估
"""
import os, glob
import numpy as np
from PIL import Image

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
FR = os.path.join(TMP, "doubao_frames")

files = sorted(glob.glob(os.path.join(FR, "f_*.png")))
print("frames:", len(files))

# 背景色采样：取四角
print("\n=== 背景色采样（四角 20x20 中位色）===")
for fp in files[:5] + files[len(files)//2:len(files)//2+3] + files[-3:]:
    im = Image.open(fp).convert("RGB")
    a = np.array(im)
    corners = np.concatenate([
        a[:20, :20].reshape(-1, 3),
        a[:20, -20:].reshape(-1, 3),
        a[-20:, :20].reshape(-1, 3),
        a[-20:, -20:].reshape(-1, 3),
    ])
    med = np.median(corners, axis=0).astype(int)
    print("  %s  corner_median=%s" % (os.path.basename(fp), tuple(med)))

# 逐帧 bbox：用"非背景"判定（与角点色的距离 > 阈值）
print("\n=== 逐帧角色 bbox（背景距阈 40）===")
boxes = []
for fp in files:
    im = Image.open(fp).convert("RGB")
    a = np.array(im).astype(int)
    bg = np.median(np.concatenate([
        a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3),
        a[-20:, :20].reshape(-1, 3), a[-20:, -20:].reshape(-1, 3)]), axis=0)
    d = np.sqrt(((a - bg) ** 2).sum(axis=2))
    mask = d > 40
    ys, xs = np.where(mask)
    if len(ys) == 0:
        boxes.append(None)
        continue
    boxes.append((xs.min(), ys.min(), xs.max(), ys.max(), mask.sum()))

print("  idx   x0   y0   x1   y1    w    h   area")
for i, b in enumerate(boxes):
    if i % 8 == 0 or i in (96,):
        if b:
            print("  %3d  %4d %4d %4d %4d  %4d %4d  %6d" % (i, b[0], b[1], b[2], b[3],
                  b[2]-b[0], b[3]-b[1], b[4]))

if all(b for b in boxes):
    x0 = [b[0] for b in boxes]; y0 = [b[1] for b in boxes]
    x1 = [b[2] for b in boxes]; y1 = [b[3] for b in boxes]
    print("\n=== 漂移范围 ===")
    print("  x0: %d ~ %d (span %d)" % (min(x0), max(x0), max(x0)-min(x0)))
    print("  y0: %d ~ %d (span %d)" % (min(y0), max(y0), max(y0)-min(y0)))
    print("  x1: %d ~ %d (span %d)" % (min(x1), max(x1), max(x1)-min(x1)))
    print("  y1: %d ~ %d (span %d)" % (min(y1), max(y1), max(y1)-min(y1)))
    print("  高度: %d ~ %d" % (min(b[3]-b[1] for b in boxes), max(b[3]-b[1] for b in boxes)))
