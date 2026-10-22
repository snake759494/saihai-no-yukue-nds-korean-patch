"""부대 이름표 ↔ 원본 화자 이름표(1106) 글자 모양 대조."""
import sys, json
import numpy as np, cv2
sys.path.insert(0, __import__('os').path.dirname(__file__))
import ld, tex, tags
from pathlib import Path
W = Path(__file__).resolve().parent.parent
F = ld.load()
KO = json.loads((W / 'translation/graphics/tags.json').read_text(encoding='utf8'))
def tagmask(k):
    px = tags.decode(F[1106], k)
    disp = [r[:] for r in px]
    for y in range(8, 16): disp[y] = [0]*8 + px[y][:56]
    a = np.array([[1.0 if v == 1 else 0.0 for v in r[:54]] for r in disp[1:15]], np.float32)
    ys, xs = np.nonzero(a)
    return a[ys.min():ys.max()+1, xs.min():xs.max()+1] if len(xs) else None
cand = {}
for k, ko in KO.items():
    m = tagmask(int(k))
    if m is not None: cand[ko] = m
cand['？？？'] = tagmask(37)
def norm(a):
    a = a - a.mean(); n = np.linalg.norm(a); return a / n if n else a
res = {}
for i in range(1125, 1140):
    px = np.array(tex.dec(F[i][:8192]))
    for k in range(10):
        y0 = 1 + 6*k
        if y0 + 6 > 64: break
        for c in range(8):
            blk = px[y0:y0+6, c*32:c*32+32]
            core = (blk == 2).astype(np.float32)
            if core.sum() < 4: continue
            ys, xs = np.nonzero(core); core = core[ys.min():ys.max()+1, xs.min():xs.max()+1]
            h, w = core.shape
            sc = []
            for ko, m in cand.items():
                ratio = m.shape[1] / m.shape[0]
                if abs(ratio * h - w) > max(5, w * 0.35): continue
                r = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
                sc.append((float((norm(core) * norm(r)).sum()), ko))
            sc.sort(reverse=True)
            res[f'{i}_{k}_{c}'] = sc[:3]
json.dump(res, open(W / 'translation/labels/auto2.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
old = {}
import glob
for f in glob.glob(str(W / 'translation/labels/out_*.json')): old.update(json.load(open(f, encoding='utf8')))
agree = sum(1 for k, v in res.items() if v and old.get(k) == v[0][1])
print(len(res), 'agree', agree)
for k, v in list(res.items())[:30]: print(k, old.get(k), [(round(s, 2), n) for s, n in v])
