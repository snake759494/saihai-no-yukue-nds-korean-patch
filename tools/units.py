"""스크립트(712~734) 번역 단위 추출/삽입 공용."""
import struct
import scr
MSG = {5, 6, 8}
def _valid_tail(b):
    try: t = b.decode('cp932')
    except UnicodeDecodeError: return False
    parts = t.split('\0')
    if parts[-1] != '': return False
    ok = False
    for s in parts[:-1]:
        if s == '': continue
        if not all(c.isprintable() or c == '\n' for c in s): return False
        if not any(ord(c) > 0x2000 for c in s): return False
        ok = True
    return ok
def text_start(rec):
    fl, cmd = struct.unpack_from('<HH', rec, 2)
    if fl < 2:
        return 0x28 if cmd in MSG else None
    if fl not in (2, 3, 5, 6): return None
    for s in range(0x28, len(rec), 2):
        if rec[s-2:s] in (b'\0\0', b'\x0f\x27', b'\xff\x00') and _valid_tail(bytes(rec[s:])):
            return s
    return None
def split(rec, s):
    return bytes(rec[s:]).rstrip(b'\0').split(b'\0')
def join(rec, s, parts):
    body = b'\0'.join(parts) + b'\0'
    if (s + len(body)) % 2: body += b'\0'
    new = bytearray(rec[:s]) + body
    struct.pack_into('<H', new, 0, len(new))
    return new
