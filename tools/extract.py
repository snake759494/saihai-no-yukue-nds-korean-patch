"""모든 표시 문자열을 고유 단위로 추출 → translation/src/*.json"""
import sys, json, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ld, scr, units, auxfmt
W = Path(__file__).resolve().parent.parent
F = ld.load()
order = {}   # ja -> (first file, kind)
def add(b, where):
    t = b.decode('cp932')
    if t and t not in order: order[t] = where
r, _ = auxfmt.p711(F[711])
for x in r:
    for s in bytes(x[8:]).rstrip(b'\0').split(b'\0'): add(s, 'dict')
for i in range(712, 735):
    h, it = scr.parse(F[i])
    for k, x in it:
        if k != 'R': continue
        s = units.text_start(x)
        if s is None: continue
        for p in units.split(x, s): add(p, f'{i}')
h, g = auxfmt.p735(F[735])
for n, gg in g:
    for x in gg:
        for s in bytes(x[0x28:]).rstrip(b'\0').split(b'\0'): add(s, 'memo')
out = W / 'translation/src'; out.mkdir(parents=True, exist_ok=True)
items = list(order.items())
CH = 400
for c in range(0, len(items), CH):
    part = [{'id': c + j, 'where': w, 'ja': t} for j, (t, w) in enumerate(items[c:c+CH])]
    (out / f'{c//CH:03d}.json').write_text(json.dumps(part, ensure_ascii=False, indent=0), encoding='utf8')
print(len(items), sum(len(t) for t, _ in items))
