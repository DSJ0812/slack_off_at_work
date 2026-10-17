# -*- coding: utf-8 -*-
import os, glob
import numpy as np
from PIL import Image
FR = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/dino_anim3/frames"
LB, RB = (438, 0, 1000, 1000), (0, 0, 562, 1000)

def motion(clip, box, label):
    fs = sorted(glob.glob(os.path.join(FR, clip, "*.png")))
    arrs = [np.array(Image.open(f).convert("RGBA").crop(box)).astype(int) for f in fs]
    tot = np.zeros(arrs[0].shape[:2])
    for i in range(len(arrs) - 1):
        tot += np.abs(arrs[i + 1] - arrs[i]).sum(axis=2)
    ys = tot.sum(axis=1); xs = tot.sum(axis=0)
    H = len(ys); W = len(xs)
    yc = (ys * np.arange(H)).sum() / ys.sum()
    xc = (xs * np.arange(W)).sum() / xs.sum()
    half = H // 2
    print("%s  (%dx%d)" % (label, W, H))
    print("   运动重心: y=%.0f/%d (%.0f%%)  x=%.0f/%d" % (yc, H, 100 * yc / H, xc, W))
    print("   上半部运动量=%.0f  下半部=%.0f  → 比值 %.2f" % (ys[:half].sum(), ys[half:].sum(),
          ys[:half].sum() / max(1, ys[half:].sum())))

motion("HideLRB", LB, "贴左探头")
motion("HideRRB", RB, "贴右探头")
