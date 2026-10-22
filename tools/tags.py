"""화자 이름표(1106번, 4bpp 64×16 OBJ, 타일 16개씩) 처리."""
def decode(d, k):
    px = [[0]*64 for _ in range(16)]
    for t in range(16):
        for y in range(8):
            for x in range(8):
                v = (d[(k*16+t)*32 + y*4 + x//2] >> (4*(x&1))) & 15
                px[(t//8)*8+y][(t%8)*8+x] = v
    return px
def encode(d, k, px):
    for t in range(16):
        for y in range(8):
            for x in range(0, 8, 2):
                d[(k*16+t)*32 + y*4 + x//2] = px[(t//8)*8+y][(t%8)*8+x] | px[(t//8)*8+y][(t%8)*8+x+1] << 4
import json, collections
from pathlib import Path
import font as _font
W = Path(__file__).resolve().parent.parent
_G = {}
def _bdf(n):
    if n not in _G: _G[n] = _font.read_bdf(str(W / f'fonts/galmuri/{n}.bdf'))
    return _G[n]
def text_px(s, name, asc):
    g = _bdf(name); x = 0; pts = set()
    for c in s:
        gl = g[ord(c)]
        for (a, b) in _font.bitmap(gl, asc): pts.add((x + a, b))
        x += gl['dw']
    return pts, x
def redraw(px, s, x0=9, maxw=38):
    out = [r[:] for r in px]
    T = {1, 4, 5, 6}
    for y in range(1, 15):
        for x in range(52):
            if px[y][x] in T or (x < 12 and px[y][x] in (2, 3)):
                for dx in range(1, 64):
                    c = [px[y][xx] for xx in (x - dx, x + dx) if 0 <= xx < 64 and px[y][xx] not in T and px[y][xx] > 2]
                    if c: out[y][x] = c[0]; break
    for name, asc in (('Galmuri11', 13), ('Galmuri11-Condensed', 13), ('Galmuri9', 12), ('Galmuri7', 11)):
        pts, w = text_px(s, name, asc)
        if w <= maxw: break
    ys = [b for _, b in pts]; top = min(ys); gh = max(ys) - top + 1
    y0 = 2 + max(0, (12 - gh) // 2)
    for (a, b) in pts:
        Y = y0 + b - top; X = x0 + a - (8 if Y >= 8 else 0)   # 아래 8줄은 타일 한 칸 왼쪽에 저장됨
        if 0 <= X < 64 and 0 <= Y < 15: out[Y][X] = 1
    return out
def build(F):
    N = json.loads((W / 'translation/graphics/tags.json').read_text(encoding='utf8'))
    d = bytearray(F[1106])
    for k, s in N.items():
        k = int(k); encode(d, k, redraw(decode(d, k), s))
    return bytes(d)
