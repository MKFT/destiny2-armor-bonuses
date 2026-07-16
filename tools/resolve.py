# -*- coding: utf-8 -*-
"""由 Bungie manifest 解析 56 套裝的官方英/繁 名稱+說明 → cache/derived/resolved.json。
需先跑 tools/download.sh 下載 cache/manifest_en/ 與 cache/manifest_zhcht/。"""
import os, json
BASE=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(BASE,"cache")
def load(lang,defn): return json.load(open(os.path.join(D,f"manifest_{lang}",defn+".json")))
se=load("en","DestinyEquipableItemSetDefinition"); sz=load("zhcht","DestinyEquipableItemSetDefinition")
pe=load("en","DestinySandboxPerkDefinition");      pz=load("zhcht","DestinySandboxPerkDefinition")
def perk(h,src):
    d=src.get(str(h)); dp=(d or {}).get("displayProperties",{})
    return dp.get("name",""), dp.get("description","")
resolved=[]
for h,s in se.items():
    perks=[]
    for sp in sorted(s["setPerks"], key=lambda x:x["requiredSetCount"]):
        ph=sp["sandboxPerkHash"]; ne,de=perk(ph,pe); nz,dz=perk(ph,pz)
        perks.append({"count":sp["requiredSetCount"],"name_en":ne,"desc_en":de,"name_zh":nz,"desc_zh":dz})
    resolved.append({"hash":h,"name_en":s["displayProperties"]["name"],
                     "name_zh":sz[h]["displayProperties"]["name"],"perks":perks})
os.makedirs(os.path.join(D,"derived"),exist_ok=True)
json.dump(resolved,open(os.path.join(D,"derived","resolved.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("resolved.json 已重建,共",len(resolved),"套裝")
