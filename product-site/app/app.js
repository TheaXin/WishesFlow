'use strict';
const C=window.WishFlow, S=window.WishFlowStore;
const $=id=>document.getElementById(id);
const money=n=>new Intl.NumberFormat('zh-CN',{style:'currency',currency:'CNY'}).format(n/100);
const labels={home:'个人首页',dashboard:'仪表盘',attendance:'考勤打卡',habits:'习惯打卡',wishes:'心愿单',data:'数据与版本'};
const statuses={active:'积累中',unlocked:'已解锁',completed:'已实现'};
let sqliteRuntime,schemaText,store,database=S.fresh(), profileId='', blocked=false, filter='all';
let route=labels[location.hash.slice(1)]?location.hash.slice(1):'home';
function el(tag,text,cls) {const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=text;if(cls)n.className=cls;return n;}
function link(text,href,cls='button-link') {const n=el('a',text,cls);n.href=href;return n;}
function button(text,action,cls) {const n=el('button',text,cls);n.type='button';n.addEventListener('click',action);return n;}
function notify(message,error=false) {$('notice').textContent=message;$('notice').hidden=!message;$('notice').classList.toggle('error',error);}
function report(error) {const storageError=['QuotaExceededError','SecurityError'].includes(error.name);notify(storageError?'浏览器无法保存记录。请检查存储权限或空间，先导出备份。此次操作未保存。':error.message,true);}
function current() {return database.profiles.find(p=>p.id===profileId);}
function remember(id) {profileId=id;try {if(id)sessionStorage.setItem('wishflow.current-profile',id);else sessionStorage.removeItem('wishflow.current-profile');}catch(_){/* The current selection can remain in memory when session storage is unavailable. */}}
async function load() {
  try {if(!store)throw Error('SQLite 尚未加载。');database=await store.read();blocked=false;if(profileId&&!current())remember('');}
  catch(e){blocked=true;report(Error('无法读取资料。现有记录未被覆盖，请到“数据与版本”导出原始记录或恢复有效备份。'));}
}
async function update(change,message='已保存到当前浏览器。') {
  try {if(blocked||!current())throw Error('请先选择可用的使用者资料。');database=await change(store,profileId);render();notify(message);return true;}
  catch(e){report(e);return false;}
}
async function selectProfile(name) {
  try {if(blocked)throw Error('请先恢复有效备份或检查浏览器存储权限。');remember(await store.select(name));await load();filter='all';history.replaceState(null,'','#home');route='home';render();notify('已进入 '+current().name+' 的个人空间。');}
  catch(e){report(e);}
}
function empty(container,text,href,action) {const n=el('div',text,'empty');if(href){n.append(el('br'),link(action,href,'text-link'));}container.append(n);}
function metric(name,value) {const n=el('div',null,'metric');n.append(el('span',name),el('strong',value));return n;}
function progress(w,balance) {const p=el('progress');p.max=w.cents;p.value=w.status==='active'?Math.max(0,Math.min(balance,w.cents)):w.cents;p.setAttribute('aria-label',w.title+'积累进度');return p;}
function renderWelcome() {
  const profiles=$('existing-profiles');profiles.replaceChildren();
  if(database.profiles.length){profiles.append(el('p','或继续已有资料','muted fine'));const options=el('div',null,'profile-options');database.profiles.forEach(p=>options.append(button(p.name,()=>selectProfile(p.name),'secondary')));profiles.append(options);}
  $('profile-form').querySelector('button').disabled=blocked;
}
function renderHome(d) {
  $('home-heading').textContent=current().name+' 的个人首页';
  const activeSources=d.sources.filter(s=>s.kind!=='habit'||s.active!==false);
  const todayDone=d.entries.filter(e=>e.day===C.today()).length;
  const stages=[d.wishes.length>0,activeSources.length>0,todayDone>0,d.wishes.some(w=>w.status!=='active')];
  ['step-wish','step-source','step-checkin','step-complete'].forEach((id,i)=>$(id).classList.toggle('done',stages[i]));
  const target=$('home-next');target.replaceChildren();const box=el('section',null,'home-focus');
  if(!d.wishes.length){
    box.append(el('h2','你的下一步：设定第一个心愿'));const form=el('form',null,'panel');form.id='home-wish-form';
    const nameLabel=el('label','这次最想实现什么？');nameLabel.htmlFor='first-wish-title';const name=el('input');name.id='first-wish-title';name.name='title';name.required=true;name.maxLength=80;name.placeholder='例如：看一场演唱会';
    const amountLabel=el('label','大约需要多少心愿金？');amountLabel.htmlFor='first-wish-amount';const amount=el('input');amount.id='first-wish-amount';amount.name='amount';amount.type='number';amount.min='0.01';amount.max='100000000';amount.step='0.01';amount.value='1500';amount.required=true;
    const save=el('button','保存心愿，继续下一步');save.type='submit';form.append(nameLabel,name,amountLabel,amount,save);
    form.addEventListener('submit',async e=>{e.preventDefault();await update((db,id)=>db.addWish(id,name.value,amount.value,1),'第一个心愿已保存，接下来配置一个行动。');});box.append(form);
  }else if(!activeSources.length){
    box.append(el('h2','你的下一步：配置一个行动'));const choices=el('div',null,'pair');
    for(const [title,copy,href,cta]of [['从习惯开始','阅读、运动、学习或早睡，完成一次就为心愿加一笔。','#habits','添加第一个习惯'],['从稳定投入开始','把工作、接单或规律投入，记录为一笔心愿金。','#attendance','配置收入来源']]){const card=el('div',null,'panel');card.append(el('h3',title),el('p',copy),link(cta,href));choices.append(card);}box.append(choices);
  }else{
    box.append(el('h2','今天的个人计划'));const grid=el('div',null,'metrics');grid.append(metric('可用心愿金',money(C.summary(d).balance)),metric('已配置行动',activeSources.length+' 项'),metric('今日已完成',todayDone+' 项'));grid.style.gridTemplateColumns='repeat(3,1fr)';box.append(grid);
    const panel=el('div',null,'panel');panel.append(el('h3',todayDone?'继续为心愿完成一点':'现在就去完成一次打卡'),el('p','记录已经完成的行动，或补记过去的坚持。'));const actions=el('div',null,'button-row');actions.append(link('去习惯打卡','#habits'),link('去考勤打卡','#attendance','button-link secondary'));panel.append(actions);box.append(panel);
  }
  target.append(box);
}
function renderDashboard(d) {
  const totals=C.summary(d), metrics=$('dashboard-metrics');metrics.replaceChildren();
  for(const [key,label]of [['balance','可用心愿金'],['attendance','考勤累计'],['habits','习惯累计'],['reserved','已为心愿预留']])metrics.append(metric(label,money(totals[key])));
  renderTrend(d);
  const overview=$('wish-overview');overview.replaceChildren();
  if(!d.wishes.length)empty(overview,'先写下一个真正想实现的目标。','#wishes','设定第一个心愿');
  for(const w of C.orderedWishes(d)){const row=el('div',null,'mini-wish');row.append(el('b',w.title),el('small',`${money(w.cents)} · ${statuses[w.status]} · 优先级 ${w.priority}`),progress(w,totals.balance));overview.append(row);}
  const history=$('history');history.replaceChildren();
  if(!d.entries.length){empty(history,'完成一次考勤或习惯打卡后，这里会留下记录。');return;}
  const table=el('table'),head=el('thead'),tr=el('tr');['日期','项目','来源','获得心愿金'].forEach(t=>tr.append(el('th',t)));head.append(tr);table.append(head);const body=el('tbody');
  [...d.entries].map((e,i)=>({...e,index:i})).sort((a,b)=>b.day.localeCompare(a.day)||b.index-a.index).slice(0,20).forEach(e=>{const row=el('tr');[e.day,e.title,e.kind==='habit'?'习惯':'考勤','+'+money(e.cents)].forEach(t=>row.append(el('td',t)));body.append(row);});table.append(body);const wrap=el('div',null,'table-scroll');wrap.append(table);history.append(wrap);
}
function renderTrend(d) {
  const container=$('trend');container.replaceChildren();const rows=C.trend(d);
  if(!rows.length){empty(container,'还没有积累记录。完成一次打卡，看看心愿金如何增长。','#habits','去完成一个习惯');return;}
  container.append(el('div',money(rows.at(-1).cumulative),'chart-value'));
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 520 210');svg.setAttribute('role','img');svg.setAttribute('aria-label','累计获得的心愿金，按打卡日期排列。详细数值见下方数据表。');svg.classList.add('trend-chart');
  const max=rows.at(-1).cumulative||1;
  for(let i=0;i<4;i++){const line=document.createElementNS(ns,'line');line.setAttribute('x1','5');line.setAttribute('x2','515');line.setAttribute('y1',String(15+i*55));line.setAttribute('y2',String(15+i*55));line.setAttribute('stroke','#e1e9f7');line.setAttribute('stroke-dasharray','4 5');svg.append(line);}
  const points=rows.map((r,i)=>`${rows.length===1?260:12+i*496/(rows.length-1)},${180-r.cumulative/max*160}`);
  const path=document.createElementNS(ns,'polyline');path.setAttribute('points',points.join(' '));path.setAttribute('fill','none');path.setAttribute('stroke','#7895d4');path.setAttribute('stroke-width','3');path.setAttribute('stroke-linejoin','round');svg.append(path);
  // At most 100 visible markers; the table retains every daily total.
  rows.forEach((r,i)=>{if(i!==rows.length-1&&i%Math.ceil(rows.length/100)!==0)return;const [cx,cy]=points[i].split(',');const dot=document.createElementNS(ns,'circle');dot.setAttribute('cx',cx);dot.setAttribute('cy',cy);dot.setAttribute('r','4');dot.setAttribute('fill','#ee9bb0');const text=document.createElementNS(ns,'title');text.textContent=r.day+' · '+money(r.cumulative);dot.append(text);svg.append(dot);});container.append(svg);
  const caption=el('div',null,'chart-caption');caption.append(el('span',rows[0].day),el('span',rows.at(-1).day));container.append(caption);
  const details=el('details');details.append(el('summary','查看每日积累数据'));const table=el('table'),thead=el('thead'),tr=el('tr');['日期','当日获得','累计获得'].forEach(t=>tr.append(el('th',t)));thead.append(tr);table.append(thead);const body=el('tbody');rows.forEach(r=>{const row=el('tr');[r.day,money(r.cents),money(r.cumulative)].forEach(t=>row.append(el('td',t)));body.append(row);});table.append(body);details.append(table);container.append(details);
}
function renderAttendance(d) {
  const incomes=d.sources.filter(s=>s.kind==='attendance'),select=$('income-select'),previous=select.value;
  select.replaceChildren();for(const s of [...incomes].reverse()){const option=el('option',`${s.title} · ${money(s.cents)}/次`);option.value=s.id;select.append(option);}if(incomes.some(s=>s.id===previous))select.value=previous;
  select.disabled=!incomes.length||blocked;$('attendance-date').disabled=!incomes.length||blocked;
  if(!incomes.length){const option=el('option','先新增一个收入来源');option.value='';select.append(option);}
  const list=$('income-list');list.replaceChildren();if(!incomes.length){empty(list,'例如：全职工作、自由接单或其他稳定投入。');$('income-details').open=true;}
  for(const s of [...incomes].reverse()){const row=el('div',null,'source-row');row.append(el('b',s.title),el('small',`每次计入 ${money(s.cents)}`));list.append(row);}updateAttendanceState();
}
function updateAttendanceState() {
  const d=current()?.data;if(!d)return;const source=$('income-select').value,date=$('attendance-date').value;
  const done=d.entries.some(e=>e.sourceId===source&&e.day===date),valid=C.validDay(date)&&date<=C.today();
  $('attendance-submit').disabled=blocked||!source||!valid||done;
  $('attendance-state').textContent=!source?'先新增收入来源，再开始打卡。':!valid?'请选择今天或之前的有效日期。':done?'这项来源在 '+date+' 已经打卡。':'按所选日期记录，可补记过去的投入。';
}
function renderHabits(d) {
  const container=$('habit-list'),habits=d.sources.filter(s=>s.kind==='habit'&&s.active!==false),date=$('habit-date').value;container.replaceChildren();
  const valid=C.validDay(date)&&date<=C.today(),count=habits.filter(s=>d.entries.some(e=>e.sourceId===s.id&&e.day===date)).length;
  $('habit-count').textContent=valid?`所选日期已完成 ${count} / ${habits.length} 项`:'请选择今天或之前的有效日期。';
  if(!habits.length){empty(container,'添加第一个习惯，让今天有一个小小的完成感。');$('habit-details').open=true;}
  for(const s of [...habits].reverse()){const done=d.entries.some(e=>e.sourceId===s.id&&e.day===date),card=el('article',null,'habit-card'),info=el('div');info.append(el('h3',s.title),el('small',`完成一次，获得 ${money(s.cents)}`));const action=button(done?'当日已完成':'完成',()=>update((db,id)=>db.checkin(id,s.id,$('habit-date').value),'已记录「'+s.title+'」。'));action.setAttribute('aria-label',(done?'当日已完成：':'完成习惯：')+s.title);action.disabled=blocked||done||!valid;card.append(info,action);container.append(card);}
}
function renderWishes(d) {
  const balance=C.summary(d).balance;$('wish-balance').textContent=money(balance);const container=$('wish-list');container.replaceChildren();
  document.querySelectorAll('[data-filter]').forEach(b=>{const status=b.dataset.filter;const count=status==='all'?d.wishes.length:d.wishes.filter(w=>w.status===status).length;b.textContent=(status==='all'?'全部':statuses[status])+' '+count;b.setAttribute('aria-pressed',String(status===filter));});
  const wishes=C.orderedWishes(d).filter(w=>filter==='all'||w.status===filter);
  if(!wishes.length){empty(container,d.wishes.length?'这个状态还没有心愿。':'还没有心愿。写下想要的生活，行动才有方向。');return;}
  for(const status of ['active','unlocked','completed']){
    const group=wishes.filter(w=>w.status===status);if(!group.length)continue;
    const section=el('section',null,'wish-group');section.append(el('h2',`${statuses[status]} · ${group.length}`));const grid=el('div',null,'wish-grid');
    for(const w of group){const card=el('article',null,'wish-card '+w.status);card.append(el('span',statuses[w.status],'status-label'),el('h3',w.title),el('p',`目标 ${money(w.cents)} · 优先级 ${w.priority}`,'wish-meta'),progress(w,balance));const copy=el('div',null,'progress-copy');const percent=w.status==='active'?Math.min(100,Math.floor(balance/w.cents*100)):100;copy.append(el('span',w.status==='active'?money(Math.min(balance,w.cents))+' / '+money(w.cents):'预算持续记为已使用'),el('span',percent+'% 已积累'));card.append(copy);
      if(w.status==='completed')card.append(el('p','已实现，值得庆祝。','muted fine'));
      else{const action=button(w.status==='active'?'解锁这个心愿':'标记为已实现 ✦',()=>update((db,id)=>db.advance(id,w.id),w.status==='active'?'心愿已解锁，预算已预留。':'已记下这份实现，预算持续记为已使用。'));action.disabled=blocked||(w.status==='active'&&balance<w.cents);card.append(action);if(w.status==='active'&&balance<w.cents)card.append(el('small','还差 '+money(w.cents-balance),'muted'));}
      grid.append(card);
    }section.append(grid);container.append(section);
  }
}
function render() {
  const p=current(),hasProfile=!!p,showWelcome=!hasProfile&&route!=='data';
  $('welcome').hidden=!showWelcome;$('pages').hidden=!hasProfile||route==='data';$('page-data').hidden=route!=='data';
  document.querySelectorAll('#pages [data-page]').forEach(page=>{page.hidden=page.dataset.page!==route;});
  $('profile-name').textContent=p?p.name:'你的个人空间';$('profile-hint').textContent=p?'本机资料 · 昵称区分':'先选择一个昵称';$('avatar').textContent=p?[...p.name][0]:'✦';$('switch-profile').hidden=!p;
  const title=showWelcome?'开始使用':labels[route];document.title=title+' · 心愿 Flow 浏览器版';$('breadcrumb').textContent=(['attendance','habits'].includes(route)?'每日行动 / ':route==='data'?'管理 / ':'我的心愿 / ')+title;
  $('today-label').textContent=new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'long'});
  document.querySelectorAll('[data-route]').forEach(a=>{if(a.dataset.route===route)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  renderWelcome();
  if(p){renderHome(p.data);renderDashboard(p.data);renderAttendance(p.data);renderHabits(p.data);renderWishes(p.data);}
  $('backup-count').textContent=`包含 ${database.profiles.length} 份昵称资料；导出后请定期更新备份。`;
  let hasLegacy=false;try{hasLegacy=(localStorage.getItem(S.KEY)??localStorage.getItem(S.LEGACY))!==null;}catch(_){}
  $('export-legacy').hidden=!hasLegacy;$('migration-note').hidden=!hasLegacy;
  document.querySelectorAll('#income-form button,#habit-form button,#wish-form button').forEach(b=>{b.disabled=blocked||!p;});
}
async function refresh(){await load();render();}
function syncRoute(event){if(event&&!blocked)notify('');const next=location.hash.slice(1);route=labels[next]?next:'home';if(!current()&&!['home','data'].includes(route)){route='home';history.replaceState(null,'','#home');notify('请先选择使用者，再进入功能页面。');}$('app-nav').parentElement.classList.remove('menu-open');$('menu-toggle').setAttribute('aria-expanded','false');$('menu-toggle').textContent='展开页面导航';render();$('main').focus({preventScroll:true});window.scrollTo({top:0});}
document.querySelector('.skip-link').addEventListener('click',e=>{e.preventDefault();$('main').focus();});
$('profile-form').addEventListener('submit',e=>{e.preventDefault();selectProfile($('nickname').value);});
$('switch-profile').addEventListener('click',()=>{remember('');history.replaceState(null,'','#home');route='home';render();notify('请选择另一位使用者。原有资料会继续保留。');$('nickname').focus();});
document.querySelectorAll('[data-route]').forEach(a=>a.addEventListener('click',()=>{document.querySelector('.sidebar').classList.remove('menu-open');$('menu-toggle').setAttribute('aria-expanded','false');$('menu-toggle').textContent='展开页面导航';}));
$('menu-toggle').addEventListener('click',()=>{const expanded=document.querySelector('.sidebar').classList.toggle('menu-open');$('menu-toggle').setAttribute('aria-expanded',String(expanded));$('menu-toggle').textContent=expanded?'收起页面导航':'展开页面导航';});
for(const [id,kind]of [['income-form','attendance'],['habit-form','habit']]){$(id).addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget,data=new FormData(form);if(await update((db,id)=>db.addSource(id,data.get('title'),kind,data.get('amount')),kind==='habit'?'习惯已保存，可以开始打卡。':'收入来源已保存，可以开始打卡。'))form.reset();});}
$('attendance-form').addEventListener('submit',e=>{e.preventDefault();update((db,id)=>db.checkin(id,$('income-select').value,$('attendance-date').value),'考勤已记录，心愿金已计入。');});
$('income-select').addEventListener('change',updateAttendanceState);$('attendance-date').addEventListener('change',updateAttendanceState);$('habit-date').addEventListener('change',()=>{if(current())renderHabits(current().data);});
$('wish-form').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget,data=new FormData(form);if(await update((db,id)=>db.addWish(id,data.get('title'),data.get('amount'),data.get('priority')),'新心愿已保存。')){form.reset();$('wish-details').open=false;}});
$('open-wish-form').addEventListener('click',()=>{$('wish-details').open=true;$('wish-title').focus();});
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;if(current())renderWishes(current().data);}));
function download(raw,name,mime='application/json'){const url=URL.createObjectURL(new Blob([raw],{type:mime}));const a=el('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('export').addEventListener('click',async()=>{try{if(!store)throw Error('SQLite 尚未加载。');download(await store.exportDatabase(),'wishflow-'+C.today()+'.sqlite3','application/vnd.sqlite3');notify('已发起 SQLite 数据库下载，请确认文件已保存。');}catch(e){report(e);}});
$('export-legacy').addEventListener('click',()=>{try{const raw=localStorage.getItem(S.KEY)??localStorage.getItem(S.LEGACY);if(raw===null)throw Error('未找到旧版记录。');download(raw,'wishflow-before-upgrade.json');notify('已发起升级前原始记录的下载。');}catch(e){report(e);}});
$('import').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;try{
 if(file.size>50*1024*1024)throw Error('数据库或备份不能大于 50 MB。');if(!store)throw Error('SQLite 尚未加载。');
 const bytes=new Uint8Array(await file.arrayBuffer());let count,next,isSQLite=new TextDecoder().decode(bytes.slice(0,16))==='SQLite format 3\0';
 if(isSQLite){let probe;try{probe=WishFlowSQLite.open(sqliteRuntime,schemaText,bytes);const users=probe.users();for(const name of users){C.nickname(name);C.validate(probe.snapshot(name));}count=users.length;}finally{probe?.close();}}
 else {next=S.normalizeBackup(JSON.parse(new TextDecoder().decode(bytes)));count=next.profiles.length;}
 if(!confirm(`已验证 ${count} 份资料。导入会替换当前浏览器 SQLite 全部业务记录。确认已经备份并继续？`))return;
 if(isSQLite)await store.importDatabase(bytes);else await store.restoreJSON(next);blocked=false;remember('');await load();render();notify('备份已恢复，请返回个人首页选择资料。');
 }catch(error){report(Error('导入失败：'+error.message+' 原有资料未改变。'));}finally{e.target.value='';}});
window.addEventListener('hashchange',syncRoute);window.addEventListener('focus',async()=>{for(const id of ['attendance-date','habit-date'])$(id).max=C.today();if(store&&!blocked){try{const latest=await store.read();if(JSON.stringify(latest)!==JSON.stringify(database)){database=latest;if(!current())remember('');render();}}catch(e){blocked=true;render();report(e);}}});
try{profileId=sessionStorage.getItem('wishflow.current-profile')||'';}catch(_){}
for(const id of ['attendance-date','habit-date']){$(id).value=C.today();$(id).max=C.today();}
blocked=true;render();notify('正在加载本机 SQLite 数据库…');
(async()=>{try{
 [sqliteRuntime,schemaText]=await Promise.all([initSqlJs({locateFile:file=>'vendor/sql.js/'+file}),fetch('schema.sql').then(response=>{if(!response.ok)throw Error('无法读取共享表结构。');return response.text();})]);
 store=WishFlowSQLiteStore.create({SQL:sqliteRuntime,schema:schemaText,legacyStorage:window.localStorage});store.subscribe(()=>refresh());await load();syncRoute();if(!blocked)notify('');
}catch(error){blocked=true;render();report(error);}})();
