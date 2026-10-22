import struct
from pathlib import Path
W=Path(__file__).resolve().parent.parent
def load():
    idx=(W/'ext/LINKDATAIDX.bin').read_bytes();d=(W/'ext/LINKDATA.bin').read_bytes()
    n=(len(idx)-8)//8
    return [d[o:o+s] for o,s in (struct.unpack_from('<2I',idx,8+i*8) for i in range(n))]
