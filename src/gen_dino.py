# -*- coding: utf-8 -*-
"""
Q版小恐龙 · VPet 动画素材生成器
风格：扁平卡通（纯色块 + 统一深褐描边 + 极简五官）
几何严格对照参考图（1024 画布逐项测量后换算到 1000 画布）
规格：1000x1000 透明 PNG，命名符合 VPet 规范
"""
import os
import math
from PIL import Image, ImageDraw

W = H = 1000
SS = 2                                     # 超采样倍数（抗锯齿）
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'dino_demo')

# ================= 配色 =================
BODY    = (232, 67, 60, 255)               # 主体 正红
EDGE    = (74, 38, 32, 255)                # 描边 深褐（所有轮廓共用）
C_BELLY = (253, 240, 213, 255)             # 肚皮 米白
SPIKE   = (245, 160, 64, 255)              # 背刺 橙

CX, CY = 500, 495
OW = 9                                     # 外轮廓描边宽度

# ================= 几何（局部坐标，原点 = 角色中心） =================
HEAD      = (0, -131, 207, 163)            # 头
TORSO_UP  = (0, 110, 172, 125)             # 上身
TORSO_DN  = (0, 230, 175, 110)             # 下身
LEGS      = [(-88, 290, -14, 375), (14, 290, 88, 375)]     # 腿（圆角矩形）
LEG_R     = 30
BELLY_G   = (0, 172, 117, 148)             # 肚皮
EYE_Y, EYE_X, EYE_R = -111, 85, 19         # 眼睛
MOUTH_Y   = -82                            # 嘴巴
SPIKES    = [((175, -50), 42), ((150, 5), 52),
             ((168, 70), 48), ((170, 135), 34)]            # 背刺（根部, 尺寸）
TAIL_P0   = (-20, 170)                     # 尾巴起点
TAIL_LEN, TAIL_ANG, TAIL_HW = 315, 13, 62  # 尾巴长 / 角度 / 半宽


def _bez(p0, p1, p2, n=16):
    """二次贝塞尔（局部坐标）"""
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                    mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))
    return out


def _bez3(p0, p1, p2, p3, n=20):
    """三次贝塞尔（局部坐标）"""
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        a, b, c, e = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    return out


