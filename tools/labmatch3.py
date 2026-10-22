"""전투별 참전 무장 명단으로 후보를 제한한 부대 이름표 대조."""
import sys, json, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, __import__('os').path.dirname(__file__))
import ld, tex
from pathlib import Path
W = Path(__file__).resolve().parent.parent
F = ld.load()
P = {  # 전체 이름: (성, 이름, 한국어 성, 한국어 이름)
 '石田三成': ('石田', '三成', '이시다', '미쓰나리'), '島左近': ('島', '左近', '시마', '사콘'), '宇喜多秀家': ('宇喜多', '秀家', '우키타', '히데이에'),
 '大谷吉継': ('大谷', '吉継', '오타니', '요시쓰구'), '小早川秀秋': ('小早川', '秀秋', '고바야카와', '히데아키'), '島津義弘': ('島津', '義弘', '시마즈', '요시히로'),
 '島津豊久': ('島津', '豊久', '시마즈', '도요히사'), '吉川広家': ('吉川', '広家', '깃카와', '히로이에'), '毛利秀元': ('毛利', '秀元', '모리', '히데모토'),
 '安国寺恵瓊': ('安国寺', '恵瓊', '안코쿠지', '에케이'), '小西行長': ('小西', '行長', '고니시', '유키나가'), '徳川家康': ('徳川', '家康', '도쿠가와', '이에야스'),
 '本多忠勝': ('本多', '忠勝', '혼다', '다다카쓰'), '井伊直政': ('井伊', '直政', '이이', '나오마사'), '福島正則': ('福島', '正則', '후쿠시마', '마사노리'),
 '黒田長政': ('黒田', '長政', '구로다', '나가마사'), '細川忠興': ('細川', '忠興', '호소카와', '다다오키'), '藤堂高虎': ('藤堂', '高虎', '도도', '다카토라'),
 'ニセ高虎': ('藤堂', '高虎', '도도', '다카토라'), '田中吉政': ('田中', '吉政', '다나카', '요시마사'), '池田輝政': ('池田', '輝政', '이케다', '데루마사'),
 'お勝の方': ('お勝', 'お勝の方', '오카쓰', '오카쓰노카타'), '明石全登': ('明石', '全登', '아카시', '다케노리'), '可児才蔵': ('可児', '才蔵', '가니', '사이조'),
 '稲葉貞通': ('稲葉', '貞通', '이나바', '사다미치'), '筒井定次': ('筒井', '定次', '쓰쓰이', '사다쓰구'), '阿多盛淳': ('阿多', '盛淳', '아타', '모리아쓰'),
 '舞兵庫': ('舞', '兵庫', '마이', '효고'), '竹中重門': ('竹中', '重門', '다케나카', '시게카도'), '加藤嘉明': ('加藤', '嘉明', '가토', '요시아키'),
 '平塚為広': ('平塚', '為広', '히라쓰카', '다메히로'), '戸田勝成': ('戸田', '勝成', '도다', '가쓰시게'), '京極高知': ('京極', '高知', '교고쿠', '다카토모'),
 '戸川達安': ('戸川', '達安', '도가와', '다쓰야스'), '蒲生郷舎': ('蒲生', '郷舎', '가모', '사토이에'), '稲葉正成': ('稲葉', '正成', '이나바', '마사나리'),
 '松野重元': ('松野', '重元', '마쓰노', '시게모토'), '平岡頼勝': ('平岡', '頼勝', '히라오카', '요리카쓰'), '奥平貞治': ('奥平', '貞治', '오쿠다이라', '사다하루'),
 '織田長益': ('織田', '長益', '오다', '나가마스'), '金森長近': ('金森', '長近', '가나모리', '나가치카'), '生駒一正': ('生駒', '一正', '이코마', '가즈마사'),
 '松平忠吉': ('松平', '忠吉', '마쓰다이라', '다다요시'), '赤座直保': ('赤座', '直保', '아카자', '나오야스'), '小川祐忠': ('小川', '祐忠', '오가와', '스케타다'),
 '朽木元綱': ('朽木', '元綱', '구쓰키', '모토쓰나'), '脇坂安治': ('脇坂', '安治', '와키자카', '야스하루'), '寺沢広高': ('寺沢', '広高', '데라자와', '히로타카'),
 '長束正家': ('長束', '正家', '나쓰카', '마사이에'), '長宗我部盛親': ('長宗我部', '盛親', '조소카베', '모리치카'), '山内一豊': ('山内', '一豊', '야마노우치', '가즈토요'),
 '浅野幸長': ('浅野', '幸長', '아사노', '요시나가'),
}
battles = json.loads((W / 'translation/labels/battles.json').read_text(encoding='utf8'))
pools = {}
for b in battles: pools.setdefault(b['file'], set()).update(n for n in b['names'] if n in P)
fnt = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 24)
def cand_img(s, w, h):
    im = Image.new('L', (24*len(s) + 4, 26)); ImageDraw.Draw(im).text((0, 0), s, font=fnt, fill=255)
    a = np.array(im, np.float32); ys, xs = np.nonzero(a > 80)
    a = a[ys.min():ys.max()+1, xs.min():xs.max()+1]
    return cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)
