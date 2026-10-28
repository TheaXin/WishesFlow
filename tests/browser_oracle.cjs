// JSON-in / JSON-out driver used by Python to compare each operation against real SQLite.
const fs=require('node:fs'),C=require('../product-site/app/core.js');
const input=JSON.parse(fs.readFileSync(0,'utf8')),profiles=new Map(input.users.map(u=>[u,C.empty()]));
const result=[];
for(const op of input.operations){let accepted=true;const d=profiles.get(op.user);
 try {
  if(op.type==='source')C.addSource(d,op.id,op.title,op.kind,op.amount);
  else if(op.type==='wish')C.addWish(d,op.id,op.title,op.amount,op.priority);
  else if(op.type==='checkin')C.checkin(d,op.id,op.day);
  else if(op.type==='advance')C.advance(d,op.id);
  else throw Error('Unknown operation');
 }catch(_){accepted=false;}
 result.push({accepted,profiles:Object.fromEntries([...profiles].map(([u,s])=>[u,{summary:C.summary(s),trend:C.trend(s).map(r=>[r.day,r.cents,r.cumulative]),wishes:C.orderedWishes(s).map(w=>[w.title,w.cents,w.priority,w.status]),entries:s.entries.length,sources:s.sources.length,sourceRows:s.sources.map(x=>[x.id,x.title,x.kind,x.cents]).sort(),entryRows:s.entries.map(x=>[x.sourceId,x.day,x.title,x.kind,x.cents]).sort()}]))});
}
process.stdout.write(JSON.stringify(result));
