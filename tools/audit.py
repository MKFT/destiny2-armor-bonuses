# -*- coding: utf-8 -*-
"""稽核 docs/data/site.json 的內部一致性,並用官方技能說明反查可疑的協同標籤。

背景:協同標籤(synergy_icons.json)是人工視覺辨識來的,manifest 沒有這份資料。
2026-07 的一輪稽核用「官方說明當裁判」找出並修正了 10 筆錯誤 —— 這份資料不可靠,
所以要有這支腳本。遊戲改版、官方改寫技能說明時,同類錯誤會自己浮出來,不必再靠人逐套盯。

檢查 1-5 是硬性的(不通過則 exit 1);檢查 6 是線索產生器,只列出可疑項供人工判讀。
用法: python3 tools/audit.py
"""
import json, os, re, sys
from collections import Counter

BASE=os.path.dirname(os.path.abspath(__file__))
DOCS=os.path.abspath(os.path.join(BASE,"..","docs"))
site=json.load(open(os.path.join(DOCS,"data","site.json"),encoding="utf-8"))

KEY={k["id"]:k for k in site["key"]}
SETS=[s for c in site["columns"] for s in c["sets"]]
fail=[]
def ok(msg):   print(f"  \033[32m✓\033[0m {msg}")
def bad(msg):  print(f"  \033[31m✗\033[0m {msg}"); fail.append(msg)
def note(msg): print(f"    {msg}")

print("\n=== 1. 協同標籤都能反查到圖例 ===")
miss=[(s["name_en"],c,i) for s in SETS for c in ("2","4") for i in s["synergy"][c] if i not in KEY]
bad(f"反查失敗: {miss}") if miss else ok(f"{len(SETS)} 套裝的協同標籤全部命中 {len(KEY)} 個圖例")
# tags 應等於 2件+4件的聯集(前端篩選直接吃這個欄位,錯了會篩出錯的結果)
tb=[s["name_en"] for s in SETS if s["tags"]!=sorted(set(s["synergy"]["2"])|set(s["synergy"]["4"]))]
bad(f"tags 不等於 2+4 聯集: {tb}") if tb else ok("tags 欄位皆等於 2件+4件的聯集")

print("\n=== 2. 沒有任何一件是空標籤 ===")
empty=[(s["name_en"],c) for s in SETS for c in ("2","4") if not s["synergy"][c]]
bad(f"空標籤: {empty}") if empty else ok("每套裝的 2件與 4件都至少有一個標籤")

print("\n=== 3. 標記原則:4件相對 2件應「完全相同」或「完全不重疊」 ===")
# 標記原則:2件標過的 4件就不重複標;若兩者標籤集合完全相同則合併顯示為「2·4」。
PARTIAL_OK={
  "resonant-fury": "2件與4件都確實提供治療(2件受近戰傷害後回血、4件切換武器治療並消耗層數),"
                   "但4件另有 WEAPONS/GLAIVES 使兩者集合不同、無法合併 —— 這是上述二分法"
                   "(不重複 XOR 合併)表達不了的情況,非錯誤。",
}
same=[];disj=[];part=[]
for s in SETS:
    a,b=set(s["synergy"]["2"]),set(s["synergy"]["4"])
    (same if a==b else disj if not (a&b) else part).append(s)
unexpected=[s for s in part if s["id"] not in PARTIAL_OK]
print(f"    完全相同(合併 2·4) {len(same)} / 完全不重疊(不重複標) {len(disj)} / 部分重疊 {len(part)}")
if unexpected:
    for s in unexpected:
        bad(f'{s["name_zh"]} ({s["name_en"]}) 部分重疊,重疊={sorted(set(s["synergy"]["2"])&set(s["synergy"]["4"]))}')
else:
    ok(f"{len(same)+len(disj)}/{len(SETS)} 符合原則,{len(part)} 個已知例外")
    for s in part: note(f'例外 {s["name_zh"]} ({s["name_en"]}): {PARTIAL_OK[s["id"]]}')

