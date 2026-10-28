"""The exact same fixture also runs against browser core.js in browser_parity.test.cjs."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from db import db

FIXTURE = json.loads((Path(__file__).parent / 'fixtures/accounting.json').read_text())

class AccountingParityTest(unittest.TestCase):
    def test_shared_business_contract(self):
        original = db.DB_PATH
        with tempfile.TemporaryDirectory() as folder:
            db.DB_PATH = Path(folder) / 'parity.sqlite3'
            try:
                db.init_db()
                ids = {}
                def run(op):
                    user, key = op['user'], op['id']
                    if op['type'] == 'source':
                        fn = db.add_income if op['kind'] == 'attendance' else db.add_habit
                        fn(user, op['title'], float(op['amount']))
                        table = 'income' if op['kind'] == 'attendance' else 'habit_task'
                        with db.connection() as conn:
                            ids[key] = (op['kind'], conn.execute(f'SELECT MAX(id) FROM {table}').fetchone()[0])
                    elif op['type'] == 'wish':
                        db.add_wish(user, op['title'], float(op['amount']), op['priority'])
                        with db.connection() as conn:
                            ids[key] = ('wish', conn.execute('SELECT MAX(id) FROM wishlist').fetchone()[0])
                    elif op['type'] == 'checkin':
                        kind, id_ = ids[key]
                        fn = db.record_attendance if kind == 'attendance' else db.record_habit_checkin
                        fn(user, id_, date.fromisoformat(op['day']))
                    elif op['type'] == 'advance':
                        id_ = ids[key][1]
                        with db.connection() as conn:
                            status = conn.execute('SELECT status FROM wishlist WHERE id=? AND user_id=?', (id_, user)).fetchone()
                        if status and status[0] == 'unlocked': db.complete_wish(user, id_)
                        else: db.unlock_wish(user, id_)
                for op in FIXTURE['operations']:
                    with self.subTest(op=op):
                        if op.get('error'):
                            with self.assertRaises(db.WishFlowError): run(op)
                        else: run(op)
                for user, expected in FIXTURE['expected'].items():
                    self.assertEqual({k: round(v * 100) for k, v in db.pool_summary(user).items()}, {k: expected[k] for k in ('attendance', 'habits', 'reserved', 'balance')})
                    with db.connection() as conn:
                        daily = conn.execute('SELECT date,SUM(amount) FROM (SELECT date,earned_amount AS amount FROM attendance WHERE user_id=? UNION ALL SELECT date,reward_amount FROM habit_checkin WHERE user_id=?) GROUP BY date ORDER BY date', (user,user)).fetchall()
                        states = conn.execute('SELECT status FROM wishlist WHERE user_id=? ORDER BY id', (user,)).fetchall()
                    total = 0; rows = []
                    for row in daily:
                        cents = round(row[1]*100); total += cents; rows.append([row[0],cents,total])
                    self.assertEqual(rows, expected['days'])
                    self.assertEqual([r[0] for r in states], expected['statuses'])
            finally:
                db.DB_PATH = original
