"""從中文版 index.html 產生英文版 en/index.html

用法：python3 tools/build_en.py
翻譯對照在 i18n/en.json（中文片段 → 英文）；地名、單位資料與比對用規則保留中文
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from i18n_common import runs, skip_mask, CJK

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
h = open(os.path.join(ROOT, 'index.html'), encoding='utf8').read()
EN = json.load(open(os.path.join(ROOT, 'i18n/en.json'), encoding='utf8'))
def typo(t):
    # 英文裡的引號改成彎引號，避免弄壞 HTML 屬性或 JS 字串
    t = t.replace("'", '\u2019')
    def q(m):
        i = m.start(); pv = t[i-1] if i else ''; nx = t[i+1] if i + 1 < len(t) else ''
        if pv in ' (' and pv: return '\u201c'
        if not pv and nx and nx != ' ': return '\u201c'
        return '\u201d'
    return re.sub(r'"', q, t)
EN = {k: typo(v) for k, v in EN.items()}

MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
       'August', 'September', 'October', 'November', 'December']

# 1. 保護：程式裡比對中文資料的字串（資料本身不翻）
PROTECT = ["t.includes('分機')?','+t.split('分機')"]
saved = []
for p in PROTECT:
    assert p in h, p
    h = h.replace(p, f'\x00{len(saved)}\x00')
    saved.append(p)

# 2. 整句替換：數字開頭、語序不同、程式樣板
PRE = [
    ("n.toLocaleString('zh-TW')+' 元'", "'NT$'+n.toLocaleString('en-US')"),
    ("v.toLocaleString('zh-TW')+' 元'", "'NT$'+v.toLocaleString('en-US')"),
    ("return `${y} 年 ${+m} 月 ${+dd} 日`",
     "return `${['January','February','March','April','May','June','July','August','September','October','November','December'][m-1]} ${+dd}, ${y}`"),
    ("const its=raw?INTENT.filter(x=>x[0].test(raw))", "const its=raw?INTENT.filter(x=>x[0].test(raw.toLowerCase()))"),
    ('<small>115 年起不限年齡</small>', '<small>No age limit from 2026</small>'),
    ('4 萬元裡，買輔具用了 1 萬，裝扶手用了 8 千，還剩 2 萬 2 千',
     'Of NT$40,000: devices used NT$10,000, grab bars NT$8,000, NT$22,000 left'),
    ('買輔具<br>1 萬', 'Devices<br>NT$10,000'),
    ('裝扶手<br>8 千', 'Grab bars<br>NT$8,000'),
    ('還剩 2 萬 2 千', 'NT$22,000 left'),
    ('3 年內選定後不能換　115 年 6 月 30 日前已經用過 4 萬元那一種的人，要滿 3 年才能改選智慧輔具',
     'The choice is fixed for 3 years. If you used the NT$40,000 group before June 30, 2026, you can switch only after that period ends'),
    ('6 萬元裡，家裡無障礙改善最多用 2 萬元', 'Of the NT$60,000, at most NT$20,000 can go to home accessibility'),
    ('115 年 6 月 30 日起', 'From June 30, 2026'),
    ("s:'6 月 3 日是《長期照顧服務法》公布施行的日子，明年起會辦理相關活動，肯定第一線長照人員'",
     "s:'June 3 is the day the Long-term Care Services Act was promulgated. Related events will be held from next year to recognize frontline LTC workers'"),
    ("'6 月 3 日「臺灣長照日」是怎麼來的？'", "'How did June 3 become “Taiwan Long-term Care Day”?'"),
    ("'6 月 3 日是《長期照顧服務法》公布的日子，衛福部 115 年 11 月宣布每年這一天為臺灣長照日'",
     "'June 3 is the day the Long-term Care Services Act was promulgated. In November 2026 the MOHW announced that this day will be Taiwan Long-term Care Day every year'"),
    ("h:'65 歲以上、55 歲以上的原住民、醫師診斷有失智症，或醫院說符合「急性後期整合照護」'",
     "h:'Aged 65 or older, Indigenous persons aged 55 or older, diagnosed with dementia by a physician, or the hospital says they qualify for Post-Acute Care (PAC)'"),
    ("'3 年總數 '", "'3-year total '"),
    ("' 3 年總數'", "' the 3-year total'"),
    ("其中 ${fmt(over)} 超過", "Of this, ${fmt(over)} exceeds "),
    ("用滿 ${it.y} 年才能再申請・", "Can reapply after ${it.y} years · "),
    ("　未輸入報價時以 ${fmt(it.p)} 示範", " · Example price ${fmt(it.p)} (no quote entered)"),
    ("y>0?`${y} 年`", "y>0?`${y} years`"),
    ("用滿 ${y} 才能再申請", "Can reapply after ${y}"),
    ("`項次 ${o.c}`", "`Item no. ${o.c}`"),
    ("`第 ${o.c} 項`", "`Item ${o.c}`"),
    ("再顯示 ${Math.min(12,res.length-shown)} 項（還有 ${res.length-shown} 項）",
     "Show ${Math.min(12,res.length-shown)} more (${res.length-shown} remaining)"),
    ("　據點 ${np} 處", " · ${np} service points"),
    ("　便利站 ${nc} 處", " · ${nc} convenience points"),
    ("已勾 ${n} 項，看可能的補助項目 ↓", "${n} ticked — see possible subsidy items ↓"),
    ("第 ${done.length+1} 題", "Question ${done.length+1}"),
    ("全部特約 ${all.length} 家", "All contracted (${all.length})"),
    ("第 ${l} 級", "Level ${l}"),
    ("第 ${stI+1}／${STEPS.length} 步：", "Step ${stI+1}/${STEPS.length}: "),
    ("不指定（${DIST[c].length} 個鄉鎮市區）", "Any district (${DIST[c].length})"),
    ("${esc(c)}有 ${CENTERS[c].length} 家輔具中心，依住的區域分工",
     "${esc(cen(c))} has ${CENTERS[c].length} assistive technology centers, each serving different areas"),
    ("'看全部 '+pick.length+' 家'", "'Show all '+pick.length"),
    ("名稱有「無障礙、工程」等字 ${nb} 家", "Names containing “accessibility”, “engineering”, etc. (${nb})"),
    ("${esc(c)}的長照特約單位共 ${pick.length} 家${d?`，<strong>${esc(d)}有 ${nd} 家</strong>，排在最前面`:''}",
     "${esc(cen(c))}: ${pick.length} LTC-contracted providers${d?`; <strong>${nd} in ${esc(d)}</strong>, listed first`:''}"),
    ("<b>${(v/10000).toFixed(1)} 萬</b>", "<b>${Math.round(v/1000)}k</b>"),
    ("'6 個月'", "'6 months'"),
    ("sub:'領津貼或生活補助'", "sub:'Receiving an allowance or living subsidy'"),
    ("長照 3.0・115 年 7 月 1 日上路", "LTC 3.0 · in effect from July 1, 2026"),
    ('核定公文發文後 <strong>6 個月內</strong>要買好並辦理請款',
     'Buy and claim <strong>within 6 months</strong> of the approval letter date'),
    ("'6 個月內購買'", "'Buy within 6 months'"),
    ("'核定公文發文後 6 個月內要買好並辦理請款'", "'Buy and claim within 6 months of the approval letter date'"),
]
for a, b in PRE:
    n = h.count(a)
    if not n:
        print('PRE not found:', a[:60]); continue
    h = h.replace(a, b)

# 3. 數字開頭的金額與日期（只處理位於中文片段開頭的）
RUNSTART = re.compile('[\u2e80-\uffef]')
def at_start(s, i):
    j = i - 1
    while j >= 0 and s[j] in ' 0123456789,.%':
        j -= 1
    return j < 0 or not RUNSTART.match(s[j])

def money(m):
    a = m.group(1); b = m.group(2) if m.lastindex and m.lastindex >= 2 else None
    v = int(a) * 10000 + (int(b) * 1000 if b else 0)
    return f'NT${v:,}'
GEN = [
    (re.compile(r'(\d{4}) 年 (\d{1,2}) 月 (\d{1,2}) 日'), lambda m: f'{MON[int(m.group(2))-1]} {int(m.group(3))}, {m.group(1)}'),
    (re.compile(r'(1\d\d) 年 (\d{1,2}) 月 (\d{1,2}) 日'), lambda m: f'{MON[int(m.group(2))-1]} {int(m.group(3))}, {int(m.group(1))+1911}'),
    (re.compile(r'(\d+) 萬 (\d) 千元?'), money),
    (re.compile(r'(\d+) 萬元?'), money),
]
mask = skip_mask(h)
for rx, fn in GEN:
    out = []; last = 0
    for m in rx.finditer(h):
        if mask[m.start()] or not at_start(h, m.start()):
            continue
        out.append(h[last:m.start()]); out.append(fn(m)); last = m.end()
    out.append(h[last:]); h = ''.join(out)
    mask = skip_mask(h)

# 4. 逐段翻譯
out = []; last = 0; miss = {}
for a, b, core in runs(h):
    if core in EN:
        t = EN[core]
        pm = re.search(r'(?<![\w.$])(\d+) $', h[max(last, a-8):a])
        if pm and re.search(r'\b' + pm.group(1) + r'\b', t[:40]):
            a -= len(pm.group(0))          # 譯文已含開頭數字
        nxt = h[b:b+2]
        if t and nxt in ('${', "'+", '`+') and re.match(r'[A-Za-z0-9.:,)]', t[-1]):
            t = t + ' '
        if t and re.match(r'[A-Za-z0-9(]', t[0]) and (h[a-1:a] == '}' or h[a-2:a] in ("+'", '+`')):
            t = ' ' + t
        out.append(h[last:a]); out.append(t); last = b
    elif not core.endswith('*/'):
        miss[core] = miss.get(core, 0) + 1
out.append(h[last:]); h = ''.join(out)

# 5. 全形標點改半形（略過保留中文的資料區）
PUN = {'「': '\u201c', '」': '\u201d', '『': '\u201c', '』': '\u201d', '，': ', ', '：': ': ', '（': ' (', '）': ')',
       '、': ', ', '　': '  ', '；': '; ', '／': '/', '？': '?', '！': '!', '《': '', '》': '',
       '・': ' · ', '～': '–', '【': '[', '】': ']'}
mask = skip_mask(h)
def in_comment_or_skip(i):
    return mask[i]
buf = []
for i, ch in enumerate(h):
    if ch in PUN and not mask[i]:
        # 地名與單位資料（臺北市…）旁的括號保留
        prev = h[i-1] if i else ''
        if ch in '（）、' and CJK.match(prev or ' '):
            buf.append(ch); continue
        buf.append(PUN[ch])
    else:
        buf.append(ch)
h = ''.join(buf)
h = re.sub(r'(?<=[A-Za-z0-9)%\u201d])  (?=[A-Z\u201c])', '. ', h)   # 全形空白分句
h = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', h)
h = h.replace(' (', ' (').replace('( ', '(')
h = re.sub(r'(?<=[>(\s]) \(', '(', h)

# 5b. 中英相接處補空白（中文不需要空白，英文需要）
TAG = r'</?(?:a|b|strong|span|small|em|i|br|mark|abbr)(?:\s[^<>]*)?/?>'
h = re.sub(r'([A-Za-z0-9%),.;:!?\u2019\u201d])((?:' + TAG + r')+)(?=[A-Za-z0-9(\u201c$])', r'\1 \2', h)
h = re.sub(r'((?:' + TAG + r')+)', lambda m: m.group(1), h)

# 5c. 英文版專用的小修正
POST = [
    ("narrow&&sl?'Co-pay '+sl.replace('Co-pay ',''):sv", "narrow&&sl?(/^You /.test(sl)?sl:'You '+sl):sv"),
    ("[5,410,210,180,180,'stair',", "[5,410,210,180,180,'Stairs',"),
    ("WHO_T[r][i].join(' ')]", "WHO_T[r][i].join(' → ')]"),
    ("(c?' · Lives in '+c+d:'')", "(c?' · Lives in '+cen(c)+(d?' '+d:''):'')"),
    ("for(const ch of t){if(x.measureText(line+ch).width>w&&line){out.push(line);line=ch}else line+=ch}",
     "for(const ch of t.split(/(?<=[ /])|(?=[\\u3400-\\u9fff])/)){if(x.measureText(line+ch).width>w&&line){out.push(line.trimEnd());line=ch.trimStart()}else line+=ch}"),
    ("L.push('Lives in: '+c+d)", "L.push('Lives in: '+cen(c)+(d?' '+d:''))"),
    ("['stair',[", "['Stairs',["),
    ("['assessment report',", "['Assessment report',"),
    ("LSBASE='audio/'", "LSBASE='../audio/'"),
    ("const LSN=", "window.SAY_EN={\"about\": \"This is an independent guide, not a government site. Eligibility and amounts are decided by the government. For LTC call 1966; for disability devices ask your district office or assistive technology center; for medical devices ask the Department of Health.\", \"check\": \"Let’s see if your family member can apply. Usually people aged 65+, Indigenous people 55+, Disability Certificate holders, people with dementia, or patients eligible for Post-Acute Care can apply for LTC. Answer a few questions and we’ll tell you who to contact.\", \"warn\": \"The most important thing: apply first, buy later. If you buy first, you usually can’t get the subsidy. For LTC, wait for the care plan approval, then buy or rent from a contracted supplier. For disability devices, buy and claim within 6 months of approval.\", \"flow\": \"Applying takes four steps: get assessed, wait for approval, buy or rent the device, then pay your share. LTC, disability and medical devices go through different offices — switch with the buttons above. You can also start by phone or online.\", \"calc\": \"Estimate how much is covered. Pick your city, device and income status, enter the quote, and compare LTC and disability subsidies. LTC devices and home modification share one 3-year allowance — you can check what’s left here too.\", \"all\": \"Over 300 LTC, disability and medical devices. No need to know the official name — type something like “slippery bathroom”. Each item shows the maximum subsidy and whether an assessment is needed.\", \"v3\": \"Since July 2026, LTC 3.0 adds smart assistive technology, like beds that alert family when someone gets up. It’s mostly rented: NT$60,000 per 3 years, but you choose it instead of the NT$40,000 group and can’t switch for 3 years.\", \"home\": \"If home is hard to get around or slippery, the government can subsidize grab bars, threshold leveling, anti-slip work and bathroom changes. Tap the floor plan to see options. Get assessed and approved first, then use a contracted provider.\", \"county\": \"Choose where you live to see nearby assistive technology centers and LTC-contracted suppliers. Centers can assess needs and lend devices — call ahead to book.\", \"dict\": \"Official letters use hard terms like LTC need level, approval, reimbursement and co-payment. Tap a term for a plain explanation.\", \"history\": \"How device and accessibility subsidies changed from LTC 1.0 to 3.0: rules once varied by city, now there’s a national standard and rentable smart devices.\", \"foreign\": \"No Taiwan ID? From June 30, 2026, eligible foreign professionals and their families can apply for LTC. Others generally can’t get subsidies; when buying devices yourself, check the medical device license number.\", \"news\": \"Weekly updates on devices and LTC from the MOHW and other agencies. Tap the source links for details.\", \"links\": \"Official links: the 1966 LTC hotline, the Assistive Technology Resource Portal and online applications. Official sources prevail.\"};const LSN="),
    ("subject=%E8%BC%94%E5%85%B7%E8%A3%9C%E5%8A%A9%E6%8C%87%E5%8D%97%E9%87%9D%EF%BC%9A%E6%84%8F%E8%A6%8B%E5%9B%9E%E9%A5%8B&body=%E6%83%B3%E8%AA%AA%E7%9A%84%E4%BA%8B%EF%BC%88%E9%8C%AF%E8%AA%A4%E3%80%81%E5%BB%BA%E8%AD%B0%E3%80%81%E6%83%B3%E7%9C%8B%E5%88%B0%E7%9A%84%E5%85%A7%E5%AE%B9%E9%83%BD%E5%8F%AF%E4%BB%A5%EF%BC%89%EF%BC%9A%0A%0A%E7%9B%B8%E9%97%9C%E7%9A%84%E5%8D%80%E5%A1%8A%EF%BC%88%E5%A6%82%E6%9E%9C%E6%9C%89%EF%BC%89%EF%BC%9A%0A%0A%E8%B3%87%E6%96%99%E4%BE%86%E6%BA%90%E7%B6%B2%E5%9D%80%EF%BC%88%E5%A6%82%E6%9E%9C%E6%9C%89%EF%BC%89%EF%BC%9A%0A%0A%EF%BC%88%E8%AB%8B%E4%B8%8D%E8%A6%81%E5%AF%AB%E8%BA%AB%E5%88%86%E8%AD%89%E5%AD%97%E8%99%9F%E3%80%81%E7%97%85%E6%AD%B7%E7%AD%89%E5%80%8B%E4%BA%BA%E8%B3%87%E6%96%99%EF%BC%89%0A", "subject=Assistive%20Device%20Subsidy%20Compass%3A%20feedback&body=Your%20feedback%20%28errors%2C%20suggestions%20or%20content%20you%20would%20like%20to%20see%29%3A%0A%0ARelated%20section%20%28if%20any%29%3A%0A%0ASource%20link%20%28if%20any%29%3A%0A%0A%28Please%20do%20not%20include%20ID%20numbers%2C%20medical%20records%20or%20other%20personal%20data%29%0A"),
    ("data-modeall-soft>Assistive technology centers<small>& suppliers</small>", "data-modeall-soft>Centers<small>& suppliers</small>"),
    ("</style>", "@media(max-width:560px){.brand .bn{display:none}.ls-btns{grid-template-columns:1fr 1fr}}</style>"),
    ("Find assistive technology centers and LTC-contracted suppliers near you",
     "Find assistive technology centers and LTC-contracted suppliers near you. Names and addresses stay in Chinese, as registered — handy for map apps or taxi drivers"),
]
for a, b in POST:
    if a not in h:
        print('POST not found:', a[:60]); continue
    h = h.replace(a, b)
CAP = '''<script>/* EN: capitalize short labels (display text only) */
(()=>{const S='button,option,h3,h4,label>span,summary>span,text,th,.tile,.cat,.g,.lv';
const cap=r=>{(r.matches&&r.matches(S)?[r]:[]).concat([...(r.querySelectorAll?r.querySelectorAll(S):[])]).forEach(e=>{
 if(e.childNodes.length!==1||e.firstChild.nodeType!==3)return;const t=e.firstChild.nodeValue;
 if(!/^[a-z]/.test(t))return;if(e.tagName==='OPTION'&&!e.hasAttribute('value'))e.value=t;
 e.firstChild.nodeValue=t[0].toUpperCase()+t.slice(1)})};
cap(document.body);new MutationObserver(ms=>ms.forEach(m=>m.addedNodes.forEach(n=>n.nodeType===1&&cap(n)))).observe(document.body,{childList:true,subtree:true})})();
</script>'''
h = re.sub(r'([A-Za-z]):(?=\$\{)', r'\1: ', h)
h = h.replace('</body>', CAP + '\n</body>')

# 6. 還原保護字串
for k, p in enumerate(saved):
    h = h.replace(f'\x00{k}\x00', p)

# 7. 語系、路徑、meta
h = h.replace("'zh-TW'", "'en-US'")
h = h.replace('<html lang="zh-Hant-TW">', '<html lang="en">')
h = h.replace('content="zh_TW"', 'content="en_US"')
BASE = 'https://chennn231-code.github.io/assistive-device-compass/'
h = h.replace(f'<link rel="canonical" href="{BASE}">',
              f'<link rel="canonical" href="{BASE}en/">\n<link rel="alternate" hreflang="zh-Hant-TW" href="{BASE}">\n<link rel="alternate" hreflang="en" href="{BASE}en/">')
h = h.replace("const src='img/'", "const src='../img/'")
h = h.replace("fetch('data/ltc-ef.json')", "fetch('../data/ltc-ef.json')")
h = re.sub(r'(src|href)="img/', r'\1="../img/', h)
h = re.sub(r"url\((['\"]?)img/", r"url(\1../img/", h)

# 8. 縣市選單顯示英文（值仍是中文，資料比對不受影響）
COUNTY = {'臺北市': 'Taipei City', '新北市': 'New Taipei City', '桃園市': 'Taoyuan City', '臺中市': 'Taichung City',
          '臺南市': 'Tainan City', '高雄市': 'Kaohsiung City', '基隆市': 'Keelung City', '新竹市': 'Hsinchu City',
          '嘉義市': 'Chiayi City', '新竹縣': 'Hsinchu County', '苗栗縣': 'Miaoli County', '彰化縣': 'Changhua County',
          '南投縣': 'Nantou County', '雲林縣': 'Yunlin County', '嘉義縣': 'Chiayi County', '屏東縣': 'Pingtung County',
          '宜蘭縣': 'Yilan County', '花蓮縣': 'Hualien County', '臺東縣': 'Taitung County', '澎湖縣': 'Penghu County',
          '金門縣': 'Kinmen County', '連江縣': 'Lienchiang County (Matsu)'}
cmap = 'const CEN=' + json.dumps(COUNTY, ensure_ascii=False) + ';const cen=c=>CEN[c]?CEN[c]+\' \'+c:c;'
h = h.replace('<script>', '<script>' + cmap, 1) if '<script>' in h else h
h = h.replace("map(c=>`<option>${c}</option>`)", "map(c=>`<option value=\"${c}\">${cen(c)}</option>`)")

# 8b. 英文字型與排版：拉丁字先用 Source Sans 3 / Source Serif 4，避免中文字型把引號排成全形
h = h.replace('family=Noto+Sans+TC:wght@400;700&family=Noto+Serif+TC:wght@700;900',
              'family=Source+Sans+3:wght@400;600;700&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&family=Noto+Sans+TC:wght@400;700&family=Noto+Serif+TC:wght@700;900')
h = h.replace('"Noto Sans TC"', '"Source Sans 3","Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans TC"').replace('"Noto Serif TC"', '"Source Serif 4",Georgia,"Times New Roman","Noto Serif TC"')
EN_CSS = """
/* EN layout: more air, shorter lines */
:root{--h1:clamp(36px,5.6vw,60px);--h2:clamp(25px,2.7vw,31px);--h3:19px}
body{line-height:1.6;font-size:17px}
p,li{text-wrap:pretty}
.sh p,.lead,.note,.sec p{max-width:68ch}
h1,h2,h3{letter-spacing:-.01em;line-height:1.2}
.hero h1{max-width:13ch}
.note,small{line-height:1.5}
.tabs label,.btn,.chip{letter-spacing:0}
.toc-list a,.callbar a,.callbar button{line-height:1.25}
"""
h = h.replace('</style>', EN_CSS + '</style>', 1)

# 9. 中英切換
SW = '<a class="tb langsw" href="en/" hreflang="en" lang="en" aria-label="English version">EN</a>'
assert SW in h
h = h.replace(SW, '<a class="tb langsw" href="../" hreflang="zh-Hant-TW" lang="zh-Hant-TW" aria-label="切換到中文版">中文</a>')
open(os.path.join(ROOT, 'en/index.html'), 'w', encoding='utf8').write(h)

left = [m.group(0) for m in re.finditer(r'[㐀-鿿][^<>"\'`\n]{0,30}', h)]
print('missing segments:', len(miss))
for k, v in list(miss.items())[:80]:
    print('  MISS', v, repr(k[:70]))
print('CJK runs left in output:', len(left))