def draw_dino(squash=0.0, dy=0, eye=1.0, blush=0.55, breathe=0.0,
              asleep=False, shy=0.0, mouth_open=0.0, hand_in=0.0, tears=0.0):
    """绘制单帧，返回 1000x1000 RGBA 图像"""
    SW, SH = W * SS, H * SS
    img = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))

    cx, cy = CX * SS, (CY + dy) * SS
    sx = 1 + squash * 0.16 + breathe * 0.010
    sy = 1 - squash * 0.24 + breathe * 0.016

    def P(x, y):
        return (cx + x * SS * sx, cy + y * SS * sy)

    def PP(seq):
        return [P(x, y) for (x, y) in seq]

    def E(dr, x, y, rx, ry, **kw):
        dr.ellipse(list(P(x - rx, y - ry)) + list(P(x + rx, y + ry)), **kw)

    def RR(dr, x0, y0, x1, y1, r, grow=0, **kw):
        a = P(x0 - grow, y0 - grow)
        b = P(x1 + grow, y1 + grow)
        dr.rounded_rectangle([a[0], a[1], b[0], b[1]],
                             radius=max(1, int(r * SS * sx)), **kw)

    d = ImageDraw.Draw(img)
    L = lambda v: max(1, int(round(v * SS)))

    # ---------- 1. 呆毛（描边色粗线打底 + 红色细线 + 末端圆头） ----------
    tuft = _bez((0, -290), (-45, -335), (28, -352))
    d.line(PP(tuft), fill=EDGE, width=L(30), joint='curve')
    d.line(PP(tuft), fill=BODY, width=L(15), joint='curve')
    E(d, 28, -352, 15, 15, fill=EDGE)
    E(d, 28, -352, 7.5, 7.5, fill=BODY)

    # ---------- 2. 尾巴（半椭圆轮廓，尾尖圆钝，向右略向下） ----------
    a = math.radians(TAIL_ANG)
    ca, sa = math.cos(a), math.sin(a)
    na, nb = -sa, ca
    pa, pb = [], []
    for i in range(24):
        t = i / 23
        px = TAIL_P0[0] + TAIL_LEN * ca * t
        py = TAIL_P0[1] + TAIL_LEN * sa * t
        hw = TAIL_HW * math.sqrt(max(0.0, 1 - t * t))
        pa.append(P(px + na * hw, py + nb * hw))
        pb.append(P(px - na * hw, py - nb * hw))
    d.polygon(pa + pb[::-1], fill=BODY, outline=EDGE, width=L(9))

    # ---------- 3. 背刺（四片橙色三角，长在身体右侧） ----------
    for (bx, by), size in SPIKES:
        a = math.radians(15)
        nx_, ny_ = math.cos(a), -math.sin(a)
        tx_, ty_ = -ny_, nx_
        hgt, wid = size * 1.55, size * 1.30
        pts = []
        M = 14
        for i in range(M + 1):
            u = i / M
            hw = wid * 0.5 * (1 - u) ** 0.75
            px, py = bx + nx_ * hgt * u, by + ny_ * hgt * u
            pts.append(P(px + tx_ * hw, py + ty_ * hw))
        for i in range(M, -1, -1):
            u = i / M
            hw = wid * 0.5 * (1 - u) ** 0.75
            px, py = bx + nx_ * hgt * u, by + ny_ * hgt * u
            pts.append(P(px - tx_ * hw, py - ty_ * hw))
        d.polygon(pts, fill=SPIKE, outline=EDGE, width=L(9))

    # ---------- 4. 身体主体（画两遍：外扩描边层 + 原尺寸填充层） ----------
    ells = [HEAD, TORSO_UP, TORSO_DN]
    for (x, y, rx, ry) in ells:
        E(d, x, y, rx + OW, ry + OW, fill=EDGE)
    for (x0, y0, x1, y1) in LEGS:
        RR(d, x0, y0, x1, y1, LEG_R, grow=OW, fill=EDGE)
    for (x, y, rx, ry) in ells:
        E(d, x, y, rx, ry, fill=BODY)
    for (x0, y0, x1, y1) in LEGS:
        RR(d, x0, y0, x1, y1, LEG_R, fill=BODY)

    # ---------- 5. 肚皮 ----------
    E(d, *BELLY_G, fill=C_BELLY)

    # ---------- 6. 小手（从身体轮廓分叉出来的弧线，末端圆钝） ----------
    for sxx in (-1, 1):
        g = hand_in * 16
        arm = _bez((sxx * (158 - g), 55),
                   (sxx * (165 - g), 140),
                   (sxx * (82 - g), 135))
        d.line(PP(arm), fill=EDGE, width=L(10), joint='curve')
        E(d, sxx * (82 - g), 135, 11, 11, fill=EDGE)

    # ---------- 7. 脸 ----------
    for sxx in (-1, 1):
        ex = sxx * EYE_X
        if asleep or eye <= 0.08:
            d.line(PP(_bez((ex - 25, EYE_Y), (ex, EYE_Y + 13), (ex + 25, EYE_Y))),
                   fill=EDGE, width=L(9), joint='curve')
        else:
            r = EYE_R * eye * (1 - shy * 0.20)
            E(d, ex, EYE_Y, r, r, fill=EDGE)

    my = MOUTH_Y
    if asleep:
        E(d, 0, my, 13, 10, fill=EDGE)
    elif mouth_open > 0.12:
        E(d, 0, my + 8, 12 + 20 * mouth_open, 9 + 24 * mouth_open, fill=EDGE)
    else:
        d.line(PP(_bez((-31, my - 8), (-15, my + 10), (0, my - 4), 8)
                  + _bez((0, my - 4), (15, my + 10), (31, my - 8), 8)),
               fill=EDGE, width=L(8), joint='curve')

    # ---------- 8. 泪珠（仅不舒服时） ----------
    if tears > 0.05:
        for sxx in (-1, 1):
            E(d, sxx * 126, EYE_Y + 50 + 26 * tears,
              14 * tears, 19 * tears, fill=(140, 208, 255, 255))

    return img.resize((W, H), Image.LANCZOS)


CLIPS = {}          # 动作目录 -> [(帧路径, 帧时长), ...]


def save(img, sub, name, idx, dur=125):
    folder = os.path.join(OUT, sub)
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, '%s_%03d_%d.png' % (name, idx, dur))
    img.save(p)
    CLIPS.setdefault(sub, []).append((p, dur))
    return p


preview = []

# ===== Default / Nomal：呼吸（害羞的常态） =====
for i in range(12):
    b = math.sin(i / 12 * 2 * math.pi)
    p = save(draw_dino(breathe=b, dy=int(-4 * b), shy=0.35),
             'Default/Nomal/1', '呼吸', i, 125)
    if i == 3:
        preview.append(('默认·呼吸', p))

# ===== Default / Happy：开心跳动 =====
for i in range(10):
    j = abs(math.sin(i / 10 * math.pi))
    p = save(draw_dino(dy=int(-62 * j), shy=0.0, squash=-0.10 * j,
                       mouth_open=0.60 * j),
             'Default/Happy/1', '开心', i, 100)
    if i == 2:
        preview.append(('开心跳动', p))

# ===== Default / Ill：不舒服 =====
for i in range(8):
    b = math.sin(i / 8 * 2 * math.pi)
    p = save(draw_dino(breathe=b * 0.6, dy=int(14 + 4 * b), shy=0.65,
                       eye=0.6, squash=0.10, tears=0.6),
             'Default/Ill/1', '不舒服', i, 160)
    if i == 2:
        preview.append(('不舒服', p))

