// boot + 事件接線
import { state, parseHash, initOrder, persist, pushURL, syncLast, panelPref } from './state.js';
import { build, compute } from './filter.js';
import { mount, apply, openCols } from './render.js';

const $ = s => document.querySelector(s);
let ready = false;

function refresh() { apply(compute(state)); }

function changed({ replace = false, save = true } = {}) {
  refresh();
  pushURL(replace);
  if (save) persist();
}

const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const pushQ = debounce(() => pushURL(true), 250);   // 打字每個字都塞一筆歷史會很煩

async function boot() {
  const site = await fetch('data/site.json').then(r => {
    if (!r.ok) throw new Error(`site.json ${r.status}`);
    return r.json();
  });
  initOrder(site.key, site.notable);
  build(site);
  mount(site);
  parseHash();
  syncLast();

  // 篩選面板:首次造訪依斷點決定(桌機展開、手機收起),之後照使用者的選擇。
  // HTML 的 open 屬性無法用 media query 控制,所以這一步只能在 JS 做。
  const pref = panelPref.get();
  let panelWant = pref === null ? matchMedia('(min-width: 768px)').matches : pref;
  $('#filters').open = panelWant;
  $('#filters').addEventListener('toggle', e => {
    if (e.target.open === panelWant) return;  // 同上:程式自己寫的不算使用者選擇
    panelWant = e.target.open;
    panelPref.set(panelWant);
  });

  syncLangBtns();

  ready = true;
  refresh();
}

// 語言按鈕的三態外觀:未選 / 副(2) / 主(1)。state.langs 是唯一真相,這裡只反映它。
function syncLangBtns() {
  const [main, sub] = state.langs;
  for (const b of document.querySelectorAll('.lang-btn')) {
    const id = b.dataset.lang;
    const role = id === main ? 'main' : id === sub ? 'sub' : '';
    role ? (b.dataset.role = role) : delete b.dataset.role;
    b.setAttribute('aria-pressed', String(!!role));
  }
}

// 意圖語意:點擊表達「我要這個怎樣」,不是開/關。
//   點主 → 我只要它(收成純主)   點副 → 我要它當主(互換)   點未選 → 也想看它(成為副,滿了取代副)
function pickLang(id) {
  const [main, sub] = state.langs;
  if (id === main) state.langs = [main];
  else if (id === sub) state.langs = [sub, main];
  else if (!main) state.langs = [id];
  else state.langs = [main, id];
}

// ── 事件 ───────────────────────────────────────────────────────────────
document.addEventListener('change', e => {
  if (!ready) return;
  if (e.target.matches('.chips input')) {
    const t = e.target;
    t.checked ? state.tags.add(t.value) : state.tags.delete(t.value);
    changed();
  }
});

// ⓘ 搜尋說明。滑鼠的 hover 全在 CSS,這裡只管「點開固定住」—— 觸控與鍵盤沒有 hover 可用。
const tip = (on = null) => {
  const b = $('#q-help');
  const want = on ?? b.getAttribute('aria-expanded') !== 'true';
  b.setAttribute('aria-expanded', String(want));
  $('#q-tip').classList.toggle('on', want);
};

document.addEventListener('click', e => {
  if (e.target.closest('#q-help')) return tip();
  if (!e.target.closest('#q-tip')) tip(false);

  const lb = e.target.closest('.lang-btn');
  if (lb) {
    pickLang(lb.dataset.lang);
    syncLangBtns();
    return changed({ replace: true });       // 切語言不塞歷史,跟打字一樣
  }

  const n = e.target.closest('.ntb');
  if (n) {                                   // 單選,可取消
    state.notable = state.notable === n.dataset.n ? null : n.dataset.n;
    return changed();
  }
  if (e.target.closest('#clear')) {
    state.tags.clear(); state.notable = null; state.q = '';
    return changed();
  }
  if (e.target.closest('#toggle-all')) {
    const open = $('#toggle-all').dataset.act === 'open';
    for (const c of openCols()) c.el.open = open;
    return refresh();                        // 只更新按鈕文字,開合已直接寫進 DOM
  }
});

// 手風琴的開合不進 state,只需在使用者點開/收起後把「全部展開/收起」的文字更新一下
document.addEventListener('toggle', () => { if (ready) refresh(); }, true);  // toggle 不冒泡 → 捕獲

$('#q').addEventListener('input', e => {
  state.q = e.target.value;
  refresh(); pushQ();
});
$('#q').addEventListener('keydown', e => {
  if (e.key === 'Escape' && state.q) { state.q = ''; e.target.value = ''; changed({ replace: true }); }
});
addEventListener('keydown', e => {
  if (e.key === 'Escape') tip(false);
  if (e.key !== '/' || e.metaKey || e.ctrlKey) return;
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
  e.preventDefault(); $('#q').focus();
});

const totop = $('#totop');
const pageTop = $('.hd h1');
pageTop.tabIndex = -1;                       // 只為了讓下面的 focus() 送得進來
addEventListener('scroll', () => { totop.hidden = scrollY < innerHeight; }, { passive: true });
totop.addEventListener('click', () => {
  const smooth = !matchMedia('(prefers-reduced-motion: reduce)').matches;
  scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
  // 不用 #q:聚焦 <input> 在手機一定會叫出虛擬鍵盤,而按這顆鈕多半只是想去改篩選
  pageTop.focus({ preventScroll: true });
});

// 上一頁/下一頁與手動改網址;pushState/replaceState 不觸發此事件
addEventListener('hashchange', () => {
  if (!ready) return;
  parseHash(); syncLast();
  syncLangBtns();
  refresh();
});

boot().catch(err => {
  console.error(err);
  document.querySelector('#results').innerHTML =
    `<p class="noresult">資料載入失敗:${err.message}<br>
     若你是用 file:// 開啟,請改跑 <code>python3 tools/serve.py</code>（ESM 會被 CORS 擋）。<br>
     Failed to load data. If opening via file://, serve the folder over HTTP instead.</p>`;
});
