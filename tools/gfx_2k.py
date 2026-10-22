"""256×16 텍스처(1303~1573, 4918~5262) 한글화."""
import json, glob
import numpy as np
from pathlib import Path
import tex
W = Path(__file__).resolve().parent.parent
def load_map():
    m = {}
    for f in glob.glob(str(W / 'translation/tex2k/out_*.json')):
        m.update({int(k): v for k, v in json.load(open(f, encoding='utf8')).items()})
    return m
def render(orig, s):
    px = tex.dec(orig)
    vals = set(v for r in px for v in r)
    xs = [x for x in range(256) if any(px[y][x] for y in range(16))]
    out = [[0]*256 for _ in range(16)]
    if vals <= {0, 1}:   # 머리말형: 왼쪽 정렬, 단색
        x0 = xs[0] if xs else 4
        tex.text(out, (x0, 2, 252 - x0, 13), s, 'Galmuri11', fg=1)
    else:                # 선택지형: 가운데, 흰 글자+외곽선
        tex.text(out, (2, 2, 252, 14), s, 'Galmuri11-Bold', fg=1, ol=4, align='c')
    return tex.enc(out)
def build(F):
    return {i: render(F[i], s) for i, s in load_map().items()}
