# -*- coding: utf-8 -*-
"""由 Bungie manifest 解析 56 套裝的官方五語 名稱+說明 → cache/derived/resolved.json。
需先跑 tools/download.sh 下載 cache/manifest_<lang>/(en/zhcht/zhchs/ja/ko)。

輸出的每個文字欄位是「語言碼 → 字串」的物件,語言碼與 site.json 一致:
  en=英文  zh=繁中(zh-cht)  zhs=簡中(zh-chs)  ja=日文  ko=韓文
"""
import os, json
BASE=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(BASE,"cache")
# 語言碼 → manifest 資料夾後綴。加語言只改這裡。
LANGS={"en":"en","zh":"zhcht","zhs":"zhchs","ja":"ja","ko":"ko"}
def load(folder,defn): return json.load(open(os.path.join(D,f"manifest_{folder}",defn+".json")))
SETS={l:load(f,"DestinyEquipableItemSetDefinition") for l,f in LANGS.items()}
PERKS={l:load(f,"DestinySandboxPerkDefinition")     for l,f in LANGS.items()}

def dp(src,h,field):   # 某語言某 hash 的 displayProperties 欄位
    return ((src.get(str(h)) or {}).get("displayProperties",{}) or {}).get(field,"")

resolved=[]
for h,s in SETS["en"].items():   # 以英文為錨列舉(hash 跨語言一致)
    perks=[]
    for sp in sorted(s["setPerks"], key=lambda x:x["requiredSetCount"]):
        ph=sp["sandboxPerkHash"]
        perks.append({"count":sp["requiredSetCount"],
                      "name":{l:dp(PERKS[l],ph,"name") for l in LANGS},
                      "desc":{l:dp(PERKS[l],ph,"description") for l in LANGS}})
    resolved.append({"hash":h,
                     "name":{l:dp(SETS[l],h,"name") for l in LANGS},
                     "perks":perks})
os.makedirs(os.path.join(D,"derived"),exist_ok=True)
json.dump(resolved,open(os.path.join(D,"derived","resolved.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"resolved.json 已重建,共 {len(resolved)} 套裝 × {len(LANGS)} 語")
