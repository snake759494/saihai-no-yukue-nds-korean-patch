"""그래픽 한글화 전체 적용: F(파일 목록)를 직접 수정."""
import gfx_tex, gfx_2k, gfx_panels, gfx_cards, gfx_cells, gfx_pack, stills, tags
def apply(F, tr_text, log=print):
    for k, v in stills.build(F).items(): F[k] = v
    F[1106] = tags.build(F)
    for k, v in gfx_tex.build(F, tr_text).items():
        F[k] = v if len(F[k]) == len(v) else v + F[k][len(v):]
    for k, v in gfx_2k.build(F).items(): F[k] = v
    for k, v in gfx_panels.build(F).items(): F[k] = v
    for k, b in gfx_cards.build(F).items(): F[k] = b.result()
    for k, b in gfx_cards.build_maps(F).items(): F[k] = b.result()
    F[805] = gfx_cards.build_logo(F).result()
    F[1116] = gfx_cards.build_prompt(F)[0]
    for cid, w, force in ((339, '개시', None), (343, '성공', None), (347, '실패', {334: 0, 379: 1}),
                          (835, '설득', None), (839, '설득', None), (840, '설득', None), (842, '성공', None)):
        b, g, _ = gfx_cells.process_blocks(F, cid, w, force=force); F[g] = b
    for cid, w, cy in ((836, '패배', False), (837, '승리', False), (838, '합전', False),
                       (683, '보고', True), (687, '전령', True), (841, '천안개시', False)):
        b, g = gfx_cells.process_text_cells(F, cid, w, False, cycle=cy); F[g] = b
    for cid in range(483, 533):
        b, g = gfx_cells.process_name(F, cid, gfx_cells.NAMES[cid - 483]); F[g] = b
    for i in range(1765, 1792): F[i] = gfx_pack.build_card(F, i)[0]
    F[1764] = gfx_pack.build_credits(F)[0]
    F[1792] = gfx_pack.render_end(F)[0]
    log('그래픽 적용 완료')
