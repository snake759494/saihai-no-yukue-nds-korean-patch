"""설명 텍스처(1572~1762) ↔ 인물 사전 설명문 매칭."""
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation
sys.path.insert(0, __import__('os').path.dirname(__file__))
import ld, auxfmt
from pathlib import Path
W = Path(__file__).resolve().parent.parent
F = ld.load()
r, _ = auxfmt.p711(F[711])
descs = []
for n, x in enumerate(r):
    ss = bytes(x[8:]).rstrip(b'\0').split(b'\0')
    if len(ss) > 1: descs.append((n, ss[1].decode('cp932')))
fnt = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 12)
def rend(t):
    im = Image.new('L', (256, 64)); d = ImageDraw.Draw(im)
    for i, l in enumerate(t.split('\n')): d.text((4, 5 + 14*i), l, font=fnt, fill=255)
    return np.array(im) > 100
R = [(n, t, rend(t), binary_dilation(rend(t))) for n, t in descs]
def tex(d):
    a = np.frombuffer(d, np.uint8); p = np.empty(a.size*2, np.uint8); p[0::2] = a & 15; p[1::2] = a >> 4
    return p.reshape(64, 256)
res = {}
for i in range(1572, 1763):
    m = tex(F[i]) == 2; md = binary_dilation(m)
    best = max(R, key=lambda c: (m & c[3]).sum() + (c[2] & md).sum() - 0.5*((m & ~c[3]).sum() + (c[2] & ~md).sum()))
    res[i] = best[0]
json.dump(res, open(W / 'translation/graphics/desc_map.json', 'w'))
print(len(res), res[1572], res[1573])
