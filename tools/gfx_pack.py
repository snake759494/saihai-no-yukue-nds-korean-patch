"""PACK(LZ11) 그림: 인물 카드·크레딧·끝 화면 한글화."""
import struct
import numpy as np, cv2
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pack, lz
FD = Path(__file__).resolve().parent.parent.parent
def lz11_compress(d):
    """LZ11 탐욕 압축(3바이트 해시 사슬)."""
    n = len(d); o = bytearray([0x11]) + n.to_bytes(3, 'little')
    heads = {}; i = 0
    def find(i):
        if i + 3 > n: return 0, 0
        key = d[i:i+3]; best = (0, 0); cnt = 0
        for p in reversed(heads.get(key, [])):
            if i - p > 4096: break
            L = 3; mx = min(0x10110, n - i)
            while L < mx and d[p + L] == d[i + L]: L += 1
            if L > best[0]: best = (L, i - p)
            cnt += 1
            if cnt > 48 or L == mx: break
        return best
    def add(i):
        if i + 3 <= n: heads.setdefault(d[i:i+3], []).append(i)
    while i < n:
        fp = len(o); o.append(0); fl = 0
        for b in range(8):
            if i >= n: break
            L, D = find(i)
            if L >= 3:
                fl |= 0x80 >> b; D -= 1
                if L <= 0x10: o += bytes([((L - 1) << 4) | (D >> 8), D & 255])
                elif L <= 0x110: x = L - 0x11; o += bytes([x >> 4, ((x & 15) << 4) | (D >> 8), D & 255])
                else: x = L - 0x111; o += bytes([0x10 | (x >> 12), (x >> 4) & 255, ((x & 15) << 4) | (D >> 8), D & 255])
                for k in range(L): add(i + k)
                i += L
            else:
                o.append(d[i]); add(i); i += 1
        o[fp] = fl
    while len(o) % 4: o.append(0)
    return bytes(o)
def repack(d, ents, parts):
    """parts: {엔트리 번호: 새 바이트}. 크기 그대로일 때만 제자리 교체."""
    d = bytearray(d)
    for k, b in parts.items():
        o, s = ents[k]; assert len(b) == s; d[o:o+s] = b
    return bytes(d)
