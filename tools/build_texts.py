# -*- coding: utf-8 -*-
"""把官方 manifest 資料 + 人工整理資料 + 手工圖示對應，黏成單一資料合約 docs/data/site.json。

site.json 是網站與大圖「共用的唯一資料來源」:每個 perk 自帶徽章路徑、每套裝自帶已解析的
協同標籤 id、每個圖例自帶檔名與分組。消費端(make_image.py / 網頁)因此完全不需要反查邏輯。

同時產生 docs/exports/*.txt 文字成品,以及網站用的圖例 sprite。
"""
import json, os, re, sys
from PIL import Image

BASE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(BASE,".."))
CACHE=os.path.join(BASE,"cache")
SRC=os.path.join(ROOT,"src")
DOCS=os.path.join(ROOT,"docs")

resolved=json.load(open(os.path.join(CACHE,"derived","resolved.json"),encoding="utf-8"))
by_en={r["name_en"]:r for r in resolved}
# 手工資料:協同圖示(人工辨識)與技能徽章對應。兩者的鍵規則不同,在此一次解決。
SYN=json.load(open(os.path.join(SRC,"synergy_icons.json"),encoding="utf-8"))
PERKICONS=json.load(open(os.path.join(SRC,"perk_icons.json"),encoding="utf-8"))

# 欄位分組 + 高數值來源(來自資訊圖,manifest 無此資料)。名稱為官方現行英文名。
COLUMNS=[
 ("world","世界/遺落之地","Distortions & Lost Sectors", [
   ("Wildwood","DISTORTIONS / MASTER LOST SECTORS: EDZ"),
   ("Exodus Down","DISTORTIONS / MASTER LOST SECTORS: NESSUS"),
   ("Reverie Dawn","DISTORTIONS / MASTER LOST SECTORS: DREAMING CITY"),
   ("Dreambane","DISTORTIONS / MASTER LOST SECTORS: MOON"),
   ("Crystocrene","DISTORTIONS / MASTER LOST SECTORS: EUROPA"),
   ("Seventh Seraph","DISTORTIONS / MASTER LOST SECTORS: COSMODROME"),
   ("Veritas","DISTORTIONS / MASTER LOST SECTORS: THRONE WORLD"),
   ("Thunderhead","MASTER LOST SECTORS / OVERRIDE: NEOMUNA"),
   ("First Ascent","MASTER LOST SECTORS / OVERTHROW: PALE HEART"),
   ("AION Adapter","THE SIEVE / MYTHIC EXPLORATION / GEAR FOCUSING: KEPLER"),
   ("AION Renewal","THE SIEVE / MYTHIC EXPLORATION / GEAR FOCUSING: KEPLER"),
   ("Thriving Survivor","GRANDMASTER LAWLESS FRONTIER JOBS"),
   ("Shrewd Survivor","GRANDMASTER LAWLESS FRONTIER JOBS"),
 ]),
 ("vanguard","先鋒/熔爐聚焦","Vanguard", [
   ("Techsec","VANGUARD FOCUSING"),
   ("Smoke Jumper Set","VANGUARD FOCUSING"),
   ("Ferropotent","VANGUARD FOCUSING"),
   ("Luminopotent","VANGUARD FOCUSING"),
   ("Bushido","VANGUARD FOCUSING"),
   ("Swordmaster","VANGUARD FOCUSING"),
   ("Eutechnology","VANGUARD FOCUSING"),
   ("Lustrous","TENET OF BRAVERY FOCUSING"),
   ("Cyberserpent Null","GAMBIT"),
 ]),
 ("crucible","熔爐 PvP","Crucible", [
   ("Last Discipline","CRUCIBLE FOCUSING"),
   ("Disaster Corps Set","CRUCIBLE FOCUSING"),
   ("Wild Anthem","CRUCIBLE FOCUSING"),
   ("Triumphal Anthem","CRUCIBLE FOCUSING"),
   ("Iron Panoply Set","IRON BANNER"),
   ("Iron Battalion Set","IRON BANNER"),
   ("Per Audacia","COMPETITIVE CRUCIBLE"),
   ("Twofold Crown","TRIALS OF OSIRIS"),
   ("New Demotic","TRIALS OF OSIRIS"),
   ("Cruel Electrum","TRIALS OF OSIRIS"),
   ("Circuit","SPARROW RACING"),
 ]),
 ("dungeon","地城","Dungeon", [
   ("Techeun's Regalia","FEATURED DUNGEON: SHATTERED THRONE"),
   ("Apostate's Blade","FEATURED DUNGEON: PIT OF HERESY"),
   ("CODA","FEATURED DUNGEON: PROPHECY"),
   ("Yearning Echo","FEATURED OR MASTER DUNGEON: GRASP OF AVARICE"),
   ("Deep Explorer","FEATURED OR MASTER DUNGEON: DUALITY"),
   ("TM Custom","FEATURED OR MASTER DUNGEON: SPIRE OF THE WATCHER"),
   ("Taken King","FEATURED OR MASTER DUNGEON: GHOSTS OF THE DEEP"),
   ("Dark Age","FEATURED OR MASTER DUNGEON: WARLORDS RUIN"),
   ("Spacewalk","FEATURED OR MASTER DUNGEON: VESPER'S HOST"),
   ("Flain","FEATURED OR MASTER DUNGEON: SUNDERED DOCTRINE"),
   ("Sage Protector","EQUILIBRIUM DUNGEON WITH FEATS ENABLED"),
 ]),
 ("raid","突襲","Raid", [
   ("Great Hunt","FEATURED OR MASTER RAID: LAST WISH"),
   ("Kentarch 3","FEATURED OR MASTER RAID: GARDEN OF SALVATION"),
   ("Legacy's Oath","FEATURED OR MASTER RAID: DEEP STONE CRYPT"),
   ("Atheon's Memory","FEATURED OR MASTER RAID: VAULT OF GLASS"),
   ("Resonant Fury","FEATURED OR MASTER RAID: VOW OF THE DISCIPLE"),
   ("Crota's Memory","FEATURED OR MASTER RAID: CROTA'S END"),
   ("Nezarec's Nightmare","FEATURED OR MASTER RAID: ROOT OF NIGHTMARES"),
   ("Oryx's Memory","FEATURED OR MASTER RAID: KING'S FALL"),
   ("Promised","FEATURED OR MASTER RAID: SALVATION'S EDGE"),
   ("Collective Psyche","DESERT PERPETUAL RAID WITH FEATS"),
   ("Wayward Psyche Set","EPIC DESERT PERPETUAL RAID WITH FEATS"),
   ("Pantheos Resplendent","PANTHEON RAIDS WITH FEATS"),
 ]),
]

