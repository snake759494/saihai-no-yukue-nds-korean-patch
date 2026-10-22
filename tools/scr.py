import struct
BHDR = bytes([1, 0, 0, 0])
TAIL = 54
def _ok(d, q):
    if q + 4 > len(d): return False
    L, op = struct.unpack_from('<HH', d, q)
    return 0x20 <= L <= 0x600 and L % 2 == 0 and op <= 8 and q + L <= len(d)
def _chain(d, q, n=4):
    for _ in range(n):
        if q >= len(d) - 2: return True
        w = struct.unpack_from('<H', d, q)[0]
        if w == 1 or (w == 0 and len(d) - q == TAIL): return True
        if not _ok(d, q): return False
        q += w
    return True
def parse(d):
    """블록 헤더(첫 워드 1) / 레코드(첫 워드 = 길이) / 꼬리(0)를 끝까지 순회.
    블록 헤더의 가변부 길이는 뒤따르는 레코드 체인을 검증해 결정."""
    items = []; p = 0x16
    while p < len(d):
        L = struct.unpack_from('<H', d, p)[0]
        if L == 0 and len(d) - p == TAIL:
            items.append(('T', bytearray(d[p:]))); p = len(d); break
        if L == 1:
            q = p + 30
            while True:
                if q >= len(d) - 4: q = len(d); break
                if d[q:q+4] == BHDR: break
                if _ok(d, q) and _chain(d, q): break
                q += 2
            items.append(('B', bytearray(d[p:q]))); p = q
        else:
            assert _ok(d, p), hex(p)
            items.append(('R', bytearray(d[p:p+L]))); p += L
    assert p == len(d)
    return d[:0x16], items
def build(head, items):
    o = bytearray(head)
    for _, x in items: o += x
    return bytes(o)
