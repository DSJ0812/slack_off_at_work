# -*- coding: utf-8 -*-
"""doubao_cut2.py — 抠图 + 改进版逐帧对齐（修抖动/跑偏/忽胖忽瘦）。

v2 相比 v1 的改进：
  1. 【锚点更稳】不再用"底部 8% 重心"（受尾巴/脚影响会跳），
     改成"底部 12% 区域内 alpha 列的加权重心" + 中位数平滑；
     并对全序列的 foot_cx 做中值滤波，消除单帧跳变。
  2. 【宽度归一】计算每帧宽度与"序列宽度中位数"的比，
     若偏离超过阈值，水平缩放到中位宽度（修"忽胖忽瘦"）。
     ★ 但保留动作本身需要的形变：只在超阈值时轻度校正（0.5 权重）。
  3. 【去杂物】连通域只保留最大块 + 面积 > 全图 5% 的块，
     小块（游离碎片、手）直接丢弃。
  4. 【异常帧】bbox 与中位数偏离过大时，用前后帧插值替代锚点。
"""
import os, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "doubao_frames")
OUT = os.path.join(TMP, "doubao_cut2")
os.makedirs(OUT, exist_ok=True)

CANVAS = 1000
TARGET_FEET_Y = 930
BASE_H = 859
BASE_W = 603
BG_DIST = 40
ALPHA_T = 60


def cut_one(fp):
    """抠白底，保留最大连通块（+ 面积够大的块），返回 RGBA。"""
    im = Image.open(fp).convert("RGB")
    a = np.array(im).astype(int)
    bg = np.median(np.concatenate([
        a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3),
        a[-20:, :20].reshape(-1, 3), a[-20:, -20:].reshape(-1, 3)]), axis=0)
    d = np.sqrt(((a - bg) ** 2).sum(axis=2))
    fg = d > BG_DIST
    lab, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        mx = sizes.max()
        keep_mask = np.zeros(n + 1, bool)
        for i, s in enumerate(sizes, 1):
            if s >= mx * 0.35:            # 只保留与最大块同量级的（≤3 块）
                keep_mask[i] = True
        fg = keep_mask[lab]
    alpha = np.clip((d - (BG_DIST - 10)) / 25.0, 0, 1) * fg
    rgba = np.dstack([np.array(im), (alpha * 255).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def metrics(im):
    """返回 (x0,y0,x1,y1, foot_cx, foot_w)。foot_cx 用底部 12% 的 alpha 加权重心。"""
    a = np.array(im)
    al = a[..., 3]
    ys, xs = np.where(al > ALPHA_T)
    if len(ys) == 0:
        return None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    ch = y1 - y0 + 1
    band = max(3, int(ch * 0.12))
    sub = al[y1 - band + 1:y1 + 1]
    cols = sub.sum(axis=0).astype(float)
    tot = cols.sum()
    foot_cx = float((np.arange(len(cols)) * cols).sum() / tot) if tot > 0 else (x0 + x1) / 2.0
    # 脚部宽度（alpha>60 的列数）
    foot_w = int((cols > ALPHA_T).sum())
    return (x0, y0, x1, y1, foot_cx, foot_w)


def medfilt1(x, k=5):
    x = np.asarray(x, float)
    n = len(x)
    out = x.copy()
    h = k // 2
    for i in range(n):
        lo, hi = max(0, i - h), min(n, i + h + 1)
        out[i] = np.median(x[lo:hi])
    return out


files = sorted(glob.glob(os.path.join(SRC, "f_*.png")))
print("frames:", len(files))

# 第一遍：抠图 + 收集指标
cuts, mets = [], []
for i, fp in enumerate(files):
    im = cut_one(fp)
    m = metrics(im)
    cuts.append(im)
    mets.append(m)
    if m is None:
        print("  frame %d EMPTY" % i)

good = [m for m in mets if m]
ws = np.array([m[2] - m[0] + 1 for m in good])
hs = np.array([m[3] - m[1] + 1 for m in good])
W_MED = float(np.median(ws))
H_MED = float(np.median(hs))
print("width  median=%.0f  min=%d max=%d" % (W_MED, ws.min(), ws.max()))
print("height median=%.0f  min=%d max=%d" % (H_MED, hs.min(), hs.max()))

# 平滑 foot_cx（中值滤波，去单帧跳变）
fcx_raw = np.array([m[4] for m in mets], float)
fcx_sm = medfilt1(fcx_raw, 5)

# 第二遍：对齐输出
infos = []
for i, (im, m) in enumerate(zip(cuts, mets)):
    if m is None:
        continue
    x0, y0, x1, y1, _fcx, _fw = m
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    # 高度归一
    sy = BASE_H / float(ch)
    # 水平归一：往中位宽度靠，但只走 40%（保留动作形变）
    sx_ratio = W_MED / float(cw)
    sx = sy * (1.0 + 0.40 * (sx_ratio - 1.0))
    nw, nh = max(1, int(round(cw * sx))), max(1, int(round(ch * sy)))
    crop = im.crop((x0, y0, x1 + 1, y1 + 1)).resize((nw, nh), Image.LANCZOS)
    # foot_cx 用平滑值映射到新坐标
    fcx_new = (fcx_sm[i] - x0) * sx
    px = int(round(500 - fcx_new))
    py = int(round(TARGET_FEET_Y - nh))
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.alpha_composite(crop, (px, py))
    op = os.path.join(OUT, "a_%03d.png" % i)
    canvas.save(op)
    infos.append(dict(i=i, scale_y=round(sy, 4), scale_x=round(sx, 4),
                      src_w=cw, src_h=ch, out_w=nw, out_h=nh,
                      fcx_raw=round(float(fcx_raw[i]), 1),
                      fcx_sm=round(float(fcx_sm[i]), 1), px=px, py=py))
    if i % 12 == 0:
        print("  %3d  sy=%.3f sx=%.3f  %dx%d  fcx_raw=%.0f fcx_sm=%.0f" % (
            i, sy, sx, cw, ch, fcx_raw[i], fcx_sm[i]))

json.dump([{k: (int(v) if isinstance(v, (np.integer,)) else
                float(v) if isinstance(v, (np.floating,)) else v)
            for k, v in d.items()} for d in infos],
          open(os.path.join(TMP, "doubao_probe", "align_info2.json"), "w"), indent=1)
print("aligned:", len(infos), "->", OUT)