# 圖例 44 詞(官方用語),分五組。
# 【重要】攤平後的順序即 icon_01..44 的對應順序,sprite 也依此順序打包 —— 不可重排。
# 這五組在原本的順序中就是連續的,所以加上分組不影響任何既有對應。
KEY=[
 ("element","元素","Element",[
   ("SOLAR","灼燒"),("VOID","虛空"),("ARC","電弧"),("STASIS","冰凝"),("STRAND","縈絲"),
   ("PRISMATIC","稜鏡"),("KINETIC","動能")]),
 ("ability","技能","Ability",[
   ("SUPER","超能力"),("GRENADE","手榴彈"),("MELEE","近戰"),("CLASS ABILITY","職業技能"),
   ("ALL ABILITIES","全部技能")]),
 ("pickup","拾取物與狀態","Pickups & States",[
   ("ORBS OF POWER","力量球體"),("ELEMENTAL PICKUPS","元素拾取物"),("ALL AMMO","全部彈藥"),
   ("SPECIAL AMMO","特殊彈藥"),("HEAVY AMMO","重型彈藥"),("FINISHERS","終結技"),
   ("DISORIENT","迷失方向"),("EXHAUST","筋疲力盡")]),
 ("stat","生存與數值","Survivability & Stats",[
   ("HEALING","治療"),("SURVIVABILITY","生存能力"),("LIGHT","光"),("DARKNESS","黑暗"),
   ("ARMOR CHARGE","防具充能"),("HEALTH STAT","生命值"),("WEAPON STAT","武器數值"),
   ("MOBILITY","機動性")]),
 ("weapon","武器","Weapons",[
   ("WEAPONS","武器"),("SWORDS","劍"),("GLAIVES","長戈"),("ROCKETS","火箭筒"),
   ("GRENADE LAUNCHERS","榴彈發射器"),("AUTO RIFLES","自動步槍"),("SIDEARMS","手槍"),
   ("SCOUT RIFLES","斥候步槍"),("SMGS","衝鋒槍"),("HAND CANNONS","手持加農砲"),("BOWS","弓"),
   ("FUSION RIFLES","聚合步槍"),("LINEAR FUSION RIFLES","線性聚合步槍"),("SHOTGUNS","霰彈槍"),
   ("HEAT WEAPONS","熱能武器"),("MICRO MISSILES","微型導彈")]),
]

