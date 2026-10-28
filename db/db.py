from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

DB_PATH = Path(__file__).with_name("wishflow.sqlite3")


class WishFlowError(ValueError):
    """Raised when an operation cannot be applied to a user's data."""


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create or safely upgrade the local database without deleting user data."""
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                daily_amount REAL NOT NULL CHECK(daily_amount >= 0),
                user_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                income_id INTEGER NOT NULL REFERENCES income(id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                earned_amount REAL NOT NULL CHECK(earned_amount >= 0),
                user_id TEXT NOT NULL,
                UNIQUE(income_id, date, user_id)
            );
            CREATE TABLE IF NOT EXISTS habit_task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                reward_amount REAL NOT NULL CHECK(reward_amount >= 0),
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                user_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS habit_checkin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL REFERENCES habit_task(id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                reward_amount REAL NOT NULL CHECK(reward_amount >= 0),
                user_id TEXT NOT NULL,
                UNIQUE(task_id, date, user_id)
            );
            CREATE TABLE IF NOT EXISTS wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target_amount REAL NOT NULL CHECK(target_amount > 0),
                priority INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'unlocked', 'completed')),
                unlocked_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_habit_checkin_user_date ON habit_checkin(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_wishlist_user_status ON wishlist(user_id, status);
            """
        )


def _decimal_amount(value) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise WishFlowError("记录中的金额格式不正确。") from error
    if not number.is_finite():
        raise WishFlowError("记录中的金额必须是有限数值。")
    return number


def _pool_totals(conn, user_id: str) -> dict[str, Decimal]:
    def total(query):
        return sum((_decimal_amount(row[0]) for row in conn.execute(query, (user_id,))), Decimal(0))
    earned = total("SELECT earned_amount FROM attendance WHERE user_id = ?")
    habits = total("SELECT reward_amount FROM habit_checkin WHERE user_id = ?")
    reserved = total("SELECT target_amount FROM wishlist WHERE user_id = ? AND status IN ('unlocked', 'completed')")
    return {"balance": earned + habits - reserved, "attendance": earned, "habits": habits, "reserved": reserved}


def pool_summary(user_id: str) -> dict[str, float]:
    with connection() as conn:
        return {key: float(value) for key, value in _pool_totals(conn, user_id).items()}


def daily_totals(user_id: str) -> list[dict]:
    """Use decimal arithmetic for daily and cumulative totals, without rewriting stored rows."""
    with connection() as conn:
        rows = conn.execute("""SELECT date, earned_amount FROM attendance WHERE user_id = ?
            UNION ALL SELECT date, reward_amount FROM habit_checkin WHERE user_id = ?""", (user_id, user_id)).fetchall()
    days = {}
    for row in rows:
        days[row[0]] = days.get(row[0], Decimal(0)) + _decimal_amount(row[1])
    cumulative = Decimal(0)
    result = []
    for day, amount in sorted(days.items()):
        cumulative += amount
        result.append({"date": day, "amount": float(amount), "cumulative": float(cumulative)})
    return result


def _validate_checkin_date(when: date) -> None:
    if type(when) is not date or when > date.today():
        raise WishFlowError("请选择今天或之前的有效日期。")


def add_income(user_id: str, title: str, amount: float) -> None:
    _validate_title(title, "收入来源")
    _validate_amount(amount, "金额")
    with connection() as conn:
        conn.execute("INSERT INTO income(title, daily_amount, user_id) VALUES (?, ?, ?)", (title.strip(), amount, user_id))


def record_attendance(user_id: str, income_id: int, checkin_date: date) -> float:
    _validate_checkin_date(checkin_date)
    with connection() as conn:
        income = conn.execute(
            "SELECT daily_amount FROM income WHERE id = ? AND user_id = ?", (income_id, user_id)
        ).fetchone()
        if income is None:
            raise WishFlowError("找不到这项收入来源。")
        try:
            conn.execute(
                "INSERT INTO attendance(income_id, date, earned_amount, user_id) VALUES (?, ?, ?, ?)",
                (income_id, checkin_date.isoformat(), income["daily_amount"], user_id),
            )
        except sqlite3.IntegrityError as error:
            raise WishFlowError("这项来源在该日期已经打过卡了。") from error
    return float(income["daily_amount"])


