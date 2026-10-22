"""스크린샷 영역의 「이웃 화소 같음」 패턴으로 LINKDATA 선형 텍스처 위치 찾기."""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, __import__('os').path.dirname(__file__))
import ld
def find(img_path, x, y, w=30, h=10, widths=(32, 64, 128, 256)):
    F = ld.load()
    im = np.array(Image.open(img_path).convert('RGB')).astype(int)
    win = im[y:y+h, x:x+w+1]
    tk = (win[:, 1:] == win[:, :-1]).all(-1).astype(np.uint8)
    hits = []
    for i, f in enumerate(F):
        if len(f) < 512: continue
        a = np.frombuffer(f, np.uint8)
        v4 = np.empty(a.size*2, np.uint8); v4[0::2] = a & 15; v4[1::2] = a >> 4
        for name, v in (('4', v4), ('8', a)):
            for W in widths:
                H = v.size // W
                if H < h: continue
                g = v[:H*W].reshape(H, W)
                e = (g[:, 1:] == g[:, :-1]).astype(np.uint8)
                e = np.concatenate([e, np.full((H, 1), 2, np.uint8)], 1)
                s = e.tobytes(); t = tk[0].tobytes(); p = s.find(t)
                while p >= 0:
                    yy, xx = divmod(p, W)
                    if yy + h <= H and xx + w <= W - 1 and (e[yy:yy+h, xx:xx+w] == tk).all(): hits.append((i, name, W, yy, xx))
                    p = s.find(t, p + 1)
    return hits
if __name__ == '__main__':
    a = sys.argv; print(find(a[1], int(a[2]), int(a[3]), int(a[4]) if len(a) > 4 else 30, int(a[5]) if len(a) > 5 else 10))
