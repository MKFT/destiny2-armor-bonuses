# -*- coding: utf-8 -*-
"""產生 src/labels_i18n.json:給 KEY 圖例、分組標題、欄位標題、來源字串 補上 zhs/ja/ko 三語。

en 與 zh 的值早已定案在 build_texts.py 的表格裡(對應現有大圖),此檔只「疊加」新增三語,
build_texts 合併時 en/zh 一律以自己的表格為準,不受此檔影響。

三語來源:
  - 官方詞(傷害/武器類別/屬性…) 從 tools/cache/probe/ 的 manifest 定義自動抽。
  - 白話桶子(SURVIVABILITY 等) 與選詞(HEALING 用泛指、DISORIENT…) 用人工查證值(見 MULTILINGUAL.md)。
  - 來源字串的專名(突襲/地城/地點名) 從 Activity/Destination/Mode 定義自動抽,連接詞用詞表組裝。
需要 probe/ 在位(見 MULTILINGUAL.md;不在就重跑該處的下載)。
"""
import json, os, re
BASE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(BASE,".."))
PROBE=os.path.join(BASE,"cache","probe")
LANGS=["zhs","ja","ko"]                 # 只補這三語;對應 manifest 資料夾 zhchs/ja/ko
FOLDER={"zhs":"zhchs","ja":"ja","ko":"ko"}

def load(lang_folder, defn):
    p=os.path.join(PROBE,f"{lang_folder}_{defn}.json")
    return json.load(open(p,encoding="utf-8")) if os.path.exists(p) else {}

def name_index(defn):
    """en 名稱(小寫) → {zhs,ja,ko} 名稱。用英文名當錨對齊。"""
    en=load("en",defn); out={}
    langs={l:load(FOLDER[l],defn) for l in LANGS}
    for h,e in en.items():
        nm=(e.get("displayProperties",{}) or {}).get("name","")
        if nm: out[nm.lower()]={l:(langs[l].get(h,{}).get("displayProperties",{}) or {}).get("name","") for l in LANGS}
    return out

DMG=name_index("DestinyDamageTypeDefinition")
CAT=name_index("DestinyItemCategoryDefinition")
STAT=name_index("DestinyStatDefinition")
POOL={**DMG,**CAT,**STAT}

def strip_dmg(v):   # 傷害類型官方名帶「傷害/伤害」後綴,圖例標籤要乾淨
    return {l:v[l].replace("傷害","").replace("伤害","").strip() for l in LANGS}

# KEY 標籤 → manifest 官方英文名(處理改名/單複數)。抽到的直接用。
OFFICIAL={"SOLAR":"solar","VOID":"void","ARC":"arc","STASIS":"stasis","STRAND":"strand","KINETIC":"kinetic",
 "SUPER":"super","GRENADE":"grenade","MELEE":"melee","CLASS ABILITY":"class",
 "SWORDS":"sword","GLAIVES":"glaives","ROCKETS":"rocket launcher","GRENADE LAUNCHERS":"grenade launchers",
 "AUTO RIFLES":"auto rifle","SIDEARMS":"sidearm","SCOUT RIFLES":"scout rifle","HAND CANNONS":"hand cannon",
 "BOWS":"bows","FUSION RIFLES":"fusion rifle","LINEAR FUSION RIFLES":"linear fusion rifles",
 "SHOTGUNS":"shotgun","SMGS":"submachine guns","PULSE RIFLES":"pulse rifle"}
DMG_LABELS={"SOLAR","VOID","ARC","STASIS","STRAND","KINETIC"}

# 白話桶子 + 選詞 + 帶後綴的屬性標籤:人工查證值(MULTILINGUAL.md)。順序 zhs / ja / ko。
MANUAL_KEY={
 "PRISMATIC":       ("棱镜","プリズム","프리즘"),
 "ALL ABILITIES":   ("所有技能","全てのスキル","모든 능력"),
 "ORBS OF POWER":   ("能量球","力のオーブ","힘의 보주"),
 "ELEMENTAL PICKUPS":("元素拾取物","属性オブジェクト","원소 결정체"),
 "ALL AMMO":        ("所有弹药","全ての弾薬","모든 탄약"),          # 合成:所有 + 彈藥
 "SPECIAL AMMO":    ("特殊弹药","特殊弾","특수 탄약"),
 "HEAVY AMMO":      ("重型弹药","重弾","중화기 탄약"),
 "FINISHERS":       ("终结技","フィニッシャー","필살기"),
 "DISORIENT":       ("迷失","混乱","교란"),
 "EXHAUST":         ("疲惫","疲労","탈진"),
 "HEALING":         ("治疗","回復","치료"),                       # 泛指 heal,非 Cure buff
 "SURVIVABILITY":   ("生存能力","生存力","생존력"),                # 純白話,唯一凭空翻
 "LIGHT":           ("光能","光","빛"),
 "DARKNESS":        ("暗影","暗黒","어둠"),
 "ARMOR CHARGE":    ("护甲充能","アーマーチャージ","방어구 충전"),   # 簡中官方是「护甲」非「防具」
 "HEALTH STAT":     ("生命值","体力","생명력"),
 "WEAPON STAT":     ("武器数值","武器ステータス","무기 능력치"),
 "MOBILITY":        ("机动能力","機動性","기동성"),
 "WEAPONS":         ("武器","武器","무기"),                        # 泛指任何武器
 "HEAT WEAPONS":    ("热能武器","熱武器","열 무기"),
 "MICRO MISSILES":  ("微型导弹","マイクロミサイル","마이크로 미사일"),
}