def norm(a):
    a = a - a.mean(); n = np.linalg.norm(a); return a / n if n else a
def cells(i):
    px = np.array(tex.dec(F[i][:8192]))
    for k in range(10):
        y0 = 1 + 6*k
        if y0 + 6 > 64: break
        for c in range(8):
            core = (px[y0:y0+6, c*32:c*32+32] == 2).astype(np.float32)
            if core.sum() < 4: continue
            ys, xs = np.nonzero(core)
            yield f'{i}_{k}_{c}', core[ys.min():ys.max()+1, xs.min():xs.max()+1]
def forms(names):
    out = [('？？？', '？？？')]
    for n in names:
        s, g, ks, kg = P[n]; out += [(s, ks), (g, kg)]
    return out
def score(core, ja):
    h, w = core.shape
    if ja == '？？？': ja = '？？？'
    if abs(len(ja) * 8.5 - w) > 9: return -1
    return float((norm(core) * norm(cand_img(ja, w, h))).sum())
res = {}; info = {}
for i in range(1125, 1140):
    cs = list(cells(i))
    best_file = None; best_tot = -1e9
    for f, pool in pools.items():
        fm = forms(pool)
        tot = sum(max((score(c, ja) for ja, _ in fm), default=0) for _, c in cs)
        if tot > best_tot: best_tot, best_file = tot, f
    fm = forms(pools[best_file])
    info[i] = best_file
    for key, c in cs:
        sc = sorted(((score(c, ja), ja, ko) for ja, ko in fm), reverse=True)
        res[key] = sc[:3]
json.dump({k: v[0][2] for k, v in res.items() if v and v[0][0] > 0}, open(W / 'translation/labels/out_auto3.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print(info)
low = [(k, v[:2]) for k, v in res.items() if not v or v[0][0] < 0.35]
print('low', len(low), 'of', len(res))
for k, v in list(res.items())[:25]: print(k, [(round(s, 2), j) for s, j, _ in v])
# 같은 비트맵 묶음 합의
import collections
groups = collections.defaultdict(list); allsc = {}
for i in range(1125, 1140):
    fm = forms(pools[info[i]])
    for key, c in cells(i):
        groups[c.tobytes() + bytes(c.shape)].append(key)
        allsc[key] = {ko: score(c, ja) for ja, ko in fm}
final = {}
for g in groups.values():
    tot = collections.Counter()
    for k in g:
        for ko, s in allsc[k].items():
            if s > -1: tot[ko] += s
    pick = tot.most_common(1)[0][0] if tot else '？？？'
    for k in g: final[k] = pick
json.dump(final, open(W / 'translation/labels/out_final.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print('groups', len(groups), 'final', len(final))
