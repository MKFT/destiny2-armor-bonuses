# -*- coding: utf-8 -*-
"""由 docs/data/site.json 產生「重新排版乾淨版」大圖。可指定只畫某幾欄(樣圖)。

site.json 是 build 產出的單一資料合約:協同已解析成 id、徽章路徑已內嵌、標題已拆中英,
所以這裡不需要任何反查或字串切割 —— 那些膠水都在 tools/build_texts.py 解決了。
"""
import json, os, sys, gc
from PIL import Image, ImageDraw, ImageFont

BASE=os.path.dirname(os.path.abspath(__file__))
DOCS=os.path.abspath(os.path.join(BASE,"..","docs"))
data=json.load(open(os.path.join(DOCS,"data","site.json"),encoding="utf-8"))
ICON={k["id"]:k["icon"] for k in data["key"]}          # 協同標籤 id → 圖示路徑
SETS={s["id"]:s for c in data["columns"] for s in c["sets"]}   # 供 notable 的 set_ids 反查

_PIC={}
def _img(rel, size):
    """載入 docs/ 底下的素材並縮放(含快取)。"""
    im=_PIC.get(rel)
    if im is None:
        p=os.path.join(DOCS, rel)
        if not os.path.exists(p): raise SystemExit(f"!! 素材不見了: {p}")
        im=Image.open(p).convert("RGBA"); _PIC[rel]=im
    return im.resize((size,size),Image.LANCZOS)

REG="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BLD="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BLK="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
MED="/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
# NotoSansCJK 的 .ttc 內含五個區域變體,主語言決定挑哪個(拉丁字在任一變體都齊,英文沿用即可)。
LANG_IDX={"ja":0,"ko":1,"zhs":2,"zh":3,"en":3}
DESCEN=(150,157,170)

MAIN="zh"                    # 主語言;render() 依組合設定
LABEL_EN=True                # 短標籤(名稱/圖例/欄標題/協同分類)是否附英文 —— 半英/全英為 True
DESC_EN=False                # 說明是否多附一行英文 —— 只有全英為 True
SPACE_BREAK=False            # 主語言是否以空格斷行(韓/英要,中日不要 —— 見 wrap)

# 字型物件依主語言的 index 重建。所有字型統一用主語言 index,拉丁字照樣渲染。
f_colhdr=f_setzh=f_seten=f_src=f_badge=f_perkzh=f_perken=f_desc=f_descen=f_paneltitle=f_keyzh=f_keyen=f_ncat=f_nlist=None
def setfonts(idx):
    global f_colhdr,f_setzh,f_seten,f_src,f_badge,f_perkzh,f_perken,f_desc,f_descen,f_paneltitle,f_keyzh,f_keyen,f_ncat,f_nlist
    def F(p,s): return ImageFont.truetype(p,s,index=idx)
    f_colhdr=F(BLK,32)
    f_setzh=F(BLD,30); f_seten=F(MED,20); f_src=F(REG,18)
    f_badge=F(BLK,20); f_perkzh=F(BLD,25); f_perken=F(MED,19); f_desc=F(REG,22)
    f_descen=F(REG,19)   # 副語言(英文)說明
    f_paneltitle=F(BLK,34)
    f_keyzh=F(BLD,23); f_keyen=F(REG,17)
    f_ncat=F(BLD,24); f_nlist=F(REG,21)
setfonts(3)

# 海報自己的標頭文字(非 site.json 資料),依主語言。件數後綴同理。
POSTER_TITLE={"zh":"防具套裝效果","zhs":"防具套装效果","ja":"アーマーセット効果","ko":"방어구 세트 보너스","en":"ARMOR SET BONUSES"}
KEY_HD={"zh":"圖例","zhs":"图例","ja":"凡例","ko":"범례"}
NTB_HD={"zh":"顯著協同","zhs":"显著协同","ja":"注目のシナジー","ko":"주목할 시너지"}
ENDONYM={"zh":"官方繁體中文","zhs":"官方简体中文","ja":"公式日本語","ko":"공식 한국어","en":"Official English"}
PCSUF={"en":"pc","ja":"個","ko":"피스"}   # 未列的(zh/zhs)用「件」

