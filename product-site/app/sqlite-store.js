/* SQLite file persistence. IndexedDB stores the binary database; JSON is only a migration input. */
(function(root){
 'use strict';
 const A=typeof module!=='undefined'?require('./sqlite-db.js'):root.WishFlowSQLite;
 const L=typeof module!=='undefined'?require('./store.js'):root.WishFlowStore;
 const C=typeof module!=='undefined'?require('./core.js'):root.WishFlow;
 function indexedDBFiles(factory=root.indexedDB){
  const ready=new Promise((resolve,reject)=>{const request=factory.open('wishflow-sqlite-v3',1);request.onupgradeneeded=()=>request.result.createObjectStore('files');request.onerror=()=>reject(request.error);request.onblocked=()=>reject(Error('请关闭旧标签页后重新加载数据库。'));request.onsuccess=()=>{const db=request.result;db.onversionchange=()=>db.close();resolve(db);};});
  async function operation(mode,record){const db=await ready;return new Promise((resolve,reject)=>{const transaction=db.transaction('files',mode);let value=null;const request=record===undefined?transaction.objectStore('files').get('main'):transaction.objectStore('files').put(record,'main');request.onsuccess=()=>{value=request.result;};transaction.oncomplete=()=>resolve(value??null);transaction.onabort=()=>reject(transaction.error||Error('SQLite 文件保存已取消。'));transaction.onerror=()=>reject(transaction.error||Error('无法保存 SQLite 文件。'));});}
  return {load:()=>operation('readonly'),save:record=>operation('readwrite',record),close:async()=>(await ready).close()};
 }
 function create({SQL,schema,persistence,legacyStorage,lock}){
  const files=persistence||indexedDBFiles();
  const exclusive=lock||(work=>{if(!root.navigator?.locks)throw Error('当前浏览器不支持安全的 SQLite 多标签保存，请使用新版浏览器。');return root.navigator.locks.request('wishflow-sqlite-v3',work);});
  const channel=typeof window!=='undefined'&&root.BroadcastChannel?new root.BroadcastChannel('wishflow-sqlite-v3'):null;
  async function access(work){return exclusive(async()=>{
   const existing=await files.load();let adapter,names,dirty=!existing;const revision=existing?.revision||0;
   try{
    adapter=A.open(SQL,schema,existing?.bytes);names=existing?.names?[...existing.names]:[];
    if(!existing&&legacyStorage){const raw=legacyStorage.getItem(L.KEY)??legacyStorage.getItem(L.LEGACY);if(raw!==null){const legacy=L.normalizeBackup(JSON.parse(raw));for(const p of legacy.profiles){adapter.importProfile(p.name,p.data);names.push(p.name);}}}
    const state={adapter,names,mark:()=>{dirty=true;}};const result=await work(state);
    if(dirty){await files.save({bytes:adapter.bytes(),names:[...new Set(state.names)],revision:revision+1});channel?.postMessage({revision:revision+1});}
    return result;
   }finally{adapter?.close();}
  });}
  function projection(adapter,names){return {version:2,profiles:[...new Set([...names,...adapter.users()])].sort().map(name=>({id:'profile-'+name,name,data:adapter.snapshot(name)}))};}
  const read=()=>access(({adapter,names})=>projection(adapter,names));
  const select=name=>access(state=>{name=C.nickname(name);if(!state.names.includes(name)){state.names.push(name);state.mark();}return 'profile-'+name;});
  function change(id,operation){return access(state=>{const profile=projection(state.adapter,state.names).profiles.find(p=>p.id===id);if(!profile)throw Error('找不到当前资料，请重新选择。');operation(state.adapter,profile.name);state.mark();return projection(state.adapter,state.names);});}
  async function importDatabase(bytes){return exclusive(async()=>{let db;try{db=A.open(SQL,schema,bytes);const names=db.users();for(const name of names){C.nickname(name);C.validate(db.snapshot(name));}const existing=await files.load();await files.save({bytes:db.bytes(),names,revision:(existing?.revision||0)+1});channel?.postMessage({restored:true});return true;}finally{db?.close();}});}
  async function restoreJSON(data){const backup=L.normalizeBackup(data);let db;try{db=A.open(SQL,schema);for(const p of backup.profiles)db.importProfile(p.name,p.data);const bytes=db.bytes();return await exclusive(async()=>{const existing=await files.load();await files.save({bytes,names:backup.profiles.map(p=>p.name),revision:(existing?.revision||0)+1});channel?.postMessage({restored:true});return true;});}finally{db?.close();}}
  return {read,select,addSource:(id,name,kind,amount)=>change(id,(a,u)=>a.addSource(u,name,kind,amount)),addWish:(id,name,amount,priority)=>change(id,(a,u)=>a.addWish(u,name,amount,priority)),checkin:(id,source,day)=>change(id,(a,u)=>a.checkin(u,source,day)),advance:(id,wish)=>change(id,(a,u)=>a.advance(u,wish)),exportDatabase:()=>access(({adapter})=>adapter.bytes()),importDatabase,restoreJSON,close:()=>{channel?.close();return files.close?.();},subscribe:fn=>{if(channel)channel.onmessage=fn;}};
 }
 const api={create,indexedDBFiles};if(typeof module!=='undefined')module.exports=api;root.WishFlowSQLiteStore=api;
})(globalThis);
