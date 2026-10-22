"""셀(OBJ) 그래픽 글자 블록 한글화."""
import struct, collections
import numpy as np, cv2
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import nitro, groups
FD = Path(__file__).resolve().parent.parent.parent
SERIF = FD / 'SeoulHangangEB.ttf'
class Sheet:
    """RGCN 8bpp/4bpp 데이터 위에서 OBJ 단위 읽기/쓰기."""
    def __init__(self, f, unit):
        self.f = bytearray(f); g = nitro.rgcn(self.f); self.bpp8 = g['bpp'] == 4
        self.off = 0x30; self.unit = unit
    def obj_px(self, o):
        tb = 64 if o['bpp8'] else 32; tw = o['w']//8
        a = np.zeros((o['h'], o['w']), np.int32); addr = {}
        for ty in range(o['h']//8):
            for tx in range(tw):
                base = self.off + o['tile']*self.unit + (ty*tw+tx)*tb
                for y in range(8):
                    for x in range(8):
                        X = tx*8+x; Y = ty*8+y
                        if o['bpp8']:
                            p = base + y*8 + x
                            a[Y, X] = self.f[p] if p < len(self.f) else 0; addr[(Y, X)] = (p, None)
                        else:
                            p = base + y*4 + x//2
                            v = self.f[p] if p < len(self.f) else 0
                            a[Y, X] = (v >> (4*(x&1))) & 15; addr[(Y, X)] = (p, x&1)
        if o['hf']: a = a[:, ::-1]
        if o['vf']: a = a[::-1, :]
        return a, addr
    def obj_write(self, o, a):
        if o['hf']: a = a[:, ::-1]
        if o['vf']: a = a[::-1, :]
        tb = 64 if o['bpp8'] else 32; tw = o['w']//8
        for ty in range(o['h']//8):
            for tx in range(tw):
                base = self.off + o['tile']*self.unit + (ty*tw+tx)*tb
                for y in range(8):
                    for x in range(8):
                        v = int(a[ty*8+y, tx*8+x])
                        if o['bpp8']:
                            p = base + y*8 + x
                            if p < len(self.f): self.f[p] = v
                        else:
                            p = base + y*4 + x//2
                            if p < len(self.f): self.f[p] = (self.f[p] & (0xf0 if x&1 == 0 else 0x0f)) | (v << (4*(x&1)))
def assemble(sheet, objs):
    x0 = min(o['x'] for o in objs); y0 = min(o['y'] for o in objs)
    x1 = max(o['x']+o['w'] for o in objs); y1 = max(o['y']+o['h'] for o in objs)
    img = np.zeros((y1-y0, x1-x0), np.int32)
    for o in reversed(objs):
        a, _ = sheet.obj_px(o); m = a > 0
        img[o['y']-y0:o['y']-y0+o['h'], o['x']-x0:o['x']-x0+o['w']][m] = a[m]
    return img, x0, y0
def scatter(sheet, objs, img, x0, y0):
    for o in objs:
        sheet.obj_write(o, img[o['y']-y0:o['y']-y0+o['h'], o['x']-x0:o['x']-x0+o['w']])
def style_of(img, P):
    """원래 글자의 외곽선 색과 행별 채움 색."""
    m = img > 0
    if not m.any(): return None
    er = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    edge = m & ~er
    lum = P.sum(1)
    oc = collections.Counter(img[edge].tolist())
    olc = min(oc.most_common(6), key=lambda kv: lum[kv[0]])[0] if oc else 1
    rows = {}
    for y in range(img.shape[0]):
        c = collections.Counter(img[y][er[y]].tolist())
        if c: rows[y] = c.most_common(1)[0][0]
    return olc, rows
def glyph_mask(ch, w, h, font=SERIF):
    S = 4
    f = ImageFont.truetype(str(font), 100)
    bb = f.getbbox(ch); gw, gh = bb[2]-bb[0], bb[3]-bb[1]
    im = Image.new('L', (gw + 8, gh + 8)); ImageDraw.Draw(im).text((4-bb[0], 4-bb[1]), ch, font=f, fill=255)
    im = im.resize((max(1, w), max(1, h)), Image.LANCZOS)
    return np.array(im) > 110
def draw_glyph(shape, bbox, ch, sty, ol_w):
    """bbox(x0,y0,x1,y1) 안에 ch를 원래 스타일로."""
    H, Wd = shape; out = np.zeros(shape, np.int32)
    x0, y0, x1, y1 = bbox
    inner_w = max(1, x1-x0+1 - 2*ol_w); inner_h = max(1, y1-y0+1 - 2*ol_w)
    gm = glyph_mask(ch, inner_w, inner_h)
    full = np.zeros(shape, bool)
    full[y0+ol_w:y0+ol_w+inner_h, x0+ol_w:x0+ol_w+inner_w] = gm[:min(inner_h, H-y0-ol_w), :min(inner_w, Wd-x0-ol_w)]
    k = 2*ol_w + 1
    ring = cv2.dilate(full.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
    olc, rows = sty
    out[ring] = olc
    ys = sorted(rows)
    for y in range(H):
        if not full[y].any(): continue
        near = min(ys, key=lambda r: abs(r-y)) if ys else None
        out[y][full[y]] = rows[near] if near is not None else olc
    return out
def find_blocks(cell):
    """64×64 기준 OBJ + 같은 타일 묶음(+45/+50 단위)으로 이뤄진 글자 블록들."""
    out = []
    for o in cell:
        if (o['w'], o['h']) != (64, 64): continue
        t = o['tile']
        mem = [p for p in cell if t <= p['tile'] < t + 50 and o['x'] <= p['x'] < o['x'] + 80 and o['y'] <= p['y'] < o['y'] + 80]
        sz = {(p['w'], p['h']) for p in mem}
        if (16, 32) in sz and len(mem) >= 3:
            out.append((t, mem))
    return out
def process_blocks(F, cid, word, font=SERIF, min_area=0, force=None):
    G = {x['cell']: x for x in groups.cell_groups(F)}[cid]
    cf = F[cid]; mp = struct.unpack_from('<I', cf, 0x20)[0]
    cells = nitro.recn(cf); sh = Sheet(F[G['gfx']], 32 << mp)
    P = np.array(nitro.rlcn(F[G['pal']])[:256], np.int32)
    blocks = {}   # tile → (objs relative)
    ref = None
    def is_text(mem):
        img = assemble(sh, mem)[0]; c = P[img[img > 0]]
        if not len(c): return False
        return np.median(c.sum(1) / 3) > 150
    for cl in cells:
        bl = [b for b in find_blocks(cl) if is_text(b[1])]
        for t, mem in bl:
            if t not in blocks: blocks[t] = mem
        if len(bl) == len(word):
            area = sum(assemble(sh, m)[0].astype(bool).sum() for _, m in bl)
            if ref is None or area > ref[0]: ref = (area, bl)
    assert ref, f'{cid}: 기준 셀 없음'
    rb = ref[1]
    xs = [m[0]['x'] for _, m in rb]; ys = [m[0]['y'] for _, m in rb]
    vertical = (max(ys) - min(ys)) > (max(xs) - min(xs))
    rb = sorted(rb, key=lambda b: (b[1][0]['y'] if vertical else b[1][0]['x']))
    def feat(img):
        m = (img > 0).astype(np.float32)
        ys_, xs_ = np.nonzero(m)
        if not len(xs_): return None
        m = m[ys_.min():ys_.max()+1, xs_.min():xs_.max()+1]
        f = cv2.resize(m, (24, 24), interpolation=cv2.INTER_AREA); f -= f.mean(); n = np.linalg.norm(f)
        return f / n if n else f
    refs = [feat(assemble(sh, m)[0]) for _, m in rb]
    done = {}
    for t, mem in blocks.items():
        img, x0, y0 = assemble(sh, mem)
        fe = feat(img)
        if fe is None: continue
        rt = [b[0] for b in rb]
        k = rt.index(t) if t in rt else int(np.argmax([float((fe * r).sum()) for r in refs]))
        if force and t in force: k = force[t]
        sty = style_of(img, P)
        ys_, xs_ = np.nonzero(img > 0)
        bbox = (xs_.min(), ys_.min(), xs_.max(), ys_.max())
        size = max(bbox[2]-bbox[0], bbox[3]-bbox[1])
        ow = max(1, round(size / 22))
        new = draw_glyph(img.shape, bbox, word[k], sty, ow)
        scatter(sh, mem, new, x0, y0)
        done[t] = word[k]
    return bytes(sh.f), G['gfx'], done
def preview(F, cid, gfx_bytes, path, maxcells=40):
    G = {x['cell']: x for x in groups.cell_groups(F)}[cid]
    cf = F[cid]; mp = struct.unpack_from('<I', cf, 0x20)[0]
    g = nitro.rgcn(gfx_bytes); P = nitro.rlcn(F[G['pal']])
    ims = [nitro.render_cell(c, g, P, unit=32 << mp) for c in nitro.recn(cf)[:maxcells]]
    ims = [i for i in ims if i]
    W = 1024; x = y = rh = 0; s = Image.new('RGBA', (W, 2000), (60, 60, 90, 255))
    for im in ims:
        if im.width > 250: im = im.resize((250, im.height*250//im.width))
        if x + im.width > W: x = 0; y += rh + 4; rh = 0
        s.paste(im, (x, y), im); x += im.width + 4; rh = max(rh, im.height)
    s.crop((0, 0, W, y + rh + 4)).save(path)

def comps(img, vertical, n=99):
    """글자 칸 추정: 글자는 대략 정사각형 → 긴 축 길이/짧은 축 길이 개수로 균등 분할."""
    m = img > 0
    ys, xs = np.nonzero(m)
    if not len(xs): return []
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    L = (y1 - y0 + 1) if vertical else (x1 - x0 + 1); S = (x1 - x0 + 1) if vertical else (y1 - y0 + 1)
    k = max(1, min(n, round(L / S)))
    res = []
    for i in range(k):
        a = (y0 if vertical else x0) + L * i // k; b = (y0 if vertical else x0) + L * (i + 1) // k - 1
        sub = np.zeros_like(m)
        if vertical: sub[a:b+1] = m[a:b+1]
        else: sub[:, a:b+1] = m[:, a:b+1]
        yy, xx = np.nonzero(sub)
        if len(xx): res.append((xx.min(), yy.min(), xx.max(), yy.max()))
    return res
def process_text_cells(F, cid, word, vertical=False, font=SERIF, cycle=False):
    """셀 전체가 글자인 묶음: 셀마다 성분 분리 → 기준 글자와 대조 → 다시 그리기."""
    G = {x['cell']: x for x in groups.cell_groups(F)}[cid]
    cf = F[cid]; mp = struct.unpack_from('<I', cf, 0x20)[0]
    cells = [c for c in nitro.recn(cf) if c]; sh = Sheet(F[G['gfx']], 32 << mp)
    P = np.array(nitro.rlcn(F[G['pal']])[:256], np.int32)
    imgs = [assemble(sh, c) for c in cells]
    def feat(m):
        m = m.astype(np.float32); f = cv2.resize(m, (24, 24), interpolation=cv2.INTER_AREA)
        f -= f.mean(); n = np.linalg.norm(f); return f / n if n else f
    ref = None
    for (img, x0, y0) in imgs:
        cs = [c for c in comps(img, vertical, len(word)) if (c[2]-c[0]) * (c[3]-c[1]) > 30]
        if len(cs) == len(word):
            area = int((img > 0).sum())
            if ref is None or area > ref[0]: ref = (area, img, cs)
    assert ref, f'{cid}: 기준 셀 없음'
    refs = [feat(ref[1][c[1]:c[3]+1, c[0]:c[2]+1] > 0) for c in ref[2]]
    out_imgs = []
    for (img, x0, y0) in imgs:
        new = np.zeros_like(img)
        cs = [c for c in comps(img, vertical, 99 if cycle else len(word)) if (c[2]-c[0]) >= 3 and (c[3]-c[1]) >= 3]
        k0 = None
        for j, c in enumerate(cs):
            sub = img[c[1]:c[3]+1, c[0]:c[2]+1]
            if k0 is None:
                k0 = int(np.argmax([float((feat(sub > 0) * r).sum()) for r in refs])) if cycle else 0
            k = (k0 + j) % len(word)
            sty = style_of(sub, P)
            if sty is None: continue
            size = max(c[2]-c[0], c[3]-c[1]); ow = max(1, round(size / 22))
            g = draw_glyph(sub.shape, (0, 0, sub.shape[1]-1, sub.shape[0]-1), word[k], sty, ow)
            new[c[1]:c[3]+1, c[0]:c[2]+1] = np.where(g > 0, g, new[c[1]:c[3]+1, c[0]:c[2]+1])
        out_imgs.append(new)
    for (img, x0, y0), new, c in zip(imgs, out_imgs, cells):
        scatter(sh, c, new, x0, y0)
    return bytes(sh.f), G['gfx']
def text_objs(sh, P, cell):
    out = []
    for o in cell:
        a, _ = sh.obj_px(o); m = a > 0
        if m.sum() < 8: continue
        c = P[a[m]]; lum = c.sum(1) / 3
        if np.median(lum) > 140 and m.mean() < 0.75: out.append(o)
    return out
def name_ref(F, cid):
    G = {x['cell']: x for x in groups.cell_groups(F)}[cid]
    cf = F[cid]; mp = struct.unpack_from('<I', cf, 0x20)[0]; cells = nitro.recn(cf)
    sh = Sheet(F[G['gfx']], 32 << mp); P = np.array(nitro.rlcn(F[G['pal']])[:256], np.int32)
    eye = {o['tile'] for c in cells[1:6] for o in c}
    best = max(cells, key=lambda c: len({o['tile'] for o in c} - eye))
    txt = [o for o in best if o['tile'] not in eye]
    return G, cells, sh, P, txt, eye
NAMES = ['시마 사콘', '우키타 히데이에', '오타니 요시쓰구', '고바야카와 히데아키', '시마즈 요시히로', '시마즈 도요히사',
 '모리 히데모토', '안코쿠지 에케이', '고니시 유키나가', '도쿠가와 이에야스', '혼다 다다카쓰', '이이 나오마사',
 '후쿠시마 마사노리', '구로다 나가마사', '호소카와 다다오키', '도도 다카토라', '다나카 요시마사', '이케다 데루마사',
 '오카쓰노카타', '아카시 다케노리', '아타 모리아쓰', '마이 효고', '히라쓰카 다메히로', '도다 가쓰시게',
 '가모 사토이에', '기모쓰키 가네모리', '나쓰카 마사이에', '조소카베 모리치카', '가니 사이조', '이나바 사다미치',
 '쓰쓰이 사다쓰구', '다케나카 시게카도', '가토 요시아키', '교고쿠 다카토모', '도가와 다쓰야스', '이나바 마사나리',
 '마쓰노 시게모토', '히라오카 요리카쓰', '오쿠다이라 사다하루', '오다 나가마스', '가나모리 나가치카', '이코마 가즈마사',
 '마쓰다이라 다다요시', '아카자 나오야스', '오가와 스케타다', '구쓰키 모토쓰나', '와키자카 야스하루', '데라자와 히로타카',
 '야마노우치 가즈토요', '아사노 요시나가']
def text_line(s, maxw, h, font=SERIF):
    for size in range(h + 4, 6, -1):
        f = ImageFont.truetype(str(font), size * 4)
        bb = f.getbbox(s)
        w = (bb[2] - bb[0]) // 4
        if w <= maxw: break
    im = Image.new('L', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8)); ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), s, font=f, fill=255)
    im = im.resize((max(1, im.width // 4), max(1, im.height // 4)), Image.LANCZOS)
    return np.array(im) > 100
def process_name(F, cid, name):
    G, cells, sh, P, txt, eye = name_ref(F, cid)
    img, x0, y0 = assemble(sh, txt)
    sty = style_of(img, P)
    ys, xs = np.nonzero(img > 0)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max(), ys.max()
    H, Wd = img.shape
    gm = text_line(name, Wd - 4, by1 - by0 - 3)
    new = np.zeros_like(img)
    gh, gw = gm.shape
    ox = max(1, min(Wd - gw - 1, bx0 + ((bx1 - bx0) - gw) // 2)); oy = max(1, by0 + ((by1 - by0) - gh) // 2)
    full = np.zeros(img.shape, bool); full[oy:oy+gh, ox:ox+gw] = gm[:H-oy, :Wd-ox]
    ring = cv2.dilate(full.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    shadow = np.zeros_like(ring); shadow[2:, 2:] = ring[:-2, :-2]
    olc, rows = sty; rs = sorted(rows)
    lum = P.sum(1); darkest = min(set(img[img > 0].tolist()), key=lambda i: lum[i])
    new[shadow & ~ring] = darkest
    new[ring] = olc
    for y in range(H):
        if full[y].any():
            near = min(rs, key=lambda r: abs(r - y))
            new[y][full[y]] = rows[near]
    orig_sheet = Sheet(bytes(sh.f), sh.unit)
    scatter(sh, txt, new, x0, y0)
    done = {o['tile'] for o in txt}
    om = (img > 0).astype(np.float32)
    for c in cells:
        tc = [o for o in c if o['tile'] not in eye and o['tile'] not in done]
        if not tc: continue
        ic, cx0, cy0 = assemble(orig_sheet, tc)
        if not (ic > 0).any(): continue
        m = (ic > 0).astype(np.float32)
        if m.shape[0] > om.shape[0] or m.shape[1] > om.shape[1]: continue
        r = cv2.matchTemplate(om, m, cv2.TM_CCORR_NORMED); _, v, _, (dx, dy) = cv2.minMaxLoc(r)
        if v < 0.6: continue
        nc = new[dy:dy+m.shape[0], dx:dx+m.shape[1]]
        scatter(sh, tc, nc, cx0, cy0)
        done |= {o['tile'] for o in tc}
    return bytes(sh.f), G['gfx']
