"""텍스처(선형 4bpp) 한글화."""
import json, collections
from pathlib import Path
import tex, auxfmt
W = Path(__file__).resolve().parent.parent
NANUM_B = W.parent / 'NanumSquareNeo-dEb.ttf'
def build(F, tr_text):
    """tr_text: 일본어 문자열 → 한국어(없으면 None)."""
    out = {}
    # 1) 설명문 1574~1762 ← 인물 사전 설명
    m = json.loads((W / 'translation/graphics/desc_map.json').read_text())
    r, _ = auxfmt.p711(F[711])
    for k, n in m.items():
        ja = bytes(r[n][8:]).rstrip(b'\0').split(b'\0')[1].decode('cp932')
        ko = tr_text(ja)
        if ko is None: continue
        px = [[0]*256 for _ in range(64)]
        tex.text(px, (4, 5, 250, 58), ko, 'Galmuri11', fg=2, sh=1, lh=14)
        out[int(k)] = tex.enc(px)
    # 2) 인물 이름 머리말
    px = [[0]*256 for _ in range(16)]
    tex.text(px, (8, 2, 240, 14), '이시다 미쓰나리', 'Galmuri11', fg=1)
    out[1303] = tex.enc(px)
    # 3) 오류창
    msgs = {1119: '데이터를 저장하지 못했습니다.\n전원을 끄고 카드를\n다시 꽂아 주세요.',
            1120: '데이터를 읽지 못했습니다.\n전원을 끄고 카드를\n다시 꽂아 주세요.',
            1121: '데이터가 손상되어\n읽을 수 없습니다.'}
    for i, s in msgs.items():
        px = tex.dec(F[i])
        tex.replace(px, (34, 9, 222, 50), set(range(7, 16)), 6)
        tex.text(px, (40, 10, 210, 48), s, 'Galmuri11', fg=15, ol=7, lh=16)
        out[i] = tex.enc(px)
    # 4) 화 목록·시작 메뉴 1114
    px = tex.dec(F[1114])
    chap = ['안개 속의 진실', '저마다의 속셈', '마음', '목숨이 잇는 길', '결의, 그 너머로']
    for k in range(5):
        y = 1 + 24*k
        tex.fill(px, (0, y-1, 256, 20), 0)
        tex.text(px, (1, y, 56, 18), f'제{k+1}화', 'Galmuri11-Bold', fg=1, ol=4, align='c', valign='c')
        tex.text(px, (64, y, 190, 18), chap[k], 'Galmuri11-Bold', fg=1, ol=4, align='c', valign='c')
    for x0 in (0, 128):
        tex.fill(px, (x0, 128, 92, 23), 0)
        tex.text(px, (x0, 129, 90, 10), '처음부터', 'Galmuri9', fg=1, ol=4, align='c', lh=10)
        tex.text(px, (x0, 140, 90, 10), '이어서', 'Galmuri9', fg=1, ol=4, align='c', lh=10)
    tex.fill(px, (40, 160, 180, 16), 0)   # 안내문은 OBJ(1116) 한 겹만 사용
    out[1114] = tex.enc(px)
    # 5) 명령어 1122 (8px 줄 × 4, 64px 칸 × 4)
    px = tex.dec(F[1122])
    words = ['대화', '주목', '이동', '사용']
    for row in range(4):
        for col in range(4):
            r = (col*64, row*8, 64, 8)
            c = collections.Counter(px[y][x] for y in range(r[1], r[1]+8) for x in range(r[0], r[0]+64) if px[y][x])
            fg = c.most_common(1)[0][0] if c else 1
            tex.fill(px, r, 0)
            pts, w, asc = tex.bdf_mask(words[row], 'Galmuri7', 3)
            tex.put(px, {(a, b - 1) for a, b in pts}, r[0] + (64 - w)//2, r[1], fg, clip=r)
    out[1122] = tex.enc(px)
    # 6) 수째 1123
    px = tex.dec(F[1123])
    tex.fill(px, (158, 0, 36, 16), 0)
    tex.text(px, (158, 1, 36, 15), '수째', 'Galmuri11-Bold', fg=13, ol=5, align='c', valign='c')
    out[1123] = tex.enc(px)
    out[1118] = save_atlas(F)
    out[1] = ui_atlas(F)
    out.update(battle_labels(F))
    return out
SAVE_ITEMS = [((0, 8, 76, 8), '데이터 없음', 'Galmuri7'), ((6, 16, 66, 8), '새로 만들기', 'Galmuri7'), ((0, 24, 64, 8), '전략 합전', 'Galmuri7'),
              ((76, 7, 50, 13), '저장', 'Galmuri11-Bold'), ((76, 20, 50, 13), '재개', 'Galmuri11-Bold'),
              ((0, 32, 58, 8), '・하나', 'Galmuri7'), ((0, 40, 58, 8), '・둘', 'Galmuri7'), ((0, 48, 58, 8), '・셋', 'Galmuri7'),
              ((62, 32, 50, 8), '읽는 중', 'Galmuri7'), ((62, 40, 50, 8), '저장 중', 'Galmuri7')]
def save_atlas(F):
    px = tex.dec(F[1118])
    for half in (0, 128):
        for (x, y, w, h), s, fnt in SAVE_ITEMS:
            r = (x + half, y, w, h)
            c = collections.Counter(px[Y][X] for Y in range(y, y+h) for X in range(r[0], r[0]+w) if px[Y][X])
            mc = [v for v, _ in c.most_common(2)] or [1]
            fg = mc[0]; ol = mc[1] if len(mc) > 1 else None
            tex.fill(px, r, 0)
            pts, tw, asc = tex.bdf_mask(s, fnt)
            ys = [b2 for _, b2 in pts]; top = min(ys); gh = max(ys) - top + 1
            tex.put(px, {(a2, b2 - top) for a2, b2 in pts}, r[0] + 1, y + max(0, (h - gh) // 2), fg,
                    ol=ol if (fnt.endswith('Bold') and half == 0) else None, clip=(r[0], y, w, h))
        # 하단 납작 글자 「제N화」 (높이 5px, 세로 1/2 압축)
        for k in range(5):
            y = 64 + 6*k
            for x0, w in ((3, 52), (65, 54)):
                r = (x0 + half, y, w, 5)
                c = collections.Counter(px[Y][X] for Y in range(y, y+5) for X in range(r[0], r[0]+w) if px[Y][X])
                fg = c.most_common(1)[0][0] if c else 1
                tex.fill(px, r, 0)
                pts, tw, asc = tex.bdf_mask(f'제{k+1}화', 'Galmuri11')
                ys = [b2 for _, b2 in pts]; top = min(ys)
                ox = r[0] + (w - tw) // 2
                for (a, b) in pts:
                    X = ox + a; Y = y + (b - top) // 2
                    if r[0] <= X < r[0] + w and y <= Y < y + 5: px[Y][X] = fg
    return tex.enc(px)
UI_LABELS = [['사용', '인물', '다른 전장'], ['주목', '소지품', '상세'], ['돌아가기', '말의 잎', '재도전'], ['보고', '전령', '지도'], ['정보', '발언', '선택']]
def ui_atlas(F):
    px = tex.dec(F[1])
    for r, row in enumerate(UI_LABELS):
        for c, s in enumerate(row):
            rect = (112 + 48*c, 24*r, 48, 24)
            tex.fill(px, rect, 0)
            done = False
            for sz in range(15, 10, -1):
                pts, w, _ = tex.ttf_mask(s, NANUM_B, sz)
                if w <= 44:
                    ys = [b for _, b in pts]; top = min(ys); gh = max(ys) - top + 1
                    tex.put(px, {(a, b - top) for a, b in pts}, rect[0] + (48 - w)//2, rect[1] + (24 - gh)//2, 15, sh=8, ol=2, clip=rect)
                    done = True; break
            if not done:
                tex.text(px, rect, s, 'Galmuri11-Bold', fg=15, ol=2, align='c', valign='c')
    import numpy as np, cv2
    from PIL import Image, ImageDraw, ImageFont
    for x0 in (0, 128):
        for (y, h), word in zip(((128, 12), (140, 12), (152, 16)), ('인물', '소지품', '말의 잎')):
            rows = {}
            for Y in range(y, y+h):
                c = collections.Counter(px[Y][X] for X in range(x0, x0+72) if px[Y][X] >= 7)
                if c: rows[Y] = c.most_common(1)[0][0]
            oc = collections.Counter(px[Y][X] for Y in range(y, y+h) for X in range(x0, x0+72) if 1 <= px[Y][X] <= 6)
            olc = oc.most_common(1)[0][0] if oc else 3
            tex.fill(px, (x0, y, 72, h), 0)
            H2 = (h - 1) * 2
            f = None
            for sz in range(H2, 8, -1):
                f = ImageFont.truetype(str(NANUM_B.parent / 'NanumSquareNeo-eHv.ttf'), sz * 4)
                bb = f.getbbox(word)
                if (bb[2] - bb[0]) // 4 <= 66: break
            im = Image.new('L', ((bb[2]-bb[0]) + 16, (bb[3]-bb[1]) + 16)); ImageDraw.Draw(im).text((8-bb[0], 8-bb[1]), word, font=f, fill=255)
            gw = max(1, im.width // 4); im = im.resize((gw, H2), Image.LANCZOS)
            g = np.array(im) > 110
            ring = cv2.dilate(g.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            sq_g = g[0::2] | g[1::2]; sq_r = ring[0::2] | ring[1::2]
            rs = sorted(rows) or [y]
            for yy in range(sq_g.shape[0]):
                Y = y + yy
                if Y >= y + h: break
                fv = rows.get(Y, rows[min(rs, key=lambda r: abs(r - Y))] if rows else 15)
                for xx in range(sq_g.shape[1]):
                    X = x0 + 3 + xx
                    if X >= x0 + 72: break
                    if sq_g[yy, xx]: px[Y][X] = fv
                    elif sq_r[yy, xx]: px[Y][X] = olc
    return tex.enc(px)
def battle_labels(F):
    import glob
    m = {}
    for f in glob.glob(str(W / 'translation/labels/out_final.json')):
        m.update(json.load(open(f, encoding='utf8')))
    out = {}
    for i in range(1125, 1140):
        px = tex.dec(F[i][:8192]); ch = False
        for k, s in m.items():
            fi, r, c = map(int, k.split('_'))
            if fi != i: continue
            x0, y0 = c*32, 1 + 6*r
            tex.fill(px, (x0, y0, 32, 6), 0)
            pts, w, asc = tex.bdf_mask(s, 'Galmuri7')
            ys = [b for _, b in pts] or [0]; top = min(ys); gh = max(ys) - top + 1
            sy = min(1.0, 5 / gh); sx = min(1.0, 30 / max(1, w))
            q = {(int(a * sx), int((b - top) * sy)) for a, b in pts}
            ww = int(w * sx); ox = x0 + (32 - ww)//2
            for (a2, b2) in q:
                for dx in (-1, 1):
                    X = ox + a2 + dx
                    if x0 <= X < x0 + 32 and (a2 + dx, b2) not in q and px[y0 + b2][X] == 0: px[y0 + b2][X] = 1
            for (a2, b2) in q:
                if 0 <= b2 < 6: px[y0 + b2][ox + a2] = 2
            ch = True
        if ch: out[i] = tex.enc(px) + F[i][8192:]
    return out
