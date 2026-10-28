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
