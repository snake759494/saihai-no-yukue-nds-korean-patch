"""일본어 → 기존 번역 찾기. 사용: python -X utf8 tools/lookup.py "文字列" """
import sys, json, glob, difflib
from pathlib import Path
W = Path(__file__).resolve().parent.parent
src = {}; ko = {}
for f in glob.glob(str(W / 'translation/src/*.json')):
    for u in json.load(open(f, encoding='utf8')): src[u['ja']] = u['id']
for f in glob.glob(str(W / 'translation/out/*.json')):
    for k, v in json.load(open(f, encoding='utf8')).items(): ko[int(k)] = v
q = sys.argv[1]
if q in src: print('일치:', ko.get(src[q])); sys.exit()
for t in difflib.get_close_matches(q, list(src), n=5, cutoff=0.5): print('유사:', t, '→', ko.get(src[t]))
