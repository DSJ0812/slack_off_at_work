# -*- coding: utf-8 -*-
"""pose_cut2.py — 抠绿底 + 对齐 + ★色彩校准（修"变胖"和"变暗"）

相比 pose_cut.py 的两处修复：
  1. 变胖：宽度归一权重 0.45 → 1.0（完全对齐中位宽度，消除 24px 形变残留）
  2. 变暗：分部位色彩映射，把 红身/米白肚/橙刺 拉齐到现有素材标准色
"""
import os, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "pose_frames")
OUT = os.path.join(TMP, "pose_cut2")
os.makedirs(OUT, exist_ok=True)

CANVAS = 1000
TARGET_FEET_Y = 930
BASE_H = 859
BG_DIST = 55
FG_SOFT = 90

# ★ 目标标准色（取自现有代码绘制素材 Default/_000_125.png）
TGT_RED    = np.array([244.0, 67.0, 63.0])
TGT_CREAM  = np.array([254.0, 233.0, 204.0])
TGT_ORANGE = np.array([245.0, 134.0, 40.0])


def bg_color(im):
    a = np.array(im).astype(float)
    corners = np.concatenate([
        a[:20,:20].reshape(-1,3), a[:20,-20:].reshape(-1,3),
        a[-20:,:20].reshape(-1,3), a[-20:,-20:].reshape(-1,3)])
    return np.median(corners, axis=0)


def cut_one(fp):
    im = Image.open(fp).convert("RGB")
    bg = bg_color(im)
    a = np.array(im).astype(float)
    d = np.sqrt(((a-bg)**2).sum(axis=2))
    bg_r,bg_g,bg_b = float(bg[0]),float(bg[1]),float(bg[2])
    k_r = bg_r/max(bg_g,1.0); k_b = bg_b/max(bg_g,1.0)
    r,g,bch = a[:,:,0],a[:,:,1],a[:,:,2]
    gmax = (g>=r)&(g>=bch)&(g>40)
    rg = r/np.maximum(g,1.0); bgk = bch/np.maximum(g,1.0)
    greenlike = gmax & (np.abs(rg-k_r)<0.14) & (np.abs(bgk-k_b)<0.14)
    fg = (d>BG_DIST) & (~greenlike)
    lab,n = ndimage.label(fg)
    if n>1:
        sizes = ndimage.sum(fg,lab,range(1,n+1))
        mx = sizes.max()
        keep = np.zeros(n+1,bool)
        for i,s in enumerate(sizes,1):
            if s>=mx*0.30: keep[i]=True
        fg = keep[lab]
    alpha = np.clip((d-(BG_DIST-15))/float(FG_SOFT-BG_DIST+15),0,1)*fg
    return np.array(im).astype(float), alpha


def color_calib(rgb, alpha):
    """★ 分部位色彩映射：把红/米白/橙拉齐到目标标准色
    用「连续权重混合」避免硬分界产生色块。
    """
    r,g,b = rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    solid = alpha > 0.6
    m = solid & (r>g+60) & (r>b+60)                  # 红身
    c = solid & (r>200)&(g>190)&(b>170)&(np.abs(r-g)<50)  # 米白肚
    o = solid & (r>g+30)&(g>b+40)&(g<200)&(~m)       # 橙刺

    out = rgb.copy()
    for msk, tgt in [(m, TGT_RED), (c, TGT_CREAM), (o, TGT_ORANGE)]:
        if msk.sum() < 30: continue
        cur = rgb[msk].mean(axis=0)
        # 逐通道线性缩放系数（带阻尼，避免过冲）
        k = np.clip(tgt/np.maximum(cur,1.0), 0.95, 1.25)
        k = 1.0 + (k-1.0)*0.92          # 阻尼 92%，留 8% 余地
        out[msk] = np.clip(rgb[msk]*k, 0, 255)
    return out


def metrics(a):
    al = a[...,3]
    ys,xs = np.where(al>60)
    if len(ys)==0: return None
    x0,y0,x1,y1 = xs.min(),ys.min(),xs.max(),ys.max()
    w = al[al>60].astype(float)
    cx = float((xs*w).sum()/w.sum())
    return (x0,y0,x1,y1,cx)


def medfilt1(x,k=5):
    x = np.asarray(x,float); n=len(x); out=x.copy(); h=k//2
    for i in range(n):
        lo,hi = max(0,i-h),min(n,i+h+1)
        out[i] = np.median(x[lo:hi])
    return out


files = sorted(glob.glob(os.path.join(SRC,"f_*.png")))
print("frames:", len(files))

raws, alphas, mets = [], [], []
for fp in files:
    rgb, al = cut_one(fp)
    raws.append(rgb); alphas.append(al)
    mets.append(metrics(np.dstack([rgb,al*255]).astype(np.uint8)))

good = [m for m in mets if m]
hs = np.array([m[3]-m[1]+1 for m in good])
ws = np.array([m[2]-m[0]+1 for m in good])
H_MED, W_MED = float(np.median(hs)), float(np.median(ws))
print("H med=%.0f (%d~%d)  W med=%.0f (%d~%d)" % (H_MED,hs.min(),hs.max(),W_MED,ws.min(),ws.max()))

cx_raw = np.array([m[4] for m in mets],float)
cx_sm = medfilt1(cx_raw,5)

infos = []
for i,(rgb,al,m) in enumerate(zip(raws,alphas,mets)):
    if m is None: continue
    x0,y0,x1,y1,_ = m
    cw,ch = x1-x0+1, y1-y0+1
    s = BASE_H/float(ch)
    # ★ 修复1：宽度完全归一到中位宽（原 0.45 → 1.0），消除"变胖变瘦"
    sx_ratio = W_MED/float(cw)
    s_x = s * (1.0 + 1.0*(sx_ratio-1.0))
    nw,nh = max(1,int(round(cw*s_x))), max(1,int(round(ch*s)))

    # 裁切并缩放
    sub_rgb = rgb[y0:y1+1, x0:x1+1]
    sub_al  = al[y0:y1+1, x0:x1+1]
    img_rgb = Image.fromarray(np.clip(sub_rgb,0,255).astype(np.uint8),"RGB").resize((nw,nh), Image.LANCZOS)
    img_al  = Image.fromarray((sub_al*255).astype(np.uint8),"L").resize((nw,nh), Image.LANCZOS)
    nrgb = np.array(img_rgb).astype(float)
    nal  = np.array(img_al).astype(float)/255.0

    # ★ 修复2：色彩校准（在缩放后做，此时像素最干净）
    nrgb = color_calib(nrgb, nal)

    cx_new = (cx_sm[i]-x0)*s_x
    px = int(round(500-cx_new)); py = int(round(TARGET_FEET_Y-nh))
    px = max(0,min(CANVAS-nw,px))
    canvas = Image.new("RGBA",(CANVAS,CANVAS),(0,0,0,0))
    layer = Image.fromarray(np.dstack([np.clip(nrgb,0,255).astype(np.uint8),(nal*255).astype(np.uint8)]),"RGBA")
    canvas.alpha_composite(layer,(px,py))
    canvas.save(os.path.join(OUT,"t_%03d.png"%i))
    infos.append(dict(i=int(i),out_w=int(nw),out_h=int(nh),px=int(px),py=int(py)))
    if i%25==0:
        print("  %3d %dx%d -> %dx%d px=%d" % (i,cw,ch,nw,nh,px))

json.dump(infos,open(os.path.join(TMP,"pose_info2.json"),"w"),indent=1)
print("aligned:",len(infos),"->",OUT)
