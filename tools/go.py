import sys, json, urllib.request
from pathlib import Path
port = json.loads((Path(__file__).resolve().parent.parent / 'shots/server.json').read_text())['port']
arg = sys.argv[1]
if arg == 'close': path, body = '/close', '{}'
else: path, body = '/', (open(arg[1:], encoding='utf8').read() if arg.startswith('@') else arg)
r = urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}{path}', body.encode(), method='POST'), timeout=600)
print(r.read().decode())
