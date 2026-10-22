"""LINKDATA의 RECN/RNAN/RGCN/RLCN 묶음 대응표."""
def runs(T, i, tag):
    s = i
    while i < len(T) and T[i] == tag: i += 1
    return s, i
def cell_groups(F):
    T = [f[:4] for f in F]; out = []; i = 0
    while i < len(T):
        if T[i] == b'RECN':
            s, e = runs(T, i, b'RECN'); n = e - s
            a = e; g = a + n if T[a] == b'RNAN' else a
            if T[a] != b'RNAN': g = a
            p = g + n
            for k in range(n):
                out.append({'cell': s + k, 'anim': (a + k) if T[a] == b'RNAN' else None, 'gfx': g + k, 'pal': p + k})
            i = p + n
        else: i += 1
    return out
