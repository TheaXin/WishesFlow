-- ================================
-- 心愿Flow 数据库表结构
-- ================================

-- 收入来源表（仅作为考勤的配置数据）
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,          -- 收入来源名称，如“基本工资”
    daily_amount REAL NOT NULL,   -- 每日应计金额
    note TEXT
);

-- 考勤打卡表（每次打卡就往资金池增加一笔虚拟收入）
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    income_id INTEGER NOT NULL,   -- 对应收入来源
    date TEXT NOT NULL,           -- 打卡日期 YYYY-MM-DD
    earned_amount REAL NOT NULL,  -- 实际获得金额
    note TEXT,
    FOREIGN KEY (income_id) REFERENCES income(id)
);

-- 习惯任务表（用户定义的习惯，如健身、背单词）
CREATE TABLE IF NOT EXISTS habit_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,          -- 习惯名称
    reward_amount REAL NOT NULL,  -- 每次完成奖励金额
    note TEXT
);

-- 习惯打卡表（完成一次习惯任务，就记录一次奖励）
CREATE TABLE IF NOT EXISTS habit_checkin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,     -- 对应习惯任务
    date TEXT NOT NULL,           -- 打卡日期 YYYY-MM-DD
    reward_amount REAL NOT NULL,  -- 实际奖励金额
    note TEXT,
    FOREIGN KEY (task_id) REFERENCES habit_task(id)
);

-- 心愿单表（最终目标，靠资金池解锁）
CREATE TABLE IF NOT EXISTS wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,          -- 心愿名称，如“新电脑”
    target_amount REAL NOT NULL,  -- 解锁所需金额
    priority INTEGER NOT NULL DEFAULT 0, -- 优先级，数字越小越优先
    unlocked INTEGER NOT NULL DEFAULT 0, -- 0 未解锁，1 已解锁
    unlocked_at TEXT              -- 解锁时间
);

-- -------------------------------
-- 视图：资金池流入明细（方便统计和可视化）
-- -------------------------------
CREATE VIEW IF NOT EXISTS v_pool_inflows AS
SELECT
    date AS occurs_on,
    'attendance' AS source_kind,
    earned_amount AS amount
FROM attendance
UNION ALL
SELECT
    date AS occurs_on,
    'habit' AS source_kind,
    reward_amount AS amount
FROM habit_checkin;