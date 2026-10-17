# -*- coding: utf-8 -*-
"""pack_full.py — 把恐龙完整帧集铺进 VPet pet 目录（每个目录放该动画类的全部帧）

与旧版 pack_mod.py 的关键区别：
  旧版按「原版该目录的文件数」取模铺帧 → 40 帧的待机被砍成 8 帧，歪头被截断、打哈欠整段丢失。
  新版每个目录直接放「该动画类的完整帧集」，帧数不受原版限制。

目标目录需事先不存在（由外层先 mv 走旧目录），保证零删除。
"""
import os
import sys

PET = r"D:/softapp/VPet_dino/VPet/mod/0000_core/pet"
SRC_VUP = os.path.join(PET, "vup")          # 原版目录结构模板
FR = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/dino_anim3/frames"
DST = os.path.join(PET, sys.argv[1] if len(sys.argv) > 1 else "dino")

# ---- 读入新帧 ----
CLIPS = {}
for name in sorted(os.listdir(FR)):
    d = os.path.join(FR, name)
    if os.path.isdir(d):
        CLIPS[name] = sorted(os.path.join(d, f) for f in os.listdir(d)
                             if f.lower().endswith(".png"))
for k, v in CLIPS.items():
    print("clip %-12s %2d frames" % (k, len(v)))

# ---- 扫描原版目录结构，记录「本身直接含 PNG」的目录 ----
# 原版 vup/ 里所有 PNG 都在叶子目录，顶层目录（Default/IDEL/Sleep/MOVE…）的根不含 PNG。
# 若给这些根目录也铺帧，会凭空造出 Type=X + Animat=Single 的多余动画，导致 VPet 匹配串台。
HAS_PNG = set()
for root, _dirs, files in os.walk(SRC_VUP):
    if any(f.lower().endswith(".png") for f in files):
        HAS_PNG.add(os.path.relpath(root, SRC_VUP).replace("\\", "/"))
print("原版直接含 PNG 的目录数：%d" % len(HAS_PNG))


CORE = ("Default", "IDEL", "MOVE", "Sleep", "Touch_Head", "Touch_Body",
        "Pinch", "Raise", "StartUP", "Shutdown", "Switch",
        "SideHide_Left_Main", "SideHide_Left_Rise",
        "SideHide_Right_Main", "SideHide_Right_Rise")


def seg_of(rel):
    """取路径中最后一个 A/B/C 段，用于区分 开始/循环/结束 三段动画。

    兼容两种写法：
      Touch_Head/A_Nomal  -> 二级目录名以 a_ 开头
      Touch_Head/Happy/A  -> 三级目录名是纯 A/B/C
    无段名（如 Touch_Head/Happy 根目录、Sleep 顶层）返回 ""。
    """
    for part in reversed(rel.replace("\\", "/").split("/")):
        p = part.lower()
        if p in ("a", "start") or p.startswith("a_"):
            return "A"
        if p in ("b", "loop") or p.startswith("b_"):
            return "B"
        if p in ("c", "end") or p.startswith("c_"):
            return "C"
    return ""


def frames_for(rel):
    """该目录应铺的帧列表。核心动画类给完整帧集；其余类只给 IDEL 前 8 帧，控制文件总数。"""
    r = rel.replace("\\", "/")
    if r not in HAS_PNG:
        return []                           # 原版该目录不含 PNG → 不铺，保持结构一致
    top = r.split("/")[0]
    if top == "Sleep":                      # 三段式：A 躺下 / B 睡眠循环 / C 起床
        return CLIPS["Sleep" + (seg_of(r) or "B")]
    if top == "Touch_Head":                 # 三段式：A 完整动作 / B 保持 / C 收尾
        seg = seg_of(r)
        return CLIPS["TouchHead" + seg] if seg else []
    if top == "Touch_Body":                 # 三段式：A 缩一下 / B 左右躲闪 / C 收住
        seg = seg_of(r)
        return CLIPS["TouchBody" + seg] if seg else []
    if top == "Pinch":                      # 三段式：A 被捏 / B 憋气 / C 喷火
        seg = seg_of(r)
        return CLIPS["Pinch" + seg] if seg else []
    if top == "Raise":                      # Raised_Static 三段 / Raised_Dynamic 摇晃
        if "dynamic" in r.lower():
            return CLIPS["RaiseDyn"]
        return CLIPS["Raise" + (seg_of(r) or "B")]
    if top.startswith("SideHide_"):         # A 缩起来 / B 缩着 / C 回正（Rise 段为探头）
        seg = seg_of(r) or "B"
        if "Right" in top:
            pre = "HideRR" if "Rise" in top else "HideR"
        else:
            pre = "HideLR" if "Rise" in top else "HideL"
        return CLIPS[pre + seg]
    if top in ("StartUP", "Shutdown"):
        return CLIPS[top]
    if top == "MOVE":
        return CLIPS["MOVE_left" if "left" in r else "MOVE_right"]
    if top in CORE:
        return CLIPS["IDEL"]
    return CLIPS["IDEL"][:8]


