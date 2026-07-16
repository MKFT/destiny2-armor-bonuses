// DOM 建構 + 把 state 反映到 DOM。
// 策略:建一次 + 只改屬性。不重繪的理由不是效能(2,300 個節點重繪只要 5-10ms),
// 而是狀態 —— 重繪會炸掉 focus、捲軸位置、<details> 開合、已 lazy load 完的圖片(會閃)。

import { state } from './state.js';
import { isFiltering, terms } from './filter.js';

const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
// 八個文字欄位全部渲染進 DOM 一次,顯示與否由 <html data-lang> 上的 CSS 決定
const bi = (zh, en, cls = 'en') => `<span class="zh">${esc(zh)}</span><span class="${cls}">${esc(en)}</span>`;
const pos = i => `${(i % 8) / 7 * 100}% ${Math.floor(i / 8) / 5 * 100}%`;   // sprite 8×6
const kb = n => n >= 1048576 ? (n / 1048576).toFixed(2) + ' MB' : Math.round(n / 1024) + ' KB';

let site, KEY, cards = [], cols = [], chips = new Map(), ntbs = new Map();

export function mount(data) {
  site = data;
  KEY = new Map(site.key.map(k => [k.id, k]));

  // 44 條 CSS 規則取代 229 個 inline style;data-tag 同時服務位置與命中高亮
  const st = document.createElement('style');
  st.textContent = site.key.map((k, i) => `.icn[data-tag="${k.id}"]{--pos:${pos(i)}}`).join('');
  document.head.appendChild(st);

  renderNotable(); renderGroups(); renderColumns(); renderExports();
  for (const v of document.querySelectorAll('.ver')) v.textContent = site.manifest_version;
}

function renderNotable() {
  $('#notable .ntb-list').innerHTML = site.notable.map(n =>
    `<button type="button" class="ntb" aria-pressed="false" data-n="${n.id}">` +
    // 用 aria-pressed 按鈕而非 radio:需要「再點一次取消」,radio 沒有這個語意
    `${bi(n.category.zh, n.category.en)}<span class="n">${n.set_ids.length}</span></button>`).join('');
  for (const b of document.querySelectorAll('.ntb')) ntbs.set(b.dataset.n, b);
}

function renderGroups() {
  $('#groups').innerHTML = site.groups.map(g => {
    const items = site.key.filter(k => k.group === g.id);
    return `<section role="group" aria-labelledby="g-${g.id}">
      <h3 id="g-${g.id}">${bi(g.label.zh, g.label.en)}</h3>
      <div class="chips">${items.map(k =>
        // 真的 checkbox + visually-hidden(clip-path 法,不是 display:none —— 那會不可聚焦)。
        // 命中數寫在 label 文字裡 → 唸出來是「灼燒 5,核取方塊,未勾選」,數字免費被播報。
        `<input type="checkbox" id="t-${k.id}" value="${k.id}" class="vh">
         <label for="t-${k.id}" class="chip"><i class="icn" data-tag="${k.id}"></i>` +
        `${bi(k.label.zh, k.label.en)}<span class="n" data-c="${k.id}"></span></label>`).join('')}</div>
    </section>`;
  }).join('');
  for (const i of document.querySelectorAll('.chips input'))
    chips.set(i.value, { input: i, n: document.querySelector(`.n[data-c="${i.value}"]`) });
}

function synHTML(s) {
  const y = s.synergy;
  // 2件與4件標籤完全相同時合併顯示為「2·4」—— 沿用大圖的做法
  const groups = y['2'].join() === y['4'].join() ? [['2·4', y['2']]] : [['2', y['2']], ['4', y['4']]];
  return groups.map(([n, ids]) =>
    `<span class="sg"><b class="pc" data-n="${n}"></b>` +
    ids.map(id => {
      const k = KEY.get(id);
      return `<i class="icn" data-tag="${id}" role="img" aria-label="${esc(k.label.zh + ' ' + k.label.en)}" title="${esc(k.label.zh + ' ' + k.label.en)}"></i>`;
    }).join('') + `</span>`).join('');
}

function cardHTML(s) {
  return `<article class="card" data-id="${s.id}">
    <div class="card-head">
      <h3 class="set-name">${bi(s.name.zh, s.name.en, 'en name-en')}</h3>
      <div class="syn">${synHTML(s)}</div>
    </div>
    <p class="src">${bi(s.source.zh, s.source.en)}</p>
    ${s.perks.map(p => `<div class="perk">
      <img class="badge" src="${p.icon}" loading="lazy" decoding="async" width="34" height="34" alt="">
      <p class="perk-name"><b class="pc" data-n="${p.count}"></b>${bi(p.name.zh, p.name.en, 'en name-en')}</p>
      <p class="desc zh">${esc(p.desc.zh)}</p>
      <p class="desc en desc-en">${esc(p.desc.en)}</p>
    </div>`).join('')}
  </article>`;
}