print("\n=== 4. NOTABLE 宣稱的套裝確實帶有對應標籤 ===")
byid={s["id"]:s for s in SETS}
gaps=[];skipped=[]
for n in site["notable"]:
    if n["id"] not in KEY:      # 例:「彈藥 AMMO」是寬鬆大標題,圖例裡只有 ALL/SPECIAL/HEAVY AMMO
        skipped.append(f'{n["category_zh"]} {n["category_en"]}'); continue
    for sid in n["set_ids"]:
        if n["id"] not in byid[sid]["tags"]:
            gaps.append(f'{n["category_en"]} 說 {byid[sid]["name_en"]} 有,但其標籤為 {byid[sid]["tags"]}')
bad("落差:\n     "+"\n     ".join(gaps)) if gaps else ok(f"{len(site['notable'])-len(skipped)} 個精選分類的名單與標籤零落差")
for s in skipped: note(f"跳過(非圖例標籤,屬寬鬆大標題): {s}")
# NOTABLE 是編輯精選子集,不是推導結果 —— 精選數 < 命中數屬正常(例:治療精選 6 套但 19 套帶標籤)。
# 反過來「精選數 > 命中數」代表 NOTABLE 宣稱了不存在的標籤,那是矛盾 —— 已由上面的落差檢查攔下,
# 不在這裡重複報,免得印出「精選為子集」這種與事實相反的話。
cnt=Counter(t for s in SETS for t in s["tags"])
subset=[f'{n["category_zh"]}{len(n["set_ids"])}/{cnt[n["id"]]}' for n in site["notable"]
        if n["id"] in KEY and len(n["set_ids"])<cnt[n["id"]]]
if subset: note("精選/命中(精選為編輯子集,正常): "+"  ".join(subset))

print("\n=== 5. 素材檔案齊全 ===")
missf=[p for p in ([s["icon"] for s in site["key"]]
                   + [pk["icon"] for s in SETS for pk in s["perks"]]
                   + ["assets/icons/sprite.png"])
       if not os.path.exists(os.path.join(DOCS,p))]
bad(f"缺檔: {missf}") if missf else ok(f'{len(site["key"])} 圖例 + {len(SETS)*2} 徽章 + sprite 全部存在')
unused=[k["id"] for k in site["key"] if cnt[k["id"]]==0]
bad(f"未被任何套裝使用的圖例: {unused}") if unused else ok(f"{len(KEY)} 個圖例每個都至少被一套裝使用")

print("\n=== 6. 官方說明關鍵字交叉稽核（線索,非定論）===")
# Destiny 的元素機制有自己的詞彙 —— 說明裡不會寫「Stasis」而是寫「Frost Armor」。
# 沒有這本字典,元素標籤會被大量誤報。這些詞是 2026-07 稽核時逐一驗證出來的。
EV={
 'solar':r'\b(solar|scorch|ignit|radiant|restoration|cure|sunspot|firesprite|incandescent)',
 'void':r'\b(void|volatile|devour|invisib|suppress|weaken|overshield)',
 'arc':r'\b(arc|jolt|blind|amplified|ionic trace|bolt charge|spark)',
 'stasis':r'\b(stasis|frost armor|freez|frozen|shatter|slow|diamond lance)',
 'strand':r'\b(strand|sever|suspend|unravel|tangle|threadling|woven mail)',
 'prismatic':r'\b(prismatic|transcend)', 'kinetic':r'\bkinetic\b',
 'super':r'\bsuper\b', 'grenade':r'\bgrenades?\b', 'melee':r'\bmelees?\b',
 'class-ability':r'\b(class ability|class energy|barricade|rift|dodge)\b',
 'orbs-of-power':r'\borbs? of power\b',
 'elemental-pickups':r'\b(elemental pickup|ionic trace|void breach|firesprite|stasis shard|warmind charge)',
 'special-ammo':r'\bspecial ammo\b', 'heavy-ammo':r'\bheavy ammo\b',
 'finishers':r'\bfinish', 'disorient':r'\bdisorient', 'exhaust':r'\bexhaust',
 'swords':r'\bswords?\b','glaives':r'\bglaives?\b','bows':r'\bbows?\b','shotguns':r'\bshotguns?\b',
 'sidearms':r'\bsidearms?\b','scout-rifles':r'\bscout rifles?\b','smgs':r'\bsubmachine guns?\b',
 'hand-cannons':r'\bhand cannons?\b','auto-rifles':r'\bauto rifles?\b','rockets':r'\brocket',
 'grenade-launchers':r'\bgrenade launcher','linear-fusion-rifles':r'\blinear fusion',
 'micro-missiles':r'\bmicro-?missile',
}
# 這些是主觀判斷,說明裡沒有對應字面,無法字面驗證
ABSTRACT={'weapons','survivability','healing','light','darkness','armor-charge',
          'health-stat','weapon-stat','mobility','all-ammo','all-abilities',
          'fusion-rifles','heat-weapons'}
