"""把 tools/voice/scripts.json 的口語稿寫進 index.html（SAY 資料），並依 audio/ 裡有的音檔決定哪些語言可播放"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = json.load(open(os.path.join(ROOT, 'tools/voice/scripts.json'), encoding='utf8'))
ORDER = ['about','check','warn','flow','calc','all','v3','home','county','dict','history','foreign','news','links']
np = lambda t: re.sub(r'。(?=$)', '', t).replace('。', '　')
rows = [[k, np(S['zh'][k]), np(S['tw'][k]), np(S['hk'][k]), np(S.get('hkpy', {}).get(k, ''))] for k in ORDER]
av = {l: [k for k in ORDER if os.path.exists(os.path.join(ROOT, f'audio/{l}_{k}.mp3'))] for l in ['zh','tw','hk']}
data = 'const SAY=' + json.dumps(rows, ensure_ascii=False) + ',SAYAV=' + json.dumps(av) + ';'
p = os.path.join(ROOT, 'index.html'); h = open(p, encoding='utf8').read()
h = re.sub(r'/\*SAYDATA\*/.*?/\*SAYDATA_END\*/', lambda m: '/*SAYDATA*/' + data + '/*SAYDATA_END*/', h, flags=re.S)
open(p, 'w', encoding='utf8').write(h)
print({l: len(v) for l, v in av.items()})
