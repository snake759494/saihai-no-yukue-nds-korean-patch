"""256×16 텍스처(2048바이트) ↔ 원문 문자열 자동 매칭."""
import sys, json, glob, re
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).parent))
import ld, auxfmt
W = Path(__file__).resolve().parent.parent
F = ld.load()
fnt = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 12)
def tmask(d):
    a = np.frombuffer(d, np.uint8); p = np.empty(a.size*2, np.uint8); p[0::2] = a & 15; p[1::2] = a >> 4
    return p.reshape(16, 256)
def crop(m):
    ys, xs = np.nonzero(m)
    if not len(xs): return None
    return m[ys.min():ys.max()+1, xs.min():xs.max()+1]
cands = set()
for f in glob.glob(str(W / 'translation/src/*.json')):
    for u in json.load(open(f, encoding='utf8')):
        t = u['ja']
        if '\n' not in t and len(t) <= 26 and '【' not in t: cands.add(t)
r, _ = auxfmt.p711(F[711])
names = {}
for x in r:
    s0 = bytes(x[8:]).split(b'\0')[0].decode('cp932')
    m = re.match(r'(.+)（(.+)）$', s0)
    if m: names[m.group(1) + '　' + m.group(2)] = s0; cands.add(m.group(1) + '　' + m.group(2))
cands = sorted(cands)
rend = {}
for t in cands:
    im = Image.new('L', (400, 16)); ImageDraw.Draw(im).text((0, 1), t, font=fnt, fill=255)
    m = np.array(im) > 100
    c = crop(m)
    if c is not None: rend[t] = c
ids = [i for i in list(range(1303, 1574)) + list(range(4918, 5263)) if len(F[i]) == 2048]
import cv2
def feat(m, w, h):
    f = cv2.resize(m.astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)
    f = cv2.GaussianBlur(f, (3, 3), 0.8); f -= f.mean(); n = np.linalg.norm(f)
    return f / n if n else f
RF = {t: (rm.shape[1], rm.shape[0]) for t, rm in rend.items()}
res = {}
for i in ids:
    px = tmask(F[i]); vals = np.bincount(px.ravel(), minlength=16)
    best = (-1e9, None, None)
    for core in [int(v) for v in np.nonzero(vals[1:])[0] + 1]:
        cm = crop(px == core)
        if cm is None or cm.sum() < 15: continue
        h, w = cm.shape
        if w < 6: continue
        fa = feat(cm, 96, 12)
        for t, rm in rend.items():
            rw, rh = RF[t]
            if abs(rw - w) > max(4, w*0.08): continue
            sc = float((fa * feat(rm, 96, 12)).sum())
            if sc > best[0]: best = (sc, t, core)
    res[i] = {'ja': names.get(best[1], best[1]), 'score': round(best[0], 3), 'core': best[2]}
json.dump(res, open(W / 'translation/graphics/tex2k_map.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
sc = sorted(v['score'] for v in res.values())
print(len(res), sc[:20], sum(1 for s in sc if s < 0.5))
