// state 物件 + URL hash 序列化 + localStorage 持久化。
//
// 手風琴的開合刻意不在這裡:它的狀態就是 <details>.open,DOM 自己記著。多養一份影子
// 狀態只會製造「誰覆蓋誰」的問題(而且真的發生過:URL 的 c= 會蓋掉本機存的偏好)。
//
// 剩下的兩者職責不同:URL 是「給別人看這個」的明確意圖,localStorage 是「我自己的偏好」。
//   lang → 兩邊都存(可分享,但省略時用個人偏好)
//   tags / notable / q → 只進 URL。篩選是當下的探索,不是偏好 ——
//     隔天打開只看到 5 套裝會讓人以為壞了。

// 顯示語言是一個有序陣列:langs[0]=主、langs[1]=副(可缺)。先點的是主、後點的是副。
// 沒有影子狀態 —— 取消一個就 splice 掉,剩下的自然遞補(見 main.js 的意圖語意)。
export const state = {
  langs: ['zh'],          // ['zh'] 純繁 | ['zh','en'] 主繁副英 | ['en','zh'] 反過來
  tags: new Set(),
  notable: null,          // 單選
  q: '',
};

export const LANGS = ['zh', 'en', 'zhs', 'ja', 'ko'];   // 認得的語言碼(順序不影響行為)
const LS = { lang: 'd2ab.lang', panel: 'd2ab.filterPanel' };

// 依瀏覽器語言自適應:挑第一個「我們有」的。繁簡要先測 zh-tw/zh-hant,否則被 zh 吞。
function pickNav() {
  for (const raw of navigator.languages || [navigator.language || '']) {
    const t = raw.toLowerCase();
    if (t.startsWith('zh-tw') || t.startsWith('zh-hant') || t.startsWith('zh-hk')) return 'zh';
    if (t.startsWith('zh')) return 'zhs';
    if (t.startsWith('ja')) return 'ja';
    if (t.startsWith('ko')) return 'ko';
  }
  return 'en';
}
const NAV_LANG = pickNav();

let KEY_ORDER = [], NOTABLE_IDS = [];
export function initOrder(key, notable) {
  KEY_ORDER = key.map(k => k.id);
  NOTABLE_IDS = notable.map(n => n.id);
}

const ls = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch { /* 無痕模式 */ } },
};

// 把任意字串解析成合法的語言序列:認不得的丟掉、去重、最多兩個。空的話回退預設。
function parseLangs(raw, fallback) {
  const out = [];
  for (const x of (raw || '').split(',')) {
    if (LANGS.includes(x) && !out.includes(x)) out.push(x);
    if (out.length === 2) break;
  }
  return out.length ? out : fallback;
}

export function parseHash() {
  const p = new URLSearchParams(location.hash.slice(1));

  // 四層 fallback:URL → 本機偏好 → 瀏覽器語言 → 繁中(最後保險)。
  // 繁中只在前三層全空/全無效時落地 —— 就是「都沒選會怎樣」的答案。
  const url = p.get('lang');
  const pref = ls.get(LS.lang);
  state.langs = parseLangs(url, parseLangs(pref, [NAV_LANG]));

  // 每個參數都要驗:認不得的值一律當沒有。少驗 notable 的話,一個過期的 #n=xxx
  // 會讓 isFiltering 為真但篩不掉任何東西 —— 介面鎖在篩選模式、卻沒有任何 chip 亮著。
  state.tags = new Set((p.get('t') || '').split(',').filter(x => KEY_ORDER.includes(x)));
  const n = p.get('n');
  state.notable = NOTABLE_IDS.includes(n) ? n : null;
  state.q = p.get('q') || '';
}

function serialize() {
  const p = new URLSearchParams();
  // 一律照 key[] 原始順序輸出以正規化 —— 同一組條件永遠得到同一個 URL
  if (state.tags.size) p.set('t', KEY_ORDER.filter(k => state.tags.has(k)).join(','));
  if (state.notable) p.set('n', state.notable);
  if (state.q) p.set('q', state.q);
  // 語言:與純瀏覽器語言相同時省略(讓分享連結最短、也讓對方用自己的偏好)
  const l = state.langs.join(',');
  if (l !== NAV_LANG) p.set('lang', l);
  return p.toString().replace(/%2C/g, ',');   // 逗號不逃逸,可讀性優先
}

export function persist() { ls.set(LS.lang, state.langs.join(',')); }
export const panelPref = {
  get() { const v = ls.get(LS.panel); return v === null ? null : v === '1'; },
  set(open) { ls.set(LS.panel, open ? '1' : '0'); },
};

let last = '';
export function pushURL(replace) {
  const h = serialize();
  if (h === last) return;
  last = h;
  const url = location.pathname + location.search + (h ? '#' + h : '');
  // pushState/replaceState 都不觸發 hashchange,所以不需要 suppress flag;
  // 上一頁/下一頁與手動改網址會觸發 hashchange → 單一監聽全覆蓋。
  history[replace ? 'replaceState' : 'pushState'](null, '', url);
}
export function syncLast() { last = serialize(); }