# 顯著協同(人工精選子集,非 synergy 資料的推導結果 —— 例:治療精選 6 套但實際 19 套帶 HEALING)
NOTABLE=[
 ("灼燒","SOLAR",["Seventh Seraph","Apostate's Blade","Collective Psyche","Lustrous"]),
 ("電弧","ARC",["Luminopotent","Circuit","Taken King"]),
 ("虛空","VOID",["Veritas","Eutechnology","Nezarec's Nightmare","Oryx's Memory"]),
 ("冰凝","STASIS",["Crystocrene","Techeun's Regalia"]),
 ("縈絲","STRAND",["Thunderhead","Flain","Collective Psyche"]),
 ("超能力","SUPER",["Iron Battalion Set","Taken King","Legacy's Oath","Wayward Psyche Set"]),
 ("手榴彈","GRENADE",["Thunderhead","CODA","Sage Protector","Great Hunt"]),
 ("近戰","MELEE",["Swordmaster","Apostate's Blade","CODA","Kentarch 3"]),
 ("職業技能","CLASS ABILITY",["Dark Age","Sage Protector"]),
 ("全部技能","ALL ABILITIES",["Techeun's Regalia","Taken King"]),
 ("力量球體","ORBS OF POWER",["Exodus Down","Crystocrene","Yearning Echo","Atheon's Memory","Nezarec's Nightmare"]),
 ("治療","HEALING",["Dreambane","Lustrous","Iron Panoply Set","Apostate's Blade","Dark Age","Resonant Fury"]),
 ("生存能力","SURVIVABILITY",["Exodus Down","Crystocrene","Bushido","Yearning Echo","Crota's Memory","Nezarec's Nightmare"]),
 ("彈藥","AMMO",["Thriving Survivor","Ferropotent","Last Discipline","Cyberserpent Null","Oryx's Memory"]),
 ("元素拾取物","ELEMENTAL PICKUPS",["Veritas","Luminopotent","Eutechnology","Yearning Echo"]),
]

