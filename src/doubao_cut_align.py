# -*- coding: utf-8 -*-
"""doubao_cut_align.py — 抠白底 + 逐帧对齐，输出测试 GIF。

策略：
  1. 抠图：背景近纯白 (252,251,252)，用"到背景色的距离"做阈值；
     再用连通域保住角色（最大连通块），吃掉孤立噪点。
  2. 对齐：每帧算角色 bbox → 统一缩放到目标高度 → 使【脚底中心】落在素材 (500,930)。
     ★ 这一步是抗抖动的关键：把每帧的角色都摆到同一个"站位"。
  3. 输出：1000x1000 透明 PNG 序列 + 合成 GIF（带棋盘底以便看透明区）。
"""
import os, glob
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "doubao_frames")
OUT = os.path.join(TMP, "doubao_cut")
os.makedirs(OUT, exist_ok=True)

# 素材规格（对齐目标）
CANVAS = 1000
TARGET_FEET_Y = 930          # 脚底 y（与 dino_base.png 一致）
BASE_H = 859                 # dino_base 的角色高度（用于等比缩放参考）
BASE_W = 603
BG_DIST = 40                 # 背景距离阈值


def cut_one(fp):
    im = Image.open(fp).convert("RGB")
    a = np.array(im).astype(int)
    h, w = a.shape[:2]
    # 背景色：四角中位
    bg = np.median(np.concatenate([
        a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3),
        a[-20:, :20].reshape(-1, 3), a[-20:, -20:].reshape(-1, 3)]), axis=0)
    d = np.sqrt(((a - bg) ** 2).sum(axis=2))
    fg = d > BG_DIST
    # 连通域：保留最大块（角色），其余视为噪点
    lab, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        keep = np.argmax(sizes) + 1
        fg = (lab == keep)
    # alpha：用距离做软边（阈值~阈值+25 之间渐变）
    alpha = np.clip((d - (BG_DIST - 10)) / 25.0, 0, 1)
    alpha = alpha * fg
    rgba = np.dstack([np.array(im), (alpha * 255).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def aligned(fp):
    """抠图 + 对齐到统一站位，返回 1000x1000 RGBA。"""
    im = cut_one(fp)
    a = np.array(im)
    al = a[..., 3]
    ys, xs = np.where(al > 60)
    if len(ys) == 0:
        return None, None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    # 脚底中心：底部 8% 区域的重心 x
    cut_y = y1 - max(2, int(ch * 0.08))
    foot = al[cut_y:y1 + 1]
    fys, fxs = np.where(foot > 60)
    foot_cx = (fxs.mean() + x0) if len(fxs) else (x0 + x1) / 2.0

    # 缩放到 BASE_H
    scale = BASE_H / float(ch)
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    crop = im.crop((x0, y0, x1 + 1, y1 + 1)).resize((nw, nh), Image.LANCZOS)

    # 放置：脚底 (foot_cx 缩放后) → (500, 930)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    fcx_s = (foot_cx - x0) * scale
    px = int(round(500 - fcx_s))
    py = int(round(TARGET_FEET_Y - nh))
    canvas.alpha_composite(crop, (px, py))
    info = dict(scale=scale, cw=cw, ch=ch, foot_cx=foot_cx, px=px, py=py)
    return canvas, info


files = sorted(glob.glob(os.path.join(SRC, "f_*.png")))
print("frames:", len(files))
out_files = []
for i, fp in enumerate(files):
    img, info = aligned(fp)
    if img is None:
        print("  frame %d empty, skip" % i)
        continue
    op = os.path.join(OUT, "a_%03d.png" % i)
    img.save(op)
    out_files.append(op)
    if i % 12 == 0:
        print("  %3d  scale=%.3f  src=%dx%d  foot_cx=%.0f" % (i, info["scale"], info["cw"], info["ch"], info["foot_cx"]))

print("aligned:", len(out_files))

# 合成 GIF（棋盘底 + 偶尔红线标脚底）
def checker(size, sq=25):
    c = Image.new("RGB", (size, size), (255, 255, 255))
    d = ImageDraw.Draw(c)
    for yy in range(0, size, sq):
        for xx in range(0, size, sq):
            if (xx // sq + yy // sq) % 2:
                d.rectangle([xx, yy, xx + sq - 1, yy + sq - 1], fill=(232, 232, 236))
    return c


gif_frames = []
for i, op in enumerate(out_files):
    im = Image.open(op).convert("RGBA")
    bgc = checker(CANVAS)
    bgc.alpha_composite if False else None
    bgc.paste(im, (0, 0), im)
    d = ImageDraw.Draw(bgc)
    d.line([(0, TARGET_FEET_Y), (CANVAS, TARGET_FEET_Y)], fill=(255, 80, 80), width=3)
    gif_frames.append(bgc.resize((400, 400), Image.LANCZOS))

gp = os.path.join(TMP, "doubao_probe", "align_test.gif")
gif_frames[0].save(gp, save_all=True, append_images=gif_frames[1:],
                   duration=42, loop=0, optimize=True)
print("GIF ->", gp)

# 同时拼一张关键帧对照图
ROWS = 8
sel = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]
tile = Image.new("RGB", (300 * len(sel), 300), (255, 255, 255))
dd = ImageDraw.Draw(tile)
for c, idx in enumerate(sel):
    if idx >= len(out_files):
        continue
    im = Image.open(out_files[idx]).convert("RGBA")
    bgc = checker(CANVAS)
    bgc.paste(im, (0, 0), im)
    dd.line([(0, TARGET_FEET_Y), (CANVAS, TARGET_FEET_Y)], fill=(255, 80, 80), width=3)
    tile.paste(bgc.resize((300, 300), Image.LANCZOS), (c * 300, 0))
    dd.text((c * 300 + 6, 6), str(idx), fill=(200, 40, 40))
tp = os.path.join(TMP, "doubao_probe", "align_row.png")
tile.save(tp)
print("ROW ->", tp)
