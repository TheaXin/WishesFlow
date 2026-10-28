/* Shared accounting contract: amounts are integer cents; reservations remain after completion. */
(function (root) {
  'use strict';
  const empty = () => ({ version: 1, sources: [], entries: [], wishes: [] });
  function amount(value) {
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0 || n > 100000000 || !/^\d+(\.\d{1,2})?$/.test(String(value))) throw Error('金额需大于 0，最多两位小数，且不超过一亿元。');
    return Math.round(n * 100);
  }
  function title(value) {
    const t = String(value || '').trim();
    if (!t || t.length > 100) throw Error('名称需为 1 至 100 个字符。');
    return t;
  }
  function summary(s) {
    const attendance = s.entries.filter(e => e.kind === 'attendance').reduce((n,e) => n+e.cents,0);
    const habits = s.entries.filter(e => e.kind === 'habit').reduce((n,e) => n+e.cents,0);
    const reserved = s.wishes.filter(w => w.status !== 'active').reduce((n,w) => n+w.cents,0);
    return { attendance, habits, reserved, balance: attendance+habits-reserved };
  }
  function checkin(s, id, day) {
    const source = s.sources.find(x => x.id === id);
    if (!source) throw Error('找不到打卡项目。');
    if (s.entries.some(x => x.sourceId === id && x.day === day)) throw Error('这个项目今天已经打卡。');
    s.entries.push({ sourceId: id, day, title: source.title, kind: source.kind, cents: source.cents });
  }
  function advance(s, id) {
    const w = s.wishes.find(x => x.id === id);
    if (!w || w.status === 'completed') throw Error('这个心愿当前无法更新。');
    if (w.status === 'active' && summary(s).balance < w.cents) throw Error('可用心愿金不足。');
    w.status = w.status === 'active' ? 'unlocked' : 'completed';
  }
  function validate(s) {
    const fail = () => { throw Error('备份格式或记账数据不正确。'); };
    if (!s || s.version !== 1 || !['sources','entries','wishes'].every(k => Array.isArray(s[k]) && s[k].length <= 100000)) fail();
    const ids = new Set(), keys = new Set();
    const money = n => Number.isSafeInteger(n) && n > 0 && n <= 10000000000;
    for (const x of s.sources) {
      if (!x || typeof x.id !== 'string' || ids.has(x.id) || !['habit','attendance'].includes(x.kind) || !money(x.cents) || typeof x.title !== 'string') fail();
      title(x.title); ids.add(x.id);
    }
    for (const x of s.entries) {
      if (!x || typeof x.day !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(x.day) || new Date(x.day).toISOString().slice(0,10) !== x.day || !money(x.cents)) fail();
      const source = s.sources.find(y => y.id === x.sourceId);
      if (!source || source.kind !== x.kind || typeof x.title !== 'string') fail();
      title(x.title);
      const key = x.sourceId + ':' + x.day;
      if (keys.has(key)) fail(); keys.add(key);
    }
    for (const x of s.wishes) {
      if (!x || typeof x.id !== 'string' || ids.has(x.id) || !money(x.cents) || !Number.isSafeInteger(x.priority) || x.priority < 1 || !['active','unlocked','completed'].includes(x.status) || typeof x.title !== 'string') fail();
      title(x.title); ids.add(x.id);
    }
    const totals = summary(s);
    if (!Object.values(totals).every(Number.isSafeInteger) || totals.balance < 0) fail();
    return s;
  }
  const api = { empty, amount, title, summary, checkin, advance, validate };
  if (typeof module !== 'undefined') module.exports = api;
  root.WishFlow = api;
})(globalThis);
