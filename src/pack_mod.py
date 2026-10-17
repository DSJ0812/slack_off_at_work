# -*- coding: utf-8 -*-
"""pack_mod.py — 把恐龙素材打包成 VPet 独立 mod（硬链接，不占额外空间）
产出: <VPet>/mod/dino/{info.lps, pet/dino.lps, pet/dino/...}
"""
import os, re, shutil, sys

VP  = r"D:/softapp/Steam/steamapps/common/VPet"
SRC = os.path.join(VP, "mod", "0000_core", "pet", "vup")
LPS = os.path.join(VP, "mod", "0000_core", "pet", "vup.lps")
MOD = os.path.join(VP, "mod", "dino")
DST = os.path.join(MOD, "pet", "dino")
FR  = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/dino_anim/frames"

if not os.path.isdir(SRC):
    sys.exit("找不到原版素材目录: " + SRC)
if not os.path.isdir(FR):
    sys.exit("找不到帧目录: " + FR)

# ---- 清空目标（幂等） ----
if os.path.isdir(MOD):
    shutil.rmtree(MOD)
os.makedirs(os.path.join(MOD, "pet"), exist_ok=True)

# ---- 读入我们的帧 ----
OUR = {}
for name in os.listdir(FR):
    d = os.path.join(FR, name)
    if not os.path.isdir(d):
        continue
    items = []
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(".png"):
            continue
        m = re.search(r"_(\d+)\.png$", f)
        items.append((os.path.join(d, f), int(m.group(1)) if m else 125))
    if items:
        OUR[name] = items
print("载入动画:", {k: len(v) for k, v in OUR.items()})


def pick_clip(rel):
    p = rel.replace("\\", "/")
    top = p.split("/")[0]
    if top in ("Sleep", "Touch_Head", "StartUP", "Shutdown"):
        return top
    if top == "MOVE":
        sub = p.split("/")[1] if "/" in p else ""
        return "MOVE_left" if "left" in sub else "MOVE_right"
    return "IDEL"


# ---- 遍历原版结构，硬链接我们的帧 ----
n_link = n_copy = n_skip = 0
usage = {}
for root, dirs, files in os.walk(SRC):
    rel = os.path.relpath(root, SRC)
    if rel == ".":
        continue
    outdir = os.path.join(DST, rel)
    os.makedirs(outdir, exist_ok=True)
    clip = pick_clip(rel)
    frames = OUR[clip]
    for f in files:
        if not f.lower().endswith(".png"):
            n_skip += 1
            continue
        m = re.search(r"_(\d+)_(\d+)\.png$", f, re.I) or re.search(r"_(\d+)\.png$", f, re.I)
        idx = int(m.group(1)) if m else 0
        src, dur = frames[idx % len(frames)]
        newf = re.sub(r"_\d+(\.png)$", r"_%d\1" % dur, f, flags=re.I)
        dst = os.path.join(outdir, newf)
        if os.path.exists(dst):
            os.remove(dst)
        try:
            os.link(src, dst)
            n_link += 1
        except OSError:
            shutil.copy2(src, dst)
            n_copy += 1
        usage[clip] = usage.get(clip, 0) + 1

print("硬链接 %d 个, 复制 %d 个, 跳过非 PNG %d 个" % (n_link, n_copy, n_skip))
print("各动画被复用次数:", usage)

# ---- 写角色定义 pet/dino.lps（复制原版，改 pet 名 + 热区） ----
txt = open(LPS, encoding="utf-8-sig").read()
rep = [
    ("pet#vup:|intor#虚拟主播模拟器默认人物形象:|path#vup:|petname#萝莉斯:|",
     "pet#dino:|intor#Q版红色小恐龙:|path#dino:|petname#小恐龙:|"),
    ("tag#all,vup,girl:|", "tag#all,dino:|"),
    ("touchhead:|px#159:|py#16:|sw#189:|sh#178:|",
     "touchhead:|px#104:|py#35:|sw#291:|sh#215:|"),
    ("touchbody:|px#166:|py#206:|sw#163:|sh#136:|",
     "touchbody:|px#125:|py#250:|sw#235:|sh#150:|"),
    ("pinch:|px#149:|py#128:|sw#56:|sh#59:|",
     "pinch:|px#140:|py#200:|sw#160:|sh#50:|"),
    ("raisepoint:|happy_x#290:|happy_y#128:|nomal_x#290:|nomal_y#128:|"
     "poorcondition_x#290:|poorcondition_y#128:|ill_x#225:|ill_y#115:|",
     "raisepoint:|happy_x#250:|happy_y#30:|nomal_x#250:|nomal_y#30:|"
     "poorcondition_x#250:|poorcondition_y#30:|ill_x#230:|ill_y#30:|"),
]
miss = []
for a, b in rep:
    if a in txt:
        txt = txt.replace(a, b)
    else:
        miss.append(a[:24])
open(os.path.join(MOD, "pet", "dino.lps"), "w", encoding="utf-8").write(txt)
print("dino.lps 已写；未匹配的替换项:", miss if miss else "无")

# ---- 写 mod 描述 info.lps ----
info = """vupmod#Dino:|author#Lenovo:|gamever#11000:|ver#10000:|
intro#Q版红色小恐龙桌面宠物:|一只圆滚滚、又萌又害羞的小恐龙|
authorid#0:|
itemid#2:|
cachedate#2026/10/04:|
lang#en:|A chubby shy red dino desktop pet#A chubby shy red dino desktop pet:|Dino#Dino:|
lang#zh-Hans:|Q版红色小恐龙桌面宠物#Q版红色小恐龙桌面宠物:|小恐龙#小恐龙:|
"""
open(os.path.join(MOD, "info.lps"), "w", encoding="utf-8").write(info)
print("info.lps 已写")

# ---- 校验 ----
tot = sum(len(fs) for _, _, fs in os.walk(DST))
print("\nmod 目录:", MOD)
print("生成文件总数:", tot)
print("磁盘占用:", end=" ")
os.system('du -sh "%s" 2>/dev/null' % MOD.replace("\\", "/"))
