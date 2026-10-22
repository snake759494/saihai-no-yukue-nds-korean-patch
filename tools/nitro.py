"""RGCN/RLCN 최소 파서·렌더러."""
import struct
from PIL import Image
def rgcn(f):
    # RGCN 헤더 0x10, RAHC 블록
    p = 0x10
    assert f[p:p+4] == b'RAHC'
    th, tw, bpp = struct.unpack_from('<HHI', f, p + 8)
    dlen, doff = struct.unpack_from('<II', f, p + 0x18)
    data = f[p + 8 + doff - 8 + 8: ][:dlen] if False else f[p + 0x20: p + 0x20 + dlen]
    return {'th': th, 'tw': tw, 'bpp': bpp, 'data': data, 'map': struct.unpack_from('<I', f, p + 0x14)[0]}
def rlcn(f):
    p = 0x10
    bpp, _, dlen, doff = struct.unpack_from('<IIII', f, p + 8)
    d = f[p + 0x18: p + 0x18 + dlen]
    return [((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3) for c in struct.unpack_from(f'<{len(d)//2}H', d)]
def render(g, pal, width_tiles=None):
    bpp = 8 if g['bpp'] == 4 else 4
    tb = 64 if bpp == 8 else 32
    n = len(g['data']) // tb
    tw = width_tiles or (g['tw'] if 0 < g['tw'] < 0x100 and g['tw'] * max(1, g['th']) == n else 32)
    th = (n + tw - 1) // tw
    im = Image.new('RGB', (tw * 8, th * 8))
    px = im.load()
    for t in range(n):
        tx, ty = t % tw, t // tw
        for y in range(8):
            for x in range(8):
                if bpp == 8: v = g['data'][t*64 + y*8 + x]
                else:
                    b = g['data'][t*32 + y*4 + x//2]; v = (b >> (4 * (x & 1))) & 15
                px[tx*8+x, ty*8+y] = pal[v] if v < len(pal) else (255, 0, 255)
    return im
SHAPES = {(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),(1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),(2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}
def recn(f):
    p = 0x10
    n, attr, coff = struct.unpack_from('<HHI', f, p + 8)
    base = p + 8 + coff
    esz = 16 if attr & 1 else 8
    oambase = base + n * esz
    cells = []
    for c in range(n):
        no, cat, ooff = struct.unpack_from('<HHI', f, base + c * esz)
        objs = []
        for k in range(no):
            a0, a1, a2 = struct.unpack_from('<HHH', f, oambase + ooff + k * 6)
            y = a0 & 0xff; y = y - 256 if y >= 128 else y
            x = a1 & 0x1ff; x = x - 512 if x >= 256 else x
            w, h = SHAPES[(a0 >> 14, a1 >> 14)]
            objs.append({'x': x, 'y': y, 'w': w, 'h': h, 'tile': a2 & 0x3ff, 'pal': a2 >> 12, 'bpp8': bool(a0 & 0x2000), 'hf': bool(a1 & 0x1000), 'vf': bool(a1 & 0x2000)})
        cells.append(objs)
    return cells
def render_cell(objs, g, pal, unit=32):
    if not objs: return None
    x0 = min(o['x'] for o in objs); y0 = min(o['y'] for o in objs)
    x1 = max(o['x'] + o['w'] for o in objs); y1 = max(o['y'] + o['h'] for o in objs)
    im = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0)); px = im.load()
    d = g['data']
    for o in reversed(objs):
        tb = 64 if o['bpp8'] else 32
        base = o['tile'] * unit
        tw = o['w'] // 8
        for ty in range(o['h'] // 8):
            for tx in range(tw):
                off = base + (ty * tw + tx) * tb
                for y in range(8):
                    for x in range(8):
                        if o['bpp8']:
                            if off + y*8 + x >= len(d): continue
                            v = d[off + y*8 + x]; c = pal[v] if v < len(pal) else (255,0,255)
                        else:
                            if off + y*4 + x//2 >= len(d): continue
                            b = d[off + y*4 + x//2]; v = (b >> (4*(x&1))) & 15
                            c = pal[o['pal']*16 + v] if o['pal']*16+v < len(pal) else (255,0,255)
                        if v == 0: continue
                        X = tx*8 + x; Y = ty*8 + y
                        if o['hf']: X = o['w'] - 1 - X
                        if o['vf']: Y = o['h'] - 1 - Y
                        px[o['x'] - x0 + X, o['y'] - y0 + Y] = c + (255,)
    return im
def strip_img(data, pal, blocks=4, bw=8, bh=8):
    """64×64 OBJ 블록(타일 64개)을 가로로 이어 붙인 4bpp 그림."""
    im = Image.new('RGB', (blocks * bw * 8, bh * 8)); px = im.load()
    for b in range(blocks):
        for t in range(bw * bh):
            tt = b * bw * bh + t
            for y in range(8):
                for x in range(8):
                    o = tt * 32 + y * 4 + x // 2
                    if o >= len(data): continue
                    v = (data[o] >> (4 * (x & 1))) & 15
                    px[b * bw * 8 + (t % bw) * 8 + x, (t // bw) * 8 + y] = pal[v]
    return im