# 高數值來源 官方繁中對照(地點/活動/廠商名皆取自 Bungie manifest 正式譯名)
SRC_ZH={
 "DISTORTIONS / MASTER LOST SECTORS: EDZ":"扭曲 / 大師遺落之地:歐洲死區",
 "DISTORTIONS / MASTER LOST SECTORS: NESSUS":"扭曲 / 大師遺落之地:涅索斯",
 "DISTORTIONS / MASTER LOST SECTORS: DREAMING CITY":"扭曲 / 大師遺落之地:千夢之城",
 "DISTORTIONS / MASTER LOST SECTORS: MOON":"扭曲 / 大師遺落之地:月球",
 "DISTORTIONS / MASTER LOST SECTORS: EUROPA":"扭曲 / 大師遺落之地:木衛二",
 "DISTORTIONS / MASTER LOST SECTORS: COSMODROME":"扭曲 / 大師遺落之地:太空發射場",
 "DISTORTIONS / MASTER LOST SECTORS: THRONE WORLD":"扭曲 / 大師遺落之地:列王之境",
 "MASTER LOST SECTORS / OVERRIDE: NEOMUNA":"大師遺落之地 / 覆寫行動:尼爾穆那",
 "MASTER LOST SECTORS / OVERTHROW: PALE HEART":"大師遺落之地 / 推翻:冰冷之心",
 "THE SIEVE / MYTHIC EXPLORATION / GEAR FOCUSING: KEPLER":"篩網 / 神話探索 / 裝備專注:克卜勒",
 "GRANDMASTER LAWLESS FRONTIER JOBS":"宗師無序邊疆委託",
 "VANGUARD FOCUSING":"先鋒專注",
 "TENET OF BRAVERY FOCUSING":"勇敢教條專注",
 "GAMBIT":"千謀百計",
 "CRUCIBLE FOCUSING":"熔爐專注",
 "IRON BANNER":"鋼鐵旗幟",
 "COMPETITIVE CRUCIBLE":"競賽對戰熔爐",
 "TRIALS OF OSIRIS":"歐西里斯的試煉",
 "SPARROW RACING":"快雀競速",
 "FEATURED DUNGEON: SHATTERED THRONE":"精選地城:破碎王座",
 "FEATURED DUNGEON: PIT OF HERESY":"精選地城:異端深坑",
 "FEATURED DUNGEON: PROPHECY":"精選地城:預言",
 "FEATURED OR MASTER DUNGEON: GRASP OF AVARICE":"精選或大師地城:貪婪之握",
 "FEATURED OR MASTER DUNGEON: DUALITY":"精選或大師地城:二元性",
 "FEATURED OR MASTER DUNGEON: SPIRE OF THE WATCHER":"精選或大師地城:守望者尖塔",
 "FEATURED OR MASTER DUNGEON: GHOSTS OF THE DEEP":"精選或大師地城:鬼魅深淵",
 "FEATURED OR MASTER DUNGEON: WARLORDS RUIN":"精選或大師地城:戰爭軍閥廢墟",
 "FEATURED OR MASTER DUNGEON: VESPER'S HOST":"精選或大師地城:太白星之主",
 "FEATURED OR MASTER DUNGEON: SUNDERED DOCTRINE":"精選或大師地城:潰裂教義",
 "EQUILIBRIUM DUNGEON WITH FEATS ENABLED":"平衡之境地城(啟用功績)",
 "FEATURED OR MASTER RAID: LAST WISH":"精選或大師突襲:最後遺願",
 "FEATURED OR MASTER RAID: GARDEN OF SALVATION":"精選或大師突襲:救贖之園",
 "FEATURED OR MASTER RAID: DEEP STONE CRYPT":"精選或大師突襲:深石地窖",
 "FEATURED OR MASTER RAID: VAULT OF GLASS":"精選或大師突襲:琉璃寶庫",
 "FEATURED OR MASTER RAID: VOW OF THE DISCIPLE":"精選或大師突襲:門徒之誓",
 "FEATURED OR MASTER RAID: CROTA'S END":"精選或大師突襲:克洛塔的結局",
 "FEATURED OR MASTER RAID: ROOT OF NIGHTMARES":"精選或大師突襲:夢魘根源",
 "FEATURED OR MASTER RAID: KING'S FALL":"精選或大師突襲:國王的殞落",
 "FEATURED OR MASTER RAID: SALVATION'S EDGE":"精選或大師突襲:救贖邊緣",
 "DESERT PERPETUAL RAID WITH FEATS":"永久沙漠突襲(含功績)",
 "EPIC DESERT PERPETUAL RAID WITH FEATS":"史詩永久沙漠突襲(含功績)",
 "PANTHEON RAIDS WITH FEATS":"萬神殿突襲(含功績)",
}
def src_zh(src): return SRC_ZH.get(src, src)

def disp(name):  # 顯示用:去掉多餘 " Set" 後綴
    return name[:-4] if name.endswith(" Set") else name
def normset(n):  # synergy_icons.json 的鍵規則(全大寫、去 " SET")
    return n.upper().replace(" SET","").strip()
def slug(s):     # URL / 前端用的 id
    return re.sub(r"[^a-z0-9]+","-", s.lower().replace("'","").replace("’","")).strip("-")

CN="一二三四五"
def col_title_full(i, zh, en):   # 文字檔沿用的完整欄位標題
    return f"第{CN[i]}欄 · {zh} ({en})"

KEY_FLAT=[(g,en,zh) for g,_,_,items in KEY for en,zh in items]
LABEL2ID={en:slug(en) for _,en,_ in KEY_FLAT}
MANIFEST_VER=json.load(open(os.path.join(CACHE,"manifest.json")))["Response"]["version"]

# ---- 驗證所有引用名稱都存在 ----
missing=set()
for _,_,_,sets in COLUMNS:
    for n,_ in sets:
        if n not in by_en: missing.add(n)
for _,_,ss in NOTABLE:
    for n in ss:
        if n not in by_en: missing.add(n)
if missing:
    # 一定要停:繼續跑的話下面 by_en[n] 照樣 KeyError,只是把這行友善訊息埋在 traceback 底下
    raise SystemExit(f"!! resolved.json 裡找不到這些名稱(遊戲改名了?):{sorted(missing)}")