BG=(22,24,29); CARD=(33,36,44); CARD2=(30,33,40)
TXT=(212,217,224); MUTED=(138,145,157); FAINT=(110,116,128)
SETZH=(244,246,250); PERK=(125,198,255)
ACC=[(220,180,120),(150,208,162),(232,150,150),(184,162,236),(240,206,124)]

scratch=Image.new("RGB",(4,4)); sd=ImageDraw.Draw(scratch)
def tw(s,f): b=sd.textbbox((0,0),s,font=f); return b[2]-b[0]
def th(f): b=sd.textbbox((0,0),"股Ag",font=f); return b[3]-b[1]

def wrap(text,font,maxw):
    # 斷行:中/日逐字斷(無詞間空格);韓/英要在空格處斷,否則單字被從中間劈開。
    # SPACE_BREAK 由主語言決定;英文夾在中日版裡(括號、雙語說明)靠 isascii 那條也能空格斷。
    out=[]; cur=""
    for ch in text:
        if ch=="\n":
            out.append(cur); cur=""; continue
        if tw(cur+ch,font)<=maxw: cur+=ch
        else:
            if ch!=" " and " " in cur and (SPACE_BREAK or (cur[-1].isascii() and ch.isascii())):
                sp=cur.rfind(" "); out.append(cur[:sp]); cur=cur[sp+1:]+ch
            else: out.append(cur); cur=ch
    if cur: out.append(cur)
    return out