# 「延續標記」:4件的說明引用了 2件的具名效果,所以 2件的標籤合理地延續到 4件,
# 4件自己的說明裡自然找不到那些字面。這不是錯誤,列在此處免得每次稽核都重報。
CARRY_OVER={
 ("aion-renewal","4"):   ({"rockets","grenade-launchers","micro-missiles"},
   "4件「Once per activation of Force Converter…」引用 2件的 Force Converter,"
   "而該武器類型限制是 2件定義的"),
 ("sage-protector","4"): ({"grenade","class-ability"},
   "4件「ready Blade Focus」與 2件「Sword hits return grenade and class energy…"
   "if Blade Focus is active」互相引用,能量來源在 2件"),
}
sus=[]
for s in SETS:
    for p in s["perks"]:
        c=str(p["count"]); txt=p["desc_en"].lower()
        tg=re.sub(r'grenade launchers?','',txt)     # 避免 grenade 誤中 grenade launcher
        carry=CARRY_OVER.get((s["id"],c),(set(),""))[0]
        for tid in s["synergy"][c]:
            if tid in ABSTRACT or tid not in EV or tid in carry: continue
            if not re.search(EV[tid], tg if tid=='grenade' else txt):
                sus.append(("多標?",s,c,tid,p["desc_en"]))
if sus:
    for k,s,c,tid,d in sus:
        print(f'  ? {s["name_zh"]} ({s["name_en"]}) {c}件 標了 [{KEY[tid]["en"]}] 但說明無對應字面')
        note(" ".join(d.split())[:120])
    note("↑ 需人工判讀。可能是新的機制詞彙尚未進字典,也可能是真的標錯。")
else:
    ok("所有可字面驗證的標籤,官方說明都找得到依據")
note(f"(跳過 {len(ABSTRACT)} 個無法字面驗證的主觀標籤,如 WEAPONS/SURVIVABILITY/HEALING)")
for (sid,c),(tags,why) in CARRY_OVER.items():
    note(f'(跳過延續標記 {byid[sid]["name_zh"]} {c}件 {sorted(tags)}: {why})')

print("\n=== 標籤命中數（改版後可比對增減）===")
for g in site["groups"]:
    ids=[k["id"] for k in site["key"] if k["group"]==g["id"]]
    print(f'  {g["zh"]:<7}'+"  ".join(f'{KEY[i]["zh"]}{cnt[i]}' for i in ids))

print()
if fail:
    print(f"\033[31m稽核未通過:{len(fail)} 項\033[0m"); sys.exit(1)
print(f"\033[32m稽核通過\033[0m — {len(SETS)} 套裝 / {len(KEY)} 圖例 / {len(site['notable'])} 精選分類")
