"""LINKDATA 0번 폰트 시트(RGCN 4bpp, 112×50 타일, 64열×14px 셀) 읽기/쓰기 + BDF 로더."""
import struct
HDR = 0x30; TW = 112
def getpx(data, x, y):
    t = (y >> 3) * TW + (x >> 3); o = HDR + t * 32 + (y & 7) * 4 + ((x & 7) >> 1)
    return (data[o] >> (4 * (x & 1))) & 15
def setpx(data, x, y, v):
    t = (y >> 3) * TW + (x >> 3); o = HDR + t * 32 + (y & 7) * 4 + ((x & 7) >> 1)
    sh = 4 * (x & 1); data[o] = (data[o] & ~(15 << sh)) | (v << sh)
def cell(i): return (i & 63) * 14, (i >> 6) * 14
def read_bdf(path):
    g = {}; cur = None
    with open(path, encoding='latin1') as f:
        for line in f:
            w = line.split()
            if not w: continue
            if w[0] == 'ENCODING': cur = {'enc': int(w[1])}
            elif w[0] == 'DWIDTH' and cur is not None: cur['dw'] = int(w[1])
            elif w[0] == 'BBX' and cur is not None: cur['bbx'] = tuple(map(int, w[1:5]))
            elif w[0] == 'BITMAP': cur['rows'] = []
            elif w[0] == 'ENDCHAR': g[cur['enc']] = cur; cur = None
            elif cur is not None and 'rows' in cur: cur['rows'].append(int(w[0], 16) << (8 - len(w[0]) * 4 % 8 if len(w[0]) * 4 % 8 else 0) if False else (int(w[0], 16), len(w[0]) * 4))
    return g
def bitmap(gl, ascent):
    """(x,y) 픽셀 집합. y는 셀 상단 기준(ascent=베이스라인 위치)."""
    w, h, xo, yo = gl['bbx']; pts = set()
    for r, (v, nb) in enumerate(gl['rows']):
        for c in range(w):
            if v >> (nb - 1 - c) & 1: pts.add((xo + c, ascent - yo - h + r))
    return pts