def key_labels():
    site=json.load(open(os.path.join(ROOT,"docs","data","site.json"),encoding="utf-8"))
    out={}; gaps=[]
    for k in site["key"]:
        en=k["label"]["en"]
        if en in OFFICIAL and OFFICIAL[en] in POOL:
            v=POOL[OFFICIAL[en]]
            out[en]=strip_dmg(v) if en in DMG_LABELS else dict(v)
        elif en in MANUAL_KEY:
            out[en]=dict(zip(LANGS, MANUAL_KEY[en]))
        else:
            gaps.append(en)
    return out, gaps

# 分組標題(5)、欄位標題(5):人工。zhs / ja / ko。
GROUPS={
 "element":       ("元素","エレメント","속성"),
 "ability":       ("技能","スキル","능력"),
 "pickup":        ("拾取物与状态","取得物と状態","획득물과 상태"),
 "stat":          ("生存与数值","生存と数値","생존과 수치"),
 "weapon":        ("武器","武器","무기"),
}
COLUMNS={
 "world":    ("世界/遗落之地","世界/ロストセクター","세계/로스트 섹터"),
 "vanguard": ("先锋/熔炉聚焦","バンガード/るつぼフォーカス","뱅가드/크루시블 포커싱"),
 "crucible": ("熔炉 PvP","るつぼ PvP","크루시블 PvP"),
 "dungeon":  ("地城","ダンジョン","던전"),
 "raid":     ("突袭","レイド","레이드"),
}

# ── 來源字串 SRC:專名(突襲/地城/地點名) 自動抽 + 連接詞詞表組裝 ──
def activity_index():
    """建 en 名稱(小寫,去 ': Normal' 之類後綴) → {zhs,ja,ko}。涵蓋 Destination/Mode/Activity。"""
    out={}
    for defn in ("DestinyDestinationDefinition","DestinyActivityModeDefinition","DestinyActivityDefinition"):
        en=load("en",defn); langs={l:load(FOLDER[l],defn) for l in LANGS}
        for h,e in en.items():
            nm=(e.get("displayProperties",{}) or {}).get("name","")
            if not nm: continue
            base=re.split(r":\s", nm)[0].strip().lower()   # 去 "Last Wish: Normal" 的後綴
            if base and base not in out:
                out[base]={l:re.split(r"[:：]\s?", (langs[l].get(h,{}).get("displayProperties",{}) or {}).get("name",""))[0].strip() for l in LANGS}
    return out
ACT=activity_index()

