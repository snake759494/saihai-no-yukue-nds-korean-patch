"""LZ11 압축 PACK(PAL/CHR/SCR) 파서·렌더러."""
import struct
from PIL import Image
import lz
def unpack(raw):
    d = lz.lz11(raw); n = struct.unpack_from('<I', d, 4)[0]
    return d, [struct.unpack_from('<II', d, 8 + 8 * k) for k in range(n)]
def pal(b):
    return [((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3) for c in struct.unpack_from(f'<{(len(b)-16)//2}H', b, 16)]
def chr_info(b):
    size, bppf = struct.unpack_from('<II', b, 4)
    return (8 if bppf == 0x40 else 4), b[16:16 + size]
def tile_px(data, bpp, t, x, y):
    if bpp == 8: return data[t*64 + y*8 + x]
    v = data[t*32 + y*4 + x//2]; return (v >> (4*(x&1))) & 15
def render_tiles(data, bpp, P, tw=32):
    n = len(data) // (64 if bpp == 8 else 32); th = (n + tw - 1)//tw
    im = Image.new('RGB', (tw*8, th*8)); px = im.load()
    for t in range(n):
        for y in range(8):
            for x in range(8):
                v = tile_px(data, bpp, t, x, y)
                px[(t%tw)*8+x, (t//tw)*8+y] = P[v] if v < len(P) else (255,0,255)
    return im
def render_scr(scr, data, bpp, P):
    size, _, w, h = struct.unpack_from('<IIHH', scr, 4)
    m = struct.unpack_from(f'<{w*h}H', scr, 16)
    im = Image.new('RGB', (w*8, h*8)); px = im.load()
    for i, e in enumerate(m):
        t = e & 0x3ff; hf = e >> 10 & 1; vf = e >> 11 & 1; pl = e >> 12
        for y in range(8):
            for x in range(8):
                sx = 7-x if hf else x; sy = 7-y if vf else y
                try: v = tile_px(data, bpp, t, sx, sy)
                except IndexError: v = 0
                c = (pl*16 + v) if bpp == 4 else v
                px[(i%w)*8+x, (i//w)*8+y] = P[c] if c < len(P) else (255,0,255)
    return im
