# -*- coding: utf-8 -*-
"""db4_cut.py — 最终版：抠图 + 对齐 + 色彩校准 + ★宽度收 4% + ★倾斜扭正

在 pose_cut2 基础上新增两处修复（用户确认）：
  3. 宽度收 4%：首帧 W/H 由 0.73 → 0.702（对齐原版站立素材）
  4. 倾斜扭正：把每帧旋转回站立基准角（-0.79°），消除 B 段"斜着站"观感
"""
import os, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage

TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
SRC = os.path.join(TMP, "db4_frames")
OUT = os.path.join(TMP, "db4_cut")
os.makedirs(OUT, exist_ok=True)

CANVAS = 1000
TARGET_FEET_Y = 930
BASE_H = 859
BG_DIST = 55
FG_SOFT = 90
WIDTH_K = 1.0            # ★ 修复3：宽度不再额外收（上一版 0.958 叠加扭正后过瘦）
REF_ANGLE = -0.79        # ★ 修复4：站立基准倾角（f1 实测）

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
    k_r = bg[0]/max(bg[1],1.0); k_b = bg[2]/max(bg[1],1.0)
    r,g,bch = a[:,:,0],a[:,:,1],a[:,:,2]
    gmax = (g>=r)&(g>=bch)&(g>40)
    rg = r/np.maximum(g,1.0); bgk = bch/np.maximum(g,1.0)
    greenlike = gmax & (np.abs(rg-k_r)<0.14) & (np.abs(bgk-k_b)<0.14)
    fg = (d>BG_DIST) & (~greenlike)
    lab,n = ndimage.label(fg)
    if n>1:
        sizes = ndimage.sum(fg,lab,range(1,n+1)); mx = sizes.max()
        keep = np.zeros(n+1,bool)
        for i,s in enumerate(sizes,1):
            if s>=mx*0.30: keep[i]=True
        fg = keep[lab]
    alpha = np.clip((d-(BG_DIST-15))/float(FG_SOFT-BG_DIST+15),0,1)*fg
    return np.array(im).astype(float), alpha


def color_calib(rgb, alpha):
    r,g,b = rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    solid = alpha > 0.6
    m = solid & (r>g+60) & (r>b+60)
    c = solid & (r>200)&(g>190)&(b>170)&(np.abs(r-g)<50)
    o = solid & (r>g+30)&(g>b+40)&(g<200)&(~m)
    out = rgb.copy()
    for msk, tgt in [(m,TGT_RED),(c,TGT_CREAM),(o,TGT_ORANGE)]:
        if msk.sum() < 30: continue
        cur = rgb[msk].mean(axis=0)
        k = np.clip(tgt/np.maximum(cur,1.0), 0.95, 1.25)
        k = 1.0 + (k-1.0)*0.92
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


def body_angle(a):
    """头顶区中点 与 脚底区中点 的连线倾角（度）"""
    al = a[...,3]
    ys,xs = np.where(al>80)
    if len(ys)==0: return 0.0
    y0,y1 = ys.min(), ys.max()
    h = max(1, y1-y0)
    tm = ys <= y0+int(h*0.10)
    bm = ys >= y1-int(h*0.10)
    tx = xs[tm].mean(); bx = xs[bm].mean()
    return np.degrees(np.arctan2(tx-bx, h))


def medfilt1(x,k=5):
    x = np.asarray(x,float); n=len(x); out=x.copy(); h=k//2
    for i in range(n):
        lo,hi = max(0,i-h),min(n,i+h+1)
        out[i] = np.median(x[lo:hi])
    return out


files = sorted(glob.glob(os.path.join(SRC,"f_*.png")))
print("frames:", len(files))

raws, alphas, mets, angs = [], [], [], []
for fp in files:
    rgb, al = cut_one(fp)
    raws.append(rgb); alphas.append(al)
    tmp = np.dstack([rgb, al*255]).astype(np.uint8)
    mets.append(metrics(tmp))
    angs.append(body_angle(tmp))

good = [m for m in mets if m]
hs = np.array([m[3]-m[1]+1 for m in good])
ws = np.array([m[2]-m[0]+1 for m in good])
H_MED, W_MED = float(np.median(hs)), float(np.median(ws))
print("H med=%.0f  W med=%.0f  角度范围 %.2f~%.2f" % (H_MED, W_MED, min(angs), max(angs)))

