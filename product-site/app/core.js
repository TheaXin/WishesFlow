/* The browser and SQLite versions share the contract in tests/fixtures/accounting.json. */
(function (root) {
  'use strict';
  const empty = () => ({ version: 1, sources: [], entries: [], wishes: [] });
  const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
  function amount(value) {
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0 || n > 100000000 || !/^\d+(\.\d{1,2})?$/.test(String(value))) throw Error('金额需大于 0，最多两位小数，且不超过一亿元。');
    return Math.round(n * 100);
  }
  function title(value) {
    const t = String(value || '').trim();
    if (!t || [...t].length > 80) throw Error('名称需为 1 至 80 个字符。');
    return t;
  }
  function nickname(value) {
    const name = String(value || '').trim();
    if (!/^[\u4e00-\u9fffA-Za-z0-9_-]{1,30}$/.test(name)) throw Error('昵称支持 1–30 个中英文、数字、下划线或短横线。');
    return name;
  }
  function validDay(day) {
    if (typeof day !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(day)) return false;
    const d = new Date(day + 'T12:00:00Z');
    return Number.isFinite(d.getTime()) && d.toISOString().slice(0,10) === day;
  }
  function summary(s) {
    const attendance = s.entries.filter(e => e.kind === 'attendance').reduce((n,e) => n+e.cents,0);
    const habits = s.entries.filter(e => e.kind === 'habit').reduce((n,e) => n+e.cents,0);
    const reserved = s.wishes.filter(w => w.status !== 'active').reduce((n,w) => n+w.cents,0);
    return { attendance, habits, reserved, balance: attendance+habits-reserved };
  }
  function checkin(s, id, day) {
    if (!validDay(day) || day > today()) throw Error('请选择今天或之前的有效日期。');
    const source = s.sources.find(x => x.id === id);
    if (!source) throw Error('找不到打卡项目。');
    if (s.entries.some(x => x.sourceId === id && x.day === day)) throw Error('这个项目在所选日期已经打卡。');
    s.entries.push({ sourceId: id, day, title: source.title, kind: source.kind, cents: source.cents });
  }
  function advance(s, id) {
    const w = s.wishes.find(x => x.id === id);
    if (!w || w.status === 'completed') throw Error('这个心愿当前无法更新。');
    if (w.status === 'active' && summary(s).balance < w.cents) throw Error('可用心愿金不足。');
    w.status = w.status === 'active' ? 'unlocked' : 'completed';
    if (w.status === 'unlocked') w.unlockedAt = new Date().toISOString();
    else w.completedAt = new Date().toISOString();
  }
  function orderedWishes(s) {
    const rank = { active: 0, unlocked: 1, completed: 2 };
    return [...s.wishes].sort((a,b) => rank[a.status]-rank[b.status] || a.priority-b.priority);
  }
  function trend(s) {
    const days = new Map();
    for (const e of s.entries) days.set(e.day, (days.get(e.day) || 0)+e.cents);
    let cumulative = 0;
    return [...days].sort(([a],[b]) => a.localeCompare(b)).map(([day,cents]) => ({day,cents,cumulative:cumulative+=cents}));
  }
  function addSource(s, id, name, kind, value) {
    if (!['habit','attendance'].includes(kind)) throw Error('请选择有效项目类型。');
    s.sources.push({id, title:title(name), kind, cents:amount(value)});
  }
  function addWish(s, id, name, value, priority) {
    const p = Number(priority);
    if (!Number.isSafeInteger(p) || p < 1) throw Error('优先级必须是正整数。');
    s.wishes.push({id,title:title(name),cents:amount(value),priority:p,status:'active',createdAt:new Date().toISOString()});
  }
  function validate(s) {
    const fail = () => { throw Error('备份格式或记账数据不正确。'); };
    if (!s || s.version !== 1 || !['sources','entries','wishes'].every(k => Array.isArray(s[k]) && s[k].length <= 100000)) fail();
    const ids = new Set(), keys = new Set(), sources = new Map();
    const money = n => Number.isSafeInteger(n) && n > 0 && n <= 10000000000;
    // v1 allowed 100 characters: preserve existing records; new input is limited to 80.
    const storedTitle = t => typeof t === 'string' && t.trim().length > 0 && [...t].length <= 100;
    for (const x of s.sources) {
      if (!x || typeof x.id !== 'string' || !x.id || ids.has(x.id) || !['habit','attendance'].includes(x.kind) || !money(x.cents) || !storedTitle(x.title)) fail();
      ids.add(x.id); sources.set(x.id,x);
    }
    for (const x of s.entries) {
      if (!x || !validDay(x.day) || !money(x.cents)) fail();
      const source = sources.get(x.sourceId);
      if (!source || source.kind !== x.kind || !storedTitle(x.title)) fail();
      const key = JSON.stringify([x.sourceId,x.day]);
      if (keys.has(key)) fail(); keys.add(key);
    }
    for (const x of s.wishes) {
      if (!x || typeof x.id !== 'string' || !x.id || ids.has(x.id) || !money(x.cents) || !Number.isSafeInteger(x.priority) || x.priority < 1 || !['active','unlocked','completed'].includes(x.status) || !storedTitle(x.title)) fail();
      ids.add(x.id);
    }
    const totals = summary(s);
    if (!Object.values(totals).every(Number.isSafeInteger) || totals.balance < 0) fail();
    return s;
  }
  const api = { empty, today, amount, title, nickname, validDay, summary, checkin, advance, orderedWishes, trend, addSource, addWish, validate };
  if (typeof module !== 'undefined') module.exports = api;
  root.WishFlow = api;
})(globalThis);
