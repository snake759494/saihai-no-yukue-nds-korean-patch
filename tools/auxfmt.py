"""711(인물 사전)·735(메모) 파서."""
import struct
def p711(d):
    recs = []; p = 0
    while p + 4 <= len(d):
        idx, L = struct.unpack_from('<HH', d, p)
        if L == 0: break
        recs.append(bytearray(d[p:p+L])); p += L
    return recs, d[p:]
def b711(recs, tail):
    return b''.join(recs) + tail
def p735(d):
    head = d[:0x20]; p = 0x20; groups = []
    while p < len(d):
        n = struct.unpack_from('<H', d, p)[0]; p += 2
        g = []
        for _ in range(n):
            L = struct.unpack_from('<H', d, p)[0]
            g.append(bytearray(d[p:p+L])); p += L
        groups.append((n, g))
    return head, groups
def b735(head, groups):
    o = bytearray(head)
    for n, g in groups:
        o += struct.pack('<H', len(g))
        for r in g: o += r
    return bytes(o)
