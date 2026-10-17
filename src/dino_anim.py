# -*- coding: utf-8 -*-
"""dino_anim.py — 拆层 + 生成 VPet 动画
v2 增补：睡觉加被子/Z字；摸头加按压回弹+扭动+爱心；待机加歪头+重心移动
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "dino_base.png")
OUT = os.path.join(TMP, "dino_anim3")
os.makedirs(OUT, exist_ok=True)

BASE, SS = 1000, 2
W = H = BASE * SS
ANCHOR = (1000, 1860)          # 脚底中心（2000 坐标系）
EDGE = (65, 22, 16)
BG = (234, 242, 251)

BLANKET      = (162, 206, 240)
BLANKET_EDGE = (74, 112, 148)
BLANKET_TOP  = (212, 235, 252)
HEART_COL    = (255, 112, 134)
ZZZ_COL      = (146, 182, 218)
STAR_COL     = (255, 206, 66)
STAR_EDGE    = (214, 148, 18)
TEAR_COL     = (126, 200, 240)     # 泪珠主体（浅蓝）
TEAR_EDGE    = ( 58, 118, 162)     # 泪珠描边（深蓝）
TEAR_HI      = (235, 248, 255)     # 泪珠高光

src = Image.open(SRC).convert("RGBA")
arr = np.array(src)

# ---------------- 1. 拆层 ----------------
WIN = {
    "eyeL":  (315, 346, 362, 392),
    "eyeR":  (521, 342, 568, 389),
    "mouth": (400, 388, 483, 424),
}
PAD = 4


def ring_color(x0, y0, x1, y1, r=6):
    pts = []
    for x in range(max(0, x0 - r), min(BASE, x1 + 1 + r)):
        for y in (y0 - r - 1, y0 - r, y1 + r, y1 + r + 1):
            if 0 <= y < BASE:
                pts.append(arr[y, x, :3])
    for y in range(max(0, y0 - r), min(BASE, y1 + 1 + r)):
        for x in (x0 - r - 1, x0 - r, x1 + r, x1 + r + 1):
            if 0 <= x < BASE:
                pts.append(arr[y, x, :3])
    return tuple(int(v) for v in np.median(np.array(pts), axis=0))


board = src.copy()
d0 = ImageDraw.Draw(board)
layers = {}
for k, (x0, y0, x1, y1) in WIN.items():
    layers[k] = src.crop((x0 - PAD, y0 - PAD, x1 + 1 + PAD, y1 + 1 + PAD))
    col = ring_color(x0, y0, x1, y1)
    d0.rectangle([x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD], fill=col + (255,))
    print("cut %-6s backfill=%-16s layer=%s" % (k, col, layers[k].size))

board2 = board.resize((W, H), Image.LANCZOS)
L2 = {k: v.resize((v.width * SS, v.height * SS), Image.LANCZOS) for k, v in layers.items()}

EYE2 = [("eyeL", 678, 738), ("eyeR", 1089, 731)]
MOUTH_C = (883, 812)
CHEEK2 = [(560, 862), (1190, 852)]


# ---------------- 2. 小图形 ----------------
def draw_z(dr, cx, cy, s, col):
    w, h = 50 * s, 66 * s
    lw = max(3, int(12 * s))
    p = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
         (cx - w / 2, cy + h / 2), (cx + w / 2, cy + h / 2)]
    dr.line([p[0], p[1]], fill=col, width=lw)
    dr.line([p[1], p[2]], fill=col, width=lw)
    dr.line([p[2], p[3]], fill=col, width=lw)
    for px, py in p:
        dr.ellipse([px - lw / 2, py - lw / 2, px + lw / 2, py + lw / 2], fill=col)


def draw_heart(dr, cx, cy, s, col):
    r = 38 * s
    dr.ellipse([cx - r, cy - r * 0.92, cx, cy + r * 0.42], fill=col)
    dr.ellipse([cx, cy - r * 0.92, cx + r, cy + r * 0.42], fill=col)
    dr.polygon([(cx - r * 0.96, cy - r * 0.10),
                (cx + r * 0.96, cy - r * 0.10),
                (cx, cy + r * 1.12)], fill=col)


def draw_star(dr, cx, cy, s, col):
    """五角星，s=1 时外接圆半径 58（2000 坐标系）"""
    R = 58 * s
    r = R * 0.45
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rad = R if k % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    dr.polygon(pts, fill=col)


def draw_droplet(dr, cx, cy, s, alpha=1.0):
    """水滴形泪珠：上尖下圆。s=1 时高约 78（2000 坐标系）。alpha 0~1"""
    a = int(255 * max(0.0, min(1.0, alpha)))
    if a <= 4:
        return
    h, w = 100 * s, 64 * s
    tip_y, body_y, r = cy - h * 0.64, cy + h * 0.12, w * 0.5
    for e, col in ((5 * s, TEAR_EDGE + (a,)), (0.0, TEAR_COL + (a,))):
        dr.polygon([(cx, tip_y - e), (cx - r - e, body_y),
                    (cx + r + e, body_y)], fill=col)
        dr.ellipse([cx - r - e, body_y - r - e, cx + r + e, body_y + r + e], fill=col)
    hr = r * 0.34                                   # 左上高光
    dr.ellipse([cx - r * 0.45 - hr, body_y - r * 0.38 - hr,
                cx - r * 0.45 + hr, body_y - r * 0.38 + hr],
               fill=TEAR_HI + (int(a * 0.85),))


# ---------------- 3. 姿态合成 ----------------
def pose(eye_open=1.0, eye_zoom=1.0, closed=False, blush=0.0, mouth_open=0.0,
         hearts=None, star_eyes=0.0, tears=None):
    hearts = hearts or ()
    tears = tears or ()
    img = board2.copy()

    # 眼睛：eye_open 低于阈值时改用闭眼弧线（便于在关键帧里平滑过渡到闭眼）
    if (not closed) and eye_open > 0.15:
        for k, cx, cy in EYE2:
            lay = L2[k]
            lw, lh = lay.size
            nw = max(1, int(round(lw * eye_zoom)))
            nh = max(1, int(round(lh * eye_zoom * eye_open)))
            l2 = lay if (nw == lw and nh == lh) else lay.resize((nw, nh), Image.LANCZOS)
            img.alpha_composite(l2, (cx - nw // 2, cy - nh // 2))
    else:
        dd = ImageDraw.Draw(img)
        for _, cx, cy in EYE2:
            dd.arc([cx - 56, cy - 56, cx + 56, cy + 56], 25, 155,
                   fill=EDGE + (255,), width=18)

    # 星星眼：盖在眼睛之上
    if star_eyes > 0.02 and eye_open > 0.15:
        ds = ImageDraw.Draw(img)
        for _, cx, cy in EYE2:
            s = 0.92 * star_eyes * eye_zoom
            draw_star(ds, cx, cy, s * 1.18, STAR_EDGE + (int(230 * min(1.0, star_eyes)),))
            draw_star(ds, cx, cy, s, STAR_COL + (int(255 * min(1.0, star_eyes * 1.5)),))

    # 嘴巴
    if mouth_open > 0.03:
        dd = ImageDraw.Draw(img)
        rw = int(70 + 52 * mouth_open)
        rh = int(24 + 72 * mouth_open)
        dd.ellipse([MOUTH_C[0] - rw, MOUTH_C[1] - rh, MOUTH_C[0] + rw, MOUTH_C[1] + rh],
                   fill=EDGE + (255,))
        if mouth_open > 0.45:
            dd.ellipse([MOUTH_C[0] - 32, MOUTH_C[1] + rh - 42,
                        MOUTH_C[0] + 32, MOUTH_C[1] + rh - 6], fill=(238, 118, 128, 255))
    else:
        lay = L2["mouth"]
        lw, lh = lay.size
        img.alpha_composite(lay, (MOUTH_C[0] - lw // 2, MOUTH_C[1] - lh // 2))

    # 腮红
    if blush > 0.01:
        bl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        db = ImageDraw.Draw(bl)
        for cx, cy in CHEEK2:
            db.ellipse([cx - 84, cy - 54, cx + 84, cy + 54],
                       fill=(255, 128, 130, int(130 * blush)))
        m = ImageChops.multiply(bl.split()[3], board2.split()[3])
        bl.putalpha(m)
        img.alpha_composite(bl)

    # 漂浮爱心
    if hearts:
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        df = ImageDraw.Draw(fl)
        for cx, cy, s, a in hearts:
            draw_heart(df, cx, cy, s, HEART_COL + (int(255 * max(0.0, min(1.0, a))),))
        img.alpha_composite(fl)

    # 泪珠（画在最上层，会跟着 affine 一起缩放/位移）
    if tears:
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dt = ImageDraw.Draw(tl)
        for cx, cy, s, a in tears:
            draw_droplet(dt, cx, cy, s, a)
        img.alpha_composite(tl)
    return img


def affine(layer, sx=1.0, sy=1.0, rot=0.0, dx=0.0, dy=0.0):
    th = math.radians(rot)
    cs, sn = math.cos(th), math.sin(th)
    a = cs / sx;  b = sn / sx
    d = -sn / sy; e = cs / sy
    px = ANCHOR[0] + dx; py = ANCHOR[1] + dy
    c = ANCHOR[0] - (a * px + b * py)
    f = ANCHOR[1] - (d * px + e * py)
    return layer.transform((W, H), Image.AFFINE, (a, b, c, d, e, f),
                           resample=Image.BICUBIC)


def draw_blanket_1000(img, amt, lift=0.0):
    """躺姿坐标系（1000）下绘制被子：从右侧滑入，波浪边缘 + 被沿 + 褶皱"""
    if amt <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    sh = (1.0 - amt) * 300
    x0, x1 = 492 + sh, 990 + sh
    y0, y1 = 272 - lift, 788

    def wave(xa, xb, yb, amp=15):
        return [(x, yb + amp * math.sin((x - xa) / 62.0))
                for x in range(int(xa), int(xb) + 1, 8)]

    o = 12
    d.polygon(wave(x0 - o, x1 + o, y0 - o) + [(x1 + o, y1 + o), (x0 - o, y1 + o)],
              fill=BLANKET_EDGE + (255,))
    d.polygon(wave(x0, x1, y0) + [(x1, y1), (x0, y1)], fill=BLANKET + (255,))
    d.rectangle([x0, y0 + 46, x0 + 60, y1 - 18], fill=BLANKET_TOP + (255,))
    for fx in (x0 + 250, x0 + 400):
        d.line([(fx, y0 + 62), (fx, y1 - 46)], fill=(188, 221, 246, 210), width=9)
    img.alpha_composite(lay)


def draw_zzz_1000(img, items):
    if not items:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for cx, cy, s, a in items:
        draw_z(d, cx, cy, s, ZZZ_COL + (int(255 * max(0.0, min(1.0, a))),))
    img.alpha_composite(lay)


def draw_drool_1000(img, amt, drop=0.0):
    """躺姿坐标系下从嘴角流下的口水。amt=口水长度 0~1；drop=水滴下落进度 0~1"""
    if amt <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = 407, 566                     # 躺姿下嘴角位置（站立 (441,407) 逆时针 90° 而来）
    L = 26 + 88 * amt
    w = int(16 + 9 * amt)
    col = (232, 248, 255, 230)            # 亮白蓝，与被子(162,206,240)拉开差别
    edge = (150, 195, 225, 150)           # 描边，保证在红色身体上看得清
    pts = [(cx, cy), (cx + 5 * amt, cy + L)]
    r = w / 2.0
    d.line(pts, fill=edge, width=w + 6)
    for px, py in pts:
        d.ellipse([px - r - 3, py - r - 3, px + r + 3, py + r + 3], fill=edge)
    d.line(pts, fill=col, width=w)
    for px, py in pts:
        d.ellipse([px - r, py - r, px + r, py + r], fill=col)
    if drop > 0.01:                       # 末端挂的水滴，随时间下落
        dyy = cy + L + drop * 110
        rr = 13
        d.ellipse([cx + 5 * amt - rr - 3, dyy - rr * 1.25 - 3,
                   cx + 5 * amt + rr + 3, dyy + rr * 1.25 + 3], fill=edge)
        d.ellipse([cx + 5 * amt - rr, dyy - rr * 1.25,
                   cx + 5 * amt + rr, dyy + rr * 1.25], fill=col)
    img.alpha_composite(lay)


def frame(sx=1.0, sy=1.0, rot=0.0, dx=0.0, dy=0.0, alpha=1.0, flip=False,
          post_rot=0.0, post_dx=0.0, post_dy=0.0, post_blanket=0.0,
          post_zzz=None, post_lift=0.0, post_drool=None, **kw):
    t = affine(pose(**kw), sx, sy, rot, dx, dy)
    if alpha < 0.999:
        t.putalpha(t.split()[3].point(lambda v: int(v * alpha)))
    if post_rot:
        t = t.rotate(post_rot, center=(W / 2, H / 2), resample=Image.BICUBIC)
    if post_dx or post_dy:                      # 旋转之后再平移（绕画面中心转完才好定位）
        t = t.transform((W, H), Image.AFFINE,
                        (1, 0, -post_dx, 0, 1, -post_dy), resample=Image.BICUBIC)
    out = t.resize((BASE, BASE), Image.LANCZOS)
    if post_blanket > 0.01:
        draw_blanket_1000(out, post_blanket, post_lift)
    if post_drool:
        draw_drool_1000(out, post_drool[0], post_drool[1])
    if post_zzz:
        draw_zzz_1000(out, post_zzz)
    if flip:
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    return out


def ease_out_back(t, s=1.9):
    t -= 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def kf(keys, t):
    """关键帧插值（smoothstep）"""
    if t <= keys[0][0]:
        return list(keys[0][1:])
    if t >= keys[-1][0]:
        return list(keys[-1][1:])
    for i in range(len(keys) - 1):
        if keys[i][0] <= t <= keys[i + 1][0]:
            t0, t1 = keys[i][0], keys[i + 1][0]
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return [a + (b - a) * u for a, b in zip(keys[i][1:], keys[i + 1][1:])]
    return list(keys[-1][1:])


CLIPS = {}
FRAMES = {}
def rec(name, img, dur):
    lst = CLIPS.setdefault(name, [])
    idx = len(lst)
    lst.append((img, dur))
    fd = os.path.join(OUT, "frames", name)
    os.makedirs(fd, exist_ok=True)
    fp = os.path.join(fd, "%s_%03d_%d.png" % (name.lower(), idx, dur))
    img.save(fp)          # 同名覆盖保持 inode → 素材目录里的硬链接会自动同步新内容
    FRAMES.setdefault(name, []).append(fp)


def rec2(name, name_flip, img, dur):
    """同时生成原图与水平镜像版（SideHide 左右两侧共用一套设计）"""
    rec(name, img, dur)
    rec(name_flip, img.transpose(Image.FLIP_LEFT_RIGHT), dur)


# ---------------- 4. 动画 ----------------
# 4.1 StartUP 启动
N = 12
for i in range(N):
    t = i / (N - 1)
    s = 0.45 + 0.55 * ease_out_back(t)
    rec("StartUP", frame(sx=s, sy=s, alpha=min(1.0, t * 2.6)), 80)

# 4.2 IDEL 待机：呼吸 + 眨眼 + 歪头 + 打哈欠（拉长到 72 帧，把打哈欠降到约 9 秒一次）
N = 72
for i in range(N):
    t = i / N
    br = math.sin(t * 2 * math.pi * 4)      # 四个呼吸周期（约 2.3 秒一次）
    sy = 1 + 0.022 * br
    sx = 1 - 0.011 * br
    tilt = 0.0
    if 12 <= i <= 26:                       # 歪头：小幅倾斜，中段保持（无平移）
        u = (i - 12) / 14.0
        tilt = -4.0 * math.sin(math.pi * u) ** 0.55
    eo, d, mo = 1.0, 125, 0.0
    for b in (6, 30, 64):                   # 三次快眨眼
        if i == b:
            eo, d = 0.40, 70
        elif i == b + 1:
            eo, d = 0.07, 55
        elif i == b + 2:
            eo, d = 0.42, 70
    if 44 <= i <= 58:                       # 打哈欠：张嘴 + 眯眼（不全闭）
        u = (i - 44) / 14.0
        o = math.sin(math.pi * (u ** 0.8))
        mo = o
        eo = 1 - 0.82 * o
        d = 150
    rec("IDEL", frame(sx=sx, sy=sy, rot=tilt,
                      eye_open=eo, mouth_open=mo), d)

# 4.3 MOVE 走路
N = 8
for side, flip in (("right", False), ("left", True)):
    for i in range(N):
        t = i / N
        w = math.sin(t * 2 * math.pi)
        st = 1 + 0.035 * w
        rec("MOVE_" + side,
            frame(sx=1 / math.sqrt(st), sy=st, rot=3.2 * w,
                  dy=-abs(w) * 20, flip=flip), 110)

# 4.4a Sleep A_Start：躺下（站姿 → 躺姿，被子在后半段滑入）
NA = 8
for i in range(NA):
    t = i / (NA - 1)
    e = t * t * (3 - 2 * t)                 # smoothstep
    bl = max(0.0, (t - 0.40) / 0.60)        # 后 60% 被子滑入
    rec("SleepA", frame(closed=True, blush=0.30 * e, mouth_open=0.16 * e,
                        post_rot=90 * e, post_blanket=bl), 110)

# 4.4b Sleep B_Loop：睡眠循环（躺着 + 偶尔流口水 + 飘 Z）
# 拉长到 48 帧（约 8.6 秒），让流口水变成"偶尔发生"而不是一直挂着
N = 48
DROOL_A, DROOL_B = 22, 33                   # 口水只在这段帧内出现（约 2.2 秒）
for i in range(N):
    t = i / N
    br = math.sin(t * 2 * math.pi * 4)      # 四个呼吸周期
    da = dd = 0.0
    if DROOL_A <= i <= DROOL_B:
        k = i - DROOL_A                     # 0..11
        da = min(1.0, k / 5.0)              # 前 5 帧口水变长
        dd = max(0.0, (k - 7) / 4.0)        # 之后末端水滴下落
        if dd > 1.0:
            dd = 0.0                        # 水滴落完即消失
    zzz = []
    for k in range(3):
        u = (t + k * 0.34) % 1.0
        if u < 0.78:
            v = u / 0.78
            zzz.append((505 + v * 145, 195 - v * 150, 0.68 + v * 0.55,
                        min(1.0, v * 4) * (1 - v)))
    rec("SleepB", frame(sx=1 - 0.012 * br, sy=1 + 0.024 * br,
                        closed=True, blush=0.30, mouth_open=0.16,
                        post_rot=90, post_blanket=1.0, post_zzz=zzz,
                        post_lift=br * 6,
                        post_drool=(da, dd)), 180)

# 4.4c Sleep C_End：起床（躺姿 → 站姿，被子在前半段滑走）
#   后 40% 睁眼 + 微张口，做出"刚睡醒"的辨识度（避免和摸头的闭眼享受撞脸）
NC = 10
for i in range(NC):
    t = i / (NC - 1)
    e = t * t * (3 - 2 * t)                 # smoothstep
    bl = max(0.0, 1.0 - t / 0.45)           # 前 45% 被子滑走
    if t < 0.60:
        closed, eo, mo = True, 0.0, 0.16 * (1 - e)
    else:
        u = (t - 0.60) / 0.40
        closed, eo = False, min(1.0, u * 2.2)
        mo = 0.16 + 0.44 * math.sin(math.pi * u)
    rec("SleepC", frame(closed=closed, eye_open=eo, blush=0.30 * (1 - e),
                        mouth_open=mo, post_rot=90 * (1 - e), post_blanket=bl), 110)

# 4.5a Touch_Head A_Start：完整摸头反应（一次播完）
#   被摸到一缩 + 睁大眼 → 眯眼左右蹭动（不是全闭，避免像睡着）→ 睁眼星星眼 + 飘爱心
N = 22
for i in range(N):
    t = i / (N - 1)
    sy, rot, eo, ez, bl, st, mo = kf([
        (0.00, 1.000,  0.0, 1.00, 1.00, 0.00, 0.00, 0.00),
        (0.13, 0.950,  0.0, 1.00, 1.42, 0.22, 0.00, 0.00),
        (0.26, 1.018, -3.6, 0.34, 1.00, 0.46, 0.00, 0.00),
        (0.38, 1.006,  2.8, 0.30, 1.00, 0.50, 0.00, 0.00),
        (0.50, 1.016, -3.6, 0.34, 1.00, 0.48, 0.00, 0.00),
        (0.62, 1.004,  2.6, 0.30, 1.00, 0.48, 0.00, 0.00),
        (0.74, 1.012, -1.8, 0.44, 1.00, 0.46, 0.00, 0.00),
        (0.88, 1.048,  0.0, 1.00, 1.44, 0.42, 0.90, 0.03),
        (1.00, 1.000,  0.0, 1.00, 1.18, 0.32, 0.60, 0.00),
    ], t)
    d = 80 if t < 0.20 else (115 if t < 0.78 else 100)
    hearts = []
    for k in range(3):
        u = (t - 0.70 - k * 0.09) / 0.30
        if 0.0 < u < 1.0:
            hearts.append((1120 + u * 210, 850 - u * 470, 0.70 + u * 0.70,
                           min(1.0, u * 5) * (1 - u) ** 0.6))
    rec("TouchHeadA", frame(sx=1 / math.sqrt(max(0.3, sy)), sy=sy, rot=rot,
                            eye_open=eo, eye_zoom=ez, blush=bl,
                            star_eyes=st, mouth_open=mo, hearts=hearts), d)

# 4.5b Touch_Head B_Loop：保持姿势（2 帧极微呼吸，循环时看不出重复）
for i in range(2):
    rec("TouchHeadB", frame(sy=1 + 0.006 * i, eye_open=1.0, eye_zoom=1.16,
                            blush=0.32, star_eyes=0.55, mouth_open=0.03), 220)

# 4.5c Touch_Head C_End：收尾回正（星星眼与腮红淡出）
N = 4
for i in range(N):
    t = i / (N - 1)
    e = t * t * (3 - 2 * t)
    rec("TouchHeadC", frame(sy=1 - 0.012 * math.sin(math.pi * t),
                            eye_open=1.0, eye_zoom=1.16 - 0.16 * e,
                            blush=0.32 * (1 - e), star_eyes=0.55 * (1 - e),
                            mouth_open=0.03 * (1 - e)), 90)

# 4.6 Raise 被提起：明显挣扎 + 泪珠
#   素材本来就占满画面高度（70~930），无法靠上移表现离地 →
#   改用「整体缩小到 0.90 + 上移 90px」，脚下腾出空白 = 悬空感
TEAR_L = (631, 792)                 # 左眼外眼角下方（2000 坐标系）
TEAR_R = (1136, 785)                # 右眼外眼角下方


def tears_pair(dy_l=0.0, dy_r=0.0, s=0.80, a=0.9):
    return [(TEAR_L[0], TEAR_L[1] + dy_l, s, a),
            (TEAR_R[0], TEAR_R[1] + dy_r, s, a)]


# 4.6a A_Start：被猛地拎起来（身体被拉长 → 缩回 + 瞪眼张嘴 + 泪珠鼓出）
N = 8
for i in range(N):
    t = i / (N - 1)
    e = t ** 0.65
    stretch = math.sin(math.pi * t) * 0.05          # 拎起瞬间的纵向拉伸
    s = 1 - 0.10 * e
    u = (i - 4) / 3.0                               # 后 3 帧泪珠从眼角鼓出来
    tr = tears_pair(s=0.62 + 0.20 * u, a=0.85 * u) if u > 0 else None
    rec("RaiseA", frame(sx=s * (1 - stretch * 0.5), sy=s * (1 + stretch),
                        dy=-90 * e, rot=3.5 * math.sin(t * math.pi * 2) * e,
                        eye_zoom=1 + 0.45 * e, mouth_open=0.78 * e,
                        tears=tr), 90)

# 4.6b B_Loop：悬空挣扎（身体左右扭动 + 泪珠挂眼角 + 张嘴喊）
N = 6
for i in range(N):
    t = i / N
    s = math.sin(t * 2 * math.pi)
    c = math.cos(t * 2 * math.pi)
    rec("RaiseB", frame(sx=0.90 - 0.025 * c, sy=0.90 + 0.025 * c,
                        dy=-90 - 8 * abs(s), rot=9.0 * s,
                        eye_zoom=1.45, mouth_open=0.55 + 0.12 * c,
                        tears=tears_pair(18 + 10 * s, 18 - 10 * s, 0.82, 0.92)), 130)

# 4.6c C_End：被放下（落地回弹 + 泪珠滑落 + 松一口气）
N = 8
for i in range(N):
    t = i / (N - 1)
    e = t * t * (3 - 2 * t)
    s = 0.90 + 0.10 * e
    b = math.sin(math.pi * t) * 0.035               # 落地回弹
    tr = None
    if t < 0.80:                                    # 泪珠下滑 → 淡出
        a = 1.0 - t / 0.80
        yy = 26 + t * 250
        tr = tears_pair(yy, yy - 7, 0.82 * (0.55 + 0.45 * a), a)
    rec("RaiseC", frame(sx=s, sy=s + b, dy=-90 * (1 - e),
                        rot=3.6 * (1 - e),
                        eye_zoom=1.45 - 0.55 * e,
                        eye_open=1.0 - 0.75 * max(0.0, (t - 0.72) / 0.28),
                        mouth_open=0.78 * (1 - e) + 0.10 * math.sin(math.pi * t),
                        tears=tr), 95)

# 4.6d Raised_Dynamic：被拎着晃（拖动时循环）
#   ★★ 帧时长刻意拉到 800ms：VPet 的 DisplayRaised() 在拖动中会被反复触发
#      （鼠标每移动 >20px 就把 rasetype 重置为 0 → 重播本动画），而每次 Display
#      都可能在 Image1/2/3 三个公共控件之间轮换 → 旧控件脱离可视树 →
#      Main.xaml.cs:475 的 CaptureMouse() 失败 → 拖动当场结束。
#      素材层改不掉这个机制，只能把「一轮播放」拉长，让轮换窗口变稀疏：
#      3 帧 × 140ms = 0.42 秒 → 3 帧 × 800ms = 2.4 秒，掉抓频率降到约 1/6。
N = 3
for i in range(N):
    s = math.sin(i / N * 2 * math.pi)
    rec("RaiseDyn", frame(sx=0.90, sy=0.90, dy=-90 - 10 * abs(s),
                          rot=8.0 * s, eye_zoom=1.45, mouth_open=0.50,
                          tears=tears_pair(20, 20, 0.82, 0.92)), 800)

# 4.7 SideHide 躲到屏幕边缘
#   原版是「侧身蜷缩」姿态，我们只有正面素材 → 改成整体横躺 90° 贴墙。
#   坐标系换算：VPet 内部按 500 系算，side#left#219 表示窗口被推出屏幕 219（500 系）
#     → 可见区 = 500 系 [219,500] = 素材 1000 系 [438,1000] = 2000 系 [876,2000]（贴左边缘）
#     → 可见区 = 500 系 [0,281]  = 素材 1000 系 [0,562]   = 2000 系 [0,1124] （贴右边缘）
#   ★★ 朝向按【头顶】判，不是按嘴：要的是"头探进屏幕里"（头顶朝屏幕内侧）。
#     PIL rotate(+90) 逆时针 → 头顶朝左
#     PIL rotate(-90) 顺时针 → 头顶朝右
#   两侧都让头顶朝屏幕内：
#     · 贴左边缘 rot=-90：头顶朝右（屏幕内）✓
#     · 贴右边缘 rot=+90：头顶朝左（屏幕内）✓
#   dx0 = 躲着时的位移（0 → 整个头落在可见区内），dx_probe = 探头时的位移（往屏幕内伸）
#   ※ 恐龙尾巴与肚皮横躺后横向坐标完全重叠，无法只露尾巴（已用标定图验证）
HIDE_S = 0.86                       # 统一缩小，避免横躺时被 2000 画布裁掉


def hide_seq(tag, rot, dx0, dx_probe=None, wobble=3.5, dy_amp=120.0):
    """生成某一侧的六段。
    rot=横躺角度，dx0=躲着时的横向位移，dx_probe=探头时的横向位移（None 则同 dx0）
    ★ dy_amp：探头时的垂直浮沉幅度。符号随 rot 翻转 —— 因为旋转是绕【画布中心】做的，
      贴左时头在画布右侧、贴右时头在画布左侧，同样的旋转角会让头往相反方向跑；
      让 dy 的符号跟着翻转，两侧头的实际摆动幅度才一致。
    """
    if dx_probe is None:
        dx_probe = dx0
    dy_sign = 1.0 if rot > 0 else -1.0
    # Main A_Start：横躺贴墙
    for i in range(8):
        t = i / 7.0
        e = t * t * (3 - 2 * t)
        rec("Hide%sA" % tag, frame(sx=HIDE_S, sy=HIDE_S, post_rot=rot * e,
                                   post_dx=dx0 * e, eye_open=1 - 0.5 * e,
                                   blush=0.30 * e), 95)
    # Main B_Loop：躲着（半睁眼偷偷看 + 轻微呼吸）
    for i in range(4):
        s = math.sin(i / 4.0 * 2 * math.pi)
        rec("Hide%sB" % tag, frame(sx=HIDE_S * (1 + 0.012 * s),
                                   sy=HIDE_S * (1 + 0.012 * s),
                                   post_rot=rot, post_dx=dx0 + 8 * s,
                                   eye_open=0.52, blush=0.30), 200)
    # Main C_End：站起来回正
    for i in range(8):
        t = i / 7.0
        e = t * t * (3 - 2 * t)
        rec("Hide%sC" % tag, frame(sx=HIDE_S + 0.14 * e, sy=HIDE_S + 0.14 * e,
                                   post_rot=rot * (1 - e), post_dx=dx0 * (1 - e),
                                   eye_open=0.52 + 0.48 * e,
                                   blush=0.30 * (1 - e)), 95)
    # Rise A_Start：把露出的部分往外探
    for i in range(4):
        t = i / 3.0
        e = t * t * (3 - 2 * t)
        rec("Hide%sRA" % tag, frame(sx=HIDE_S, sy=HIDE_S, post_rot=rot,
                                    post_dx=dx0 + (dx_probe - dx0) * e,
                                    eye_open=0.52 + 0.48 * e, blush=0.30), 110)
    # Rise B_Loop：探头张望 / 尾巴摆动
    for i in range(6):
        t = i / 6.0
        s = math.sin(t * 2 * math.pi)
        rec("Hide%sRB" % tag, frame(sx=HIDE_S, sy=HIDE_S,
                                    post_rot=rot + wobble * s,
                                    post_dx=dx_probe, post_dy=dy_amp * dy_sign * s,
                                    eye_open=1.0, blush=0.30), 150)
    # Rise C_End：缩回去
    for i in range(4):
        t = i / 3.0
        e = t * t * (3 - 2 * t)
        rec("Hide%sRC" % tag, frame(sx=HIDE_S, sy=HIDE_S, post_rot=rot,
                                    post_dx=dx_probe + (dx0 - dx_probe) * e,
                                    eye_open=1 - 0.48 * e, blush=0.30), 110)


hide_seq("L", -90, 0, dx_probe=200, wobble=6.0)   # 贴左：躲着露整头，探头往屏幕内伸
hide_seq("R",  90, 0, dx_probe=-200, wobble=6.0)  # 贴右：躲着露整头，探头往屏幕内伸

# 4.8 Shutdown 退出
N = 10
for i in range(N):
    t = i / (N - 1)
    s = 1 - 0.5 * (t ** 1.3)
    rec("Shutdown", frame(sx=s, sy=s, dy=26 * t, alpha=1 - t ** 1.6,
                          eye_open=1 - 0.6 * t), 90)

# 4.7 Eat 吃东西：张嘴迎接 → 咀嚼两次 → 咽下
N = 12
for i in range(N):
    t = i / (N - 1)
    if i <= 2:                              # 张嘴
        mo = 0.80 * (i / 2.0)
    elif i <= 9:                            # 咀嚼（两次开合）
        u = (i - 3) / 6.0
        mo = 0.30 + 0.45 * (0.5 + 0.5 * math.cos(u * 4 * math.pi))
    else:                                   # 咽下
        mo = 0.30 * (1 - (i - 9) / 2.0)
    rec("Eat", frame(mouth_open=mo, blush=0.18 * t,
                     sy=1 + 0.010 * math.sin(t * 4 * math.pi)), 110)

# 4.8 Drink 喝水：仰头张口 → 吞咽 → 放下
N = 12
for i in range(N):
    t = i / (N - 1)
    if i <= 3:                              # 仰头张口
        mo = 0.55 * (i / 3.0)
        rot = -4.5 * (i / 3.0)
    elif i <= 8:                            # 吞咽
        mo = 0.55 - 0.35 * ((i - 4) / 4.0)
        rot = -4.5 + 2.0 * ((i - 4) / 4.0)
    else:                                   # 放下
        mo = 0.20 * (1 - (i - 9) / 2.0)
        rot = -2.5 + 2.5 * ((i - 9) / 2.0)
    rec("Drink", frame(mouth_open=max(0.0, mo), rot=rot,
                       blush=0.16 * t), 110)


# ---------------- 4.9 Touch_Body 摸身体 = 怕痒 ----------------
#   设计要点（必须和「摸头」拉开分辨率）：
#     · 摸头是【原地】眯眼左右蹭（rot ±3.6°，无位移）
#     · 摸身体是【整体横移躲闪】dx ±200（2000 系）+ 张嘴笑 + 身体缩紧 sy 0.93
#     · 摸头用「星星眼 + 爱心」，摸身体改用「汗滴」（位置在脸侧，受力点也不同）
#   与 Raise（被提起）的区分：Raise 是等比缩小 0.90 + 上移 90 + 泪珠；
#       这里无上移、无泪珠，且是横向位移。
SWEAT_COL = (168, 216, 250)
SWEAT_EDGE = ( 92, 150, 200)


def draw_sweat_1000(img, items):
    """汗滴（浅蓝圆润水滴 + 高光）。与泪珠（深蓝细长）刻意做出区别"""
    if not items:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for cx, cy, s, a in items:
        aa = int(255 * max(0.0, min(1.0, a)))
        if aa <= 4:
            continue
        r = 25 * s
        d.polygon([(cx + r * 0.26, cy - r * 0.78),
                   (cx + r * 1.42, cy - r * 2.10),
                   (cx + r * 0.98, cy - r * 0.26)], fill=SWEAT_COL + (aa,))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SWEAT_COL + (aa,),
                  outline=SWEAT_EDGE + (aa,), width=max(2, int(5 * s)))
        hr = r * 0.32
        d.ellipse([cx - r * 0.46 - hr, cy - r * 0.40 - hr,
                   cx - r * 0.46 + hr, cy - r * 0.40 + hr],
                  fill=(255, 255, 255, int(aa * 0.9)))
    img.alpha_composite(lay)


def tb_frame(sy=1.0, sx=1.0, rot=0.0, dx=0.0, eye_open=1.0,
             mouth_open=0.0, blush=0.0, sweat=None):
    img = frame(sx=sx, sy=sy, rot=rot, dx=dx, eye_open=eye_open,
                mouth_open=mouth_open, blush=blush)
    if sweat:
        draw_sweat_1000(img, sweat)
    return img


# 4.9a A_Start：被摸到一缩 → 惊吓 → 开始躲
N = 10
for i in range(N):
    t = i / (N - 1)
    k = kf([
        (0.00, 1.000, 0.0, 1.00, 1.00,   0.0),
        (0.18, 0.925, 0.0, 1.00, 1.58,   0.0),   # 身体猛地一缩 + 瞪大眼
        (0.42, 0.955, -6.5, 0.30, 1.05, 70.0),   # 眯眼张嘴 + 开始躲
        (0.70, 0.930, 5.5, 0.26, 1.10, -60.0),
        (1.00, 0.935, 0.0, 0.30, 1.00,  120.0),
    ], t)
    sy, rot, eo, mo, dx = k
    sw = [(232, 430, 0.95, max(0.0, (t - 0.35) / 0.5)),
          (648, 448, 0.74, max(0.0, (t - 0.55) / 0.45))] if t > 0.35 else None
    d = 95 if t < 0.25 else 115
    rec("TouchBodyA", tb_frame(sx=1.02, sy=sy, rot=rot, dx=dx, eye_open=eo,
                               mouth_open=mo, blush=0.36 * t, sweat=sw), d)

# 4.9b B_Loop：左右快速躲闪（一个完整来回，帧时长最短 → "痒得受不了"）
N = 8
for i in range(N):
    t = i / N
    ph = t * 2 * math.pi
    s = math.sin(ph)
    img = frame(sx=1.02, sy=0.935 + 0.030 * math.cos(ph * 2),
                rot=6.0 * s, dx=150 * s,
                eye_open=0.24, mouth_open=max(0.0, 0.48 + 0.20 * s),
                blush=0.40)
    draw_sweat_1000(img, [(232 - 160 * s, 430, 0.95, 0.92),
                          (648 - 160 * s, 448, 0.74, 0.78)])
    rec("TouchBodyB", img, 100)

# 4.9c C_End：躲闪收住 → 回正 → 眯眼淡出
N = 6
for i in range(N):
    t = i / (N - 1)
    e = t * t * (3 - 2 * t)
    sw = [(232 + 30 * e, 430, 0.95, (1 - e)), (648 + 30 * e, 448, 0.74, (1 - e))] \
        if e < 0.98 else None
    rec("TouchBodyC", tb_frame(sx=1.02, sy=0.935 + 0.065 * e, rot=4.0 * (1 - e),
                               dx=70 * (1 - e),
                               eye_open=0.24 + 0.76 * e,
                               mouth_open=max(0.0, 0.30 * (1 - e)),
                               blush=0.40 * (1 - e), sweat=sw), 100)


# ---------------- 4.10 Pinch 捏 = 缩小本体 + 喷火 ----------------
#   ★ C 路线的几何（素材 1000 系，已实渲验证）：
#     原 bbox x[198,801] y[70,929]，脚底中心 (500,930)，嘴 (441,406)
#     缩到 s=0.62 后平移 (dx=+210, dy=-70) → 角色落到【右下角】
#       bbox x[523,897] y[327,859]，嘴 → (673, 535)
#     右上… 不，是【左上】留出空间，火焰从嘴斜向左上喷，绝不穿模。
#   ★ frame() 吃 2000 系，所以传给它的 dx/dy 要 ×2。
#   ★ 火焰画在 frame() 之后（1000 系），起点用上面推导的 (673, 535)。
PINCH_S = 0.62                 # 捏的时候整体缩小
PINCH_DX, PINCH_DY = 210.0, -70.0        # 1000 系


def pinch_mouth_pos(s=PINCH_S, dx=PINCH_DX, dy=PINCH_DY, rot=0.0,
                    mx=441.0, my=406.0, ax=500.0, ay=930.0):
    """算「缩放 + 旋转 + 平移」之后嘴的真实位置（1000 系）。

    ★ frame() 的缩放/旋转都绕脚底中心 (ax, ay)，顺序是 缩放→旋转→平移，
      所以这里必须按同样顺序推导，否则火焰起点会偏离嘴（之前硬编码 673
      就因此偏了 22px）。
    """
    x = ax + (mx - ax) * s
    y = ay + (my - ay) * s
    th = math.radians(rot)
    c, sn = math.cos(th), math.sin(th)
    xr = ax + (x - ax) * c - (y - ay) * sn
    yr = ay + (x - ax) * sn + (y - ay) * c
    return xr + dx, yr + dy


# 火焰起点 = 嘴再沿喷射方向外移 OUT（避免根部把下巴糊住）
FIRE_OUT = 62.0
PINCH_MX, PINCH_MY = pinch_mouth_pos(rot=-4.0)

# 火焰配色：外 → 内 的「径向」三层（不再用 4 层截断色带）
FIRE_OUTER = (255, 74, 22)      # 橙红（外焰）
FIRE_MID = (255, 148, 34)       # 橙（中焰）
FIRE_CORE = (255, 226, 120)     # 黄白（焰心）


def _blob(lay, cx, cy, r, col, a, sq=1.0):
    """画一个圆团（sq<1 压扁成椭圆）"""
    if r < 0.6 or a <= 0:
        return
    d = ImageDraw.Draw(lay)
    rr = r
    d.ellipse([cx - rr, cy - rr * sq, cx + rr, cy + rr * sq],
              fill=col + (int(a),))


def draw_fire_1000(img, L, w0, alpha, seed=0.0, bx=None, by=None,
                   ang=-136.0, curve=16.0, glow=0.0):
    """从嘴斜向左上喷火 —— 圆团叠加式。

    ★★ 关键：三层各自「一次性」在同一图层内绘制（层内是实心覆盖，不是
       alpha 反复合成）→ 避免重叠边缘出现等距明暗条纹（糖葫芦/弹簧感）。
    ★ 用户要求：不要嘴部那一圈辉光（像奶嘴）。
    """
    del glow
    if alpha <= 0.02 or L <= 1:
        return
    bx = PINCH_MX if bx is None else bx
    by = PINCH_MY if by is None else by
    # ★ 起点沿喷射方向外移 FIRE_OUT，让根部脱离下巴（真正"从嘴里喷出"）
    a0 = math.radians(ang)
    bx += math.cos(a0) * FIRE_OUT
    by += math.sin(a0) * FIRE_OUT

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    n = 44                                   # 团数密 → 连续顺滑
    pts = []
    for i in range(n + 1):
        u = i / n
        a = math.radians(ang + curve * u * 0.6)
        x = bx + math.cos(a) * u * L
        y = by + math.sin(a) * u * L
        # ★ 包络：根部最粗 → 沿程单调收细（真火焰的口径分布）
        env = 1.0 - 0.88 * (u ** 0.85)
        # ★ 根部稍微收一点，避免贴脸那一下太"墩"
        root_k = 0.72 + 0.28 * min(1.0, u / 0.18)
        wob = (1.0
               + 0.14 * math.sin(u * 2.7 + seed * 1.3)
               + 0.07 * math.sin(u * 6.1 - seed * 0.7))
        r = w0 * (0.10 + 1.55 * env) * root_k * wob
        # 末端横向飘摆（焰舌）
        sway = math.sin(u * 2.2 + seed) * w0 * 0.9 * u * u
        pa = math.radians(ang + 90)
        pts.append((x + math.cos(pa) * sway, y + math.sin(pa) * sway, r))

    for cx, cy, r in pts:                    # ① 外焰（实心）
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=FIRE_OUTER + (255,))
    for cx, cy, r in pts:                    # ② 中焰
        rr = r * 0.70
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=FIRE_MID + (255,))
    for cx, cy, r in pts:                    # ③ 焰心（收窄到 0.34）
        rr = r * 0.34
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=FIRE_CORE + (255,))

    if alpha < 0.995:                        # 整体 alpha 收放（喷出/收火）
        ka = alpha
        lay.putalpha(lay.split()[3].point(lambda v: int(v * ka)))

    for k in range(5):                       # 末端火星
        su = 0.82 + 0.18 * ((k * 0.37 + seed * 0.31) % 1.0)
        sa = math.radians(ang + (k - 2) * 9 + seed * 6)
        sx = bx + math.cos(sa) * su * L
        sy = by + math.sin(sa) * su * L
        rr = w0 * (0.16 + 0.10 * ((k * 0.53) % 1.0))
        d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr],
                  fill=FIRE_MID + (int(255 * alpha),))
    img.alpha_composite(lay)


# ---- 局部形变：掐住左脸往外拽 ----
#   原理：把左脸矩形区域【单独裁出】→ 平移/拉伸 → 贴回 → 用羽化遮罩融合边缘。
#   ★ 坐标系是 1000 系（frame() 之后）。
#   ★★ 关键：捏的时候角色被缩到 PINCH_S 并平移到 (PINCH_DX, PINCH_DY)，
#      所以脸部区域必须做同样的变换，否则拽的是空气。
#   原始左脸（素材 1000 系）：x[280,432] y[344,456]
#     对应 vup.lps 的 pinch#px140 py172 sw76 sh56（500 系 ×2）
CHEEK_RAW = (280, 344, 432, 456)


def cheek_box_scaled(s=PINCH_S, dx=PINCH_DX, dy=PINCH_DY):
    """把原始脸部框按「绕脚底中心缩放 + 平移」换算到当前画面位置。

    frame() 的缩放锚点在 1000 系是 (500, 930)；dx/dy 是 1000 系平移量。
    """
    ax, ay = 500.0, 930.0
    x0, y0, x1, y1 = CHEEK_RAW
    nx0 = ax + (x0 - ax) * s + dx
    nx1 = ax + (x1 - ax) * s + dx
    ny0 = ay + (y0 - ay) * s + dy
    ny1 = ay + (y1 - ay) * s + dy
    return (int(nx0), int(ny0), int(nx1), int(ny1))


def _feather_mask(size, box, pad=22):
    """生成羽化遮罩：矩形内 255，边缘 pad 像素内平滑过渡到 0"""
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rectangle([box[0], box[1], box[2], box[3]], fill=255)
    return m.filter(ImageFilter.GaussianBlur(pad))


def pull_cheek(img, amt=1.0, dx=0.0, dy=0.0, sx=1.0, sy=1.0,
               s=PINCH_S, pdx=PINCH_DX, pdy=PINCH_DY):
    """把左脸往外拽（捏脸效果）。amt=0 无变化，1 全量。

    dx/dy：脸部位移（负 x = 往左拽，负 y = 往上拽）—— 1000 系
    sx/sy：脸部局部缩放（>1 = 拉长）
    """
    if amt <= 0.02:
        return img
    box = cheek_box_scaled(s, pdx, pdy)
    x0, y0, x1, y1 = box
    cw, ch = max(1, x1 - x0), max(1, y1 - y0)
    face = img.crop(box)
    lw, lh = max(1, int(round(cw * sx))), max(1, int(round(ch * sy)))
    face = face.resize((lw, lh), Image.BICUBIC)
    ncx = (x0 + x1) / 2.0 + dx * amt
    ncy = (y0 + y1) / 2.0 + dy * amt
    patch = Image.new("RGBA", img.size, (0, 0, 0, 0))
    patch.alpha_composite(face, (int(ncx - lw / 2), int(ncy - lh / 2)))
    mask = _feather_mask(img.size, box, 20)
    a = patch.split()[3].point(lambda v: int(v * amt))
    patch.putalpha(ImageChops.multiply(mask, a))
    img.alpha_composite(patch)
    return img


# 4.10a A_Start：被捏住的瞬间 —— 参照【原版只有 1 帧】的设计
#   ★★ 重大发现（读原版素材）：
#     原版 Pinch 结构 = A_Start **1 帧** / B_Loop 6 帧 / C_End **21 帧**。
#     → 说明"被捏住"这个动作【不需要前摇】，瞬间到位；表演主要放在 C 段收尾。
#     我们之前做 A 段 10 帧前摇，和原版设计哲学完全相反（用户也反馈"AB 帧怪怪的"）。
#   ★ 现在改成 2 帧：
#       f0 = 常态（1 帧过渡，避免从待机切过来太生硬）
#       f1 = 已被捏住（瞪眼 → 忍痛，头被拽歪）
#   ★ 尺寸：原尺寸 1.0（喷火只在 C 段）
PINCH_PRE_S = 1.0
#   ★ rot 绕脚底中心 (500,930)，头离锚点约 430px：
#     rot=3° 甩 22px、5° 甩 37px、11° 甩 82px（出框）。表现"被拽歪"以位移为主。
CHEEK_DX = -46.0                       # 被拽时的横向位移（1000 系，负=往左）
CHEEK_DY = -22.0                       # 竖直
CHEEK_ROT = 4.5                        # 头歪的小角度
#   ★ eye_zoom ≤ 1.4（1.9 会变成两个占脸大黑球，已实测）
EYE_STARTLE_Z = 1.35                   # 瞪圆
EYE_PAIN_Z = 1.05                      # 忍痛时收到

rec("PinchA", frame(sx=1.0, sy=0.990, rot=0.0, dx=0.0, dy=0.0,
                    eye_open=1.0, eye_zoom=EYE_STARTLE_Z,
                    mouth_open=0.02, blush=0.10), 80)
rec("PinchA", frame(sx=1.0, sy=1.000, rot=CHEEK_ROT, dx=CHEEK_DX * 2, dy=CHEEK_DY * 2,
                    eye_open=0.30, eye_zoom=EYE_PAIN_Z,
                    mouth_open=0.62, blush=0.80), 80)

# 4.10b B_Loop：按住不放 → 【大幅】左右扭动挣扎（参照原版 6 帧）
#   ★★ 看原版素材：B 段 6 帧 = 萝莉斯左右大幅扭动 + 双臂挥舞。
#     用户反馈过两次"左右扭不明显"，这次直接把幅度拉满：
#     rot 摆动 ±9°（配 sy=0.94 缩小，头距锚点 404px，9° 甩 63px，安全）
#     dx 摆动 ±70（1000 系 → 两倍系 ±140）
#   ★ 相位：dx 用 sin（左右），sy/sx 用 cos 2 倍频（挤压呼吸）
N = 7                              # ★ 7 帧（奇数）：sin 采样不重复，循环无卡顿
for i in range(N):
    t = i / N
    ph = t * 2 * math.pi
    s = math.sin(ph)
    c2 = math.cos(ph * 2)
    rec("PinchB", frame(sx=0.94 - 0.030 * c2, sy=0.94 + 0.045 * c2,
                        rot=CHEEK_ROT + 9.0 * s,
                        dx=(20.0 + 70 * s) * 2,
                        dy=(CHEEK_DY * 0.6 + 12 * abs(s)) * 2,
                        eye_open=0.30, eye_zoom=EYE_PAIN_Z,
                        mouth_open=0.55 + 0.30 * s, blush=0.88), 100)

# 4.10c C_End：松手 → 甩头回弹 → 缩小让位 → 喷火 → 收火（参照原版 C 段 21 帧的"缓慢收尾"）
#   18 帧：① 松手猛甩头 + 回弹 + 缩小（0~0.30）
#          ② 火柱暴涨 → 持续喷 → 收火（0.30~1.0）
N = 18
for i in range(N):
    t = i / (N - 1)
    if t < 0.30:                     # ① 松手猛甩头 + 回弹 + 开始缩小
        u = t / 0.30
        e = u * u * (3 - 2 * u)
        over = math.sin(math.pi * u) * 0.62
        rot = CHEEK_ROT * (1 - e) - 20.0 * over
        dx = CHEEK_DX * (1 - e) - 52 * over
        dy = CHEEK_DY * (1 - e) - 10 * over
        s_now = 1.0 + (PINCH_S - 1.0) * e
        dpx = (PINCH_DX - 0) * e
        dpy = (PINCH_DY - 0) * e
        rec("PinchC", frame(sx=s_now, sy=s_now, rot=rot,
                            dx=(dx + dpx) * 2, dy=(dy + dpy) * 2,
                            eye_open=0.30 + 0.70 * e, eye_zoom=1.10,
                            mouth_open=0.30 + 0.65 * e,
                            blush=0.85 * (1 - 0.5 * e)), 100)
    else:
        u = (t - 0.30) / 0.70
        if u < 0.34:                 # ③ 火柱生长（从 0 起，拉长到 34% → 约 4 帧）
            e = (u / 0.34) ** 1.6
        elif u < 0.68:               # ④ 持续喷火
            e = 1.0
        else:                        # ⑤ 收火 + 火星消散
            v = (u - 0.68) / 0.32
            e = 1 - v * v * (3 - 2 * v)
        L = 620 * e
        img = frame(sx=PINCH_S, sy=PINCH_S * (1 + 0.02 * e),
                    rot=-4.0 * e,
                    dx=PINCH_DX * 2, dy=PINCH_DY * 2,
                    eye_open=1.0 - 0.74 * e, eye_zoom=1.30,
                    mouth_open=0.95 * e, blush=0.85 * e)
        # ★ alpha 快速拉满（≥0.55 即不透明），生长用长度 L 表达，
        #   避免"火焰淡入"的半透明感
        fa = min(1.0, 0.35 + 1.4 * e) if e > 0.02 else 0.0
        # ★ L 太短时火苗缩在嘴边像"腮红痘" → 低于阈值整帧不出火
        if L < 130:
            fa = 0.0
        draw_fire_1000(img, L, 58, fa, seed=t * 3.0)
        rec("PinchC", img, 100)


# ---------------- 5. 导出 ----------------
# 清掉各 clip 目录里不属于本次帧列表的旧帧（帧数/时长变化留下的残留）
for _name, _fps in FRAMES.items():
    _fd = os.path.dirname(_fps[0])
    _keep = set(os.path.basename(p) for p in _fps)
    for _f in os.listdir(_fd):
        if _f.lower().endswith(".png") and _f not in _keep:
            os.remove(os.path.join(_fd, _f))
            print("  清掉残留帧 %s/%s" % (_name, _f))


def export_gif(frames, path):
    imgs = []
    for img, _ in frames:
        c = Image.new("RGBA", (BASE, BASE), BG + (255,))
        c.alpha_composite(img)
        imgs.append(c.convert("RGB").resize((380, 380), Image.LANCZOS))
    imgs[0].save(path, save_all=True, append_images=imgs[1:],
                 duration=[d for _, d in frames], loop=0, disposal=2)
    return len(imgs)


ORDER = ("StartUP", "IDEL", "MOVE_right", "MOVE_left",
         "SleepA", "SleepB", "SleepC",
         "TouchHeadA", "TouchHeadB", "TouchHeadC",
         "RaiseA", "RaiseB", "RaiseC", "RaiseDyn",
         "HideLA", "HideLB", "HideLC", "HideLRA", "HideLRB", "HideLRC",
         "HideRA", "HideRB", "HideRC", "HideRRA", "HideRRB", "HideRRC",
         "TouchBodyA", "TouchBodyB", "TouchBodyC",
         "PinchA", "PinchB", "PinchC",
         "Eat", "Drink", "Shutdown")
total = 0
for name in ORDER:
    fr = CLIPS[name]
    n = export_gif(fr, os.path.join(OUT, name + ".gif"))
    total += n
    print("GIF %-12s %2d frames" % (name, n))

board.save(os.path.join(OUT, "_board.png"))
for k, v in layers.items():
    v.save(os.path.join(OUT, "_layer_%s.png" % k))
print("\nTOTAL %d frames" % total)

COLS, CELL = 6, 190
sheet = Image.new("RGB", (CELL * COLS, CELL * len(ORDER)), (255, 255, 255))
for r, nm in enumerate(ORDER):
    fr = CLIPS[nm]
    for c in range(COLS):
        j = int(round(c * (len(fr) - 1) / (COLS - 1)))
        bgc = Image.new("RGBA", (BASE, BASE), (255, 255, 255, 255))
        bgc.alpha_composite(fr[j][0])
        sheet.paste(bgc.convert("RGB").resize((CELL, CELL), Image.LANCZOS),
                    (c * CELL, r * CELL))
sheet.save(os.path.join(OUT, "_sheet.png"))
print("SHEET -> _sheet.png %s" % (sheet.size,))
