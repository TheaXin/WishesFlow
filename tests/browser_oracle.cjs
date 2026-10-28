// JSON-in / JSON-out driver used by Python to compare each operation against real SQLite.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),C=require('../product-site/app/core.js');
const input=JSON.parse(fs.readFileSync(0,'utf8')),profiles=new Map(input.users.map(u=>[u,C.empty()]));
(async()=>{
const vendor=path.resolve(__dirname,'../product-site/app/vendor/sql.js');
const SQL=await require(path.join(vendor,'sql-wasm.js'))({locateFile:file=>path.join(vendor,file)});
const sqlite=require('../product-site/app/sqlite-db.js').open(SQL,fs.readFileSync(path.resolve(__dirname,'../product-site/app/schema.sql'),'utf8'));
const ids=new Map();
const result=[];
for(const op of input.operations){let accepted=true;const d=profiles.get(op.user);
 try {
  if(op.type==='source')C.addSource(d,op.id,op.title,op.kind,op.amount);
  else if(op.type==='wish')C.addWish(d,op.id,op.title,op.amount,op.priority);
  else if(op.type==='checkin')C.checkin(d,op.id,op.day);
  else if(op.type==='advance')C.advance(d,op.id);
  else throw Error('Unknown operation');
 }catch(_){accepted=false;}
 let sqlAccepted=true;
 try{
  if(op.type==='source')ids.set(op.id,sqlite.addSource(op.user,op.title,op.kind,op.amount));
  else if(op.type==='wish')ids.set(op.id,sqlite.addWish(op.user,op.title,op.amount,op.priority));
  else if(op.type==='checkin')sqlite.checkin(op.user,ids.get(op.id)||'missing',op.day);
  else if(op.type==='advance')sqlite.advance(op.user,ids.get(op.id)||'missing');
 }catch(_){sqlAccepted=false;}
 assert.equal(sqlAccepted,accepted,'WASM SQLite acceptance differs: '+JSON.stringify(op));
 const aliases=new Map([...ids].map(([alias,id])=>[id,alias]));
 for(const [user,expected]of profiles){
  const actual=sqlite.snapshot(user);
  const projection=s=>({sources:s.sources.map(x=>[aliases.get(x.id)||x.id,x.title,x.kind,x.cents]).sort(),entries:s.entries.map(x=>[aliases.get(x.sourceId)||x.sourceId,x.day,x.title,x.kind,x.cents]).sort(),wishes:C.orderedWishes(s).map(w=>[w.title,w.cents,w.priority,w.status]),trend:C.trend(s)});
  assert.deepEqual(sqlite.totals(user),C.summary(expected),'WASM SQLite totals differ');
  assert.deepEqual(projection(actual),projection(expected),'WASM SQLite records differ: '+JSON.stringify(op));
 }
 result.push({accepted,profiles:Object.fromEntries([...profiles].map(([u,s])=>[u,{summary:C.summary(s),trend:C.trend(s).map(r=>[r.day,r.cents,r.cumulative]),wishes:C.orderedWishes(s).map(w=>[w.title,w.cents,w.priority,w.status]),entries:s.entries.length,sources:s.sources.length,sourceRows:s.sources.map(x=>[x.id,x.title,x.kind,x.cents]).sort(),entryRows:s.entries.map(x=>[x.sourceId,x.day,x.title,x.kind,x.cents]).sort()}]))});
}
process.stdout.write(JSON.stringify(result));
sqlite.close();
})().catch(error=>{console.error(error);process.exitCode=1;});
