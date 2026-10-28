const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),vendor=path.join(root,'product-site/app/vendor/sql.js');
const init=require(path.join(vendor,'sql-wasm.js')),A=require('../product-site/app/sqlite-db.js');
(async()=>{const SQL=await init({locateFile:file=>path.join(vendor,file)}),schema=fs.readFileSync(path.join(root,'product-site/app/schema.sql'),'utf8');const adapter=A.open(SQL,schema,new Uint8Array(fs.readFileSync(process.argv[2])));
 const before={users:adapter.users(),a:adapter.snapshot('甲'),totals:adapter.totals('甲')};
 if(process.argv[4]==='mutate'){const wish=before.a.wishes[0];adapter.advance('甲',wish.id);adapter.advance('甲',wish.id);const source=adapter.addSource('乙','浏览器新增','attendance','20.29');adapter.checkin('乙',source,'2026-09-23');}
 fs.writeFileSync(process.argv[3],adapter.bytes());console.log(JSON.stringify({before,after:{a:adapter.totals('甲'),b:adapter.totals('乙'),users:adapter.users()}}));adapter.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
