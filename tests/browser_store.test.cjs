const {test}=require('node:test');const assert=require('node:assert/strict');
const C=require('../product-site/app/core.js'),S=require('../product-site/app/store.js');
function memory(initial={}) { const m=new Map(Object.entries(initial)); return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,v),m}; }
test('v1 migration preserves every record, long legacy names and original bytes; reload is idempotent',()=>{
 const old=C.empty();old.sources.push({id:'a',title:'旧'.repeat(100),kind:'habit',cents:100});C.checkin(old,'a','2026-09-23');
 const raw=JSON.stringify(old),storage=memory({[S.LEGACY]:raw}),store=S.create(storage);
 const next=store.read();assert.equal(next.profiles[0].name,'旧版资料');assert.deepEqual(next.profiles[0].data,old);assert.equal(storage.getItem(S.LEGACY),raw);assert.deepEqual(store.read(),next);
 assert.throws(()=>C.title('长'.repeat(81)));
});
test('nickname isolation, switching and refresh preserve independent balances',()=>{
 const storage=memory(),store=S.create(storage),a=store.select('小心愿'),b=store.select('Thea');
 store.update(a,d=>{C.addSource(d,'s','工作','attendance','100');C.checkin(d,'s','2026-09-23');});
 assert.equal(store.select('小心愿'),a);const reloaded=S.create(storage).read();assert.equal(C.summary(reloaded.profiles.find(p=>p.id===a).data).balance,10000);assert.equal(C.summary(reloaded.profiles.find(p=>p.id===b).data).balance,0);
 for(const n of ['','a b','<script>','a'.repeat(31)])assert.throws(()=>store.select(n));
});
test('storage failure is atomic; failed migration leaves original data',()=>{
 const raw=JSON.stringify(C.empty());const storage=memory({[S.LEGACY]:raw});storage.setItem=()=>{throw Error('QuotaExceeded');};assert.throws(()=>S.create(storage).read());assert.equal(storage.getItem(S.LEGACY),raw);assert.equal(storage.getItem(S.KEY),null);
 const ok=memory(),store=S.create(ok),id=store.select('甲');const before=ok.getItem(S.KEY);ok.setItem=()=>{throw Error('QuotaExceeded');};assert.throws(()=>store.update(id,d=>C.addSource(d,'a','工作','attendance','100')));assert.equal(ok.getItem(S.KEY),before);
});
test('malformed existing data and invalid imports never overwrite stored records',()=>{
 const bad=memory({[S.LEGACY]:'broken'});assert.throws(()=>S.create(bad).read());assert.equal(bad.getItem(S.LEGACY),'broken');assert.equal(bad.getItem(S.KEY),null);
 const storage=memory(),store=S.create(storage);store.select('甲');const before=storage.getItem(S.KEY);assert.throws(()=>store.restore({version:2,profiles:[{},{}]}));assert.equal(storage.getItem(S.KEY),before);
});
test('restore multi-profile and legacy backups; duplicate profile rejected',()=>{
 const storage=memory(),store=S.create(storage);store.select('甲');store.select('乙');const backup=store.read();assert.deepEqual(store.restore(JSON.parse(JSON.stringify(backup))),backup);
 assert.throws(()=>store.restore({version:2,profiles:[backup.profiles[0],backup.profiles[0]]}));assert.equal(store.read().profiles.length,2);
 assert.equal(store.restore(C.empty()).profiles[0].name,'旧版资料');
});
test('selected dates validated, historical reward snapshots and ordered daily trend',()=>{
 const d=C.empty();C.addSource(d,'a','工作','attendance','100');C.checkin(d,'a','2026-09-23');d.sources[0].cents=20000;C.checkin(d,'a','2026-09-22');
 assert.equal(d.entries[0].cents,10000);assert.deepEqual(C.trend(d),[{day:'2026-09-22',cents:20000,cumulative:20000},{day:'2026-09-23',cents:10000,cumulative:30000}]);
 for(const date of ['2026-02-30','2099-01-01','bad'])assert.throws(()=>C.checkin(d,'a',date));assert.throws(()=>C.checkin(d,'a','2026-09-23'));
});
test('wish ordering follows status, priority, insertion order',()=>{
 const d=C.empty();for(const [id,p,status]of [['a',2,'active'],['b',1,'completed'],['c',1,'unlocked'],['d',1,'active'],['e',1,'active']])d.wishes.push({id,priority:p,status,cents:100,title:id});
 assert.deepEqual(C.orderedWishes(d).map(w=>w.id),['d','e','a','c','b']);
});
