'use strict';
const Core = window.WishFlow;
const KEY = 'wishflow.browser.v1';
let state = Core.empty();
let blocked = false;
const $ = id => document.getElementById(id);
const money = n => new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(n / 100);
const day = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
const notice = text => { $('notice').textContent = text; };
try {
  const raw = localStorage.getItem(KEY);
  if (raw) state = Core.validate(JSON.parse(raw));
} catch (_) { blocked = true; notice('无法读取浏览器记录。请先导出原始备份，检查网站存储权限，或导入有效备份恢复；现有数据不会被覆盖。'); }
function transact(change) {
  try {
    if (blocked) throw Error('存储不可用或记录损坏，请先导出备份后恢复。');
    const raw = localStorage.getItem(KEY);
    const next = raw ? Core.validate(JSON.parse(raw)) : Core.empty();
    change(next);
    Core.validate(next);
    localStorage.setItem(KEY, JSON.stringify(next));
    state = next;
    render();
    notice('已保存到当前浏览器。');
    return true;
  } catch (e) { notice(e.name === 'QuotaExceededError' || e.name === 'SecurityError' ? '浏览器无法保存记录。请检查存储权限或空间，并先导出备份。此次操作未保存。' : e.message); return false; }
}
function node(tag, text, cls) { const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n; }
function render() {
  const totals = Core.summary(state);
  for (const name of ['balance','attendance','habits','reserved']) $(name).textContent = money(totals[name]);
  $('sources').replaceChildren(); $('wish-list').replaceChildren(); $('history').replaceChildren();
  if (!state.sources.length) $('sources').append(node('p', '先添加一个项目，完成后就能累积心愿金。'));
  for (const s of state.sources) {
    const row = node('article', '', 'row'), info = node('div');
    info.append(node('b', s.title), node('small', `${s.kind === 'habit' ? '习惯' : '考勤'} · 每次 ${money(s.cents)}`));
    const done = state.entries.some(e => e.sourceId === s.id && e.day === day());
    const button = node('button', done ? '今日已打卡' : '今日打卡'); button.disabled = done || blocked;
    button.addEventListener('click', () => transact(next => Core.checkin(next,s.id,day())));
    row.append(info,button); $('sources').append(row);
  }
  if (!state.wishes.length) $('wish-list').append(node('p', '添加一个想实现的心愿，设定金额与优先级。'));
  for (const w of [...state.wishes].sort((a,b) => a.priority-b.priority)) {
    const row = node('article','','row'), info = node('div','','wish-info');
    info.append(node('b',w.title),node('small',`优先级 ${w.priority} · 目标 ${money(w.cents)} · ${{active:'积累中',unlocked:'已解锁',completed:'已实现'}[w.status]}`));
    const progress = node('progress'); progress.max = w.cents; progress.value = w.status === 'active' ? Math.max(0,Math.min(totals.balance,w.cents)) : w.cents; progress.setAttribute('aria-label',w.title+'预算进度'); info.append(progress);
    const button = node('button',w.status === 'active' ? '解锁心愿' : w.status === 'unlocked' ? '标记已实现' : '已实现');
    button.disabled = blocked || w.status === 'completed' || (w.status === 'active' && totals.balance < w.cents);
    button.addEventListener('click',() => transact(next => Core.advance(next,w.id)));
    row.append(info,button); $('wish-list').append(row);
  }
  if (!state.entries.length) $('history').append(node('p','还没有打卡记录。每一次行动都会记录在这里。'));
  for (const e of [...state.entries].reverse().slice(0,20)) { const row = node('div','','row'); row.append(node('span',`${e.day} · ${e.title}`),node('b','+'+money(e.cents))); $('history').append(row); }
  document.querySelectorAll('form button').forEach(b => { b.disabled = blocked; });
}
$('source-form').addEventListener('submit',event => {
  event.preventDefault(); const form = event.currentTarget, data = new FormData(form);
  if (transact(next => next.sources.push({ id: crypto.randomUUID(), title: Core.title(data.get('title')), kind: data.get('kind'), cents: Core.amount(data.get('amount')) }))) form.reset();
});
$('wish-form').addEventListener('submit',event => {
  event.preventDefault(); const form = event.currentTarget, data = new FormData(form);
  if (transact(next => { const priority = Number(data.get('priority')); if (!Number.isSafeInteger(priority) || priority < 1) throw Error('优先级必须为正整数。'); next.wishes.push({ id: crypto.randomUUID(), title: Core.title(data.get('title')), cents: Core.amount(data.get('amount')), priority, status: 'active' }); })) form.reset();
});
$('export').addEventListener('click',() => {
  try {
    const raw = localStorage.getItem(KEY) || JSON.stringify(state);
    const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }));
    const a = node('a'); a.href=url; a.download=`wishflow-${day()}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000); notice('已导出备份，请妥善保存。');
  } catch (_) { notice('无法访问浏览器存储，请检查网站权限。'); }
});
$('import').addEventListener('change',async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    if (file.size > 10*1024*1024) throw Error('备份不能大于 10 MB。');
    const next = Core.validate(JSON.parse(await file.text()));
    if (!confirm('导入会替换当前浏览器版的全部记录。请确认已导出需要保留的数据。继续导入？')) return;
    localStorage.setItem(KEY, JSON.stringify(next)); state=next; blocked=false; render(); notice('备份已恢复到当前浏览器。');
  } catch (e) { notice('导入失败：'+e.message+' 原有记录未改变。'); }
  finally { event.target.value=''; }
});
window.addEventListener('storage',e => {
  if (e.key !== KEY) return;
  try { state=e.newValue ? Core.validate(JSON.parse(e.newValue)) : Core.empty(); blocked=false; render(); notice('已更新其他标签页保存的记录。'); }
  catch (_) { blocked=true; render(); notice('其他标签页的记录无法读取，请先导出备份。'); }
});
window.addEventListener('focus',render);
render();
