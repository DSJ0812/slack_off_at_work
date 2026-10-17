# -*- coding: utf-8 -*-
import os, glob
import numpy as np
from PIL import Image
FR = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/dino_anim3/frames"
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"

def load(clip, i):
    fs = sorted(glob.glob(os.path.join(FR, clip, "*.png")))
    return Image.open(fs[i]).convert("RGBA"), len(fs)

for tag, A, B in [("左", "HideLA", "HideLB"), ("右", "HideRA", "HideRB")]:
    ia, na = load(A, -1)          # 末帧
    ib, nb = load(B, 0)            # 首帧
    d = np.abs(np.array(ia).astype(int) - np.array(ib).astype(int))
    print("%s: %s[%d] vs %s[0]  mean=%.2f max=%d" % (tag, A, na-1, B, d.mean(), d.max()))

# 贴左 A段全部8帧 + B段前2帧，横排看过渡
def strip(clips, box, path, h=200):
    ims = []
    for clip, rng in clips:
        fs = sorted(glob.glob(os.path.join(FR, clip, "*.png")))
        for i in rng:
            if i < len(fs):
                ims.append((clip, os.path.basename(fs[i]),
                            Image.open(fs[i]).convert("RGBA").crop(box)))
    out = Image.new("RGB", (len(ims)*170+8, h+34), (255,255,255))
    d0 = ImageDraw.Draw(out) if False else None
    from PIL import ImageDraw
    d0 = ImageDraw.Draw(out)
    for c,(clip,name,im) in enumerate(ims):
        w = max(1,int(im.width*h/im.height))
        im2 = im.resize((w,h), Image.LANCZOS)
        bg = Image.new("RGB",(w,h),(250,250,252)); bg.paste(im2,(0,0),im2)
        out.paste(bg,(c*170+4,28))
        d0.text((c*170+4,8), name.replace(".png",""), fill=(0,0,0))
    out.save(path); print("saved", path)

strip([("HideLA", range(0,8)), ("HideLB", range(0,2))], (438,0,1000,1000),
      os.path.join(TMP, "ab_L.png"))