def name_box(rgb):
    L = rgb.astype(int).sum(2) / 3
    dark = L < 60; white = L > 225
    near_w = cv2.dilate(white.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    m = (dark & near_w).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n <= 1: return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[k, :4]
    return x, y, w, h
from gfx_bmp import Bmp
HEAVY = FD / 'NanumSquareNeo-eHv.ttf'
CARD_NAMES = {1765: '이시다 미쓰나리', 1766: '시마 사콘', 1767: '다마키', 1768: '우키타 히데이에', 1769: '오타니 요시쓰구',
 1770: '고바야카와 히데아키', 1771: '시마즈 요시히로', 1772: '시마즈 도요히사', 1773: '깃카와 히로이에', 1774: '모리 히데모토',
 1775: '안코쿠지 에케이', 1776: '고니시 유키나가', 1777: '하쓰', 1778: '요도도노\n·히데요리', 1779: '도쿠가와 이에야스',
 1780: '혼다 다다카쓰', 1781: '이이 나오마사', 1782: '혼다 마사노부', 1783: '후쿠시마 마사노리', 1784: '구로다 나가마사',
 1785: '호소카와 다다오키', 1786: '도도 다카토라', 1787: '다나카 요시마사', 1788: '이케다 데루마사', 1789: '호소카와 가라샤',
 1790: '오카쓰노카타', 1791: '하쓰'}
def card_mask(rgb):
    L = rgb.astype(int).sum(2) / 3
    dark = L < 60; white = L > 225
    near_w = cv2.dilate(white.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    m = (dark & near_w).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[k, :4]
    # 같은 높이대의 인접 성분(・秀頼 등) 포함
    box = [x, y, x + w, y + h]
    for j in range(1, n):
        xx, yy, ww, hh, aa = st[j]
        if aa > 40 and (abs(yy - (y + h)) < 30 or abs(yy - y) < 10) and abs(xx - x) < 60:
            box = [min(box[0], xx), min(box[1], yy), max(box[2], xx + ww), max(box[3], yy + hh)]
    reg = np.zeros(L.shape, bool); reg[box[1]-3:box[3]+4, box[0]-3:box[2]+4] = True
    tm = reg & ((L < 70) | white)
    return box, cv2.dilate(tm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
def build_card(F, i):
    d, ents = pack.unpack(F[i])
    o, s = ents[1]; chrb = d[o:o+s]; po, ps = ents[0]
    hdr = chrb[:16]; data = chrb[16:16+0xc000]
    b = Bmp(data, d[po+16:po+ps])
    box, m = card_mask(b.rgb)
    b.inpaint(m, 5)
    x0, y0, x1, y1 = box; cx = (x0 + x1) // 2
    name = CARD_NAMES[i]; lines = name.split('\n')
    h = max(12, min(20, (y1 - y0) // len(lines) if len(lines) > 1 else y1 - y0))
    maxw = 124
    from PIL import ImageFont
    for sz in range(h, 8, -1):
        f = ImageFont.truetype(str(HEAVY), sz)
        if max(f.getbbox(l)[2] for l in lines) <= maxw: break
    tw = max(f.getbbox(l)[2] for l in lines)
    # 원래 위치가 오른쪽이면 오른쪽 정렬, 왼쪽이면 왼쪽 정렬
    if cx > 128: rx = min(250, x1 + 2) - tw
    else: rx = max(4, x0 - 2)
    ry = y0 + ((y1 - y0) - (sz + 2) * len(lines)) // 2
    b.text((rx, ry, tw + 2, (sz + 2) * len(lines)), name, ttf=HEAVY, size=sz, col=(10, 10, 10), ol=(250, 250, 250), align='l', lh=sz + 2)
    newchr = hdr + b.result() + chrb[16+0xc000:]
    nd = repack(d, ents, {1: newchr})
    return lz11_compress(nd), b
def pack_build(blobs):
    n = len(blobs); hdr = bytearray(b'PACK' + struct.pack('<I', n)); off = 8 + 8*n; body = bytearray()
    for b in blobs:
        hdr += struct.pack('<II', off + len(body), len(b)); body += b
    return bytes(hdr + body)
def scr_decode(scr, data):
    size, _, w, h = struct.unpack_from('<IIHH', scr, 4)
    m = struct.unpack_from(f'<{w*h}H', scr, 16)
    idx = np.zeros((h*8, w*8), np.int32)
    for i, e in enumerate(m):
        t = e & 0x3ff; hf = e >> 10 & 1; vf = e >> 11 & 1; pl = e >> 12
        for y in range(8):
            for x in range(8):
                sx = 7-x if hf else x; sy = 7-y if vf else y
                o = t*32 + sy*4 + sx//2
                v = (data[o] >> (4*(sx&1))) & 15 if o < len(data) else 0
                idx[(i//w)*8+y, (i%w)*8+x] = pl*16 + v
    return idx, w, h
def scr_encode(idx, P):
    """idx(뱅크*16+값) → 4bpp 타일·맵. 타일마다 뱅크 하나로 통일."""
    H, Wd = idx.shape; w, h = Wd//8, H//8
    P = np.array(P, np.int32); tiles = []; tmap = {}; m = []
    for ty in range(h):
        for tx in range(w):
            blk = idx[ty*8:ty*8+8, tx*8:tx*8+8]
            nb = blk[(blk & 15) != 15]
            bank = int(np.bincount((nb >> 4)).argmax()) if len(nb) else int(np.bincount((blk.ravel() >> 4)).argmax())
            vals = np.zeros((8, 8), np.int32)
            for y in range(8):
                for x in range(8):
                    v = blk[y, x]
                    if v >> 4 == bank or (v & 15) == 15: vals[y, x] = v & 15
                    else:
                        c = P[v]; cand = P[bank*16:bank*16+16]
                        vals[y, x] = int(((cand - c)**2).sum(1).argmin())
            key = vals.tobytes()
            if key not in tmap:
                tmap[key] = len(tiles)
                t = bytearray(32)
                for y in range(8):
                    for x in range(0, 8, 2): t[y*4 + x//2] = vals[y, x] | (vals[y, x+1] << 4)
                tiles.append(bytes(t))
            m.append(tmap[key] | (bank << 12))
    assert len(tiles) <= 1024, len(tiles)
    return b''.join(tiles), struct.pack(f'<{len(m)}H', *m), w, h
CREDIT_LINES = ['지휘봉의 행방', '스태프', '디렉터', '메인 프로그래머', '메인 플래너', 'CG 디렉터', '사운드 디렉터', '플래너',
 '프로그래머', 'CG 디자이너', 'CG 관리', '사운드 에디터', '소프트웨어 매뉴얼', '홍보', '협력', '프로듀서',
 '모리나카 다카시', '미야우치 준', '세키구치 가즈토시', '가게요시 마사미', '나카무라 신이치로', '나카야마 시게키', '야마나카 가나코',
 '다카하시 가오리', '하기와라 마리코', '사카네 고스케', '기도 유키', '오모리 마유코', '하타케야마 스미코', '야마모토 아사미',
 '쓰지 가오리', '고구레 아야', '나가타 교코', '고바야시 케이', '히라타 료', '후지타 겐사쿠', '오에 모토하루', '기요토 마키코',
 '야마자키 게이코', '야마우치 사오리', '가메이 료타', '다나베 마사히코', '요시마쓰 요지로', '이무라 준페이', '가쓰라 쓰요시',
 '폰트웍스 주식회사', '주식회사 브리지', '베이징 코에이 소프트웨어 유한공사', '톈진 코에이 소프트웨어 유한공사', '오가사와라 겐이치']
def build_credits(F):
    d, ents = pack.unpack(F[1764])
    parts = [d[o:o+s] for o, s in ents]
    P = pack.pal(parts[4]); bpp, data = pack.chr_info(parts[5])
    idx, w, h = scr_decode(parts[6], data)
    fg = (idx & 15) != 15
    rows = np.nonzero(fg[16:].any(1))[0] + 16; bands = []
    for y in rows:
        if bands and y - bands[-1][1] <= 1: bands[-1][1] = y
        else: bands.append([y, y])
    bands = bands[:50]
    Pa = np.array(P, np.int32); lum = Pa.sum(1)
    out = idx.copy()
    for k, ((a, b), s) in enumerate(zip(bands, CREDIT_LINES)):
        sub = idx[a:b+1]; m = fg[a:b+1]
        xs = np.nonzero(m.any(0))[0]; x0, x1 = xs.min(), xs.max()
        bank = int(np.bincount((sub[m] >> 4)).argmax())
        cc = np.bincount(sub[m], minlength=256); cc[[bank*16 + 15]] = 0
        order = [int(i) for i in np.argsort(-cc) if cc[i] and i >> 4 == bank]
        core = order[0]; edge = order[1] if len(order) > 1 else core
        ramp = [core, edge]
        out[a:b+1][m] = bank*16 + 15
        bold = k < 16
        fnt = ImageFont.truetype(str(FD / ('NanumSquareNeo-dEb.ttf' if bold else 'NanumSquareNeo-cBd.ttf')), 13 * 4)
        maxw = 252 - x0 if k < 45 else 252 - x0
        im = Image.new('L', (1200, 16 * 4)); ImageDraw.Draw(im).text((0, 0), s, font=fnt, fill=255)
        bb = im.getbbox(); im = im.crop((0, 0, bb[2] + 4, 16 * 4)); im = im.resize((max(1, im.width // 4), 16), Image.LANCZOS)
        g = np.array(im)
        if g.shape[1] > maxw:
            g = np.array(Image.fromarray(g).resize((maxw, 16), Image.LANCZOS))
        cx = x0 if k >= 2 else (x0 + x1) // 2 - g.shape[1] // 2
        if k in (0, 1): cx = max(0, (x0 + x1) // 2 - g.shape[1] // 2)
        for y in range(min(16, 848 - a)):
            for x in range(g.shape[1]):
                X = cx + x
                if 0 <= X < 256 and g[y, x] > 110:
                    out[a - 1 + y, X] = ramp[0]
    chrd, scrm, w, h = scr_encode(out, P)
    chr_blob = b'CHR ' + struct.pack('<III', len(chrd), 0x20, 0) + chrd
    scr_blob = parts[6][:16] + scrm
    blobs = parts[:5] + [chr_blob, scr_blob]
    return lz11_compress(pack_build(blobs)), out, Pa
def build_end(F):
    d, ents = pack.unpack(F[1792])
    parts = [d[o:o+s] for o, s in ents]
    P = pack.pal(parts[3]); bpp, data = pack.chr_info(parts[4])
    idx, w, h = scr_decode(parts[5], data)
    return idx, P, parts
def scr_decode8(scr, data):
    size, _, w, h = struct.unpack_from('<IIHH', scr, 4)
    m = struct.unpack_from(f'<{w*h}H', scr, 16)
    idx = np.zeros((h*8, w*8), np.int32)
    for i, e in enumerate(m):
        t = e & 0x3ff; hf = e >> 10 & 1; vf = e >> 11 & 1
        blk = np.frombuffer(data[t*64:t*64+64], np.uint8).reshape(8, 8) if t*64+64 <= len(data) else np.zeros((8, 8), np.uint8)
        if hf: blk = blk[:, ::-1]
        if vf: blk = blk[::-1]
        idx[(i//w)*8:(i//w)*8+8, (i%w)*8:(i%w)*8+8] = blk
    return idx, w, h
def scr_encode8(idx):
    H, Wd = idx.shape; tiles = []; tmap = {}; m = []
    for ty in range(H//8):
        for tx in range(Wd//8):
            key = idx[ty*8:ty*8+8, tx*8:tx*8+8].astype(np.uint8).tobytes()
            if key not in tmap: tmap[key] = len(tiles); tiles.append(key)
            m.append(tmap[key])
    assert len(tiles) <= 1024
    return b''.join(tiles), struct.pack(f'<{len(m)}H', *m)
def build_end(F):
    d, ents = pack.unpack(F[1792])
    parts = [d[o:o+s] for o, s in ents]
    P = np.array(pack.pal(parts[3])[:256], np.int32)
    bpp, data = pack.chr_info(parts[4])
    idx, w, h = scr_decode8(parts[5], data) if bpp == 8 else scr_decode(parts[5], data)
    return idx, P, parts, bpp
def render_end(F):
    from PIL import ImageFilter
    idx, P, parts, bpp = build_end(F)
    S = 4; Wd, H = 256*S, 192*S
    def layer(text, font, size, cy):
        f = ImageFont.truetype(str(font), size*S); bb = f.getbbox(text)
        m = Image.new('L', (Wd, H)); ImageDraw.Draw(m).text(((Wd - (bb[2]-bb[0]))//2 - bb[0], cy*S - (bb[3]-bb[1])//2 - bb[1]), text, font=f, fill=255)
        return m
    t1 = layer('지휘봉의 행방', FD / 'NanumSquareNeo-eHv.ttf', 15, 52)
    t2 = layer('끝', FD / 'SeoulHangangEB.ttf', 40, 102)
    img = Image.new('RGB', (Wd, H), (0, 0, 0))
    for m, glow, fill in ((t1, (180, 220, 230), (220, 40, 70)), (t2, (90, 170, 120), (225, 245, 240))):
        g = m.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(10))
        img.paste(Image.new('RGB', (Wd, H), glow), (0, 0), g.point(lambda v: min(255, v*2)))
        img.paste(Image.new('RGB', (Wd, H), (255, 255, 255)), (0, 0), m.filter(ImageFilter.MaxFilter(5)))
        img.paste(Image.new('RGB', (Wd, H), fill), (0, 0), m)
    img = np.array(img.resize((256, 192), Image.LANCZOS)).astype(np.int32)
    flat = img.reshape(-1, 3)
    q = np.empty(len(flat), np.int32)
    for i in range(0, len(flat), 4096):
        c = flat[i:i+4096]; q[i:i+4096] = ((c[:, None, :] - P[None, :, :])**2).sum(2).argmin(1)
    newidx = q.reshape(192, 256)
    ch, sm = scr_encode8(newidx)
    chr_blob = parts[4][:4] + struct.pack('<I', len(ch)) + parts[4][8:16] + ch
    scr_blob = parts[5][:16] + sm
    blobs = parts[:4] + [chr_blob, scr_blob]
    return lz11_compress(pack_build(blobs)), newidx, P
