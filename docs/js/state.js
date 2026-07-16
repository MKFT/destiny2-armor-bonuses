// state 物件 + URL hash 序列化 + localStorage 持久化。
//
// 手風琴的開合刻意不在這裡:它的狀態就是 <details>.open,DOM 自己記著。多養一份影子
// 狀態只會製造「誰覆蓋誰」的問題(而且真的發生過:URL 的 c= 會蓋掉本機存的偏好)。
//
// 剩下的兩者職責不同:URL 是「給別人看這個」的明確意圖,localStorage 是「我自己的偏好」。
//   lang → 兩邊都存(可分享,但省略時用個人偏好)
//   tags / notable / q → 只進 URL。篩選是當下的探索,不是偏好 ——
//     隔天打開只看到 5 套裝會讓人以為壞了。

export const state = {
  lang: 'zh',            // 'zh' | 'en' | 'both'
  tags: new Set(),
  notable: null,         // 單選
  q: '',
};

const LS = { lang: 'd2ab.lang', panel: 'd2ab.filterPanel' };
const LANGS = ['zh', 'en', 'both'];
const NAV_LANG = (navigator.language || '').toLowerCase().startsWith('zh') ? 'zh' : 'en';

let KEY_ORDER = [], NOTABLE_IDS = [];
export function initOrder(key, notable) {
  KEY_ORDER = key.map(k => k.id);
  NOTABLE_IDS = notable.map(n => n.id);
}

const ls = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch { /* 無痕模式 */ } },
};

export function parseHash() {
  const p = new URLSearchParams(location.hash.slice(1));

  const l = p.get('lang') || ls.get(LS.lang) || NAV_LANG;
  state.lang = LANGS.includes(l) ? l : 'zh';

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
  if (state.lang !== NAV_LANG) p.set('lang', state.lang);
  return p.toString().replace(/%2C/g, ',');   // 逗號不逃逸,可讀性優先
}

export function persist() { ls.set(LS.lang, state.lang); }
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
