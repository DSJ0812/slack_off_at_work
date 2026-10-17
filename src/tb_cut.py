# -*- coding: utf-8 -*-
"""tb_cut.py — 抠绿底 + 逐帧对齐 + 归一化，输出到 tb_cut/

相比 doubao_cut2.py：
  · 背景色从「四角中位数」自动估计（豆包实际给的是柔和草绿 (137,180,116)，
    不是纯 #00FF00，所以不能硬编码）
  · 猴子身上的红色/米黄/橙色与背景差异极大，抠图零风险
  · 对齐：高度归一 + 底部重心水平居中（转身段用整体 bbox 中心兜底）
"""
import os, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "tb_frames")
OUT = os.path.join(TMP, "tb_cut")
os.makedirs(OUT, exist_ok=True)

CANVAS = 1000
TARGET_FEET_Y = 930
BASE_H = 859                    # 与现有素材一致的角色高度
BG_DIST = 55                    # 背景判定阈值（绿 vs 红差异远大于此）
FG_SOFT = 90                    # 羽化过渡上限


def bg_color(im):
    a = np.array(im).astype(float)
    corners = np.concatenate([
        a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3),
        a[-20:, :20].reshape(-1, 3), a[-20:, -20:].reshape(-1, 3)])
    return np.median(corners, axis=0)


def cut_one(fp):
    im = Image.open(fp).convert("RGB")
    bg = bg_color(im)
    a = np.array(im).astype(float)
    d = np.sqrt(((a - bg) ** 2).sum(axis=2))

    # ★★ 关键改进：AI 会生成「深绿接触阴影」（如 (94,124,76)），
    #    它与背景绿的欧氏距离达 81 > 阈值，会被误判成前景留在脚底。
    #    但它的 R/G、B/G 通道比与背景几乎一致（0.76/0.61 vs 0.76/0.64），
    #    而恐龙本体红/橙完全不符合（G 不是最大通道）。
    #    → 用「色相比值」额外剔除一切绿系像素，零误伤。
    bg_r, bg_g, bg_b = float(bg[0]), float(bg[1]), float(bg[2])
    k_r = bg_r / max(bg_g, 1.0)
    k_b = bg_b / max(bg_g, 1.0)
    r, g, bch = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    gmax = (g >= r) & (g >= bch) & (g > 40)
    rg = r / np.maximum(g, 1.0)
    bgk = bch / np.maximum(g, 1.0)
    greenlike = gmax & (np.abs(rg - k_r) < 0.14) & (np.abs(bgk - k_b) < 0.14)

    fg = (d > BG_DIST) & (~greenlike)
    lab, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        mx = sizes.max()
        keep = np.zeros(n + 1, bool)
        for i, s in enumerate(sizes, 1):
            if s >= mx * 0.30:
                keep[i] = True
        fg = keep[lab]
    alpha = np.clip((d - (BG_DIST - 15)) / float(FG_SOFT - BG_DIST + 15), 0, 1) * fg
    rgba = np.dstack([np.array(im), (alpha * 255).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def metrics(im):
    al = np.array(im)[..., 3]
    ys, xs = np.where(al > 60)
    if len(ys) == 0:
        return None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    # 水平重心（按 alpha 加权，比 bbox 中心稳）
    w = al[al > 60].astype(float)
    cx = float((xs * w).sum() / w.sum())
    return (x0, y0, x1, y1, cx)


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

cuts, mets = [], []
for i, fp in enumerate(files):
    im = cut_one(fp)
    m = metrics(im)
    cuts.append(im)
    mets.append(m)
    if m is None:
        print("  EMPTY frame", i)

good = [m for m in mets if m]
hs = np.array([m[3] - m[1] + 1 for m in good])
ws = np.array([m[2] - m[0] + 1 for m in good])
H_MED = float(np.median(hs))
W_MED = float(np.median(ws))
print("height median=%.0f (%d~%d)  width median=%.0f (%d~%d)"
      % (H_MED, hs.min(), hs.max(), W_MED, ws.min(), ws.max()))

# ★ 水平重心做中值滤波，消掉转身段单帧跳变（f65、f101）
cx_raw = np.array([m[4] for m in mets], float)
cx_sm = medfilt1(cx_raw, 5)

infos = []
for i, (im, m) in enumerate(zip(cuts, mets)):
    if m is None:
        continue
    x0, y0, x1, y1, _cx = m
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    s = BASE_H / float(ch)
    # ★ 宽度轻度归一：往中位宽度靠 45%（压转身段"忽胖忽瘦"，保留动作形变）
    sx_ratio = W_MED / float(cw)
    s_x = s * (1.0 + 0.45 * (sx_ratio - 1.0))
    nw, nh = max(1, int(round(cw * s_x))), max(1, int(round(ch * s)))
    crop = im.crop((x0, y0, x1 + 1, y1 + 1)).resize((nw, nh), Image.LANCZOS)
    # 用平滑后的重心做水平锚定
    cx_new = (cx_sm[i] - x0) * s_x
    px = int(round(500 - cx_new))
    py = int(round(TARGET_FEET_Y - nh))
    px = max(0, min(CANVAS - nw, px))        # 防出框
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.alpha_composite(crop, (px, py))
    canvas.save(os.path.join(OUT, "t_%03d.png" % i))
    infos.append(dict(i=int(i), s=round(float(s), 4), src_w=int(cw), src_h=int(ch),
                      out_w=int(nw), out_h=int(nh), px=int(px), py=int(py),
                      cx_raw=round(float(cx_raw[i]), 1), cx_sm=round(float(cx_sm[i]), 1)))
    if i % 20 == 0:
        print("  %3d  s=%.3f sx=%.3f %dx%d -> %dx%d px=%d" % (i, s, s_x, cw, ch, nw, nh, px))

json.dump(infos, open(os.path.join(TMP, "tb_info.json"), "w"), indent=1)
print("aligned:", len(infos), "->", OUT)