# SRC 連接詞詞表(zhs / ja / ko)。key 為英文片段(大寫)。
VOCAB={
 "DISTORTIONS":("扭曲","歪み","왜곡"),
 "MASTER LOST SECTORS":("大师遗落之地","マスター・ロストセクター","마스터 로스트 섹터"),
 "MASTER":("大师","マスター","마스터"),
 "FEATURED OR MASTER":("精选或大师","注目またはマスター","주요 또는 마스터"),
 "FEATURED":("精选","注目","주요"),
 "DUNGEON":("地城","ダンジョン","던전"),
 "RAID":("突袭","レイド","레이드"),
 "OVERRIDE":("覆写行动","オーバーライド","오버라이드"),
 "OVERTHROW":("推翻","オーバースロー","전복"),
 "THE SIEVE":("筛网","ザ・シーヴ","시브"),
 "MYTHIC EXPLORATION":("神话探索","神話探索","신화 탐험"),
 "GEAR FOCUSING":("装备专注","ギアフォーカス","장비 포커싱"),
 "FOCUSING":("专注","フォーカス","포커싱"),
 "GRANDMASTER LAWLESS FRONTIER JOBS":("宗师无序边疆委托","グランドマスター・無法フロンティア依頼","그랜드마스터 무법 변경 임무"),
 "VANGUARD":("先锋","バンガード","뱅가드"),
 "TENET OF BRAVERY":("勇敢教条","勇気の信条","용맹의 교리"),
 "CRUCIBLE":("熔炉","るつぼ","크루시블"),
 "IRON BANNER":("钢铁旗帜","アイアンバナー","철기 깃발"),
 "COMPETITIVE":("竞赛对战","競技","경쟁전"),
 "TRIALS OF OSIRIS":("欧西里斯的试炼","オシリスの試練","오시리스의 시련"),
 "SPARROW RACING":("快雀竞速","スパロウレース","스패로우 레이싱"),
 "EQUILIBRIUM":("平衡之境","イクリブリアム","평형"),
 "WITH FEATS ENABLED":("(启用功绩)","(偉業有効)","(위업 활성화)"),
 "WITH FEATS":("(含功绩)","(偉業付き)","(위업 포함)"),
 "DESERT PERPETUAL":("永久沙漠","永劫の砂漠","영원한 사막"),
 "EPIC":("史诗","エピック","서사"),
 "PANTHEON":("万神殿","パンテオン","판테온"),
 "GAMBIT":("千谋百计","ギャンビット","갬빗"),
}
# SRC 專名寫法 → manifest 實際英文名(帶 The/不同名/撇號差異的才要列)。
ALIAS={"DREAMING CITY":"the dreaming city","MOON":"the moon","NESSUS":"nessus orbit",
       "THRONE WORLD":"savathûn's throne world","PALE HEART":"the pale heart",
       "SHATTERED THRONE":"the shattered throne","WARLORDS RUIN":"warlord's ruin"}

def tr_src(en):
    """把英文來源字串逐段譯成三語。專名優先查 activity index,其餘查 VOCAB。"""
    out={}
    for l_i,l in enumerate(LANGS):
        s=en
        # 先換多詞片語(長的先換,避免 MASTER 先吃掉 MASTER LOST SECTORS)
        for k in sorted(VOCAB, key=len, reverse=True):
            if k in s: s=s.replace(k, VOCAB[k][l_i])
        # 冒號後的專名:先過別名再查 activity index
        def repl(m):
            noun=m.group(1).strip()
            hit=ACT.get(ALIAS.get(noun, noun.lower()))
            return ":"+(hit[l] if hit else noun)
        s=re.sub(r":\s*([A-Z][A-Z0-9'’ ]+)$", repl, s)
        # zhs/ja 詞間不打空格(中日排版慣例);韓文保留空格
        if l in ("zhs","ja"): s=re.sub(r"(?<=[^\x00-\x7f]) (?=[^\x00-\x7f])","",s)
        out[l]=s
    return out

def build_src():
    site=json.load(open(os.path.join(ROOT,"docs","data","site.json"),encoding="utf-8"))
    srcs=sorted({s["source"]["en"] for c in site["columns"] for s in c["sets"]})
    out={}; untr=[]
    for en in srcs:
        t=tr_src(en); out[en]=t
        # 偵測沒被譯到的(還殘留大量 ASCII 字母)
        for l in LANGS:
            if re.search(r"[A-Z]{4,}", t[l]): untr.append((en,l,t[l])); break
    return out, untr

if __name__=="__main__":
    key,kgap=key_labels()
    # NOTABLE 的「彈藥 AMMO」是寬鬆大標題,KEY 裡沒有(只有 ALL/SPECIAL/HEAVY AMMO),單獨補
    key["AMMO"]=dict(zip(LANGS,("弹药","弾薬","탄약")))
    src,untr=build_src()
    # groups/columns 由三元組轉成 {zhs,ja,ko} 物件(與 key/src 一致,build 端統一用 dict)
    groups={k:dict(zip(LANGS,v)) for k,v in GROUPS.items()}
    columns={k:dict(zip(LANGS,v)) for k,v in COLUMNS.items()}
    data={"key":key,"groups":groups,"columns":columns,"src":src}
    json.dump(data,open(os.path.join(ROOT,"src","labels_i18n.json"),"w",encoding="utf-8"),
              ensure_ascii=False,indent=1)
    print(f"labels_i18n.json:{len(key)} KEY / {len(GROUPS)} 分組 / {len(COLUMNS)} 欄 / {len(src)} 來源")
    if kgap: print("!! KEY 沒補到:",kgap)
    if untr:
        print(f"!! 來源可能沒完全譯到 {len(untr)} 條(殘留英文):")
        for en,l,v in untr[:10]: print(f"   [{l}] {en} → {v}")
