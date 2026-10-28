/* Actual SQLite storage adapter. UI snapshots are projections, never the persisted database. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'?require('./core.js'):root.WishFlow;
 const fields={income:['id','title','daily_amount','user_id'],attendance:['id','income_id','date','earned_amount','user_id'],habit_task:['id','title','reward_amount','active','user_id'],habit_checkin:['id','task_id','date','reward_amount','user_id'],wishlist:['id','title','target_amount','priority','status','unlocked_at','created_at','user_id']};
 function open(SQL,schema,bytes){
  const db=bytes?new SQL.Database(bytes):new SQL.Database();
  function rows(sql,args=[]){const stmt=db.prepare(sql);try{stmt.bind(args);const result=[];while(stmt.step())result.push(stmt.getAsObject());return result;}finally{stmt.free();}}
  try{
   if(!bytes)db.run(schema);
   if(rows('PRAGMA quick_check')[0].quick_check!=='ok')throw Error('SQLite 数据库完整性检查失败。');
   const reference=new SQL.Database();try{reference.run(schema);for(const table of Object.keys(fields)){for(const pragma of ['table_info','foreign_key_list','index_list']){const expected=reference.exec('PRAGMA '+pragma+'('+table+')')[0]?.values||[];const actual=db.exec('PRAGMA '+pragma+'('+table+')')[0]?.values||[];if(JSON.stringify(actual)!==JSON.stringify(expected))throw Error('SQLite 表结构或约束与本地版不一致：'+table);}}}finally{reference.close();}
   if(rows('PRAGMA foreign_key_check').length)throw Error('SQLite 数据库包含失效的关联记录。');
   for(const [child,parent,key]of [['attendance','income','income_id'],['habit_checkin','habit_task','task_id']])if(rows(`SELECT 1 FROM ${child} c JOIN ${parent} p ON c.${key}=p.id WHERE c.user_id<>p.user_id LIMIT 1`).length)throw Error('SQLite 记录关联了其他使用者的资料。');
   configure();
  }catch(error){db.close();throw error;}
  function configure(){db.run('PRAGMA foreign_keys=ON');db.create_function('money_cents',value=>C.amount(String(value)));}
  function exportBytes(){const result=db.export();configure();return result;}
  const scalar=(sql,args)=>Object.values(rows(sql,args)[0])[0];
  function totals(user){
   const attendance=scalar('SELECT COALESCE(SUM(money_cents(earned_amount)),0) FROM attendance WHERE user_id=?',[user]);
   const habits=scalar('SELECT COALESCE(SUM(money_cents(reward_amount)),0) FROM habit_checkin WHERE user_id=?',[user]);
   const reserved=scalar("SELECT COALESCE(SUM(money_cents(target_amount)),0) FROM wishlist WHERE user_id=? AND status IN ('unlocked','completed')",[user]);
   return {attendance,habits,reserved,balance:attendance+habits-reserved};
  }
  function users(){return rows('SELECT user_id FROM income UNION SELECT user_id FROM habit_task UNION SELECT user_id FROM wishlist UNION SELECT user_id FROM attendance UNION SELECT user_id FROM habit_checkin ORDER BY user_id').map(r=>r.user_id);}
  function snapshot(user){
   const s=C.empty();
   for(const r of rows('SELECT * FROM income WHERE user_id=? ORDER BY id',[user]))s.sources.push({id:'attendance:'+r.id,title:r.title,kind:'attendance',cents:C.amount(String(r.daily_amount))});
   for(const r of rows('SELECT * FROM habit_task WHERE user_id=? ORDER BY id',[user]))s.sources.push({id:'habit:'+r.id,title:r.title,kind:'habit',cents:C.amount(String(r.reward_amount)),active:r.active===1});
   for(const [kind,table,parent,key,amount]of [['attendance','attendance','income','income_id','earned_amount'],['habit','habit_checkin','habit_task','task_id','reward_amount']]){
    for(const r of rows(`SELECT c.*,p.title FROM ${table} c JOIN ${parent} p ON c.${key}=p.id WHERE c.user_id=? ORDER BY c.date,c.id`,[user]))s.entries.push({sourceId:kind+':'+r[key],day:r.date,title:r.title,kind,cents:C.amount(String(r[amount]))});
   }
   for(const r of rows('SELECT * FROM wishlist WHERE user_id=? ORDER BY id',[user]))s.wishes.push({id:'wish:'+r.id,title:r.title,cents:C.amount(String(r.target_amount)),priority:r.priority,status:r.status,createdAt:r.created_at,unlockedAt:r.unlocked_at});
   return s;
  }
  function transaction(work){db.run('BEGIN IMMEDIATE');try{const result=work();db.run('COMMIT');return result;}catch(e){db.run('ROLLBACK');throw e;}}
  function addSource(user,name,kind,value){C.nickname(user);const title=C.title(name),cents=C.amount(value);if(!['attendance','habit'].includes(kind))throw Error('来源类型无效。');const table=kind==='attendance'?'income':'habit_task',amount=kind==='attendance'?'daily_amount':'reward_amount';return transaction(()=>{db.run(`INSERT INTO ${table}(title,${amount},user_id) VALUES (?,?,?)`,[title,cents/100,user]);return kind+':'+scalar('SELECT last_insert_rowid()',[]);});}
  function addWish(user,name,value,priority){C.nickname(user);const draft=C.empty();C.addWish(draft,'draft',name,value,priority);const w=draft.wishes[0];return transaction(()=>{db.run('INSERT INTO wishlist(title,target_amount,priority,user_id) VALUES (?,?,?,?)',[w.title,w.cents/100,w.priority,user]);return 'wish:'+scalar('SELECT last_insert_rowid()',[]);});}
  function checkin(user,source,day){if(!C.validDay(day)||day>C.today())throw Error('请选择今天或之前的有效日期。');const match=/^(attendance|habit):(\d+)$/.exec(source);if(!match)throw Error('找不到打卡项目。');const kind=match[1],id=Number(match[2]),table=kind==='attendance'?'income':'habit_task',amount=kind==='attendance'?'daily_amount':'reward_amount',child=kind==='attendance'?'attendance':'habit_checkin',key=kind==='attendance'?'income_id':'task_id',earned=kind==='attendance'?'earned_amount':'reward_amount';return transaction(()=>{const row=rows(`SELECT ${amount} AS amount FROM ${table} WHERE id=? AND user_id=?`+(kind==='habit'?' AND active=1':''),[id,user])[0];if(!row)throw Error('找不到可用打卡项目。');C.amount(String(row.amount));if(rows(`SELECT id FROM ${child} WHERE ${key}=? AND date=? AND user_id=?`,[id,day,user]).length)throw Error('该项目在所选日期已经打卡。');db.run(`INSERT INTO ${child}(${key},date,${earned},user_id) VALUES (?,?,?,?)`,[id,day,row.amount,user]);});}
  function advance(user,id){const match=/^wish:(\d+)$/.exec(id);if(!match)throw Error('找不到心愿。');return transaction(()=>{const w=rows('SELECT * FROM wishlist WHERE id=? AND user_id=?',[Number(match[1]),user])[0];if(!w||!['active','unlocked'].includes(w.status))throw Error('心愿当前无法更新。');if(w.status==='active'){if(totals(user).balance<C.amount(String(w.target_amount)))throw Error('可用心愿金不足。');db.run("UPDATE wishlist SET status='unlocked',unlocked_at=? WHERE id=? AND user_id=?",[new Date().toISOString(),w.id,user]);}else db.run("UPDATE wishlist SET status='completed' WHERE id=? AND user_id=?",[w.id,user]);});}
  function importProfile(user,data){
   C.nickname(user);C.validate(data);
   if(users().includes(user))throw Error('资料已存在，不能重复迁移。');
   transaction(()=>{
    const ids=new Map();
    for(const source of data.sources){const table=source.kind==='attendance'?'income':'habit_task',amount=source.kind==='attendance'?'daily_amount':'reward_amount';
     if(source.kind==='habit')db.run(`INSERT INTO ${table}(title,${amount},active,user_id) VALUES (?,?,?,?)`,[source.title,source.cents/100,source.active===false?0:1,user]);
     else db.run(`INSERT INTO ${table}(title,${amount},user_id) VALUES (?,?,?)`,[source.title,source.cents/100,user]);
     ids.set(source.id,scalar('SELECT last_insert_rowid()',[]));
    }
    for(const entry of data.entries){const table=entry.kind==='attendance'?'attendance':'habit_checkin',key=entry.kind==='attendance'?'income_id':'task_id',amount=entry.kind==='attendance'?'earned_amount':'reward_amount';db.run(`INSERT INTO ${table}(${key},date,${amount},user_id) VALUES (?,?,?,?)`,[ids.get(entry.sourceId),entry.day,entry.cents/100,user]);}
    for(const wish of data.wishes)db.run('INSERT INTO wishlist(title,target_amount,priority,status,unlocked_at,created_at,user_id) VALUES (?,?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP),?)',[wish.title,wish.cents/100,wish.priority,wish.status,wish.unlockedAt||null,wish.createdAt||null,user]);
   });
  }
  return {users,snapshot,totals,importProfile,addSource,addWish,checkin,advance,bytes:exportBytes,close:()=>db.close()};
 }
 const api={open,fields};if(typeof module!=='undefined')module.exports=api;root.WishFlowSQLite=api;
})(globalThis);