def add_habit(user_id: str, title: str, reward: float) -> None:
    _validate_title(title, "习惯名称")
    _validate_amount(reward, "奖励")
    with connection() as conn:
        conn.execute("INSERT INTO habit_task(title, reward_amount, user_id) VALUES (?, ?, ?)", (title.strip(), reward, user_id))


def record_habit_checkin(user_id: str, task_id: int, checkin_date: date) -> float:
    _validate_checkin_date(checkin_date)
    with connection() as conn:
        habit = conn.execute(
            "SELECT reward_amount FROM habit_task WHERE id = ? AND user_id = ? AND active = 1", (task_id, user_id)
        ).fetchone()
        if habit is None:
            raise WishFlowError("找不到这个可用习惯。")
        try:
            conn.execute(
                "INSERT INTO habit_checkin(task_id, date, reward_amount, user_id) VALUES (?, ?, ?, ?)",
                (task_id, checkin_date.isoformat(), habit["reward_amount"], user_id),
            )
        except sqlite3.IntegrityError as error:
            raise WishFlowError("该习惯当天已完成。") from error
    return float(habit["reward_amount"])


def add_wish(user_id: str, title: str, target: float, priority: int) -> None:
    _validate_title(title, "心愿名称")
    _validate_amount(target, "目标金额")
    priority_value = _decimal_amount(priority)
    if isinstance(priority, bool) or priority_value < 1 or priority_value > 9007199254740991 or priority_value != priority_value.to_integral_value():
        raise WishFlowError("优先级必须是有效的正整数。")
    priority = int(priority_value)
    with connection() as conn:
        conn.execute(
            "INSERT INTO wishlist(title, target_amount, priority, user_id) VALUES (?, ?, ?, ?)",
            (title.strip(), target, priority, user_id),
        )


def unlock_wish(user_id: str, wish_id: int) -> None:
    with connection() as conn:
        wish = conn.execute(
            "SELECT target_amount, status FROM wishlist WHERE id = ? AND user_id = ?", (wish_id, user_id)
        ).fetchone()
        if wish is None or wish["status"] != "active":
            raise WishFlowError("这个心愿当前无法解锁。")
        if _pool_totals(conn, user_id)["balance"] < _decimal_amount(wish["target_amount"]):
            raise WishFlowError("可用心愿金不足，暂时还不能解锁。")
        conn.execute(
            "UPDATE wishlist SET status = 'unlocked', unlocked_at = ? WHERE id = ? AND user_id = ?",
            (datetime.now().isoformat(timespec="seconds"), wish_id, user_id),
        )


def complete_wish(user_id: str, wish_id: int) -> None:
    with connection() as conn:
        result = conn.execute(
            "UPDATE wishlist SET status = 'completed' WHERE id = ? AND user_id = ? AND status = 'unlocked'",
            (wish_id, user_id),
        )
        if result.rowcount != 1:
            raise WishFlowError("这个心愿当前无法标记为已实现。")


def _validate_title(title: str, label: str) -> None:
    if not title or not title.strip():
        raise WishFlowError(f"请填写{label}。")
    if len(title.strip()) > 80:
        raise WishFlowError(f"{label}不能超过 80 个字符。")


def _validate_amount(amount: float, label: str) -> None:
    number = _decimal_amount(amount)
    if isinstance(amount, bool) or number <= 0 or number > Decimal("100000000") or number * 100 != (number * 100).to_integral_value():
        raise WishFlowError(f"{label}需大于 0，最多两位小数，且不超过一亿元。")