def newname(fp, idx):
    """idel_000_125.png -> _000_125.png（与 VPet 原版命名一致：名字留空）"""
    base = os.path.basename(fp)
    parts = base.rsplit("_", 2)
    dur = parts[-1].split(".")[0]
    return "_%03d_%s.png" % (idx, dur)


n_dirs = n_link = n_stale = 0

# ---- 铺之前：把「原版不含 PNG」的目录里的帧移出去（历史遗留的多余 Single 动画）----
PURGE = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/purged_png"
STALE = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp/stale_frames"
n_purge = 0
for root, _d, files in os.walk(DST):
    rel = os.path.relpath(root, DST).replace("\\", "/")
    if rel in HAS_PNG:
        continue
    for f in files:
        if f.lower().endswith(".png"):
            tgt = os.path.join(PURGE, rel, f)
            os.makedirs(os.path.dirname(tgt), exist_ok=True)
            os.replace(os.path.join(root, f), tgt)
            n_purge += 1
print("清出多余 PNG：%d 个（已归档到 purged_png）" % n_purge)

for root, dirs, files in os.walk(SRC_VUP):
    rel = os.path.relpath(root, SRC_VUP)
    tgt = DST if rel == "." else os.path.join(DST, rel)
    os.makedirs(tgt, exist_ok=True)
    n_dirs += 1
    if rel == ".":
        continue
    frames = frames_for(rel)
    want = set(newname(fp, i) for i, fp in enumerate(frames))
    existing = set(f for f in os.listdir(tgt) if f.lower().endswith(".png"))

    # ★★ 不能只用"文件名集合相同"判断是否跳过！
    #    踩坑记录：豆包版和代码版的 Pinch B 段文件名都是 _000_110.png，
    #    existing == want 成立 → 整个目录被跳过 → 素材永远不更新（用户看到的还是旧帧）。
    #    正确做法：额外比较 inode —— 硬链接的源帧必须与目标帧是同一个 inode。
    def _is_synced():
        if existing != want:
            return False
        for i, fp in enumerate(frames):
            dst = os.path.join(tgt, newname(fp, i))
            try:
                if os.stat(fp).st_ino != os.stat(dst).st_ino:
                    return False        # 内容不同源（inode 不同）→ 需要重新链接
            except OSError:
                return False
        return True

    if _is_synced():
        continue                            # 帧集合 + inode 都一致 → 跳过
    for f in existing - want:
        # 过期/多余的 PNG → 移到归档目录。
        # 注意：不能用 os.remove —— 沙箱的安全删除会尝试把文件移进回收站，
        # 而硬链接无法移入回收站（报 "系统找不到指定的文件"），会导致脚本崩溃。
        _src = os.path.join(tgt, f)
        _dst = os.path.join(STALE, os.path.relpath(_src, DST))
        os.makedirs(os.path.dirname(_dst), exist_ok=True)
        os.replace(_src, _dst)
        n_stale += 1
    for i, fp in enumerate(frames):
        dst = os.path.join(tgt, newname(fp, i))
        need = True
        if os.path.exists(dst):
            try:
                need = os.stat(fp).st_ino != os.stat(dst).st_ino
            except OSError:
                need = True
            if need:
                # 目标帧与源帧不是同一 inode（内容已更新）→ 把旧的移走再重建链接
                _dst = os.path.join(STALE, os.path.relpath(dst, DST))
                os.makedirs(os.path.dirname(_dst), exist_ok=True)
                os.replace(dst, _dst)
        if need:
            os.link(fp, dst)
            n_link += 1

print("\nDONE  dirs=%d  links=%d  过期帧清理=%d" % (n_dirs, n_link, n_stale))
