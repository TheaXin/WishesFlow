"""Compare every intermediate result with actual db/db.py, rather than two expected fixtures."""
import json
import random
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path
from db import db

ROOT=Path(__file__).resolve().parents[1]

class BrowserSQLiteDifferentialTest(unittest.TestCase):
    def compare(self,operations):
        node=shutil.which('node')
        # Desktop runtime is optional; CI uses setup-node on PATH.
        bundled=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
        if not node and bundled.exists(): node=str(bundled)
        if not node: self.fail('Node.js is required for SQLite/browser differential verification')
        users=['甲','乙'];actual=json.loads(subprocess.check_output([node,str(ROOT/'tests/browser_oracle.cjs')],input=json.dumps({'users':users,'operations':operations}).encode(),timeout=20))
        original=db.DB_PATH
        with tempfile.TemporaryDirectory() as folder:
            db.DB_PATH=Path(folder)/'test.sqlite3'
            try:
                db.init_db();ids={}
                def run(op):
                    user,key=op['user'],op['id']
                    if op['type']=='source':
                        fn=db.add_income if op['kind']=='attendance' else db.add_habit;fn(user,op['title'],float(op['amount']))
                        table='income' if op['kind']=='attendance' else 'habit_task'
                        with db.connection() as conn: ids[key]=(op['kind'],conn.execute(f'SELECT MAX(id) FROM {table}').fetchone()[0])
                    elif op['type']=='wish':
                        db.add_wish(user,op['title'],float(op['amount']),op['priority'])
                        with db.connection() as conn: ids[key]=('wish',conn.execute('SELECT MAX(id) FROM wishlist').fetchone()[0])
                    elif op['type']=='checkin':
                        kind,id_=ids.get(key,('habit',-1));fn=db.record_attendance if kind=='attendance' else db.record_habit_checkin;fn(user,id_,date.fromisoformat(op['day']))
                    elif op['type']=='advance':
                        id_=ids.get(key,('wish',-1))[1]
                        with db.connection() as conn: row=conn.execute('SELECT status FROM wishlist WHERE id=? AND user_id=?',(id_,user)).fetchone()
                        if row and row[0]=='unlocked':db.complete_wish(user,id_)
                        else:db.unlock_wish(user,id_)
                def snapshot(user):
                    with db.connection() as conn:
                        wishes=conn.execute("SELECT title,target_amount,priority,status FROM wishlist WHERE user_id=? ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'unlocked' THEN 1 ELSE 2 END,priority,id",(user,)).fetchall()
                        entries=sum(conn.execute(f'SELECT COUNT(*) FROM {t} WHERE user_id=?',(user,)).fetchone()[0] for t in ['attendance','habit_checkin'])
                        sources=sum(conn.execute(f'SELECT COUNT(*) FROM {t} WHERE user_id=?',(user,)).fetchone()[0] for t in ['income','habit_task'])
                        source_rows=[];entry_rows=[]
                        for kind,table,amount_col,check_table,foreign,earned in [('attendance','income','daily_amount','attendance','income_id','earned_amount'),('habit','habit_task','reward_amount','habit_checkin','task_id','reward_amount')]:
                            aliases={value[1]:alias for alias,value in ids.items() if value[0]==kind}
                            for row in conn.execute(f'SELECT id,title,{amount_col} FROM {table} WHERE user_id=?',(user,)):
                                source_rows.append([aliases[row[0]],row[1],kind,round(row[2]*100)])
                            for row in conn.execute(f'SELECT c.{foreign},c.date,s.title,c.{earned} FROM {check_table} c JOIN {table} s ON s.id=c.{foreign} WHERE c.user_id=?',(user,)):
                                entry_rows.append([aliases[row[0]],row[1],row[2],kind,round(row[3]*100)])
                    trend=[[r['date'],round(r['amount']*100),round(r['cumulative']*100)] for r in db.daily_totals(user)]
                    return {'summary':{k:round(v*100) for k,v in db.pool_summary(user).items()},'trend':trend,'wishes':[[r[0],round(r[1]*100),r[2],r[3]] for r in wishes],'entries':entries,'sources':sources,'sourceRows':sorted(source_rows),'entryRows':sorted(entry_rows)}
                for i,(op,observed) in enumerate(zip(operations,actual)):
                    accepted=True
                    try:run(op)
                    except (db.WishFlowError,ValueError):accepted=False
                    with self.subTest(step=i,operation=op):
                        self.assertEqual(observed['accepted'],accepted,'SQLite and browser disagree on whether to accept the operation')
                        self.assertEqual(observed['profiles'],{u:snapshot(u) for u in users})
            finally:db.DB_PATH=original
    def test_exact_balance_decimal_boundary(self):
        self.compare([
            {'type':'source','user':'甲','id':'a','title':'投入','kind':'attendance','amount':'0.10'},
            {'type':'source','user':'甲','id':'b','title':'习惯','kind':'habit','amount':'0.70'},
            {'type':'checkin','user':'甲','id':'a','day':'2026-09-22'},
            {'type':'checkin','user':'甲','id':'b','day':'2026-09-22'},
            {'type':'wish','user':'甲','id':'w','title':'刚好够预算','amount':'0.80','priority':1},
            {'type':'advance','user':'甲','id':'w'}])
    def test_input_boundaries_use_the_same_contract(self):
        self.compare([
            {'type':'source','user':'甲','id':'too_precise','title':'小数边界','kind':'habit','amount':'0.001'},
            {'type':'source','user':'甲','id':'too_large','title':'金额上限','kind':'attendance','amount':'100000001'},
            {'type':'wish','user':'甲','id':'fractional','title':'非整数优先级','amount':'1.00','priority':1.5},
            {'type':'wish','user':'甲','id':'integer_float','title':'整数优先级','amount':'1.00','priority':1.0},
            {'type':'wish','user':'甲','id':'overflow','title':'过大优先级','amount':'1.00','priority':9007199254740992},
            {'type':'source','user':'甲','id':'long','title':'长'*81,'kind':'habit','amount':'1.00'}])

    def test_seeded_operation_sequences(self):
        rng=random.Random(7821);ops=[];sources=[];wishes=[]
        for user in ['甲','乙']:
            for i in range(4):
                id_=user+'s'+str(i);sources.append(id_);ops.append({'type':'source','user':user,'id':id_,'title':'行动'+str(i),'kind':'attendance' if i%2 else 'habit','amount':['0.10','0.29','0.70','20.29'][i]})
            for i in range(6):
                id_=user+'w'+str(i);wishes.append(id_);ops.append({'type':'wish','user':user,'id':id_,'title':'心愿'+str(i),'amount':['0.30','0.80','1.10','10.00','20.29','500.00'][i],'priority':1+i%3})
        for _ in range(160):
            user=rng.choice(['甲','乙'])
            if rng.random()<.6:ops.append({'type':'checkin','user':user,'id':rng.choice(sources+['missing']),'day':f'2026-09-{rng.randrange(1,25):02}'})
            else:ops.append({'type':'advance','user':user,'id':rng.choice(wishes+['missing'])})
        ops.extend([{'type':'checkin','user':'甲','id':'甲s1','day':'2099-01-01'},{'type':'checkin','user':'甲','id':'甲s1','day':'2026-02-30'}])
        self.compare(ops)
