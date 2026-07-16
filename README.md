# Destiny 2 — 防具套裝效果 (Armor Set Bonuses)

**https://mkft.github.io/destiny2-armor-bonuses/**

全 56 組防具套裝效果的互動查詢網站。譯文全採 **Bungie 官方 manifest 繁體中文(zh-cht)**，不是自行翻譯 —— 站上的用詞跟你在遊戲裡看到的一致。協同標籤與活動分類 manifest 沒有，是人工整理的，並以官方技能說明稽核（`tools/audit.py`）。

- **網站**（主要）：一欄式套裝列表、可展開收起的活動分組、44 個協同標籤的分面篩選、跨語言搜尋、中文／英文／雙語切換。手機首屏約 50KB。
- **大圖與文字檔**（附帶）：同一份資料的離線版，五欄並排的完整資訊圖 —— 想一次看完或丟連結給別人的人可以用。

---

## 結構

```
├── docs/                       ← GitHub Pages 發佈根目錄(網站的全部)
│   ├── index.html  style.css  js/{main,state,filter,render}.js
│   ├── .nojekyll               關掉 Jekyll(見下方說明)
│   ├── favicon.ico             凍結素材,取自「防具充能」圖示(16/32/48)
│   ├── data/site.json          ★ 唯一資料合約:網站與大圖都讀它
│   ├── assets/
│   │   ├── icons/icon_01..44.png   圖例 44 圖示(凍結素材)
│   │   ├── icons/sprite.png        圖例打包(build 產出,網站用)
│   │   ├── perkicons/*.png         技能徽章 112(凍結素材)
│   │   └── icon_reference_labeled.png  圖示速查表(含來源,留作文件)
│   └── exports/                成品:3 張大圖 + 3 份文字檔
├── src/                        ← 人工維護的輸入(會被 build 吃進 site.json,不上站)
│   ├── synergy_icons.json          每套裝 2/4件的協同標籤(人工整理,manifest 沒有)
│   └── perk_icons.json             每套裝 2/4件的技能徽章檔名
├── tools/                      ← 產生器
│   ├── download.sh                 manifest → cache/
│   ├── resolve.py                  manifest → resolved.json
│   ├── build_texts.py              → site.json + exports/*.txt + sprite
│   ├── make_image.py               site.json → exports/*.png
│   ├── audit.py                    資料一致性稽核
│   ├── serve.py                    本機預覽(charset 對齊 Pages,見下方)
│   └── cache/                      manifest 暫存(.gitignore)
└── prepare_data.sh             ← 完整重建(遊戲改版時跑)
```

**`docs/` 底下全是要上線的東西**，Pages 直接發佈，零複製、零同步。圖示放這裡而不是 `src/`，因為它們同時是原始素材和網站內容：放一份、commit 一次，`make_image.py` 與網頁都從這讀。

依賴：Python3 + **Pillow** + **Noto Sans CJK TC** 字型（`curl` 僅更新資料時用）。網站本身零依賴。

---

## 核心設計：`site.json` 是唯一資料合約

三份手工資料（`resolved.json` + `src/` 兩份）之間的黏合 —— 正規化套裝名去查協同、把標籤反查成圖示編號、查徽章檔名、切開中英標題 —— 全部在 **build 期**做完，產出一份黏好的 `site.json`。消費端一律不做反查，否則網頁會被迫把同一套膠水再實作一次：

```
manifest ─→ resolve ─→ resolved.json ─┐
                                       ├─→ build_texts ─→ site.json ─┬─→ make_image ─→ 大圖
              src/(協同標籤、徽章對應)─┘         └→ exports/*.txt     └─→ 網頁
```

每個 perk 自帶徽章路徑、每套裝自帶已解析成 id 的協同標籤、每個圖例自帶檔名與分組。`make_image.py` 也因此變簡單 —— 這層膠水原本就是它在執行期做的。

