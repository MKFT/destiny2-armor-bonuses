#!/usr/bin/env bash
# 精簡下載:只抓更新譯文所需的 2 種定義(英+繁,實測約 5MB),而非整包 manifest。
# 需要的定義:DestinyEquipableItemSetDefinition、DestinySandboxPerkDefinition。
# 一切輸出都進 tools/cache/(.gitignore)。
set -e
mkdir -p "$(dirname "$0")/cache"
cd "$(dirname "$0")/cache"
UA="Mozilla/5.0 (X11; Linux x86_64) Chrome/126.0 Safari/537.36"
mkdir -p manifest_en manifest_zhcht

# 【每日維護】Destiny 2 維護時,這個端點會回 HTTP 500 + 一段長得像正常 JSON 的錯誤內容
# ({"ErrorCode":2102,"ErrorStatus":"ApiKeyMissingFromRequest"...} —— 訊息誤導,其實不缺金鑰)。
# 所以:(1) 用 -f 讓 curl 對 HTTP 錯誤回非零 (2) 下載到暫存檔、驗過有 Response.version
# 才覆蓋。少了這兩層,那段錯誤會直接蓋掉好的 manifest.json,而且要等到後面某個
# KeyError 才發現 —— 屆時原始資料已經沒了。
echo "取得 manifest 索引…"
curl -fsSL -m 40 --retry 3 --retry-delay 3 --retry-all-errors \
     -A "$UA" "https://www.bungie.net/Platform/Destiny2/Manifest/" -o manifest.json.tmp \
  || { echo "!! 抓不到 manifest 索引(Bungie 可能正在每日維護)。manifest.json 未更動。" >&2
       rm -f manifest.json.tmp; exit 1; }

python3 - <<'PY' || { rm -f manifest.json.tmp; exit 1; }
import json, sys
try:
    v = json.load(open("manifest.json.tmp"))["Response"]["version"]
except Exception as e:
    print(f"!! 索引內容不對({type(e).__name__})。Bungie 可能正在每日維護。"
          f"manifest.json 未更動。", file=sys.stderr)
    sys.exit(1)
print("  索引 OK,version =", v)
PY
mv manifest.json.tmp manifest.json

python3 - <<'PY'
import json, urllib.request
m=json.load(open("manifest.json"))["Response"]["jsonWorldComponentContentPaths"]
UA={"User-Agent":"Mozilla/5.0"}
DEFS=["DestinyEquipableItemSetDefinition","DestinySandboxPerkDefinition"]
for lang,folder in [("en","manifest_en"),("zh-cht","manifest_zhcht")]:
    for defn in DEFS:
        url="https://www.bungie.net"+m[lang][defn]
        dst=f"{folder}/{defn}.json"
        # urlopen 對 4xx/5xx 會丟 HTTPError,所以這裡不需要額外的檢查;
        # 但仍先寫暫存檔,免得中途斷線留下半截的定義檔。
        data=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60).read()
        open(dst+".tmp","wb").write(data)
        import os; os.replace(dst+".tmp", dst)
        print("  下載", dst)
print("完成(只抓 4 個定義)")
PY
