import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite3")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db(force_rebuild=False):
    conn = get_conn()
    cursor = conn.cursor()

    # 如果 force_rebuild=True，则直接删掉所有表再重建
    if force_rebuild:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()
        for (table_name,) in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()

    # 尝试逐个执行 schema.sql 里的建表语句
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)

    conn.commit()
    conn.close()

# Income


def add_income(title, daily_amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO income (title, daily_amount) VALUES (?, ?)",
              (title, daily_amount))
    conn.commit()
    conn.close()


def list_income():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, title, daily_amount FROM income ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(zip(['id', 'title', 'daily_amount'], row)) for row in rows]

# Attendance


def add_attendance(income_id, date, earned_amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO attendance (income_id, date, earned_amount) VALUES (?, ?, ?)",
        (income_id, date, earned_amount)
    )
    conn.commit()
    conn.close()


def sum_attendance():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT SUM(earned_amount) FROM attendance")
    result = c.fetchone()[0]
    conn.close()
    return result or 0

# Habits


def add_habit_task(title, reward_amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO habit_task (title, reward_amount) VALUES (?, ?)",
              (title, reward_amount))
    conn.commit()
    conn.close()


def list_habit_tasks():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, title, reward_amount FROM habit_task ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(zip(['id', 'title', 'reward_amount'], row)) for row in rows]


def add_habit_checkin(task_id, date, reward_amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO habit_checkin (task_id, date, reward_amount) VALUES (?, ?, ?)",
        (task_id, date, reward_amount)
    )
    conn.commit()
    conn.close()


def sum_habits():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT SUM(reward_amount) FROM habit_checkin")
    result = c.fetchone()[0]
    conn.close()
    return result or 0

# Wishes


def add_wish(title, target_amount, priority):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO wishlist (title, target_amount, priority, unlocked) VALUES (?, ?, ?, 0)",
              (title, target_amount, priority))
    conn.commit()
    conn.close()


def list_wishes(include_unlocked=True):
    conn = get_conn()
    c = conn.cursor()
    if include_unlocked:
        c.execute(
            "SELECT id, title, target_amount, priority, unlocked FROM wishlist ORDER BY unlocked, priority")
    else:
        c.execute(
            "SELECT id, title, target_amount, priority, unlocked FROM wishlist WHERE unlocked=0 ORDER BY priority")
    rows = c.fetchall()
    conn.close()
    return [dict(zip(['id', 'title', 'target_amount', 'priority', 'unlocked'], row)) for row in rows]


def unlock_wish(wish_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE wishlist SET unlocked=1, unlocked_at=? WHERE id=? AND unlocked=0",
        (datetime.now(), wish_id)
    )
    conn.commit()
    conn.close()


def get_pool_balance():
    attendance_total = sum_attendance()
    habits_total = sum_habits()
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT SUM(target_amount) FROM wishlist WHERE unlocked=1")
    used = c.fetchone()[0] or 0
    conn.close()
    return attendance_total + habits_total - used


def greedy_unlock():
    """
    Unlock as many wishes as possible with current pool balance (highest priority first).
    Returns list of wish ids unlocked.
    """
    balance = get_pool_balance()
    wishes = list_wishes(include_unlocked=False)
    unlocked_ids = []
    wishes_sorted = sorted(wishes, key=lambda w: w['priority'])
    for wish in wishes_sorted:
        if wish['target_amount'] <= balance:
            unlock_wish(wish['id'])
            unlocked_ids.append(wish['id'])
            balance -= wish['target_amount']
        else:
            break
    return unlocked_ids
