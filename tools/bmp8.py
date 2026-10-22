"""256×192 8bpp 타일 비트맵(801/802/805/806 등) 변환."""
import struct
from PIL import Image
def pal(b): return [((c&31)<<3, (c>>5&31)<<3, (c>>10&31)<<3) for c in struct.unpack(f'<{len(b)//2}H', b)]
def to_idx(d, w=256, h=192):
    tw = w // 8; px = [[0]*w for _ in range(h)]
    for t in range(len(d) // 64):
        tx, ty = t % tw, t // tw
        for y in range(8):
            for x in range(8): px[ty*8+y][tx*8+x] = d[t*64 + y*8 + x]
    return px
def from_idx(px):
    h = len(px); w = len(px[0]); tw = w // 8; o = bytearray(w*h)
    for ty in range(h//8):
        for tx in range(tw):
            t = ty*tw + tx
            for y in range(8):
                for x in range(8): o[t*64 + y*8 + x] = px[ty*8+y][tx*8+x]
    return bytes(o)
def img(px, P):
    im = Image.new('RGB', (len(px[0]), len(px))); im.putdata([P[v] for r in px for v in r]); return im
