const {test}=require('node:test'),assert=require('node:assert/strict');
const C=require('../product-site/app/core.js'),fixture=require('./fixtures/accounting.json');
test('same accounting fixture as SQLite: isolation, historical dates, duplicate prevention and reserved funds',()=>{
 const profiles=new Map();
 function run(op){if(!profiles.has(op.user))profiles.set(op.user,C.empty());const d=profiles.get(op.user);
  if(op.type==='source')C.addSource(d,op.id,op.title,op.kind,op.amount);
  else if(op.type==='wish')C.addWish(d,op.id,op.title,op.amount,op.priority);
  else if(op.type==='checkin')C.checkin(d,op.id,op.day);
  else if(op.type==='advance')C.advance(d,op.id);
 }
 for(const op of fixture.operations){if(op.error)assert.throws(()=>run(op),undefined,JSON.stringify(op));else run(op);}
 for(const [user,expected]of Object.entries(fixture.expected)){const d=profiles.get(user);assert.deepEqual(C.summary(d),Object.fromEntries(['attendance','habits','reserved','balance'].map(k=>[k,expected[k]])));assert.deepEqual(C.trend(d).map(r=>[r.day,r.cents,r.cumulative]),expected.days);assert.deepEqual(d.wishes.map(w=>w.status),expected.statuses);C.validate(d);}
});
