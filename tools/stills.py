"""자막 그림(863~982, 256×64 4bpp, 64×64 OBJ 블록 4개) 한글로 다시 그리기."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, str(Path(__file__).parent))
import nitro
W = Path(__file__).resolve().parent.parent
FONT_EB = str(W.parent / 'SeoulHangangEB.ttf'); FONT_M = str(W.parent / 'SeoulHangangM.ttf')
def decode(data):
    px = [[0]*256 for _ in range(64)]
    for b in range(4):
        for t in range(64):
            tt = b*64 + t
            for y in range(8):
                for x in range(8):
                    v = (data[tt*32 + y*4 + x//2] >> (4*(x&1))) & 15
                    px[(t//8)*8+y][b*64 + (t%8)*8 + x] = v
    return px
def encode(px):
    out = bytearray(8192)
    for b in range(4):
        for t in range(64):
            tt = b*64 + t
            for y in range(8):
                for x in range(8):
                    v = px[(t//8)*8+y][b*64 + (t%8)*8 + x]
                    out[tt*32 + y*4 + x//2] |= v << (4*(x&1))
    return bytes(out)
def bbox(px, pred):
    ys = [y for y in range(64) for x in range(256) if pred(px[y][x])]
    xs = [x for y in range(64) for x in range(256) if pred(px[y][x])]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None
def fit_font(path, text, maxw, size):
    while True:
        f = ImageFont.truetype(path, size)
        w = max(f.getbbox(l)[2] for l in text.split('\n'))
        if w <= maxw or size <= 9: return f
        size -= 1
def render_lines(lines, box_w, box_h):
    """lines: [(text, fontpath, size)] → (fill mask, outline mask) 256×64, 4배 확대 후 축소."""
    S = 4
    m = Image.new('L', (256*S, 64*S), 0); d = ImageDraw.Draw(m)
    hs = []; fs = []
    for t, fp, sz in lines:
        f = fit_font(fp, t, 246, sz); fs.append(ImageFont.truetype(fp, f.size * S))
        hs.append(f.size + 2)
    return m, d, fs, hs
def draw(px_orig, text, style):
    bb = bbox(px_orig, lambda v: v != 0) or (0, 0, 255, 24)
    S = 4
    fill = Image.new('L', (256*S, 64*S), 0); d = ImageDraw.Draw(fill)
    if style == 'card':
        a, b = text.split('|')
        fa = fit_font(FONT_M, a, 100, 11); fb = fit_font(FONT_EB, b, 140, 17)
        A = ImageFont.truetype(FONT_M, fa.size*S); B = ImageFont.truetype(FONT_EB, fb.size*S)
        wa = A.getbbox(a)[2]; wb = B.getbbox(b)[2]; gap = 6*S
        tw = wa + gap + wb; x0 = (256*S - tw)//2
        cy = (bb[1] + bb[3] + 1) * S // 2 + 2*S
        d.text((x0, cy), a, font=A, fill=255, anchor='ls')
        d.text((x0 + wa + gap, cy), b, font=B, fill=255, anchor='ls')
    else:
        lines = text.split('\n')
        fp = FONT_M if style == 'album' else FONT_EB
        base = 13 if style == 'album' else (16 if len(lines) == 1 else 14)
        f = fit_font(fp, text, 240 if style != 'album' else 236, base)
        F = ImageFont.truetype(fp, f.size*S)
        lh = (f.size + 2) * S
        tot = lh * len(lines)
        cy0 = (bb[1] + bb[3] + 1) * S // 2 - tot // 2
        for i, l in enumerate(lines):
            w = F.getbbox(l)[2]
            x = (256*S - w)//2 if style != 'album' or len(lines) > 1 or True else 4*S
            d.text((x, cy0 + i*lh + lh//2), l, font=F, fill=255, anchor='lm')
    fill = fill.resize((256, 64), Image.LANCZOS)
    out = [[0]*256 for _ in range(64)]
    if style == 'album':
        # 흰 막대(15)는 유지하고 글자만 지운 뒤 진한 글자
        bar = bbox(px_orig, lambda v: v == 15)
        for y in range(64):
            for x in range(256):
                out[y][x] = px_orig[y][x]
                if bar and bar[0] <= x <= bar[2] and bar[1] <= y <= bar[3] and px_orig[y][x] != 0: out[y][x] = 15
        ramp = [15, 12, 10, 7, 4, 1]
        for y in range(64):
            for x in range(256):
                a = fill.getpixel((x, y))
                if a > 20 and out[y][x] != 0:
                    out[y][x] = ramp[min(5, a * 6 // 256)]
        return out
    ol = fill.point(lambda v: 255 if v > 90 else 0).filter(ImageFilter.MaxFilter(3))
    ys = [y for y in range(64) for x in range(256) if fill.getpixel((x, y)) > 90]
    y0, y1 = (min(ys), max(ys)) if ys else (0, 63)
    for y in range(64):
        for x in range(256):
            a = fill.getpixel((x, y))
            if a > 90:
                t = (y - y0) / max(1, y1 - y0)
                out[y][x] = 15 if t < 0.45 else (14 if t < 0.7 else 12)
                if a < 160: out[y][x] = 10
            elif ol.getpixel((x, y)): out[y][x] = 1 if style != 'card' else 1
    return out
def style_of(g):
    if 887 <= g <= 906: return 'album'
    if 923 <= g <= 948: return 'card'
    return 'title'
def build(F):
    caps = json.loads((W / 'translation/graphics/stills.json').read_text(encoding='utf8'))
    new = {}
    for k, t in caps.items():
        g = int(k); f = bytearray(F[g]); G = nitro.rgcn(f)
        px = decode(G['data'])
        out = draw(px, t, style_of(g))
        f[0x30:0x30+8192] = encode(out)
        new[g] = bytes(f)
    return new
def preview(F, new, path):
    sheet = Image.new('RGB', (1040, 31*66), (60, 60, 90))
    for k, g in enumerate(sorted(new)):
        P = nitro.rlcn(F[g+120])[:16]
        im = nitro.strip_img(nitro.rgcn(new[g])['data'], P)
        sheet.paste(im, ((k % 4)*260, (k//4)*66))
    sheet.save(path)
if __name__ == '__main__':
    import ld
    F = ld.load(); new = build(F); preview(F, new, W / 'tmp/stills_ko.png')
