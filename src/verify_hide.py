# -*- coding: utf-8 -*-
import os, glob
from PIL import Image, ImageDraw
FR = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/dino_anim3/frames"
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
LEFT_BOX  = (438, 0, 1000, 1000)
RIGHT_BOX = (0, 0, 562, 1000)

def cell(clip, idx_ratio, box, h=230):
    fs = sorted(glob.glob(os.path.join(FR, clip, "*.png")))
    if not fs: return None, "无 %s" % clip
    i = min(len(fs)-1, int((len(fs)-1)*idx_ratio))
    im = Image.open(fs[i]).convert("RGBA").crop(box)
    w = max(1, int(im.width*h/im.height))
    im = im.resize((w, h), Image.LANCZOS)
    bg = Image.new("RGB", (w, h), (250,250,252))
    bg.paste(im, (0,0), im)
    return bg, os.path.basename(fs[i])

def board(rows, path):
    ch = 230
    out = Image.new("RGB", (5*250+8, len(rows)*(ch+26)+8), (255,255,255))
    d0 = ImageDraw.Draw(out)
    for r,(lab, clips) in enumerate(rows):
        d0.text((6, r*(ch+26)+4), lab, fill=(0,0,0))
        for c,(clip, ratio, box) in enumerate(clips):
            bg, name = cell(clip, ratio, box)
            if bg is None:
                d0.text((c*250+6, r*(ch+26)+30), name, fill=(200,0,0)); continue
            out.paste(bg, (c*250+4, r*(ch+26)+22))
            d0.text((c*250+4, r*(ch+26)+ch+8), "%s %s" % (clip, name), fill=(80,80,80))
    out.save(path); print("saved", path)

board([
    ("贴左 躺下A(末)",  [("HideLA", 1.0, LEFT_BOX)]),
    ("贴左 躲着B(中)",  [("HideLB", 0.5, LEFT_BOX)]),
    ("贴左 探头RA(末)", [("HideLRA", 1.0, LEFT_BOX)]),
    ("贴左 探头RB(中)", [("HideLRB", 0.5, LEFT_BOX)]),
], os.path.join(TMP, "verify_L.png"))

board([
    ("贴右 躺下A(末)",  [("HideRA", 1.0, RIGHT_BOX)]),
    ("贴右 躲着B(中)",  [("HideRB", 0.5, RIGHT_BOX)]),
    ("贴右 探头RA(末)", [("HideRRA", 1.0, RIGHT_BOX)]),
    ("贴右 探头RB(中)", [("HideRRB", 0.5, RIGHT_BOX)]),
], os.path.join(TMP, "verify_R.png"))
