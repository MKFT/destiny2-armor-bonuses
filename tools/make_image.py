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
IDX=3
def F(p,s): return ImageFont.truetype(p,s,index=IDX)

f_colhdr=F(BLK,32)
f_setzh=F(BLD,30); f_seten=F(MED,20); f_src=F(REG,18)
f_badge=F(BLK,20); f_perkzh=F(BLD,25); f_perken=F(MED,19); f_desc=F(REG,22)
f_descen=F(REG,19)   # 雙語版英文說明
BILINGUAL=False; LANG="zh"   # 模式(main 依輸出檔名設定)
DESCEN=(150,157,170)
f_paneltitle=F(BLK,34)
f_keyzh=F(BLD,23); f_keyen=F(REG,17)
f_ncat=F(BLD,24); f_nlist=F(REG,21)

BG=(22,24,29); CARD=(33,36,44); CARD2=(30,33,40)
TXT=(212,217,224); MUTED=(138,145,157); FAINT=(110,116,128)
SETZH=(244,246,250); PERK=(125,198,255)
ACC=[(220,180,120),(150,208,162),(232,150,150),(184,162,236),(240,206,124)]

scratch=Image.new("RGB",(4,4)); sd=ImageDraw.Draw(scratch)
def tw(s,f): b=sd.textbbox((0,0),s,font=f); return b[2]-b[0]
def th(f): b=sd.textbbox((0,0),"股Ag",font=f); return b[3]-b[1]

def wrap(text,font,maxw):
    out=[]; cur=""
    for ch in text:
        if ch=="\n":
            out.append(cur); cur=""; continue
        if tw(cur+ch,font)<=maxw: cur+=ch
        else:
            if ch!=" " and " " in cur and cur[-1].isascii() and ch.isascii():
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
    IS=30; isg=5; ggap=16; suf="pc" if LANG=="en" else "件"
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
    _ht = col["title"]["en"] if LANG=="en" else f"{col['title']['zh']} ({col['title']['en']})"
    d.text((x0+pad,y+58//2-th(f_colhdr)//2-2), _ht, font=f_colhdr, fill=acc)
    y+=58+16
    for i,st in enumerate(col["sets"]):
        top=y
        # measure card height
        lines=[]
        if LANG=="en":
            lines.append(("setzh",st["name"]["en"]+"  ","")); lines.append(("src", st["source"]["en"], ""))
        else:
            lines.append(("setzh",st["name"]["zh"]+"  ",st["name"]["en"])); lines.append(("src", st["source"]["zh"], st["source"]["en"]))
        for p in st["perks"]:
            if LANG=="en": lines.append(("perk",f"{p['count']}pc",p["name"]["en"],"",p["icon"]))
            else: lines.append(("perk",f"{p['count']}件",p["name"]["zh"],p["name"]["en"],p["icon"]))
            dz = p["desc"]["en"] if LANG=="en" else p["desc"]["zh"]
            for seg in wrap(" ".join(dz.split()),f_desc,innerw-10):
                lines.append(("desc",seg))
            if BILINGUAL:
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
    d.text((left+pad, top+18), ("SYNERGIES KEY" if LANG=="en" else "圖例  SYNERGIES KEY"), font=f_paneltitle, fill=SETZH)
    gy=top+18+th(f_paneltitle)+20
    ncol=6; avail=right-left-2*pad; cwid=avail//ncol
    rows=(len(key)+ncol-1)//ncol; rowh=IS+16
    for i,it in enumerate(key):
        r=i//ncol; c=i%ncol
        cx=left+pad+c*cwid; cy=gy+r*rowh
        ic=_img(it["icon"], IS)
        img.paste(ic,(cx,cy),ic)
        tx=cx+IS+12; ty=cy+IS//2
        if LANG=="en":
            d.text((tx,ty),it["label"]["en"],font=f_keyzh,fill=TXT,anchor="lm")
        else:
            d.text((tx,ty-1),it["label"]["zh"],font=f_keyzh,fill=TXT,anchor="lm")
            d.text((tx+tw(it["label"]["zh"],f_keyzh)+8,ty),it["label"]["en"],font=f_keyen,fill=FAINT,anchor="lm")
    bottom=gy+rows*rowh+10
    d.rounded_rectangle([left,top,right,bottom],radius=14,outline=(72,76,88),width=2)
    return bottom

def draw_notable(d, left, right, top, notable):
    pad=24
    d.text((left+pad, top+18), ("NOTABLE SYNERGIES" if LANG=="en" else "顯著協同  NOTABLE SYNERGIES"), font=f_paneltitle, fill=SETZH)
    gy=top+18+th(f_paneltitle)+18
    ncol=3; cwid=(right-left-2*pad)//ncol
    coly=[gy]*ncol
    for i,it in enumerate(notable):
        c=i%ncol; cx=left+pad+c*cwid; cy=coly[c]
        catlbl = it["category"]["en"] if LANG=="en" else f"{it['category']['zh']} {it['category']['en']}"
        d.text((cx,cy), "◆ "+catlbl, font=f_ncat, fill=ACC[i%5]); cy+=th(f_ncat)+8
        ss=[SETS[sid] for sid in it["set_ids"]]
        names=(", ".join(s["name"]["en"] for s in ss) if LANG=="en" else "、".join(f"{s['name']['zh']}（{s['name']['en']}）" for s in ss))
        for seg in wrap(names,f_nlist,cwid-30):
            d.text((cx+14,cy),seg,font=f_nlist,fill=TXT); cy+=th(f_nlist)+6
        cy+=18; coly[c]=cy
    bottom=max(coly)+12
    d.rounded_rectangle([left,top,right,bottom],radius=14,outline=(72,76,88),width=2)
    return bottom

def render(which, out):
    global BILINGUAL, LANG
    lo=os.path.basename(out).lower(); BILINGUAL = "bilingual" in lo
    LANG = "en" if ("_en" in lo and not BILINGUAL) else "zh"
    cw=880; gap=30; mx=36
    cols=data["columns"]
    if which=="sample":
        cols=[cols[0]]
    n=len(cols)
    W=mx*2+cw*n+gap*(n-1)
    H=9000
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    # title
    tf=F(BLK,52); sf=F(MED,24)
    t="DESTINY 2 · ARMOR SET BONUSES" if LANG=="en" else "DESTINY 2 · 防具套裝效果"
    d.text(((W-tw(t,tf))//2,40),t,font=tf,fill=SETZH)
    s=("Armor Set Bonuses ｜ Official English (Bungie manifest)" if LANG=="en"
       else "Armor Set Bonuses ｜ 官方繁體中文 × English 雙語對照" if BILINGUAL
       else "Armor Set Bonuses ｜ 官方繁體中文對照（樣圖）" if which=="sample"
       else "Armor Set Bonuses ｜ 官方繁體中文對照")
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

def main():
    which=sys.argv[1] if len(sys.argv)>1 else "all"
    if which not in ("all","sample"):
        raise SystemExit(f"用法: make_image.py [all|sample] [輸出.png]\n  (收到 {which!r})")
    if len(sys.argv)>2:                       # 有指定輸出 → 只產那一種(語言依檔名)
        render(which, sys.argv[2])
    elif which=="sample":
        # 否則會拿只有一欄、沒圖例沒協同的樣圖去覆蓋三張正式大圖
        raise SystemExit("sample 必須指定輸出檔名: make_image.py sample /tmp/樣圖.png")
    else:
        for nm in ("zhTW","bilingual","EN"):
            render(which, os.path.join(DOCS,"exports",f"destiny2_armor_bonuses_{nm}.png"))

if __name__=="__main__":
    main()
