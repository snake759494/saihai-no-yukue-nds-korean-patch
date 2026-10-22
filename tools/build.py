"""한글 ROM 빌드."""
import sys, json, struct, re, glob
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndspy.rom, ndspy.codeCompression as cc
import ld, scr, units, auxfmt, font, asm, gfx_all
W = Path(__file__).resolve().parent.parent
ROM_IN = W.parent / 'Saihai no Yukue (Japan).nds'
ROM_OUT = W.parent / 'Saihai no Yukue (Korean).nds'
TBL = 0x51c34; N = 1594
F = ld.load()
arm9 = bytearray((W / 'ext/arm9d.bin').read_bytes())
T = [struct.unpack_from('<H', arm9, TBL + 2*i)[0] for i in range(N)]
# 번역 로드
src = {}; ko = {}
for f in sorted(glob.glob(str(W / 'translation/src/*.json'))):
    for u in json.load(open(f, encoding='utf8')): src[u['ja']] = u['id']
for f in sorted(glob.glob(str(W / 'translation/out/*.json'))):
    for k, v in json.load(open(f, encoding='utf8')).items(): ko[int(k)] = v
# 그래픽
def tr_text(ja):
    i = src.get(ja)
    return ko.get(i) if i is not None else None
gfx_all.apply(F, tr_text)
TAG = re.compile(r'【[^】]*】')
def norm(s):
    s = s.replace('\n', '\n')
    out = []
    for c in s:
        o = ord(c)
        if c == ' ': out.append('\u3000')
        elif 0x21 <= o <= 0x7e: out.append(chr(o + 0xfee0))
        else: out.append(c)
    return ''.join(out)
# 문자 집합
keep = {bytes([c >> 8, c & 255]).decode('cp932'): i for i, c in enumerate(T) if c < 0x829f}
need = set()
for v in ko.values():
    for part in TAG.split(norm(v)):
        for c in part:
            if ord(c) >= 0x20 and c not in keep: need.add(c)
need = sorted(need, key=lambda c: (not (0xac00 <= ord(c) <= 0xd7a3), c))
slots = [i for i, c in enumerate(T) if c >= 0x829f]
assert len(need) <= len(slots), (len(need), len(slots))
cmap = dict(keep)
for c, i in zip(need, slots): cmap[c] = i
def enc(s):
    s = norm(s); o = bytearray(); p = 0
    for m in TAG.finditer(s):
        o += _e(s[p:m.start()]); o += m.group().encode('cp932'); p = m.end()
    o += _e(s[p:]); return bytes(o)
def _e(t):
    o = bytearray()
    for c in t:
        if ord(c) < 0x20: o.append(ord(c)); continue
        code = T[cmap[c]]; o += bytes([code >> 8, code & 255])
    return o
def tr(b):
    t = b.decode('cp932')
    if t not in src: return b
    i = src[t]
    if i not in ko: print('미번역', i); return b
    return enc(ko[i])
# 폰트
g11 = font.read_bdf(str(W / 'fonts/galmuri/Galmuri11.bdf'))
fnt = bytearray(F[0])
for c, i in cmap.items():
    if c in keep: continue
    x0, y0 = font.cell(i)
    for y in range(14):
        for x in range(14): font.setpx(fnt, x0+x, y0+y, 0)
    gl = g11.get(ord(c))
    if not gl: print('글리프 없음', c); continue
    off = 1 if 0xac00 <= ord(c) <= 0xd7a3 else max(0, (12 - gl['dw']) // 2)
    for (x, y) in font.bitmap(gl, 12):
        if 0 <= x+off < 14 and 0 <= y < 14: font.setpx(fnt, x0+x+off, y0+y, 1)
# 공백(0번) 비우기
for y in range(14):
    for x in range(14): font.setpx(fnt, x, y, 0)
F[0] = bytes(fnt)
# 스크립트
for i in range(712, 735):
    h, it = scr.parse(F[i])
    for n, (k, x) in enumerate(it):
        if k != 'R': continue
        s = units.text_start(x)
        if s is None: continue
        it[n] = (k, units.join(x, s, [tr(p) for p in units.split(x, s)]))
    F[i] = scr.build(h, it)
r, tail = auxfmt.p711(F[711])
for n, x in enumerate(r):
    ps = [tr(p) for p in bytes(x[8:]).rstrip(b'\0').split(b'\0')]
    body = b'\0'.join(ps) + b'\0'
    rec = bytearray(x[:8]) + body
    while len(rec) % 4: rec += b'\0'
    struct.pack_into('<H', rec, 2, len(rec)); r[n] = rec
F[711] = auxfmt.b711(r, tail)
h, g = auxfmt.p735(F[735])
for gi, (cnt, gg) in enumerate(g):
    for n, x in enumerate(gg): gg[n] = units.join(x, 0x28, [tr(p) for p in units.split(x, 0x28)])
F[735] = auxfmt.b735(h, g)
# LINKDATA 재구성
blob = bytearray(); idx = bytearray(struct.pack('<II', 5262, 0))
for f in F:
    idx += struct.pack('<II', len(blob), len(f)); blob += f
    while len(blob) % 0x200: blob += b'\0'
orig_idx = (W / 'ext/LINKDATAIDX.bin').read_bytes()
idx += orig_idx[len(idx):]
# ARM9
arm9 = asm.patch(arm9, table_addr=0x2000000 + TBL, n=N)
rom = ndspy.rom.NintendoDSRom.fromFile(str(ROM_IN))
rom.files[0] = bytes(blob); rom.files[1] = bytes(idx)
m = rom.loadArm9()
sec = m.sections[0]
sec.data = bytearray(sec.data); sec.data[:] = arm9[:len(sec.data)]
rom.arm9 = m.save(compress=True)
rom.saveToFile(str(ROM_OUT))
print('글자', len(need), '/', len(slots), '번역', len(ko), '/', len(src), ROM_OUT.stat().st_size)
