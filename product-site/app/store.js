(function(root) {
  'use strict';
  const C = typeof module !== 'undefined' ? require('./core.js') : root.WishFlow;
  const KEY = 'wishflow.browser.v2', LEGACY = 'wishflow.browser.v1';
  const fresh = () => ({version:2,profiles:[]});
  const copy = obj => JSON.parse(JSON.stringify(obj));
  function validate(value) {
    if (!value || value.version !== 2 || !Array.isArray(value.profiles) || value.profiles.length > 1000) throw Error('资料备份格式不正确。');
    const ids=new Set(), names=new Set();
    for (const p of value.profiles) {
      if (!p || typeof p.id !== 'string' || !p.id || ids.has(p.id) || C.nickname(p.name) !== p.name || names.has(p.name)) throw Error('资料名称或编号重复，无法恢复。');
      ids.add(p.id); names.add(p.name); C.validate(p.data);
    }
    return value;
  }
  function normalizeBackup(data) {
    if (data && data.version === 1) return {version:2,profiles:[{id:'legacy',name:'旧版资料',data:C.validate(data)}]};
    return validate(data);
  }
  function create(storage) {
    function read() {
      const raw=storage.getItem(KEY);
      if (raw !== null) return validate(JSON.parse(raw));
      const legacy=storage.getItem(LEGACY);
      if (legacy === null) return fresh();
      const migrated=normalizeBackup(JSON.parse(legacy));
      // Only write after validation. The original v1 key is deliberately retained.
      storage.setItem(KEY,JSON.stringify(migrated));
      return migrated;
    }
    function save(next) { validate(next); storage.setItem(KEY,JSON.stringify(next)); return next; }
    function select(name) {
      name=C.nickname(name); const next=copy(read()); let p=next.profiles.find(p=>p.name===name);
      if (!p) { p={id:'profile-'+name,name,data:C.empty()};next.profiles.push(p);save(next); }
      return p.id;
    }
    function update(id,change) {
      const next=copy(read()), profile=next.profiles.find(p=>p.id===id);
      if (!profile) throw Error('当前资料不存在，请重新选择使用者。');
      change(profile.data); return save(next);
    }
    function restore(data) { const next=copy(normalizeBackup(data));return save(next); }
    function rawBackup() { return storage.getItem(KEY) ?? storage.getItem(LEGACY) ?? JSON.stringify(fresh()); }
    return { read,select,update,restore,rawBackup };
  }
  const api={KEY,LEGACY,fresh,validate,normalizeBackup,create};
  if (typeof module !== 'undefined') module.exports=api;
  root.WishFlowStore=api;
})(globalThis);
