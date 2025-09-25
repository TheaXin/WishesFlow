import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite3")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_rebuild=False):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = OFF;")
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    for (table_name,) in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    conn.commit()

    # 建表，所有表都带 user_id
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            daily_amount REAL NOT NULL,
            user_id TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            income_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            earned_amount REAL NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY(income_id) REFERENCES income(id)
        );

        CREATE TABLE IF NOT EXISTS habit_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            reward_amount REAL NOT NULL,
            user_id TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS habit_checkin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            reward_amount REAL NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY(task_id) REFERENCES habit_task(id)
        );

        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            priority INTEGER DEFAULT 0,
            status INTEGER DEFAULT 0,
            unlocked_at TEXT,
            user_id TEXT NOT NULL
        );
        """
    )

    conn.commit()
    conn.close()

# Income


def add_income(title, daily_amount, user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO income (title, daily_amount, user_id) VALUES (?, ?, ?)",
                  (title, daily_amount, user_id))
        conn.commit()
    except Exception as e:
        print(f"Error in add_income: {e}")
        conn.rollback()
    finally:
        conn.close()


def list_income(user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT id, title, daily_amount FROM income WHERE user_id = ? ORDER BY id DESC", (user_id,))
        rows = c.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error in list_income: {e}")
        return []
    finally:
        conn.close()

# Attendance


def add_attendance(income_id, date, earned_amount, user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO attendance (income_id, date, earned_amount, user_id) VALUES (?, ?, ?, ?)",
            (income_id, date, earned_amount, user_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error in add_attendance: {e}")
        conn.rollback()
    finally:
        conn.close()


def sum_attendance(user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT SUM(earned_amount) FROM attendance WHERE user_id = ?", (user_id,))
        result = c.fetchone()[0]
        return result or 0
    except Exception as e:
        print(f"Error in sum_attendance: {e}")
        return 0
    finally:
        conn.close()

# Habits


def add_habit_task(title, reward_amount, user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO habit_task (title, reward_amount, user_id) VALUES (?, ?, ?)",
                  (title, reward_amount, user_id))
        conn.commit()
    except Exception as e:
        print(f"Error in add_habit_task: {e}")
        conn.rollback()
    finally:
        conn.close()


def list_habit_tasks(user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT id, title, reward_amount FROM habit_task WHERE user_id = ? ORDER BY id DESC", (user_id,))
        rows = c.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error in list_habit_tasks: {e}")
        return []
    finally:
        conn.close()


def add_habit_checkin(task_id, date, reward_amount, user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO habit_checkin (task_id, date, reward_amount, user_id) VALUES (?, ?, ?, ?)",
            (task_id, date, reward_amount, user_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error in add_habit_checkin: {e}")
        conn.rollback()
    finally:
        conn.close()


def sum_habits(user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT SUM(reward_amount) FROM habit_checkin WHERE user_id = ?", (user_id,))
        result = c.fetchone()[0]
        return result or 0
    except Exception as e:
        print(f"Error in sum_habits: {e}")
        return 0
    finally:
        conn.close()

# Wishes


def add_wish(title, target_amount, priority, user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO wishlist (title, target_amount, priority, status, user_id) VALUES (?, ?, ?, 0, ?)",
                  (title, target_amount, priority, user_id))
        conn.commit()
    except Exception as e:
        print(f"Error in add_wish: {e}")
        conn.rollback()
    finally:
        conn.close()


def list_wishes(user_id, include_completed=True):
    try:
        conn = get_conn()
        c = conn.cursor()
        if include_completed:
            c.execute(
                "SELECT id, title, target_amount, priority, status FROM wishlist WHERE user_id = ? ORDER BY status ASC, priority ASC, id DESC", (user_id,))
        else:
            c.execute(
                "SELECT id, title, target_amount, priority, status FROM wishlist WHERE user_id = ? AND status=0 ORDER BY status ASC, priority ASC, id DESC", (user_id,))
        rows = c.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error in list_wishes: {e}")
        return []
    finally:
        conn.close()


def unlock_wish(wish_id, user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE wishlist SET status=1, unlocked_at=? WHERE id=? AND user_id=? AND status=0",
            (datetime.now().isoformat(), wish_id, user_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error in unlock_wish: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_pool_balance(user_id):
    try:
        attendance_total = sum_attendance(user_id)
        habits_total = sum_habits(user_id)
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT SUM(target_amount) FROM wishlist WHERE status=1 AND user_id=?", (user_id,))
        used = c.fetchone()[0] or 0
        return attendance_total + habits_total - used
    except Exception as e:
        print(f"Error in get_pool_balance: {e}")
        return 0
    finally:
        conn.close()


def greedy_unlock(user_id):
    """
    Unlock as many wishes as possible with current pool balance (highest priority first).
    Returns list of wish ids unlocked.
    """
    try:
        balance = get_pool_balance(user_id)
        wishes = list_wishes(user_id, include_completed=False)
        unlocked_ids = []
        wishes_sorted = sorted(wishes, key=lambda w: w['priority'])
        for wish in wishes_sorted:
            if wish['target_amount'] <= balance:
                unlock_wish(wish['id'], user_id)
                unlocked_ids.append(wish['id'])
                balance -= wish['target_amount']
            else:
                break
        return unlocked_ids
    except Exception as e:
        print(f"Error in greedy_unlock: {e}")
        return []
