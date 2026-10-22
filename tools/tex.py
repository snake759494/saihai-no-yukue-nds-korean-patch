"""선형 4bpp 텍스처 한글 다시 그리기 공용 도구."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import font as _font
W = Path(__file__).resolve().parent.parent
FD = W.parent
_B = {}
def bdf(n):
    if n not in _B: _B[n] = _font.read_bdf(str(W / f'fonts/galmuri/{n}.bdf'))
    return _B[n]
def dec(d, w=256):
    h = len(d) * 2 // w
    return [[(d[(y*w+x)//2] >> (4*(x&1))) & 15 for x in range(w)] for y in range(h)]
def enc(px):
    w = len(px[0]); o = bytearray(len(px) * w // 2)
    for y, r in enumerate(px):
        for x in range(0, w, 2): o[(y*w+x)//2] = r[x] | r[x+1] << 4
    return bytes(o)
def bdf_mask(s, name='Galmuri11', sx=1):
    """글자 → (점 집합, 폭, 높이). 줄바꿈 없음."""
    g = bdf(name); asc = {'Galmuri11': 12, 'Galmuri11-Bold': 12, 'Galmuri11-Condensed': 12, 'Galmuri9': 10, 'Galmuri7': 8, 'Galmuri14': 15}[name]
    x = 0; pts = set()
    for c in s:
        gl = g.get(ord(c)) or g[0x3f]
        for (a, b) in _font.bitmap(gl, asc):
            for k in range(sx): pts.add((x + a*sx + k, b))
        x += gl['dw'] * sx
    ys = [b for _, b in pts] or [0]
    return pts, x, asc
def ttf_mask(s, path, size, thr=110):
    f = ImageFont.truetype(str(path), size)
    bb = f.getbbox(s); w = bb[2] + 2; h = size + 6
    im = Image.new('L', (w, h)); ImageDraw.Draw(im).text((0, 0), s, font=f, fill=255)
    pts = {(x, y) for y in range(h) for x in range(w) if im.getpixel((x, y)) > thr}
    return pts, bb[2], size
def put(px, pts, x0, y0, fg, sh=None, ol=None, clip=None):
    H, Wd = len(px), len(px[0])
    def ok(x, y):
        if not (0 <= x < Wd and 0 <= y < H): return False
        if clip and not (clip[0] <= x < clip[0]+clip[2] and clip[1] <= y < clip[1]+clip[3]): return False
        return True
    if ol is not None:
        for (a, b) in pts:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    X, Y = x0+a+dx, y0+b+dy
                    if (a+dx, b+dy) not in pts and ok(X, Y): px[Y][X] = ol
    if sh is not None:
        for (a, b) in pts:
            X, Y = x0+a+1, y0+b+1
            if (a+1, b+1) not in pts and ok(X, Y): px[Y][X] = sh
    for (a, b) in pts:
        if ok(x0+a, y0+b): px[y0+b][x0+a] = fg
def fill(px, r, v):
    x, y, w, h = r
    for Y in range(y, y+h):
        for X in range(x, x+w):
            if 0 <= Y < len(px) and 0 <= X < len(px[0]): px[Y][X] = v
def replace(px, r, vals, v):
    x, y, w, h = r
    for Y in range(y, y+h):
        for X in range(x, x+w):
            if px[Y][X] in vals: px[Y][X] = v
def text(px, r, s, name='Galmuri11', fg=2, sh=None, ol=None, align='l', lh=None, sx=1, valign='t'):
    lines = s.split('\n')
    x, y, w, h = r
    for name2 in [name, 'Galmuri11-Condensed', 'Galmuri9', 'Galmuri7']:
        ms = [bdf_mask(l, name2, sx) for l in lines]
        if max(m[1] for m in ms) <= w: break
    lh = lh or (ms[0][2] + 2)
    tot = lh * len(lines)
    yy = y + (h - tot)//2 if valign == 'c' else y
    for i, (pts, lw, asc) in enumerate(ms):
        xx = x + (w - lw)//2 if align == 'c' else (x + w - lw if align == 'r' else x)
        put(px, pts, xx, yy + i*lh - (asc - 11 if asc > 11 else 0) - 1, fg, sh, ol)
