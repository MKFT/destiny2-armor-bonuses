#!/usr/bin/env bash
# 完整重建流程:下載官方 manifest → 產生 docs/ 底下的全部成品(site.json、txt、大圖、sprite)。
# 只有遊戲改版、官方譯文有變時才需要跑。用法:bash prepare_data.sh
#
# 素材(docs/assets/icons、docs/assets/perkicons)與人工資料(src/)為凍結資料,不由此重建。
set -e
cd "$(dirname "$0")"

echo "[1/6] 精簡下載所需 2 種定義(英+繁,約 5MB;免 API key)…"
bash tools/download.sh                    # → tools/cache/manifest{,_en,_zhcht}(.gitignore)

echo "[2/6] 解析 56 套裝官方英/繁名稱+說明…"
python3 tools/resolve.py                  # → tools/cache/derived/resolved.json

echo "[3/6] 產生資料合約、文字檔與圖例 sprite…"
python3 tools/build_texts.py              # → docs/data/site.json、docs/exports/*.txt、sprite.png

echo "[4/6] 產生大圖(繁中/雙語/英文)…"
python3 tools/make_image.py               # → docs/exports/*.png(讀 site.json)

echo "[5/6] 回填 exports 檔案大小…"
# 雞生蛋:site.json 要記大圖尺寸,但大圖又要先讀 site.json 才能產,故分兩趟。
python3 tools/build_texts.py --stamp-exports

echo "[6/6] 稽核資料一致性…"
python3 tools/audit.py                    # 不通過會中止(exit 1)

echo
echo "完成。docs/ 即可直接發佈到 GitHub Pages。"
echo "本機預覽: python3 tools/serve.py"
