# -*- coding: utf-8 -*-
"""拼对比图，快速目视检查动画改动"""
import os
from PIL import Image

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
FR = os.path.join(TMP, "dino_anim3", "frames")
BG = (240, 244, 250, 255)


def strip(items, out, cell=250):
    ims = []
    for clip, fn in items:
        im = Image.open(os.path.join(FR, clip, fn)).convert("RGBA")
        ims.append(im.resize((cell, cell), Image.LANCZOS))
    W, H = cell * len(ims), cell
    c = Image.new("RGBA", (W, H), BG)
    for i, im in enumerate(ims):
        c.alpha_composite(im, (i * cell, 0))
    c.convert("RGB").save(out)
    print(out, c.size)


# 歪头序列（i=12~26）+ 打哈欠序列（i=44~58）
strip([("IDEL", "idel_%03d_%s.png" % (i, 150 if 44 <= i <= 58 else 125))
       for i in (14, 18, 22, 26, 46, 49, 52, 55, 58)],
      os.path.join(TMP, "check_idel.png"))

# 躺下过程（SleepA，8 帧全取）
strip([("SleepA", "sleepa_%03d_110.png" % i) for i in range(8)],
      os.path.join(TMP, "check_sleepA.png"))

# 起床过程（SleepC，10 帧取 6）
strip([("SleepC", "sleepc_%03d_110.png" % i) for i in (0, 2, 4, 6, 8, 9)],
      os.path.join(TMP, "check_sleepC.png"))

# 睡眠循环（SleepB，口水只在第 22~33 帧）
strip([("SleepB", "sleepb_%03d_180.png" % i) for i in (0, 12, 22, 26, 30, 34, 40)],
      os.path.join(TMP, "check_sleep.png"))

# 摸头三段：A 完整动作(22) / B 保持(2) / C 收尾(4)
import glob as _glob


def strip_auto(clip, out, cell=200, step=1):
    fs = sorted(_glob.glob(os.path.join(FR, clip, "*.png")))[::step]
    ims = [Image.open(f).convert("RGBA").resize((cell, cell), Image.LANCZOS) for f in fs]
    W, H = cell * len(ims), cell
    c = Image.new("RGBA", (W, H), BG)
    for i, im in enumerate(ims):
        c.alpha_composite(im, (i * cell, 0))
    c.convert("RGB").save(out)
    print(out, c.size, len(ims), "frames")


strip_auto("TouchHeadA", os.path.join(TMP, "check_touchA.png"), cell=175)
strip_auto("TouchHeadB", os.path.join(TMP, "check_touchB.png"), cell=250)
strip_auto("TouchHeadC", os.path.join(TMP, "check_touchC.png"), cell=250)
strip_auto("SleepC", os.path.join(TMP, "check_sleepC.png"), cell=220)

# 被提起：四段（挣扎 + 泪珠）
for _c in ("RaiseA", "RaiseB", "RaiseC", "RaiseDyn"):
    strip_auto(_c, os.path.join(TMP, "check_%s.png" % _c), cell=175)

# 躲边缘：按「窗口被推出屏幕后的可见区」裁剪，才看得出实际露出多少
#   VPet 内部按 500 系算：side#left#219 → 窗口被推出屏幕 219（500 系）
#   可见区 = 500 系 [219,500] = 素材 1000 系 [438,1000]（贴左边缘，露右侧）
#           = 500 系 [0,281]  = 素材 1000 系 [0,562]  （贴右边缘，露左侧）


