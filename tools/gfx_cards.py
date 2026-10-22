"""화 제목 카드(4149~4158) 한글화."""
import numpy as np, cv2
from pathlib import Path
from gfx_bmp import Bmp, lum
FD = Path(__file__).resolve().parent.parent.parent
SERIF = FD / 'SeoulHangangEB.ttf'
TITLES = ['안개 속의 진실', '저마다의 속셈', '마음', '목숨이 잇는 길', '결의, 그 너머로']
def header(b):
    b.rgb[14:31, 6:100] = 0; b.changed[14:31, 6:100] = True
    b.text((10, 16, 110, 14), '지휘봉의 행방', 'Galmuri11-Bold', col=(170, 170, 170))
def bottom_mask(b):
    L = lum(b.rgb.astype(int)); m = np.zeros(L.shape, bool)
    m[120:186, 96:254] = L[120:186, 96:254] > 150
    return cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2) > 0
def build(F):
    out = {}
    for k in range(10):
        i = 4149 + k; b = Bmp(F[i], F[i+512])
        header(b); b.inpaint(bottom_mask(b), 5)
        ol = (30, 30, 40)
        if k < 5:
            b.text((100, 130, 146, 18), f'제{k+1}화', ttf=SERIF, size=15, col=(255, 255, 255), ol=ol, align='r')
            b.text((96, 150, 152, 24), TITLES[k], ttf=SERIF, size=20, col=(255, 255, 255), ol=ol, align='r')
        else:
            b.text((96, 146, 152, 28), f'제{k-4}화  끝', ttf=SERIF, size=21, col=(255, 255, 255), ol=ol, align='r')
        out[i] = b
    return out
DIRS = [('북', (116, 0, 24, 22)), ('서', (0, 84, 24, 22)), ('동', (232, 84, 24, 22)), ('남', (116, 170, 24, 22))]
def build_maps(F):
    out = {}
    for i in range(4159, 4173):
        b = Bmp(F[i], F[i+512]); L = lum(b.rgb.astype(int))
        m = np.zeros(L.shape, bool)
        for _, (x, y, w, h) in DIRS: m[y:y+h, x:x+w] = L[y:y+h, x:x+w] > 200
        m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2) > 0
        b.inpaint(m, 4)
        for s, r in DIRS: b.text(r, s, 'Galmuri11-Bold', col=(255, 255, 255), ol=(60, 50, 30), align='c')
        out[i] = b
    return out
HEAVY = FD / 'NanumSquareNeo-eHv.ttf'
def build_logo(F):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    b = Bmp(F[805], F[807])
    m = np.zeros(b.idx.shape, bool); m[56:126, 12:252] = True
    b.inpaint(m, 7)
    S = 4; W0, H0 = 240*S, 72*S
    lay = Image.new('RGBA', (W0, H0), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # 붉은 판(평행사변형) + 진한 테두리
    plate = [(14*S, 16*S), (236*S, 10*S), (226*S, 56*S), (4*S, 60*S)]
    d.polygon(plate, fill=(120, 0, 10, 255))
    inner = [(18*S, 19*S), (231*S, 13*S), (222*S, 53*S), (9*S, 57*S)]
    grad = Image.new('RGBA', (W0, H0)); gd = ImageDraw.Draw(grad)
    for y in range(H0):
        t = y / H0; gd.line([(0, y), (W0, y)], fill=(int(220 - 90*t), int(20 - 10*t), int(30 - 10*t), 255))
    pm = Image.new('L', (W0, H0)); ImageDraw.Draw(pm).polygon(inner, fill=255)
    lay.paste(grad, (0, 0), pm)
    # 밑줄 막대
    d.polygon([(10*S, 62*S), (200*S, 60*S), (198*S, 66*S), (8*S, 68*S)], fill=(200, 200, 205, 255), outline=(90, 90, 95, 255))
    f = ImageFont.truetype(str(HEAVY), 33*S)
    txt = '지휘봉의 행방'
    tw = f.getbbox(txt)[2]; x0 = (W0 - tw)//2; y0 = 6*S
    tm = Image.new('L', (W0, H0)); ImageDraw.Draw(tm).text((x0, y0), txt, font=f, fill=255)
    # 그림자·외곽선·본체
    sh = tm.filter(ImageFilter.MaxFilter(9)); shadow = Image.new('RGBA', (W0, H0), (70, 0, 5, 255))
    lay.paste(shadow, (3*S, 3*S), sh)
    ol = tm.filter(ImageFilter.MaxFilter(7)); lay.paste(Image.new('RGBA', (W0, H0), (60, 10, 15, 255)), (0, 0), ol)
    body = Image.new('RGBA', (W0, H0)); bd = ImageDraw.Draw(body)
    for y in range(H0):
        t = y / H0; c = int(255 - 70*max(0, t - 0.45)*2)
        bd.line([(0, y), (W0, y)], fill=(c, c, min(255, c + 5), 255))
    lay.paste(body, (0, 0), tm)
    lay = lay.resize((240, 72), Image.LANCZOS)
    a = np.array(lay); al = a[..., 3] > 110
    ys, xs = np.nonzero(al)
    b.rgb[ys + 54, xs + 10] = a[ys, xs, :3]; b.changed[ys + 54, xs + 10] = True
    return b
def _obj_strip(data, n=3, w=8, h=4):
    px = np.zeros((h*8, n*w*8), np.uint8)
    for k in range(n):
        for t in range(w*h):
            tt = k*w*h + t
            blk = np.frombuffer(data[tt*64:(tt+1)*64], np.uint8).reshape(8, 8)
            px[(t//w)*8:(t//w)*8+8, k*w*8+(t%w)*8:k*w*8+(t%w)*8+8] = blk
    return px
def _obj_unstrip(px, n=3, w=8, h=4):
    o = bytearray()
    for k in range(n):
        for t in range(w*h):
            o += px[(t//w)*8:(t//w)*8+8, k*w*8+(t%w)*8:k*w*8+(t%w)*8+8].tobytes()
    return bytes(o)
def build_prompt(F):
    import nitro
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    f = bytearray(F[1116]); G = nitro.rgcn(f); P = np.array(nitro.rlcn(F[1117])[:256], np.int32)
    px = _obj_strip(G['data'])
    used = sorted(set(px[px > 0].tolist()))
    def nearest(c): return int(((P - np.array(c))**2).sum(1).argmin())
    core = min(used, key=lambda i: (P[i][0] < 100) * 999 + P[i][1] + P[i][2] - P[i][0])   # 진한 빨강
    halo = sorted(used, key=lambda i: -(P[i][0] + P[i][1]))                                  # 밝은 순
    S = 4; Wd, H = 192*S, 32*S
    fnt = ImageFont.truetype(str(FD / 'NanumSquareNeo-eHv.ttf'), 15*S)
    s = 'A 버튼을 눌러 주세요'; tw = fnt.getbbox(s)[2]
    tm = Image.new('L', (Wd, H)); ImageDraw.Draw(tm).text(((Wd - tw)//2, 7*S), s, font=fnt, fill=255)
    tmask = np.array(tm.resize((192, 32), Image.LANCZOS)) > 110
    ring1 = cv2.dilate(tmask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    ring2 = cv2.dilate(tmask.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    out = np.zeros_like(px)
    out[ring2] = halo[min(len(halo)-1, len(halo)//2)]
    out[ring1] = halo[0]
    out[tmask] = core
    G2 = _obj_unstrip(out)
    f[0x30:0x30+len(G2)] = G2
    return bytes(f), out, P