# ===== Touch_Head：摸头（ABC 三段式） =====
for i in range(5):
    k = i / 4
    p = save(draw_dino(squash=0.45 * k, dy=int(24 * k), shy=0.9 * k,
                       eye=1 - 0.3 * k, tears=0.3 + 0.4 * k),
             'Touch_Head/A_Nomal', '摸头A', i, 90)
    if i == 4:
        preview.append(('摸头 A段', p))

for i in range(8):
    s = math.sin(i / 8 * 2 * math.pi)
    p = save(draw_dino(squash=0.45 + 0.06 * s, dy=24, shy=1.0,
                       eye=0.66, hand_in=0.55, tears=0.7),
             'Touch_Head/B_Nomal', '摸头B', i, 90)
    if i == 1:
        preview.append(('摸头 B段', p))

for i in range(5):
    k = 1 - i / 4
    p = save(draw_dino(squash=0.45 * k, dy=int(24 * k), shy=0.9 * k,
                       eye=1 - 0.3 * k, tears=0.3 + 0.4 * k),
             'Touch_Head/C_Nomal', '摸头C', i, 90)
    if i == 0:
        preview.append(('摸头 C段', p))

# ===== Sleep：睡觉（ABC 三段式） =====
for i in range(5):
    k = i / 4
    p = save(draw_dino(dy=int(46 * k), eye=0, asleep=(k > 0.5), squash=0.14 * k,
                       shy=0.15),
             'Sleep/A_Nomal', '躺下', i, 150)
    if i == 4:
        preview.append(('睡觉 A段', p))

for i in range(10):
    s = math.sin(i / 10 * 2 * math.pi)
    p = save(draw_dino(dy=46 + int(8 * s), eye=0, asleep=True, squash=0.14, shy=0.15),
             'Sleep/B_Nomal', '睡觉循环', i, 150)
    if i == 3:
        preview.append(('睡觉 B段', p))

for i in range(5):
    k = 1 - i / 4
    p = save(draw_dino(dy=int(46 * k), eye=k, asleep=(k > 0.5), squash=0.14 * k,
                       shy=0.15),
             'Sleep/C_Nomal', '起床', i, 150)
    if i == 0:
        preview.append(('睡觉 C段', p))
preview.append(('起床 C段', os.path.join(OUT, 'Sleep/C_Nomal', '起床_004_150.png')))

# ===== 预览拼图 =====
TH = 250
cols = 4
rows = (len(preview) + cols - 1) // cols
canvas = Image.new('RGBA', (TH * cols, TH * rows), (248, 248, 248, 255))
for idx, (label, path) in enumerate(preview):
    if not os.path.exists(path):
        continue
    im = Image.open(path).convert('RGBA').resize((TH, TH), Image.Resampling.LANCZOS)
    canvas.alpha_composite(im, ((idx % cols) * TH, (idx // cols) * TH))
prev_path = os.path.join(BASE, 'dino_demo_preview.png')
canvas.save(prev_path)

# ===== 单帧大图（看细节） =====
hero = draw_dino(shy=0.45)
hero_path = os.path.join(BASE, 'dino_hero.png')
hero.save(hero_path)

total = sum(len(f) for _, _, f in os.walk(OUT))


# ===== GIF 动图预览 =====
def make_gif(frames, out_path, size=340, bg=(238, 244, 250, 255)):
    imgs = []
    for p, dur in frames:
        im = Image.open(p).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
        c = Image.new('RGBA', (size, size), bg)
        c.alpha_composite(im, (0, 0))
        imgs.append(c.convert('P', palette=Image.ADAPTIVE, colors=255))
    imgs[0].save(out_path, save_all=True, append_images=imgs[1:],
                 duration=[d for _, d in frames], loop=0, disposal=2)
    return out_path


GIF_PLAN = [
    ('Default/Nomal/1',    'dino_1_呼吸.gif'),
    ('Default/Happy/1',    'dino_2_开心跳动.gif'),
    ('Default/Ill/1',      'dino_3_不舒服.gif'),
    ('Touch_Head/A_Nomal', 'dino_4_摸头A.gif'),
    ('Touch_Head/B_Nomal', 'dino_5_摸头B.gif'),
    ('Touch_Head/C_Nomal', 'dino_6_摸头C.gif'),
    ('Sleep/A_Nomal',      'dino_7_睡觉A.gif'),
    ('Sleep/B_Nomal',      'dino_8_睡觉B.gif'),
    ('Sleep/C_Nomal',      'dino_9_起床C.gif'),
]

gif_paths = []
for key, fname in GIF_PLAN:
    if key in CLIPS:
        gif_paths.append(make_gif(CLIPS[key], os.path.join(BASE, fname)))

combo = []
for key, _ in GIF_PLAN:
    combo.extend(CLIPS.get(key, []))
combo_path = make_gif(combo, os.path.join(BASE, 'dino_0_全部动作演示.gif'))

print('生成完成')
print('输出目录:', OUT)
print('总帧数  :', total)
print('预览拼图:', prev_path)
print('单帧大图:', hero_path)
print('GIF 动图:', len(gif_paths) + 1, '个')