def hide_strip(clips, out, box, cell_h=300):
    ims = []
    for clip in clips:
        fs = sorted(_glob.glob(os.path.join(FR, clip, "*.png")))
        im = Image.open(fs[len(fs) // 2]).convert("RGBA").crop((box[0], 0, box[1], 1000))
        w = max(1, int(im.width * cell_h / im.height))
        ims.append(im.resize((w, cell_h), Image.LANCZOS))
    W = sum(i.width for i in ims) + 6 * (len(ims) - 1)
    c = Image.new("RGBA", (W, cell_h), (198, 204, 214, 255))    # 浅灰 = 屏幕内桌面
    x = 0
    for im in ims:
        c.alpha_composite(im, (x, 0))
        x += im.width + 6
    c.convert("RGB").save(out)
    print(out, c.size, len(ims), "frames")


hide_strip(["HideLA", "HideLB", "HideLC", "HideLRA", "HideLRB", "HideLRC"],
           os.path.join(TMP, "check_hideL.png"), (438, 1000))
hide_strip(["HideRA", "HideRB", "HideRC", "HideRRA", "HideRRB", "HideRRC"],
           os.path.join(TMP, "check_hideR.png"), (0, 562))


# ---- 几何标定：直接拿原图试不同的 (横躺角, 位移) 组合，看露出的是哪个部位 ----
#   不依赖动画帧，秒出结果；用来定 post_rot / post_dx
def calib(out, combos, box, cell_h=300):
    src = Image.open(os.path.join(TMP, "dino_base.png")).convert("RGBA")
    S = 0.86
    ims = []
    for rot, dx in combos:
        t = src.resize((2000, 2000), Image.LANCZOS)
        a = 1.0 / S                                    # 绕脚底锚点 (1000,1860) 缩小到 S
        t = t.transform((2000, 2000), Image.AFFINE,
                        (a, 0, 1000 - a * 1000, 0, a, 1860 - a * 1860), resample=Image.BICUBIC)
        t = t.rotate(rot, center=(1000, 1000), resample=Image.BICUBIC)
        t = t.transform((2000, 2000), Image.AFFINE,
                        (1, 0, -dx, 0, 1, 0), resample=Image.BICUBIC)
        o = t.resize((1000, 1000), Image.LANCZOS).crop((box[0], 0, box[1], 1000))
        ims.append(o.resize((max(1, int(o.width * cell_h / o.height)), cell_h), Image.LANCZOS))
    W = sum(i.width for i in ims) + 6 * (len(ims) - 1)
    c = Image.new("RGBA", (W, cell_h), (198, 204, 214, 255))
    x = 0
    for im in ims:
        c.alpha_composite(im, (x, 0)); x += im.width + 6
    c.convert("RGB").save(out)
    print(out, c.size, "combos =", combos)


# 贴左边缘：可见区 = 素材右侧 [438,1000]
calib(os.path.join(TMP, "calib_L.png"),
      [(-90, -600), (-90, -400), (-90, -200), (90, 600), (90, 850)],
      (438, 1000))
# 贴右边缘：可见区 = 素材左侧 [0,562]
calib(os.path.join(TMP, "calib_R.png"),
      [(90, 700), (90, 400), (90, 0), (-90, 0), (-90, -400)],
      (0, 562))


# ---- 带可见区标注：完整素材 + 红色边界线，直接看出头落在哪 ----
def annotate(out, combos, box, cell=420):
    from PIL import ImageDraw
    src = Image.open(os.path.join(TMP, "dino_base.png")).convert("RGBA")
    S = 0.86
    tiles = []
    for rot, dx in combos:
        t = src.resize((2000, 2000), Image.LANCZOS)
        a = 1.0 / S
        t = t.transform((2000, 2000), Image.AFFINE,
                        (a, 0, 1000 - a * 1000, 0, a, 1860 - a * 1860), resample=Image.BICUBIC)
        t = t.rotate(rot, center=(1000, 1000), resample=Image.BICUBIC)
        t = t.transform((2000, 2000), Image.AFFINE, (1, 0, -dx, 0, 1, 0), resample=Image.BICUBIC)
        o = t.resize((1000, 1000), Image.LANCZOS)
        bg = Image.new("RGBA", (1000, 1000), (248, 250, 252, 255))
        bg.alpha_composite(o)
        d = ImageDraw.Draw(bg)
        for xx in (box[0], box[1] - 1):
            d.line([(xx, 0), (xx, 999)], fill=(230, 50, 50, 255), width=6)
        tiles.append(bg.resize((cell, cell), Image.LANCZOS))
    W = cell * len(tiles) + 6 * (len(tiles) - 1)
    c = Image.new("RGBA", (W, cell), (255, 255, 255, 255))
    x = 0
    for im in tiles:
        c.alpha_composite(im, (x, 0)); x += cell + 6
    c.convert("RGB").save(out)
    print(out, c.size, "combos =", combos)


# 红线之间 = 屏幕内可见区；红线外 = 被推出屏幕看不见
# 目标：脸朝屏幕内 → 贴左用 +90（嘴朝右），贴右用 -90（嘴朝左）
annotate(os.path.join(TMP, "ann_L.png"),
         [(90, 800), (90, 1000), (90, 600)], (438, 1000))
annotate(os.path.join(TMP, "ann_R.png"),
         [(-90, -800), (-90, -1000), (-90, -600)], (0, 562))

# ---- 验证 PIL rotate 的方向（上→左 还是 上→右）----
from PIL import ImageDraw as _ID
_t = Image.new("RGBA", (200, 200), (240, 240, 240, 255))
_d = _ID.Draw(_t)
_d.rectangle([80, 10, 120, 60], fill=(255, 0, 0))       # 顶部红块
_d.rectangle([80, 140, 120, 190], fill=(0, 90, 255))    # 底部蓝块
_shot = Image.new("RGB", (3 * 200 + 20, 200), (255, 255, 255))
for _i, _a in enumerate((0, 90, -90)):
    _shot.paste(_t.rotate(_a).convert("RGB"), (_i * 210, 0))
_shot.save(os.path.join(TMP, "rot_dir.png"))
print("rot_dir.png 从左到右 = 原图 / rotate(90) / rotate(-90)")
