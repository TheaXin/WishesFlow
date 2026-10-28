const { test } = require('node:test');
const assert = require('node:assert/strict');
const C = require('../product-site/app/core.js');
function setup() { const s=C.empty(); s.sources.push({id:'a',title:'考勤',kind:'attendance',cents:10000},{id:'h',title:'阅读',kind:'habit',cents:2000}); s.wishes.push({id:'w',title:'演唱会',cents:11000,priority:1,status:'active'}); return s; }
test('reject insufficient balance, duplicate check-ins; completion keeps budget reserved', () => {
  const s=setup(); assert.throws(() => C.advance(s,'w'));
  C.checkin(s,'a','2026-10-28'); assert.throws(() => C.checkin(s,'a','2026-10-28'));
  C.checkin(s,'h','2026-10-28'); assert.equal(C.summary(s).balance,12000);
  C.advance(s,'w'); assert.equal(C.summary(s).balance,1000);
  C.advance(s,'w'); assert.equal(C.summary(s).balance,1000); assert.equal(s.wishes[0].status,'completed');
  assert.throws(() => C.advance(s,'w')); C.validate(s);
});
test('cent precision and positive amount validation', () => {
  assert.equal(C.amount('0.29'),29); assert.equal(C.amount('19.99'),1999);
  for (const v of ['0','-1','NaN','Infinity','0.001','100000001','']) assert.throws(() => C.amount(v));
});
test('backup round-trip, invalid imports and duplicate IDs', () => {
  const s=setup(); C.checkin(s,'a','2026-10-28');
  assert.deepEqual(C.validate(JSON.parse(JSON.stringify(s))),s);
  for (const mutate of [s=>s.version=2,s=>s.sources.push(s.sources[0]),s=>s.entries.push(s.entries[0]),s=>s.entries[0].cents=-1,s=>s.entries[0].sourceId='missing',s=>s.wishes[0].status='completed',s=>s.entries[0].day='2026-02-30']) {
    const bad=JSON.parse(JSON.stringify(s)); mutate(bad); assert.throws(() => C.validate(bad));
  }
});