def draw_syn(img, d, x_right, ytop, rowh, st, acc):
    """在名稱列右側靠右畫「2件 [圖示] 4件 [圖示]」並排。"""
    syn=st["synergy"]
    if not syn["2"] and not syn["4"]: return
    if syn["2"]==syn["4"]:
        groups=[("2·4",syn["2"])]
    else:
        groups=[("2",syn["2"]),("4",syn["4"])]
    IS=30; isg=5; ggap=16; suf=PCSUF.get(MAIN,"件")
    def bpw_of(t):
        bb=sd.textbbox((0,0),t+suf,font=f_badge); return bb[2]-bb[0]+14
    total=0
    for t,ids in groups: total+=bpw_of(t)+6+len(ids)*(IS+isg)+ggap
    total-=ggap
    x=x_right-total; cy=ytop+rowh//2
    for t,ids in groups:
        bt=t+suf; bb=sd.textbbox((0,0),bt,font=f_badge); bw=bb[2]-bb[0]; bh=bb[3]-bb[1]
        bpw=bw+14; bph=bh+10
        d.rounded_rectangle([x,cy-bph//2,x+bpw,cy-bph//2+bph],radius=5,fill=acc)
        d.text((x+(bpw-bw)//2-bb[0], cy-bph//2+(bph-bh)//2-bb[1]),bt,font=f_badge,fill=(20,22,28))
        x+=bpw+6
        for sid in ids:
            ic=_img(ICON[sid],IS); img.paste(ic,(x,cy-IS//2),ic); x+=IS+isg
        x+=ggap-isg

def draw_column(img, d, x0, y0, col, acc, cw):
    """回傳底部 y。"""
    pad=20; innerw=cw-2*pad
    y=y0
    # header pill
    d.rounded_rectangle([x0,y,x0+cw,y+58],radius=14,fill=CARD,outline=acc,width=2)
    if MAIN=="en":   _ht = col["title"]["en"]
    elif LABEL_EN:   _ht = f"{col['title'][MAIN]} ({col['title']['en']})"
    else:            _ht = col["title"][MAIN]
    d.text((x0+pad,y+58//2-th(f_colhdr)//2-2), _ht, font=f_colhdr, fill=acc)
    y+=58+16
    suf=PCSUF.get(MAIN,"件")
    en_par = LABEL_EN and MAIN!="en"       # 名稱/來源/技能名後面是否放英文括號
    for i,st in enumerate(col["sets"]):
        top=y
        # measure card height
        lines=[]
        if MAIN=="en":
            lines.append(("setzh",st["name"]["en"]+"  ","")); lines.append(("src", st["source"]["en"], ""))
        else:
            lines.append(("setzh",st["name"][MAIN]+"  ", st["name"]["en"] if en_par else ""))
            lines.append(("src", st["source"][MAIN], st["source"]["en"] if en_par else ""))
        for p in st["perks"]:
            if MAIN=="en": lines.append(("perk",f"{p['count']}pc",p["name"]["en"],"",p["icon"]))
            else: lines.append(("perk",f"{p['count']}{suf}",p["name"][MAIN], p["name"]["en"] if en_par else "", p["icon"]))
            for seg in wrap(" ".join(p["desc"][MAIN].split()),f_desc,innerw-10):
                lines.append(("desc",seg))
            if DESC_EN:   # 全英:說明多附一行英文
                for seg in wrap(" ".join(p["desc"]["en"].split()),f_descen,innerw-10):
                    lines.append(("descen",seg))
        # compute height
        hh=pad
        for L in lines:
            if L[0]=="setzh": hh+=th(f_setzh)+8
            elif L[0]=="src": hh+= (th(f_src)+6)*len(wrap(L[1]+("  ("+L[2]+")" if L[2] else ""),f_src,innerw))
            elif L[0]=="perk": hh+=th(f_perkzh)+10
            elif L[0]=="desc": hh+=th(f_desc)+6
            elif L[0]=="descen": hh+=th(f_descen)+4
        hh+=pad
        d.rounded_rectangle([x0,top,x0+cw,top+hh],radius=12,fill=CARD if i%2==0 else CARD2)
        d.rectangle([x0,top,x0+5,top+hh],fill=acc)
        y=top+pad
        for L in lines:
            if L[0]=="setzh":
                d.text((x0+pad,y),L[1],font=f_setzh,fill=SETZH)
                if L[2]: d.text((x0+pad+tw(L[1],f_setzh),y+th(f_setzh)-th(f_seten)-1),f"({L[2]})",font=f_seten,fill=MUTED)
                draw_syn(img,d,x0+cw-pad, y, th(f_setzh), st, acc)   # 右上角並排協同圖示
                y+=th(f_setzh)+8
            elif L[0]=="src":
                for seg in wrap(L[1]+("  ("+L[2]+")" if L[2] else ""),f_src,innerw):
                    d.text((x0+pad,y),seg,font=f_src,fill=FAINT); y+=th(f_src)+6
            elif L[0]=="perk":
                lh=th(f_perkzh)
                pb=sd.textbbox((0,0),L[2],font=f_perkzh)   # 技能名字墨範圍
                pink_top=y+pb[1]; pink_h=pb[3]-pb[1]
                # 技能徽章(左側)
                PS=38; px=x0+pad
                pic=_img(L[4], PS)
                img.paste(pic,(px, pink_top+pink_h//2-PS//2), pic)
                bx=px+PS+8
                bb=sd.textbbox((0,0),L[1],font=f_badge)     # 徽章文字字墨範圍
                inkw=bb[2]-bb[0]; inkh=bb[3]-bb[1]
                bw=inkw+20; bt=pink_top; bh=pink_h   # 色塊上下緣精準對齊技能名字墨
                d.rounded_rectangle([bx,bt,bx+bw,bt+bh],radius=6,fill=acc)
                d.text((bx+(bw-inkw)//2-bb[0], bt+(bh-inkh)//2-bb[1]),L[1],font=f_badge,fill=(20,22,28))
                tx=bx+bw+12
                d.text((tx,y),L[2],font=f_perkzh,fill=PERK)
                if L[3]: d.text((tx+(pb[2]-pb[0])+8, y+lh-th(f_perken)),f"({L[3]})",font=f_perken,fill=MUTED)
                y+=lh+10
            elif L[0]=="desc":
                d.text((x0+pad+8,y),L[1],font=f_desc,fill=TXT); y+=th(f_desc)+6
            elif L[0]=="descen":
                d.text((x0+pad+8,y),L[1],font=f_descen,fill=DESCEN); y+=th(f_descen)+4
        y=top+hh+16
    return y

def draw_key(img, d, left, right, top, key):
    pad=26; IS=40
    hd = "SYNERGIES KEY" if MAIN=="en" else (f"{KEY_HD[MAIN]}  SYNERGIES KEY" if LABEL_EN else KEY_HD[MAIN])
    d.text((left+pad, top+18), hd, font=f_paneltitle, fill=SETZH)
    gy=top+18+th(f_paneltitle)+20
    ncol=6; avail=right-left-2*pad; cwid=avail//ncol
    rows=(len(key)+ncol-1)//ncol; rowh=IS+16
    for i,it in enumerate(key):
        r=i//ncol; c=i%ncol
        cx=left+pad+c*cwid; cy=gy+r*rowh
        ic=_img(it["icon"], IS)
        img.paste(ic,(cx,cy),ic)
        tx=cx+IS+12; ty=cy+IS//2
        if MAIN=="en":
            d.text((tx,ty),it["label"]["en"],font=f_keyzh,fill=TXT,anchor="lm")
        elif LABEL_EN:
            d.text((tx,ty-1),it["label"][MAIN],font=f_keyzh,fill=TXT,anchor="lm")
            d.text((tx+tw(it["label"][MAIN],f_keyzh)+8,ty),it["label"]["en"],font=f_keyen,fill=FAINT,anchor="lm")
        else:
            d.text((tx,ty),it["label"][MAIN],font=f_keyzh,fill=TXT,anchor="lm")   # 純:只主語言
    bottom=gy+rows*rowh+10
    d.rounded_rectangle([left,top,right,bottom],radius=14,outline=(72,76,88),width=2)
    return bottom

def draw_notable(d, left, right, top, notable):
    pad=24
    nhd = "NOTABLE SYNERGIES" if MAIN=="en" else (f"{NTB_HD[MAIN]}  NOTABLE SYNERGIES" if LABEL_EN else NTB_HD[MAIN])
    d.text((left+pad, top+18), nhd, font=f_paneltitle, fill=SETZH)
    gy=top+18+th(f_paneltitle)+18
    ncol=3; cwid=(right-left-2*pad)//ncol
    coly=[gy]*ncol
    for i,it in enumerate(notable):
        c=i%ncol; cx=left+pad+c*cwid; cy=coly[c]
        if MAIN=="en":   catlbl = it["category"]["en"]
        elif LABEL_EN:   catlbl = f"{it['category'][MAIN]} {it['category']['en']}"
        else:            catlbl = it["category"][MAIN]
        d.text((cx,cy), "◆ "+catlbl, font=f_ncat, fill=ACC[i%5]); cy+=th(f_ncat)+8
        ss=[SETS[sid] for sid in it["set_ids"]]
        if MAIN=="en":   names=", ".join(s["name"]["en"] for s in ss)
        elif LABEL_EN:   names="、".join(f"{s['name'][MAIN]}（{s['name']['en']}）" for s in ss)
        else:            names="、".join(s["name"][MAIN] for s in ss)
        for seg in wrap(names,f_nlist,cwid-30):
            d.text((cx+14,cy),seg,font=f_nlist,fill=TXT); cy+=th(f_nlist)+6
        cy+=18; coly[c]=cy
    bottom=max(coly)+12
    d.rounded_rectangle([left,top,right,bottom],radius=14,outline=(72,76,88),width=2)
    return bottom

def render(which, out, main, mode):
    global MAIN, LABEL_EN, DESC_EN, SPACE_BREAK
    MAIN=main
    LABEL_EN = mode in ("half","full") and main!="en"   # 短標籤附英文
    DESC_EN  = mode=="full" and main!="en"               # 說明附英文
    SPACE_BREAK = main in ("ko","en")                    # 韓/英以空格斷行
    setfonts(LANG_IDX[main])
    cw=880; gap=30; mx=36
    cols=data["columns"]
    if which=="sample":
        cols=[cols[0]]
    n=len(cols)
    W=mx*2+cw*n+gap*(n-1)
    H=10000   # 暫存畫布;日文較長,略調高。超出會 SystemExit(見下),不會安靜裁切
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    # title
    tf=ImageFont.truetype(BLK,52,index=LANG_IDX[main]); sf=ImageFont.truetype(MED,24,index=LANG_IDX[main])
    t = "DESTINY 2 · ARMOR SET BONUSES" if main=="en" else f"DESTINY 2 · {POSTER_TITLE[main]}"
    d.text(((W-tw(t,tf))//2,40),t,font=tf,fill=SETZH)
    tier = " × English 全文" if DESC_EN else (" × English 名稱" if LABEL_EN else "")
    s=("Armor Set Bonuses ｜ Official English (Bungie manifest)" if main=="en"
       else f"Armor Set Bonuses ｜ {ENDONYM[main]}{tier}" + (" (sample)" if which=="sample" else ""))
    d.text(((W-tw(s,sf))//2,40+th(tf)+10),s,font=sf,fill=MUTED)
    top=40+th(tf)+10+th(sf)+28
    # 圖例
    if which!="sample":
        top=draw_key(img, d, mx, W-mx, top, data["key"])+30
    maxy=top
    for i,col in enumerate(cols):
        x0=mx+i*(cw+gap)
        by=draw_column(img,d,x0,top,col,ACC[i%5],cw)
        maxy=max(maxy,by)
    # 顯著協同
    if which!="sample":
        maxy=draw_notable(d, mx, W-mx, maxy+16, data["notable"])
    # 畫布高度是寫死的,而 PIL 超出範圍既不報錯也不裁切 —— crop 會用黑色填滿多出來的部分,
    # 於是大圖安靜地帶著黑邊出貨,--stamp-exports 還會把那個錯的尺寸記進 site.json。
    # 寧可在這裡爆掉。(目前最高的是雙語版 6566,約用掉 H 的 73%)
    if maxy+30 > H:
        raise SystemExit(f"!! 畫布不夠高:內容需要 {maxy+30}px 但 H={H}。調高 H 後重跑。")
    final=img.crop((0,0,W,maxy+30))
    final.save(out,"PNG")
    print("saved",out,final.size)
    img.close(); final.close(); gc.collect()

# 13 種組合:四語各「純 / 半英(名稱附英文) / 全英(說明也附英文)」+ 純英文。
# 檔名:<語言> / <語言>-half / <語言>-full。
COMBOS=[("zhTW","zh","pure"),("zhTW-half","zh","half"),("zhTW-full","zh","full"),
        ("zhCN","zhs","pure"),("zhCN-half","zhs","half"),("zhCN-full","zhs","full"),
        ("JA","ja","pure"),   ("JA-half","ja","half"),   ("JA-full","ja","full"),
        ("KO","ko","pure"),   ("KO-half","ko","half"),   ("KO-full","ko","full"),
        ("EN","en","pure")]

def main():
    which=sys.argv[1] if len(sys.argv)>1 else "all"
    if which not in ("all","sample"):
        raise SystemExit(f"用法: make_image.py [all|sample] [輸出.png]\n  (收到 {which!r})")
    if len(sys.argv)>2:                       # 有指定輸出 → 只產一張樣圖(繁中,半英)
        render(which, sys.argv[2], "zh", "half")
    elif which=="sample":
        # 否則會拿只有一欄、沒圖例沒協同的樣圖去覆蓋正式大圖
        raise SystemExit("sample 必須指定輸出檔名: make_image.py sample /tmp/樣圖.png")
    else:
        for nm,mn,md in COMBOS:
            render(which, os.path.join(DOCS,"exports",f"destiny2_armor_bonuses_{nm}.png"), mn, md)

if __name__=="__main__":
    main()
