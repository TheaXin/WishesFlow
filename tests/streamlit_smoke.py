"""Native Streamlit page acceptance against an isolated real SQLite database."""
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from db import db
class StreamlitSQLiteAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Isolate test configuration from the user's local .streamlit/config.toml.
        cls.original_cwd=Path.cwd();cls.config_folder=tempfile.TemporaryDirectory();os.chdir(cls.config_folder.name)
    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.original_cwd);cls.config_folder.cleanup()
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.original=db.DB_PATH;db.DB_PATH=Path(self.folder.name)/'ui.sqlite3';db.init_db();self.user='本地验收'
    def tearDown(self):
        db.DB_PATH=self.original;self.folder.cleanup()
    def page(self,file):
        app=AppTest.from_file(str(ROOT/file),default_timeout=15);app.session_state['user_id']=self.user;app.run();self.assertEqual(len(app.exception),0);return app
    def click(self,app,label):
        next(b for b in app.button if b.label==label).click().run();self.assertEqual(len(app.exception),0)
    def test_duplicate_income_sources_stay_selectable_and_cents_can_be_entered(self):
        db.add_income(self.user,'同名来源',0.10);db.add_income(self.user,'同名来源',0.10)
        app=self.page('pages/02_考勤打卡.py');self.assertEqual(len(app.selectbox[0].options),2)
        app.date_input[0].set_value(date(2026,9,23));self.click(app,'完成考勤打卡');self.assertEqual(db.pool_summary(self.user)['balance'],0.10)
        app.text_input[0].set_value('分单位来源');app.number_input[0].set_value(0.01);self.click(app,'保存来源')
        with db.connection() as conn:self.assertEqual(conn.execute('SELECT COUNT(*) FROM income').fetchone()[0],3)
    def test_native_dashboard_and_wish_flow_use_exact_cent_amounts(self):
        db.add_income(self.user,'投入',0.10);db.add_habit(self.user,'习惯',0.70)
        with db.connection() as conn:
            income=conn.execute('SELECT id FROM income').fetchone()[0];habit=conn.execute('SELECT id FROM habit_task').fetchone()[0]
        db.record_attendance(self.user,income,date(2026,9,23));db.record_habit_checkin(self.user,habit,date(2026,9,23));db.add_wish(self.user,'刚好够用',0.80,1)
        dashboard=self.page('pages/01_仪表盘.py');self.assertEqual(dashboard.metric[0].value.replace(' ',''),'¥0.80')
        wishes=self.page('pages/04_心愿单.py');self.click(wishes,'解锁这个心愿');self.click(wishes,'标记为已实现 ✦')
        self.assertEqual(db.pool_summary(self.user)['balance'],0.0);self.assertEqual(db.daily_totals(self.user),[{'date':'2026-09-23','amount':0.80,'cumulative':0.80}])
if __name__=='__main__':unittest.main(verbosity=2)
