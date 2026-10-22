"""256×192 8bpp 비트맵(파일 i, 팔레트 i+512 또는 지정) 글자 지우기·다시 쓰기."""
import numpy as np, cv2
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import bmp8, tex
W = Path(__file__).resolve().parent.parent
class Bmp:
    def __init__(self, data, pal):
        self.idx = np.array(bmp8.to_idx(data), np.uint8)
        self.P = np.array(bmp8.pal(pal)[:256], np.int32)
        self.rgb = self.P[self.idx].astype(np.uint8)
        self.changed = np.zeros(self.idx.shape, bool)
    def inpaint(self, mask, r=3):
        m = cv2.dilate(mask.astype(np.uint8)*255, np.ones((3, 3), np.uint8), iterations=1)
        self.rgb = cv2.inpaint(self.rgb, m, r, cv2.INPAINT_TELEA)
        self.changed |= m > 0
    def draw_pts(self, pts, x0, y0, col, ol=None, sh=None):
        H, Wd = self.idx.shape
        def setp(x, y, c):
            if 0 <= x < Wd and 0 <= y < H: self.rgb[y, x] = c; self.changed[y, x] = True
        if ol is not None:
            for (a, b) in pts:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if (a+dx, b+dy) not in pts: setp(x0+a+dx, y0+b+dy, ol)
        if sh is not None:
            for (a, b) in pts:
                if (a+1, b+1) not in pts: setp(x0+a+1, y0+b+1, sh)
        for (a, b) in pts: setp(x0+a, y0+b, col)
    def text(self, r, s, name='Galmuri11', col=(255, 255, 255), ol=None, sh=None, align='l', lh=None, ttf=None, size=None):
        lines = s.split('\n'); x, y, w, h = r
        if ttf:
            ms = []
            for sz in range(size, 7, -1):
                ms = [tex.ttf_mask(l, ttf, sz) for l in lines]
                if max(m[1] for m in ms) <= w: break
            lh = lh or sz + 2
        else:
            for nm in [name, 'Galmuri11-Condensed', 'Galmuri9', 'Galmuri7']:
                ms = [tex.bdf_mask(l, nm) for l in lines]
                if max(m[1] for m in ms) <= w: break
            lh = lh or ms[0][2] + 2
        tot = lh * len(lines); yy = y + (h - tot)//2
        for i, (pts, lw, asc) in enumerate(ms):
            xx = x + (w - lw)//2 if align == 'c' else (x + w - lw if align == 'r' else x)
            off = 0 if ttf else -(asc - lh + 2) // 2
            self.draw_pts(pts, xx, yy + i*lh + (0 if ttf else 0) - (1 if not ttf else 2), col, ol, sh)
    def result(self):
        out = self.idx.copy()
        ys, xs = np.nonzero(self.changed)
        if len(ys):
            c = self.rgb[ys, xs].astype(np.int32)
            d = ((c[:, None, :] - self.P[None, :, :])**2).sum(2)
            out[ys, xs] = d.argmin(1)
        return bmp8.from_idx(out.tolist())
    def img(self):
        return Image.fromarray(self.P[np.array(bmp8.to_idx(self.result()))].astype(np.uint8))
def lum(a): return a[..., 0]*0.3 + a[..., 1]*0.59 + a[..., 2]*0.11
