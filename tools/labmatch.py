"""전투 지도 부대 이름표(1125~1139, 32×6 칸) ↔ 후보 성씨 자동 대조."""
import sys, json, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, __import__('os').path.dirname(__file__))
import ld, tex
from pathlib import Path
W = Path(__file__).resolve().parent.parent
txt = (W / 'translation/labels/PROMPT.md').read_text(encoding='utf8')
C = dict(re.findall(r'([^\s,→]+)→([^\s,]+)', txt.split('표기):')[1].split('결과')[0]))
F = ld.load()
fnt = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 24)
def cand_img(s, w):
    im = Image.new('L', (24*len(s) + 4, 26)); ImageDraw.Draw(im).text((0, 0), s, font=fnt, fill=255)
    a = np.array(im, np.float32); ys, xs = np.nonzero(a > 80)
    a = a[ys.min():ys.max()+1, xs.min():xs.max()+1]
    return cv2.resize(a, (w, 5), interpolation=cv2.INTER_AREA)
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
            ys, xs = np.nonzero(core)
            core = core[ys.min():ys.max()+1, xs.min():xs.max()+1]
            w = core.shape[1]
            core = cv2.resize(core, (w, 5), interpolation=cv2.INTER_AREA)
            best = []
            for ja, ko in C.items():
                if abs(len(ja) * 8.5 - w) > 7: continue
                sc = float((norm(core) * norm(cand_img(ja, w))).sum())
                best.append((sc, ja, ko))
            best.sort(reverse=True)
            res[f'{i}_{k}_{c}'] = best[:5]
json.dump(res, open(W / 'translation/labels/auto.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
for k, v in list(res.items())[:40]: print(k, [(round(s, 2), j) for s, j, _ in v])
