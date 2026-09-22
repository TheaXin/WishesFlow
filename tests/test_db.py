"""Core accounting and data-integrity tests for WishFlow."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from db import db


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_path = db.DB_PATH
        db.DB_PATH = Path(self.tempdir.name) / "test.sqlite3"
        db.init_db()
        self.user = "tester"

    def tearDown(self):
        db.DB_PATH = self.original_path
        self.tempdir.cleanup()

    def test_completed_wish_remains_deducted_from_available_balance(self):
        db.add_income(self.user, "工作", 100)
        with db.connection() as conn:
            income_id = conn.execute("SELECT id FROM income").fetchone()[0]
        db.record_attendance(self.user, income_id, date(2026, 9, 23))
        db.add_wish(self.user, "书", 80, 1)
        with db.connection() as conn:
            wish_id = conn.execute("SELECT id FROM wishlist").fetchone()[0]
        db.unlock_wish(self.user, wish_id)
        db.complete_wish(self.user, wish_id)

        summary = db.pool_summary(self.user)
        self.assertEqual(summary["balance"], 20)
        self.assertEqual(summary["reserved"], 80)

    def test_a_checkin_cannot_be_recorded_twice_on_the_same_day(self):
        db.add_habit(self.user, "阅读", 10)
        with db.connection() as conn:
            habit_id = conn.execute("SELECT id FROM habit_task").fetchone()[0]
        db.record_habit_checkin(self.user, habit_id, date(2026, 9, 23))

        with self.assertRaisesRegex(db.WishFlowError, "已完成"):
            db.record_habit_checkin(self.user, habit_id, date(2026, 9, 23))

    def test_wish_cannot_be_unlocked_without_sufficient_funds(self):
        db.add_wish(self.user, "旅行", 200, 1)
        with db.connection() as conn:
            wish_id = conn.execute("SELECT id FROM wishlist").fetchone()[0]

        with self.assertRaisesRegex(db.WishFlowError, "不足"):
            db.unlock_wish(self.user, wish_id)


if __name__ == "__main__":
    unittest.main()
