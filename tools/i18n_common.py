"""中英版共用：找出要翻譯的中文片段（略過地名、比對用資料與正規表示式）"""
import re
RUN=re.compile(r'[　-〿㐀-鿿＀-￯][^<>"\'`\n{}$|=;\\]*')
CJK=re.compile(r'[㐀-鿿]')
# 這些區塊保留中文：地名、單位資料、比對用的規則
SKIP_STARTS=['const CENTERS=','const DIST=','const BUILD=','const CTR_SRC','const areaHit','const CSLUG','const SLUGC','const REMOTE','const isRemote']
def skip_mask(h):
    mask=[False]*len(h)
    for s in SKIP_STARTS:
        i=0
        while True:
            i=h.find(s,i)
            if i<0:break
            j=h.find('\n};',i)+3 if s in('const CENTERS=',) else h.find('\n',i)
            for k in range(i,j):mask[k]=True
            i=j
    # 程式裡用來比對資料的片段
    for pat in [r"/全區\$/",r"/部分\[里村\]\$/",r"/\[區鄉鎮市\]\$/",r"/（\[\^）\]\*）/g",r"/（\[\^）\]\*）/"]:
        for m in re.finditer(pat,h):
            for k in range(m.start(),m.end()):mask[k]=True
    return mask
def runs(h):
    mask=skip_mask(h)
    for m in RUN.finditer(h):
        s=m.group(0)
        if not CJK.search(s) or mask[m.start()]:continue
        core=s.rstrip()
        yield m.start(),m.start()+len(core),core
