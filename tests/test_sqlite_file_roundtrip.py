"""A real Python SQLite file must survive browser SQLite read/write and return to Python."""
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path
from db import db
ROOT=Path(__file__).resolve().parents[1]

class SQLiteFileRoundTripTest(unittest.TestCase):
    def test_native_wasm_native_file_roundtrip(self):
        node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
        original=db.DB_PATH
        with tempfile.TemporaryDirectory() as folder:
            native=Path(folder)/'native.sqlite3';browser=Path(folder)/'browser.sqlite3';back=Path(folder)/'back.sqlite3'
            try:
                db.DB_PATH=native;db.init_db();db.add_income('甲','本地投入',0.10);db.add_habit('甲','本地习惯',0.70)
                with db.connection() as con:
                    income=con.execute('SELECT id FROM income').fetchone()[0];habit=con.execute('SELECT id FROM habit_task').fetchone()[0]
                db.record_attendance('甲',income,date(2026,9,22));db.record_habit_checkin('甲',habit,date(2026,9,22));db.add_wish('甲','恰好够用',0.80,1)
                def run(source,target,mode):return json.loads(subprocess.check_output([node,str(ROOT/'tests/sqlite_file_roundtrip.cjs'),str(source),str(target),mode],timeout=30))
                result=run(native,browser,'mutate');self.assertEqual(result['before']['totals']['balance'],80);self.assertEqual(result['after']['a']['balance'],0);self.assertEqual(result['after']['b']['balance'],2029)
                db.DB_PATH=browser
                with db.connection() as con:
                    self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])
                    w=con.execute('SELECT status,unlocked_at FROM wishlist').fetchone();self.assertEqual(w[0],'completed');self.assertTrue(w[1])
                    source=con.execute("SELECT id FROM income WHERE user_id='乙'").fetchone()[0]
                self.assertEqual(db.pool_summary('甲')['reserved'],0.80);self.assertEqual(db.pool_summary('乙')['balance'],20.29)
                db.record_attendance('乙',source,date(2026,9,24));result=run(browser,back,'inspect');self.assertEqual(result['after']['b']['balance'],4058)
                self.assertEqual(result['before']['a']['sources'][0]['title'],'本地投入');self.assertEqual(result['before']['a']['wishes'][0]['status'],'completed')
            finally:db.DB_PATH=original
