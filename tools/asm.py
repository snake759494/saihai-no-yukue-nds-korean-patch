"""ARM9 코드 패치: 문자표 이진탐색 함수 축약 + 글자 전진 폭 훅(공백 6px, 그 외 12px)."""
import keystone, struct
BASE = 0x2000000
SEARCH = 0x201c554; LIMIT = 0x201c5dc; CALLSITE = 0x201ce14
def assemble(table_addr, n, adv=12, space=6):
    src = f"""
search:
    push {{r4, lr}}
    ldr r3, tbl
    mov r1, #0
    ldr r2, cnt
lp:
    cmp r1, r2
    bge done
    add ip, r1, r2
    lsr ip, ip, #1
    add r4, r3, ip, lsl #1
    ldrh r4, [r4]
    cmp r4, r0
    addlo r1, ip, #1
    movhs r2, ip
    b lp
done:
    mov r0, r1
    pop {{r4, pc}}
tbl: .word {table_addr}
cnt: .word {n}
hook:
    ldr ip, [sp, #0x14]
    orrs ip, ip, r1
    addeq r6, r6, #{space}
    addne r6, r6, #{adv}
    bx lr
"""
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_ARM)
    code, _ = ks.asm(src, SEARCH)
    code = bytes(code)
    assert SEARCH + len(code) <= LIMIT, len(code)
    hook = SEARCH + len(code) - 20
    bl, _ = ks.asm(f"bl {hook}", CALLSITE)
    return code, bytes(bl)
def patch(arm9, **kw):
    a = bytearray(arm9)
    code, bl = assemble(**kw)
    a[SEARCH-BASE:SEARCH-BASE+len(code)] = code
    a[CALLSITE-BASE:CALLSITE-BASE+4] = bl
    return a
if __name__ == '__main__':
    c, b = assemble(0x2051c34, 1594)
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    for i in md.disasm(c, SEARCH): print(hex(i.address), i.mnemonic, i.op_str)
    for i in md.disasm(b, CALLSITE): print(hex(i.address), i.mnemonic, i.op_str)
