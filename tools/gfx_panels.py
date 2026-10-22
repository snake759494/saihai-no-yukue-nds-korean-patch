"""전투 작전 패널(4344~4350) 한글화."""
import numpy as np
from gfx_bmp import Bmp, lum
M1 = '「작전: 기마 돌격」 발동을\n위해 그림처럼 배치하라!'
M2 = '「작전: 대포」 발동을\n위해 그림처럼 배치하라!'
M3 = '「작전: 철포 사격」 발동을\n위해 그림처럼 배치하라!'
M4 = '「작전: 기마 돌격」 및\n「작전: 철포 사격」 발동을\n위해 그림처럼 배치하라!'
P = {
 4344: (4, M1, [('호소카와', '후퇴에만 전념한다……'), ('구로다', '사콘대를 추격하라!'), ('가토', '사콘대를 추격하라!')]),
 4345: (5, M2, [('가모', '대포를 지키며 대기하라!'), ('구로다', '사콘대를 추격하라!'), ('다케나카', '후퇴해 수비에 전념한다!'), ('가토', '사콘대를 추격하라!'), ('호소카와', '대기한다……')]),
 4346: (3, M4, [('아타', '이 자리에서 맞서 싸워라!'), ('도도', '요시히로대를 추격하라!'), ('오카쓰', '아타대를 치겠습니다!'), ('오다', '아타대를 추격하라!'), ('다나카', '요시히로대를 추격할까……'), ('데라자와', '수비에 전념한다!')]),
 4347: (3, M1, [('이케다', '이 자리를 사수한다!'), ('아사노', '이케다대와 합류하라!'), ('다다카쓰', '이케다대와 합류하라!'), ('아타', '다다카쓰대를 추격하라!')]),
 4348: (5, M3, [('교고쿠', '요시히로대를 추격하라!'), ('다다카쓰', '요시히로대를 추격하라!'), ('오다', '요시히로대를 추격하라!')]),
 4349: (4, M3, [('조소카베', '나쓰카대를 엄호하라!'), ('이케다', '나쓰카대를 추격하라!'), ('구로다', '조소카베대를 추격하라!'), ('가토', '나쓰카대를 추격하라!')]),
 4350: (7, M3, [('이에야스', '요시히로대를 추격하라!'), ('고바야카와', '요시히로대를 추격하라!'), ('이이', '요시히로대를 추격하라!'), ('다다카쓰', '조소카베대를 추격하라!'), ('조소카베', '다다카쓰대를 끌어들여라!')]),
}
def bands(mask, gap=2):
    rows = np.nonzero(mask.any(1))[0]; out = []
    for y in rows:
        if out and y - out[-1][1] <= gap: out[-1][1] = y
        else: out.append([y, y])
    return out
def mean_col(rgb, m):
    c = rgb[m]
    return tuple(int(v) for v in c.mean(0)) if len(c) else (255, 255, 255)
def build_one(data, pal, spec):
    n, mission, rows = spec
    b = Bmp(data, pal); a = b.rgb.astype(int); L = lum(a)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    # 머리말 상자(수)
    hm = np.zeros(L.shape, bool); hm[4:30, 150:250] = L[4:30, 150:250] > 175
    # 작전 문구(초록)
    mm = np.zeros(L.shape, bool); mm[30:76, 100:252] = (G[30:76, 100:252] > 140) & (G[30:76, 100:252] > R[30:76, 100:252] + 20)
    # 막대 줄: 이름(어두운 붉은색/검정) + 명령(파랑/빨강)
    om = np.zeros(L.shape, bool)
    blue = (B > R + 40) & (B > G + 30); red = (R > G + 70) & (R > B + 40)
    om[70:, 100:252] = (blue | red)[70:, 100:252]
    obands = bands(om)
    oc = [mean_col(b.rgb, om & (np.arange(192)[:, None] >= y0) & (np.arange(192)[:, None] <= y1)) for y0, y1 in obands]
    hcol = (255, 255, 255); mcol = mean_col(b.rgb, mm)
    boxes = []; ncols = []
    for y0, y1 in obands:
        wm = np.zeros(L.shape, bool); wm[y0-5:y1+6, 60:112] = L[y0-5:y1+6, 60:112] > 200
        ys, xs = np.nonzero(wm)
        bx = (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else (66, y0-3, 100, y1+3)
        boxes.append(bx)
        inner = np.zeros(L.shape, bool); inner[bx[1]:bx[3]+1, bx[0]:bx[2]+1] = True
        tm = inner & (L < 170)
        ncols.append(mean_col(b.rgb, tm & (L < 120)))
        b.rgb[bx[1]:bx[3]+1, bx[0]:bx[2]+1] = b.rgb[ys.min(), xs.min()] if len(xs) else (255, 255, 255)
        b.changed[bx[1]:bx[3]+1, bx[0]:bx[2]+1] = True
    full = hm | mm | om
    b.inpaint(full)
    b.text((152, 7, 92, 20), f'제한 {n}수', 'Galmuri14', col=hcol, sh=(40, 50, 20), align='c')
    three = mission.count(chr(10)) >= 2
    b.text((104, 31, 148, 40), mission, 'Galmuri9' if three else 'Galmuri11', col=mcol, align='c', lh=10 if three else 12)
    assert len(obands) == len(rows), (len(obands), len(rows))
    for (y0, y1), bx, (name, order), c, ncol in zip(obands, boxes, rows, oc, ncols):
        cy = (y0 + y1)//2
        b.text((bx[0], bx[1], bx[2]-bx[0]+1, bx[3]-bx[1]+1), name, 'Galmuri9', col=ncol, align='c')
        b.text((104, cy - 7, 146, 14), order, 'Galmuri11', col=c)
    return b
def build(F):
    return {i: build_one(F[i], F[i+512], s).result() for i, s in P.items()}