```jsonc
{
  "manifest_version": "…",
  "groups": [{ "id": "element", "zh": "元素", "en": "Element" }],
  "key":    [{ "id": "solar", "en": "SOLAR", "zh": "灼燒", "group": "element",
               "icon": "assets/icons/icon_01.png" }],
  "columns": [{ "id": "world", "title_zh": "…", "title_en": "…", "sets": [{
      "id": "wildwood", "name_en": "Wildwood", "name_zh": "原始叢林",
      "source": "…", "source_zh": "…",
      "tags": ["survivability", "weapons"],        // 2件+4件的聯集,篩選用
      "synergy": { "2": ["survivability"], "4": ["weapons"] },   // 顯示用
      "perks": [{ "count": 2, "name_en": "Watchtower", "name_zh": "守望台",
                  "desc_en": "…", "desc_zh": "…",
                  "icon": "assets/perkicons/….png" }] }] }],
  "notable": [{ "id": "solar", "category_zh": "灼燒", "category_en": "SOLAR",
                "set_ids": ["seventh-seraph", "…"] }],
  "exports": [{ "path": "exports/….png", "label_zh": "繁體中文", "label_en": "Traditional Chinese",
                "bytes": 4972328, "dim": "4592×5166" }]   // bytes 對 PNG 可能是 null,見流程第 5 步
}
```

**`key[]` 的順序即 `icon_01..44` 的對應順序，也是 sprite 的打包順序 —— 不可重排。**

`notable` 是**編輯精選的明確名單**，不是 `tags` 的推導結果：「治療」精選 6 套但實際 19 套帶 `HEALING`，而且有個分類叫「彈藥 AMMO」在 `key` 裡根本不存在。所以它只能照 `set_ids` 走。

---

## 流程

### 更新資料 `bash prepare_data.sh`

只有遊戲改版、官方譯文有變時才需要。六步全自動：