# ---- 繁中版 ----
def write_zh():
    L=[]
    L.append("DESTINY 2 — 防具套裝效果 (Armor Set Bonuses)｜繁體中文對照")
    L.append("="*60)
    L.append("翻譯全部採用 Bungie 官方 manifest 繁體中文(zh-cht);套裝/技能名稱保留官方英文,說明為官方繁中。")
    L.append("manifest 版本:"+MANIFEST_VER)
    L.append("")
    for i,(_,tzh,ten,sets) in enumerate(COLUMNS):
        L.append("");L.append("━"*60);L.append(f"【{col_title_full(i,tzh,ten)}】");L.append("━"*60)
        for n,src in sets:
            r=by_en[n]
            L.append("")
            L.append(f"■ {r['name_zh']}（{disp(n)}）")
            L.append(f"   高數值來源:{src_zh(src)}  ({src})")
            for p in r["perks"]:
                L.append(f"   {p['count']}件 | {p['name_zh']}（{p['name_en']}）")
                L.append(f"       {' '.join(p['desc_zh'].split())}")
    L.append("");L.append("━"*60);L.append("【NOTABLE SYNERGIES — 顯著協同】");L.append("━"*60)
    for czh,cen,ss in NOTABLE:
        L.append(f"[{czh} {cen}]")
        L.append("    "+"、".join(f"{by_en[x]['name_zh']}（{disp(x)}）" for x in ss))
    open(os.path.join(DOCS,"exports","destiny2_armor_bonuses_zhTW.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")

# ---- 英文版 ----
def write_en():
    L=[]
    L.append("DESTINY 2 — ARMOR SET BONUSES (Official English, Bungie manifest)")
    L.append("="*60)
    L.append("")
    for _,_,ten,sets in COLUMNS:
        L.append("");L.append("="*60);L.append(ten);L.append("="*60)
        for n,src in sets:
            r=by_en[n]
            L.append("")
            L.append(f"{disp(n)}")
            L.append(f"   HIGH STAT SOURCE: {src}")
            for p in r["perks"]:
                L.append(f"   {p['count']} Piece | {p['name_en']}")
                L.append(f"       {' '.join(p['desc_en'].split())}")
    L.append("");L.append("[NOTABLE SYNERGIES]")
    for _,cen,ss in NOTABLE:
        L.append(f"  {cen}: "+", ".join(disp(x) for x in ss))
    open(os.path.join(DOCS,"exports","destiny2_armor_bonuses_EN.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")

# ---- 中英對照版 ----
def write_bi():
    L=[]
    L.append("DESTINY 2 — ARMOR SET BONUSES｜中英對照 (Official EN / 官方繁中)")
    L.append("="*60)
    for i,(_,tzh,ten,sets) in enumerate(COLUMNS):
        L.append("");L.append("#"*60);L.append(f"## {col_title_full(i,tzh,ten)}");L.append("#"*60)
        for n,src in sets:
            r=by_en[n]
            L.append("")
            L.append(f"■ {disp(n)}  |  {r['name_zh']}")
            L.append(f"   SOURCE 高數值來源: {src}")
            L.append(f"                     {src_zh(src)}")
            for p in r["perks"]:
                L.append(f"   ── {p['count']} Piece | {p['name_en']}  ({p['name_zh']})")
                L.append(f"      EN: {' '.join(p['desc_en'].split())}")
                L.append(f"      中: {' '.join(p['desc_zh'].split())}")
    open(os.path.join(DOCS,"exports","destiny2_armor_bonuses_bilingual.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")

# ---- 圖例 sprite(網站用)----
# 圖示本身是單色遮罩,故轉為純白 + 原 alpha,讓前端用 CSS mask + currentColor 決定顏色:
# 主題、選取態、0 命中變灰、篩選命中高亮都因此變成一行 CSS,不用做多套素材。
CELL=64; SPRITE_COLS=8
def write_sprite():
    rows=(len(KEY_FLAT)+SPRITE_COLS-1)//SPRITE_COLS
    sp=Image.new("RGBA",(CELL*SPRITE_COLS, CELL*rows),(0,0,0,0))
    for i in range(len(KEY_FLAT)):
        im=Image.open(os.path.join(DOCS,"assets","icons",f"icon_{i+1:02d}.png")).convert("RGBA")
        im=im.resize((CELL,CELL),Image.LANCZOS)
        w=Image.new("RGBA",(CELL,CELL),(255,255,255,0)); w.putalpha(im.getchannel("A"))
        sp.paste(w,(CELL*(i%SPRITE_COLS), CELL*(i//SPRITE_COLS)))
    p=os.path.join(DOCS,"assets","icons","sprite.png")
    sp.save(p,"PNG",optimize=True)
    return sp.size, os.path.getsize(p)

# ---- exports metadata(網站靠它顯示檔案大小)----
# 【雞生蛋】site.json 要記 PNG 大小,但 PNG 要先讀 site.json 才能產。
# 解法:這裡先以現有檔案填(不存在則 bytes=null),等 make_image.py 跑完再由
# --stamp-exports 回填。
def build_exports():
    out=[]
    # 標籤只寫語言,不寫格式:網站的卡片本來就有 PNG/TXT 徽章,再寫一次「大圖/poster」
    # 是重複的。省下來的寬度剛好讓雙語模式的中英能各佔一行、不必縮寫。
    for nm,lzh,len_ in (("zhTW","繁體中文","Traditional Chinese"),
                        ("bilingual","中英對照","Bilingual"),
                        ("EN","英文","English")):
        for ext in (".png",".txt"):
            rel=f"exports/destiny2_armor_bonuses_{nm}{ext}"
            p=os.path.join(DOCS,rel)
            e={"path":rel,"label_zh":lzh,"label_en":len_,
               "bytes":os.path.getsize(p) if os.path.exists(p) else None}
            if ext==".png" and os.path.exists(p):
                with Image.open(p) as im: e["dim"]=f"{im.width}×{im.height}"
            out.append(e)
    return out

def stamp_exports():
    """make_image.py 產完 PNG 後回填 exports 大小,只動 site.json 的這一段。"""
    p=os.path.join(DOCS,"data","site.json")
    site=json.load(open(p,encoding="utf-8"))
    site["exports"]=build_exports()
    json.dump(site,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    return site["exports"]

# ---- 單一資料合約 site.json ----
def write_site():
    out={"manifest_version":MANIFEST_VER,
         "groups":[{"id":g,"zh":gzh,"en":gen} for g,gzh,gen,_ in KEY],
         "key":[{"id":LABEL2ID[en],"en":en,"zh":zh,"group":g,
                 "icon":f"assets/icons/icon_{i+1:02d}.png"}
                for i,(g,en,zh) in enumerate(KEY_FLAT)],
         "columns":[], "notable":[], "exports":[]}
    for cid,tzh,ten,sets in COLUMNS:
        col={"id":cid,"title_zh":tzh,"title_en":ten,"sets":[]}
        for n,src in sets:
            r=by_en[n]; sy=SYN[normset(n)]; pi=PERKICONS[disp(n)]
            syn={c:[LABEL2ID[l] for l in sy[c]] for c in ("2","4")}
            col["sets"].append({
                "id":slug(disp(n)), "name_en":disp(n), "name_zh":r["name_zh"],
                "source":src, "source_zh":src_zh(src),
                "tags":sorted(set(syn["2"])|set(syn["4"])),
                "synergy":syn,
                "perks":[{"count":p["count"],"name_en":p["name_en"],"name_zh":p["name_zh"],
                          "desc_en":p["desc_en"],"desc_zh":p["desc_zh"],
                          "icon":"assets/perkicons/"+pi[str(p["count"])]} for p in r["perks"]]})
        out["columns"].append(col)
    for czh,cen,ss in NOTABLE:
        out["notable"].append({"id":slug(cen),"category_zh":czh,"category_en":cen,
                               "set_ids":[slug(disp(x)) for x in ss]})
    out["exports"]=build_exports()
    json.dump(out,open(os.path.join(DOCS,"data","site.json"),"w",encoding="utf-8"),
              ensure_ascii=False,indent=2)
    return out

# ---- 檢查是否有來源字串沒對到官方譯文 ----
uncovered=sorted({src for _,_,_,ss in COLUMNS for _,src in ss if src not in SRC_ZH})
if uncovered:
    print("!! 未翻譯的來源:",uncovered)
else:
    print("所有高數值來源皆已對應官方繁中 ✓")

if __name__=="__main__":
    if "--stamp-exports" in sys.argv:      # make_image.py 之後跑,回填 PNG 大小
        for e in stamp_exports():
            print(f"  {e['path']:<48} {e['bytes'] or 0:>9,} B  {e.get('dim','')}")
        print("exports 大小已回填 site.json")
        sys.exit(0)
    write_zh(); write_en(); write_bi()
    (sw,sh),sb=write_sprite(); print(f"sprite: {sw}×{sh} = {sb:,} bytes ({len(KEY_FLAT)} 圖示)")
    out=write_site()
    print(f"site.json: {sum(len(c['sets']) for c in out['columns'])} 套裝 / {len(out['key'])} 圖例 / "
          f"{len(out['notable'])} 顯著協同 / {len(out['exports'])} 成品 / "
          f"{os.path.getsize(os.path.join(DOCS,'data','site.json')):,} bytes")
    print("done →", os.path.join(DOCS,"data","site.json"))