function renderColumns() {
  // 原生 <details>:自帶 button 語意、Enter/Space、aria-expanded 由 UA 維護,狀態就是 el.open。
  // 預設全部收起(不加 open):56 張卡一次攤開就是把大圖的問題原封搬過來。
  $('#results').innerHTML = site.columns.map(c =>
    `<details class="col" id="col-${c.id}" style="--cc:var(--c-${c.id})">
      <summary><span class="t">${bi(c.title.zh, c.title.en, 'en name-en')}</span><span class="cnt"></span></summary>
      <div class="cards">${c.sets.map(cardHTML).join('')}</div>
    </details>`).join('');
  cols = site.columns.map(c => {
    const el = document.getElementById('col-' + c.id);
    return { id: c.id, el, cnt: el.querySelector('.cnt') };
  });
  cards = site.columns.flatMap(c => c.sets).map(s => document.querySelector(`.card[data-id="${s.id}"]`));
}

function renderExports() {
  $('#ex-list').innerHTML = site.exports.map(e => {
    const png = e.path.endsWith('.png');
    // 別想在 <a> 上加 charset 來救 .txt 的編碼:type 屬性只是提示、瀏覽器不採用,
    // 編碼完全由伺服器的 Content-Type 決定。已實測 Pages 送 charset=utf-8,此處無需處理。
    // 標籤包成單一容器:否則 zh/en 兩個 span 在 flex 裡會各自獨立換行,高度變參差
    return `<li><a href="${e.path}">
      <span class="ex-kind">${png ? 'PNG' : 'TXT'}</span>
      <span class="ex-label">${bi(e.label.zh, e.label.en)}</span>
      <span class="ex-size">${e.bytes == null ? '' : kb(e.bytes)}${
        e.dim ? `<span class="ex-dim"> · ${e.dim}</span>` : ''}</span>
    </a></li>`;
  }).join('');
}

// ── 把 state 反映到 DOM:約 400 次屬性寫入(56 卡 + 5 欄 + 44 chip + 15 精選 + 185 圖示),
//    一個 frame 都不到 ────────────────────────────────────────────────────
export function apply(c) {
  const filtering = isFiltering(state);
  document.documentElement.dataset.lang = state.lang;

  for (let i = 0; i < cards.length; i++) cards[i].hidden = !c.full[i];
  // 只動 hidden 與計數,絕不碰 .open —— 開合完全由使用者決定。程式一旦回頭覆蓋 .open,
  // 使用者在篩選中收起的欄位就會被默默彈開,而且得再養一份影子狀態去記「他本來想怎樣」。
  for (const col of cols) {
    const n = c.colCounts[col.id] || 0;
    col.el.hidden = filtering && n === 0;      // 零命中整欄隱藏,不留空殼讓人點
    col.cnt.textContent = filtering ? `${n}` : '';
  }
  for (const [id, ch] of chips) {
    const n = c.facets.get(id) ?? 0;
    ch.n.textContent = n;
    ch.input.checked = state.tags.has(id);
    ch.input.disabled = n === 0 && !state.tags.has(id);   // 已勾選的永不 disable,否則清不掉
  }
  for (const [id, b] of ntbs) b.setAttribute('aria-pressed', String(state.notable === id));

  for (const i of document.querySelectorAll('.syn .icn'))
    i.classList.toggle('hit', state.tags.has(i.dataset.tag));

  const q = $('#q');
  q.value = state.q;
  // 三種模式都要列出來:少一種會得到 undefined 而不是無聲落回中文
  q.placeholder = { zh: q.dataset.phZh, en: q.dataset.phEn, both: q.dataset.phBoth }[state.lang];
  $('#noresult').hidden = c.total > 0;
  // 只在多詞又搜不到時才說 —— 那是使用者唯一會懷疑「是不是 OR」的時刻。
  $('#and-hint').hidden = terms(state.q).length < 2;
  $('#clear').hidden = !filtering;
  // 這個數字掛在篩選面板的標題上,所以只能數「面板裡」的條件。把搜尋也算進去的話,
  // 一打字面板就亮個 1,看起來像是有 chip 被點到了 —— 但搜尋框根本不在面板裡。
  const inPanel = state.tags.size + (state.notable ? 1 : 0);
  const fc = $('#filter-count');
  fc.hidden = !inPanel;
  fc.textContent = inPanel;

  // DOM 就是狀態,直接問它(只看沒被篩掉的欄位)
  const allClosed = cols.filter(x => !x.el.hidden).every(x => !x.el.open);
  const tg = $('#toggle-all');
  // 下面幾處的中英之間用「真的空白字元」而非 CSS margin:按鈕與 role=status 的無障礙
  // 名稱就是內文,margin 只修得好視覺 —— 螢幕閱讀器仍會唸成「全部收起Collapse all」。
  tg.innerHTML = allClosed
    ? '<span class="zh">全部展開</span> <span class="en">Expand all</span>'
    : '<span class="zh">全部收起</span> <span class="en">Collapse all</span>';
  tg.dataset.act = allClosed ? 'open' : 'close';

  $('#status').innerHTML = filtering
    ? `<span class="zh">符合 ${c.total} / ${c.n} 套</span> <span class="en">${c.total} / ${c.n} sets</span>`
    : `<span class="zh">共 ${c.n} 套裝</span> <span class="en">${c.n} sets</span>`;
}

export const openCols = () => cols.filter(c => !c.el.hidden);
