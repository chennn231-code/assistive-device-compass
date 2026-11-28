"""把瀏覽器 VOICE.chunk(i) 取回、存在工具結果檔裡的音檔組回來，轉成 audio/*.mp3，再更新網頁
用法：python3 tools/voice/ingest.py <工具結果資料夾> <chunk 數量>"""
import json, re, base64, glob, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
d, n = sys.argv[1], int(sys.argv[2])
ch = {}
for f in glob.glob(os.path.join(d, '**', '*'), recursive=True):
    if not os.path.isfile(f): continue
    try: t = open(f, encoding='utf8', errors='ignore').read()
    except Exception: continue
    for m in re.finditer(r'VCH(\d+)<<([A-Za-z0-9+/=:\n_VWAVEND]*?)>>', t.replace('\\n', '\n')): ch[int(m.group(1))] = m.group(2)
missing = [i for i in range(n) if i not in ch]
if missing: sys.exit(f'missing chunks {missing}')
allt = ''.join(ch[i] for i in range(n))
made = []
for m in re.finditer(r'VWAV:(\w+):([A-Za-z0-9+/=]+):END', allt):
    k = m.group(1); tmp = f'/tmp/{k}.wav'; open(tmp, 'wb').write(base64.b64decode(m.group(2)))
    out = os.path.join(ROOT, 'audio', k + '.mp3')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', tmp, '-af', 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,loudnorm=I=-18:TP=-2', '-ac', '1', '-ar', '24000', '-c:a', 'libmp3lame', '-b:a', '48k', out], check=True)
    made.append(k)
print('made', made)
subprocess.run([sys.executable, os.path.join(ROOT, 'tools/voice/build_say.py')], check=True)
subprocess.run([sys.executable, os.path.join(ROOT, 'tools/build_en.py')], check=True)
