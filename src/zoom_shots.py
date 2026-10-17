# -*- coding: utf-8 -*-
import os
from PIL import Image
TMP = r"D:/PythonProject/今天你摸鱼了吗/.workbuddy-ai/tmp"
p1 = r"C:/Users/Lenovo/.workbuddy-ai/clipboard-images/clipboard-2026-10-04T10-13-02-877Z-b022d863.jpg"
p2 = r"C:/Users/Lenovo/.workbuddy-ai/clipboard-images/clipboard-2026-10-04T10-13-02-879Z-5ae63df4.jpg"
a = Image.open(p1).convert("RGB"); b = Image.open(p2).convert("RGB")
print("shot1", a.size, " shot2", b.size)

W, H = a.size
z1 = a.crop((0, int(H*0.66), int(W*0.13), H))
z1 = z1.resize((z1.width*5, z1.height*5), Image.LANCZOS)
z1.save(os.path.join(TMP, "zoom_shot1.png"))

W2, H2 = b.size
z2 = b.crop((int(W2*0.86), int(H2*0.63), W2, int(H2*0.95)))
z2 = z2.resize((z2.width*5, z2.height*5), Image.LANCZOS)
z2.save(os.path.join(TMP, "zoom_shot2.png"))
print("saved", z1.size, z2.size)
