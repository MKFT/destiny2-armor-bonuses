// 篩選運算:純函式,零 DOM。吃 state 吐遮罩與計數,可單獨測。
// n=56、tags=44,暴力法上限約 2,464 次運算 —— 微秒級,不需 memo 也不需 debounce 計算。

let N = 0, SETS = [], GROUP_IDS = [];
const post = new Map();     // tag id  → Uint8Array(N)  倒排
const nPost = new Map();    // notable → Uint8Array(N)  明確名單
const groupOf = new Map();  // tag id  → group id
let hay = [];               // 每套裝的搜尋字串(八個文字欄位串起來)

export function build(site) {
  SETS = site.columns.flatMap(c => c.sets.map(s => ({ ...s, col: c.id })));
  N = SETS.length;
  GROUP_IDS = site.groups.map(g => g.id);
  post.clear(); nPost.clear(); groupOf.clear();

  for (const k of site.key) {
    groupOf.set(k.id, k.group);
    const m = new Uint8Array(N);
    SETS.forEach((s, i) => { if (s.tags.includes(k.id)) m[i] = 1; });
    post.set(k.id, m);
  }
  // notable 是編輯精選的明確名單,不是 tag 推導 —— 例如「治療」精選 6 套但實際 19 套帶 HEALING,
  // 而且有個分類叫「彈藥 AMMO」在 key 裡根本不存在。所以只能照 set_ids 建。
  const idx = new Map(SETS.map((s, i) => [s.id, i]));
  for (const n of site.notable) {
    const m = new Uint8Array(N);
    for (const sid of n.set_ids) m[idx.get(sid)] = 1;
    nPost.set(n.id, m);
  }
  // 搜尋索引跨語言:不管當前顯示模式,一律搜全部八個欄位
  hay = SETS.map(s => [s.name.zh, s.name.en, s.source.zh, s.source.en,
      ...s.perks.flatMap(p => [p.name.zh, p.name.en, p.desc.zh, p.desc.en])]
      .join('').toLowerCase().replace(/['’]/g, ''));
  return SETS;
}

const ones = () => new Uint8Array(N).fill(1);
const and = (a, b) => { const m = new Uint8Array(N); for (let i = 0; i < N; i++) m[i] = a[i] & b[i]; return m; };
const popcount = m => { let n = 0; for (let i = 0; i < N; i++) n += m[i]; return n; };
const popcountAnd = (a, b) => { let n = 0; for (let i = 0; i < N; i++) n += a[i] & b[i]; return n; };
const norm = s => s.toLowerCase().replace(/['’]/g, '');
// 斷詞:半形逗號、全形逗號、頓號、空白都當分隔,詞與詞之間是 AND。
// 中文詞與詞之間本來就不打空格,所以使用者打的空格必然是刻意的分隔;
// 而中文列舉習慣用「、」和「，」,少了它們中文使用者會覺得搜尋壞掉。
export const terms = q => norm(q).split(/[\s,，、]+/).filter(Boolean);

// 套用所有約束;exceptGid 指定時排除該組(facet drilldown 用)。
function baseMask(state, exceptGid) {
  let m = null;
  for (const gid of GROUP_IDS) {
    if (gid === exceptGid) continue;
    const tags = [...state.tags].filter(t => groupOf.get(t) === gid);
    if (!tags.length) continue;          // ← 該組無約束就跳過。當成空集合去 AND 會讓結果全滅。
    const or = new Uint8Array(N);        // 同組內 OR
    for (const t of tags) { const p = post.get(t); for (let i = 0; i < N; i++) or[i] |= p[i]; }
    m = m ? and(m, or) : or;             // 跨組 AND
  }
  if (state.notable && nPost.has(state.notable)) {
    const np = nPost.get(state.notable);
    m = m ? and(m, np) : np.slice();
  }
  const ts = terms(state.q);
  if (ts.length) {                       // 全部是空白或逗號時視同沒搜尋
    const f = m ?? ones();
    for (let i = 0; i < N; i++) if (f[i] && !ts.every(t => hay[i].includes(t))) f[i] = 0;
    m = f;
  }
  return m ?? ones();
}

export function isFiltering(state) {
  return state.tags.size > 0 || !!state.notable || terms(state.q).length > 0;
}

export function compute(state) {
  const full = baseMask(state, null);
  // facet 計數用 drilldown:排除該標籤自己所屬的組來算。
  // 未選任何條件時 = 全域數字;選了 SOLAR 後 WEAPONS 顯示的是「再加它會剩幾套」。
  // 排除自己這組,是為了讓組內連點時其他 chip 的數字不亂跳 —— 這份分布極度偏斜
  // (13 個標籤只命中 1 套、WEAPONS 命中 24 套),全域計數會讓那些「(1)」集體閃爍。
  const facets = new Map();
  for (const gid of GROUP_IDS) {
    const base = baseMask(state, gid);
    for (const [tid, g] of groupOf) if (g === gid) facets.set(tid, popcountAnd(base, post.get(tid)));
  }
  const colCounts = {};
  for (let i = 0; i < N; i++) if (full[i]) colCounts[SETS[i].col] = (colCounts[SETS[i].col] || 0) + 1;
  return { full, facets, colCounts, total: popcount(full), n: N };
}