| 步驟 | 產出 |
|---|---|
| 1. `tools/download.sh` | 打 [Bungie manifest 索引](https://www.bungie.net/Platform/Destiny2/Manifest/)（**免 API key**），只抓所需的 2 種定義（英+繁，實測約 5MB）→ `tools/cache/` |
| 2. `tools/resolve.py` | 串接 `DestinyEquipableItemSetDefinition`（56 套裝）與 `DestinySandboxPerkDefinition` → `resolved.json` |
| 3. `tools/build_texts.py` | `resolved.json` + `src/` + 腳本內人工資料 → `site.json`、`exports/*.txt`、`sprite.png` |
| 4. `tools/make_image.py` | `site.json` → `exports/*.png` |
| 5. `build_texts.py --stamp-exports` | 回填 `site.json` 的大圖檔案大小 |
| 6. `tools/audit.py` | 稽核，不通過會中止 |

> **為什麼第 5 步要分開跑**：`site.json` 要記大圖的檔案大小（網站靠它顯示「4.74 MB」），但大圖又必須先讀 `site.json` 才能產 —— 雞生蛋，所以分兩趟。

`build_texts.py` 裡的人工資料（manifest 沒有這些）：

- `COLUMNS` — 五組活動分類 + 每套裝的「高數值來源」
- `KEY` — 圖例 44 詞的中英與分組
- `NOTABLE` — 顯著協同的精選名單
- `SRC_ZH` — 高數值來源的官方中文對照

### 只產大圖

```bash
python3 tools/make_image.py                    # 一次產三種(繁中/雙語/英文)
python3 tools/make_image.py all out.png        # 指定單一輸出,語言依「檔名」判斷:
                                               #   含 bilingual → 雙語;含 _EN → 英文;其餘 → 繁中
```

### 本機預覽網站

```bash
python3 tools/serve.py          # → http://localhost:8000
```

必須起 HTTP server —— 網站用 native ESM，`file://` 會被 CORS 擋。

> **不要用 `python3 -m http.server`**：它對 `.txt` 只送 `text/plain` 不帶 charset，瀏覽器只好猜編碼，`exports/` 的中文會變亂碼 —— 但實測真實的 GitHub Pages 送的是 `text/plain; charset=utf-8`，線上其實沒問題。`tools/serve.py` 就是把本機行為對齊 Pages，免得預覽呈現一個線上不存在的問題。
>
> （`index.html` 不受影響，它有 `<meta charset>`；`site.json` 也不受影響，JSON 依規格一律以 UTF-8 解碼。只有 `.txt` 沒有任何自帶的編碼宣告，完全仰賴 header。）

---

## 資料稽核 `tools/audit.py`

`src/synergy_icons.json` 的協同標籤是人工視覺辨識來的，manifest 沒有這份資料。2026-07 的一輪稽核**用官方技能說明當裁判**，找出並修正了 10 筆錯誤（4 筆標錯、1 筆誤判、4 筆漏標、1 筆多標）—— 所以這份標籤現在的權威是官方說明，不是它最初的來源。這支腳本把當時的方法固定下來：

1. 協同標籤都能反查到圖例；`tags` 等於 2件+4件的聯集
2. 沒有任何一件是空標籤
3. **標記原則**：4件的標籤相對 2件應「完全相同」（合併顯示 2·4）或「完全不重疊」（不重複標）—— 目前 10 + 45，唯一例外 Resonant Fury 已列白名單並註明理由
4. `NOTABLE` 宣稱的套裝確實帶有對應標籤
5. 素材檔案齊全、44 個圖例都有被使用
6. **官方說明關鍵字交叉稽核** —— 內含 Destiny 機制詞彙字典（`frost armor`→冰凝、`scorch`/`ignite`→灼燒、`jolt`/`blind`→電弧、`volatile`/`devour`→虛空、`sever`/`tangle`→縈絲…）。沒有這本字典，元素標籤會被大量誤報，因為官方說明不會寫「Stasis」而是寫「Frost Armor」。

1-5 不通過會 `exit 1`；6 是線索產生器，只列出可疑項供人工判讀。**遊戲改版、官方改寫技能說明時，同類錯誤會自己浮出來。**

---

## 網站實作要點

- **無框架**：vanilla JS + native ESM，四個模組，零建置。`filter.js` 是純函式（吃 state 吐 `Uint8Array`，零 DOM，可單獨測）。
- **語言切換全靠 CSS**：八個文字欄位一次全部渲染進 DOM，切語言只改 `<html data-lang>` 一個屬性 —— 0 次重繪、不掉捲軸與焦點。被 `display:none` 的文字剛好不會被 Ctrl+F 找到、不會進無障礙樹。
  網站的中文模式是**純中文**；大圖的中文版則保留括號英文對照。
- **圖示分兩種處理**：156 個圖示全是單色遮罩，所以圖例用 sprite + CSS `mask` + `currentColor`（顏色歸 CSS 管，選取態／變灰／命中高亮都變成一行 CSS）；112 個技能徽章每張只用一次、沒有重用紅利，用 `<img loading="lazy">`。
- **分面篩選**：同組內 OR、跨組 AND。命中數用 drilldown（排除該標籤自己那組來算），否則這份極度偏斜的分布（13 個標籤只命中 1 套、`WEAPONS` 命中 24 套）會讓數字在每次點擊後亂跳。
- **搜尋**：多詞 AND，半形／全形逗號、頓號、空白都當分隔（`灼燒 治療`＝`灼燒、治療`＝`灼燒,治療`）。中文詞間本來就不打空格，所以空格必然是刻意的分隔。索引跨語言且不隨顯示模式變動 —— 純中文模式下搜 `Wildwood` 一樣找得到，`扭曲 weapon` 也能中英混打。
  這兩件事在介面上完全看不出來，所以收在搜尋框旁的 ⓘ 裡：滑鼠 hover 就看得到，觸控與鍵盤點得開（手機沒有 hover，只靠 CSS 會變成手機看不到）。四種分隔符只講「空白或逗號」—— 頓號與全形逗號是容錯，講出來反而像有語法要背。
- **手風琴預設全部收起**，開合完全交給使用者。程式**不碰 `.open`** —— 連篩選時也不會自動展開，只隱藏零命中的欄位並在標題顯示數量。因此手風琴的狀態就是 `<details>.open`，不記憶、不進 URL、沒有影子狀態。
  這是刻意的取捨：先前程式會回頭覆蓋 `.open`，結果是你在篩選中收起的欄位被默默彈開，而且得再養一份 state 去記「他本來想怎樣」—— 那份 state 又跟 URL、localStorage 打架（開別人分享的連結會蓋掉你存的偏好）。**讓 DOM 當唯一真相，整類問題一次消失。**
- **語言**存 localStorage（下次打開不重來），也可進 URL 分享；**篩選只進 URL 不持久化** —— 隔天打開只看到 5 套裝會讓人以為壞了。URL 有參數就用 URL，沒有才退回個人偏好。
- **無障礙**：手風琴用原生 `<details>`、chip 用真的 `<input type=checkbox>`、NOTABLE 用 `aria-pressed`（需要「再點一次取消」，radio 沒有這個語意）。

首屏實測（Pages 對文字類一律 gzip）：**手機約 50KB、桌機約 111KB** —— 對照單張繁中大圖 4.74 MB。

差別在圖例 sprite（62KB，PNG 不會再被 gzip）：篩選面板在手機預設收起，收起的內容不需要 mask，瀏覽器就不去載它。徽章兩邊都是 **0 張** —— 手風琴預設全收，`loading="lazy"` 的圖沒有一張在視窗裡。

### 改動時容易踩壞的四件事

這幾條在 CSS 裡都有註解，但值得先知道：

1. **語言切換器後面不可以放任何寬度會隨語言變的東西。** 結果數之所以在 `.acts`（結果列表正上方）而不在工具列，就是因為它的文字寬度隨語言變（`56 sets` / `共 56 套裝`），會擠壓彈性的搜尋框、把語言按鈕推來推去 —— 使用者剛點的那顆會從游標底下跑掉。同理，`.sub` 固定二行高、手機的「DESTINY 2」拉成獨立一行的 kicker，都是為了讓標題區高度不隨語言改變。
2. **工具列已經沒有空間了。** 320px 觸控時，ⓘ（44px）與語言鈕（129px）只留 95px 給搜尋框，`#q` 的 `flex-basis: 5rem` 就是照這個數字定的 —— 大於它就換行，sticky 工具列變兩層。basis 只決定換行門檻（`grow:1` 會把剩餘空間吃回來），所以調它不影響任何寬度下的實際尺寸。再往 `.bar` 加東西前先量一次。
3. **「詞」用 span 交錯，「句子」要整塊複製。** `<span class="zh">…</span><span class="en">…</span>` 對套裝名、圖例這種**詞**有效；對整句（頁尾、副標、ⓘ 說明）會黏成一團或各自亂折，要改成每種語言各一個 block。
4. **按鈕與 `role=status` 的中英之間要用真的空白字元，不能只靠 CSS margin** —— 它們的無障礙名稱就是內文，margin 只修得好視覺，螢幕閱讀器仍會唸成「全部收起Collapse all」。

另外 `html{scrollbar-gutter:stable}` 不能拿掉：篩選到只剩幾套時頁面變短、捲軸消失，整頁會橫向跳約 15px。`[hidden]{display:none!important}` 也是必要的 —— `hidden` 靠瀏覽器預設的 `display:none` 實作，任何作者寫的 `display` 都會蓋掉它。

---

## 部署到 GitHub Pages

Settings → Pages → Source: **Deploy from a branch** → 選分支與 **`/docs`** 資料夾。

`docs/.nojekyll` 是必要的：Pages 預設會把檔案丟給 Jekyll 處理，而 Jekyll 會忽略底線開頭的檔案，並把 `{{ }}`／`{% %}` 當成樣板語法解析（JS 裡很容易寫到）。這個空檔案叫它原封不動直接服務。

---

## 凍結素材是怎麼來的

不在日常流程，當初做好就凍結、產生器已移除：

| 素材 | 當初來源 |
|---|---|
| `docs/assets/icons/`（圖例 44） | 多來源（見下方「資料來源」）；哪個圖示出自哪裡，`icon_reference_labeled.png` 一張表列完 |
| `docs/assets/perkicons/`（技能 112） | 從 manifest 每個 SandboxPerk 的官方 icon 下載處理 |
| `src/synergy_icons.json` | 人工視覺辨識每套裝那排協同圖示（**已用官方說明稽核修正過 10 筆**，現在以官方說明為準） |
| `src/perk_icons.json` | 從 manifest 對出每套裝 2/4件技能 → 官方 icon 檔名 |
| `docs/favicon.ico` | 取 `icon_25.png`（防具充能，斯巴達頭盔）墊上站台底色 `#16181D`，存成 16/32/48 多尺寸 ICO。**底色不能省** —— 圖示是白色遮罩，直接用的話在淺色分頁列上會整個看不見。 |
| `build_texts.py` 的 COLUMNS/KEY/NOTABLE/SRC_ZH | 官方用語人工整理 |

## 資料來源

- **文字**：Bungie manifest —— 索引 `https://www.bungie.net/Platform/Destiny2/Manifest/`（**免 API key**）。套裝名、來源、技能名與說明的中英文全部直接來自官方，未經改寫。
- **圖示**：Bungie 官方符號字型/PNG 為主，另用到 [DIM](https://github.com/DestinyItemManager/DIM) 字型，其餘手繪或自製。
- **協同標籤與活動分類**：manifest 沒有這份資料，為人工整理並以官方技能說明稽核，**非官方資料**。

Destiny 2 為 Bungie, Inc. 之商標。本專案與 Bungie 無關。