cx_raw = np.array([m[4] for m in mets],float)
cx_sm = medfilt1(cx_raw,5)
ang_sm = medfilt1(np.array(angs,float), 5)     # 角度也平滑，避免逐帧抖

infos = []
for i,(rgb,al,m) in enumerate(zip(raws,alphas,mets)):
    if m is None: continue
    x0,y0,x1,y1,_ = m
    cw,ch = x1-x0+1, y1-y0+1
    s = BASE_H/float(ch)
    # 宽度完全对齐中位宽 + 全局收 4.2%
    sx_ratio = W_MED/float(cw)
    s_x = s * (1.0 + 1.0*(sx_ratio-1.0)) * WIDTH_K
    nw,nh = max(1,int(round(cw*s_x))), max(1,int(round(ch*s)))

    sub_rgb = rgb[y0:y1+1, x0:x1+1]
    sub_al  = al[y0:y1+1, x0:x1+1]
    img = Image.fromarray(
        np.dstack([np.clip(sub_rgb,0,255).astype(np.uint8),(sub_al*255).astype(np.uint8)]),
        "RGBA").resize((nw,nh), Image.LANCZOS)

    # ★ 修复4：倾斜扭正（闭环：扭正后再量一次，补掉旋转引入的残差）
    delta = angs[i] - REF_ANGLE
    if abs(delta) > 0.10:
        img = img.rotate(delta, resample=Image.BICUBIC, center=(nw/2, nh*0.985), expand=False)
        # 闭环复测 + 补偿（最多 2 轮）
        for _ in range(2):
            a_chk = np.array(img)
            al_c = a_chk[...,3]
            ys_c,xs_c = np.where(al_c>80)
            if len(ys_c)<10: break
            y0c,y1c = ys_c.min(), ys_c.max(); hc = max(1,y1c-y0c)
            tmc = ys_c<=y0c+int(hc*0.10); bmc = ys_c>=y1c-int(hc*0.10)
            residual = np.degrees(np.arctan2(xs_c[tmc].mean()-xs_c[bmc].mean(), hc)) - REF_ANGLE
            if abs(residual) < 0.25: break
            img = img.rotate(residual, resample=Image.BICUBIC,
                             center=(nw/2, nh*0.985), expand=False)

    a2 = np.array(img).astype(float)
    nrgb = color_calib(a2[...,:3], a2[...,3]/255.0)
    img = Image.fromarray(np.dstack([np.clip(nrgb,0,255).astype(np.uint8), a2[...,3].astype(np.uint8)]),"RGBA")

    # 扭正后重新量边界（旋转会改变 bbox），并按新 bbox 居中
    aa = np.array(img); al2 = aa[...,3]
    ys2,xs2 = np.where(al2>60)
    bx0,by0,bx1,by1 = xs2.min(),ys2.min(),xs2.max(),ys2.max()

    # 水平：用平滑重心换算（保持转身时的连贯），叠加 bbox 居中兜底
    cx_new = (cx_sm[i]-x0)*s_x
    px = int(round(500 - cx_new)) + int(round((nw - (bx1-bx0+1))/2.0 - bx0))
    py = int(round(TARGET_FEET_Y - by1))
    px = max(0,min(CANVAS-nw,px)); py = max(0,min(CANVAS-nh,py))
    canvas = Image.new("RGBA",(CANVAS,CANVAS),(0,0,0,0))
    canvas.alpha_composite(img,(px,py))
    canvas.save(os.path.join(OUT,"t_%03d.png"%i))
    infos.append(dict(i=int(i),ang_raw=round(float(angs[i]),2),ang_sm=round(float(ang_sm[i]),2),
                      delta=round(float(delta),2),out_w=int(nw),out_h=int(nh),px=int(px),py=int(py)))
    if i%20==0:
        print("  f%-4d ang=%+.2f delta=%+.2f  %dx%d" % (i+1,angs[i],delta,nw,nh))

json.dump(infos,open(os.path.join(TMP,"db4_info.json"),"w"),indent=1)
print("aligned:",len(infos),"->",OUT)
