import math
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from db.db import get_conn, init_db

import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体，避免乱码
rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac 系统，保证字体存在
# rcParams['font.sans-serif'] = ['SimHei']     # Windows 系统
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

st.set_page_config(page_title="心愿Flow - 仪表盘", layout="wide")
st.title("🌊 心愿Flow 仪表盘")

# 登录/会话校验，避免未设置 user_id 时报错
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.info("请先在首页登录后再查看仪表盘。")
    st.stop()

# -------------------------------
# 获取资金池数据
# -------------------------------


def get_pool_data():
    """返回 (total_pool, attendance_sum, habit_sum)。\n    兼容旧库：如果列不存在会自动重建一次后重试。"""
    user_id = st.session_state["user_id"]

    def safe_sum(conn, sql, params=()):
        try:
            row = conn.execute(sql, params).fetchone()
            return (row[0] or 0) if row is not None else 0
        except sqlite3.OperationalError:
            # 可能是旧库结构；强制重建一次再重试
            init_db(force_rebuild=True)
            with get_conn() as c2:
                r2 = c2.execute(sql, params).fetchone()
                return (r2[0] or 0) if r2 is not None else 0

    conn = get_conn()
    attendance_sum = safe_sum(
        conn,
        "SELECT COALESCE(SUM(earned_amount), 0) FROM attendance WHERE user_id = ?",
        (user_id,),
    )
    habit_sum = safe_sum(
        conn,
        "SELECT COALESCE(SUM(reward_amount), 0) FROM habit_checkin WHERE user_id = ?",
        (user_id,),
    )
    used = safe_sum(
        conn,
        "SELECT COALESCE(SUM(target_amount), 0) FROM wishlist WHERE status = 1 AND user_id = ?",
        (user_id,),
    )
    conn.close()

    total = attendance_sum + habit_sum - used
    return total, attendance_sum, habit_sum


def get_wishlist():
    conn = get_conn()
    df = pd.read_sql(
        "SELECT * FROM wishlist WHERE user_id = ? ORDER BY status ASC, priority ASC, id DESC", conn, params=(st.session_state["user_id"],))
    conn.close()
    # 兼容旧库：若没有 status 列，则从旧的 unlocked 列推断；再不行则默认未解锁(0)
    if 'status' not in df.columns:
        if 'unlocked' in df.columns:
            # 将 unlocked 布尔/0-1 映射为 0/1 的 status（0=未解锁，1=已解锁）
            df['status'] = df['unlocked'].apply(lambda v: 1 if bool(v) else 0)
        else:
            df['status'] = 0
    return df


def get_monthly_data():
    conn = get_conn()
    attendance_df = pd.read_sql(
        "SELECT strftime('%Y-%m', date) as month, COALESCE(SUM(earned_amount), 0) as attendance_amount FROM attendance WHERE user_id = ? GROUP BY month ORDER BY month", conn, params=(st.session_state["user_id"],))
    habit_df = pd.read_sql(
        "SELECT strftime('%Y-%m', date) as month, COALESCE(SUM(reward_amount), 0) as habit_amount FROM habit_checkin WHERE user_id = ? GROUP BY month ORDER BY month", conn, params=(st.session_state["user_id"],))
    conn.close()
    # Merge on month
    df = pd.merge(attendance_df, habit_df, on='month', how='outer').fillna(0)
    df['total'] = df['attendance_amount'] + df['habit_amount']
    df = df.sort_values('month')
    return df


# -------------------------------
# 资金池展示
# -------------------------------
total, attendance_sum, habit_sum = get_pool_data()

col1, col2, col3 = st.columns(3)
col1.metric("资金池余额（模拟累计）", f"¥ {total:,.0f}")
col2.metric("来自考勤", f"¥ {attendance_sum:,.0f}")
col3.metric("来自习惯打卡", f"¥ {habit_sum:,.0f}")

st.caption("提示：所有金额为模拟累计，仅用于激励习惯养成，不代表真实账户余额。")

# -------------------------------
# 饼图：资金来源占比（简化版）
# -------------------------------
st.subheader("心愿资金来源占比")
sources = ["考勤", "习惯打卡"]
values = [attendance_sum, habit_sum]
if sum(values) == 0 or any(math.isnan(v) for v in values):
    st.info("暂无数据，打卡后这里会显示资金来源占比。")
else:
    fig, ax = plt.subplots(figsize=(6, 6))
    colors = ["#A7C7E7", "#F4A7B9"]  # 低饱和度蓝、粉

    def make_autopct(values):
        def _fmt(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f"{pct:.1f}%\n(¥{val:,.0f})" if val > 0 else ""
        return _fmt

    wedges, _texts, autotexts = ax.pie(
        values,
        labels=None,                 # 不在扇区上放标签，减少重叠
        autopct=make_autopct(values),
        startangle=90,
        colors=colors,
        pctdistance=0.68,
        wedgeprops=dict(edgecolor='w', linewidth=1)
    )
    ax.axis("equal")
    ax.set_title("资金来源占比", fontsize=18)

    # 将来源与金额放到图例，避免文本重叠
    legend_labels = [f"{s} (¥{v:,.0f})" for s, v in zip(sources, values)]
    ax.legend(wedges, legend_labels, title="来源",
              loc="center left", bbox_to_anchor=(1, 0.5))

    plt.tight_layout()
    st.pyplot(fig)

# -------------------------------
# 高级可视化选项
# -------------------------------
with st.expander("查看习惯打卡资金详情"):
    conn = get_conn()
    query = """
        SELECT ht.title, COALESCE(SUM(hc.reward_amount), 0) as total_reward
        FROM habit_checkin hc
        JOIN habit_task ht ON hc.task_id = ht.id
        WHERE hc.user_id = ?
        GROUP BY ht.title
        HAVING total_reward > 0
        ORDER BY total_reward DESC
    """
    df_habit = pd.read_sql(query, conn, params=(st.session_state["user_id"],))
    conn.close()
    if not df_habit.empty:
        st.subheader("具体的习惯每日打卡心愿资金来源")
        fig2, ax2 = plt.subplots(figsize=(6, 6))
        labels = df_habit["title"].tolist()
        rewards = df_habit["total_reward"].tolist()
        pastel_colors = plt.cm.Pastel1.colors if len(
            labels) <= 9 else plt.cm.tab20.colors

        def make_autopct2(values):
            def my_autopct2(pct):
                total = sum(values)
                val = int(round(pct * total / 100.0))
                return "{:.1f}%\n(¥{:,.0f})".format(pct, val)
            return my_autopct2
        wedges2, texts2, autotexts2 = ax2.pie(
            rewards,
            labels=labels,
            autopct=make_autopct2(rewards),
            startangle=90,
            colors=pastel_colors,
            labeldistance=1.08,
            pctdistance=0.75,
            wedgeprops=dict(edgecolor='w', linewidth=1)
        )
        ax2.axis("equal")
        ax2.set_title("习惯打卡奖励分布", fontsize=14)
        plt.setp(texts2, size=13, weight="bold")
        plt.setp(autotexts2, size=12, color="dimgrey", weight="bold")
        plt.tight_layout()
        st.pyplot(fig2)

# -------------------------------
# 月度资金来源统计
# -------------------------------
st.subheader("月度资金来源统计")
monthly_df = get_monthly_data()
with st.expander("查看月度资金来源统计"):
    if monthly_df.empty:
        st.info("暂无月度数据。")
    else:
        monthly_df = monthly_df.drop_duplicates(subset=['month'])
        monthly_chart_df = monthly_df.set_index(
            'month')[['attendance_amount', 'habit_amount', 'total']]
        monthly_chart_df.columns = ['考勤', '习惯打卡', '总计']
        monthly_chart_df = monthly_chart_df.sort_index(ascending=True)

        st.line_chart(monthly_chart_df)

# -------------------------------
# 每日累计趋势
# -------------------------------
st.subheader("每日累计趋势")
with st.expander("查看每日累计趋势"):
    conn = get_conn()
    attendance_daily_df = pd.read_sql(
        "SELECT strftime('%Y-%m-%d', date) as day, COALESCE(SUM(earned_amount), 0) as attendance_amount FROM attendance WHERE user_id = ? GROUP BY day ORDER BY day", conn, params=(st.session_state["user_id"],))
    habit_daily_df = pd.read_sql(
        "SELECT strftime('%Y-%m-%d', date) as day, COALESCE(SUM(reward_amount), 0) as habit_amount FROM habit_checkin WHERE user_id = ? GROUP BY day ORDER BY day", conn, params=(st.session_state["user_id"],))
    conn.close()
    daily_df = pd.merge(attendance_daily_df, habit_daily_df,
                        on='day', how='outer').fillna(0)
    daily_df = daily_df.sort_values('day')
    daily_df['total'] = daily_df['attendance_amount'] + \
        daily_df['habit_amount']
    daily_df = daily_df.set_index('day')
    daily_df.index.name = '日期'
    daily_df = daily_df.sort_index(ascending=True)

    st.line_chart(daily_df[['attendance_amount', 'habit_amount', 'total']])

# -------------------------------
# 心愿单进度
# -------------------------------
st.subheader("心愿单进度")
wishlist = get_wishlist()

if wishlist.empty:
    st.info("还没有心愿，快去添加一个吧！")
else:
    unfinished = wishlist[wishlist['status'] == 0]
    unlocked = wishlist[wishlist['status'] == 1]
    finished = wishlist[wishlist['status'] == 2]

    st.markdown("### 未完成心愿")
    if unfinished.empty:
        st.info("暂无未完成的心愿。")
    else:
        remaining_balance = total
        for _, row in unfinished.iterrows():
            title = row["title"]
            target = row["target_amount"]
            progress = min(remaining_balance / target,
                           1.0) if target > 0 else 0
            st.write(f"**{title}** （目标：¥{target:,.0f}）")
            st.progress(progress)
            if remaining_balance >= target:
                st.info("即将解锁！")
                remaining_balance -= target
            else:
                st.caption(f"还差 ¥ {target - remaining_balance:,.0f}")

    st.markdown("### 已解锁心愿（待完成）")
    if unlocked.empty:
        st.info("暂无已解锁但未完成的心愿。")
    else:
        for _, row in unlocked.iterrows():
            title = row["title"]
            target = row["target_amount"]
            st.write(f"**{title}** （目标：¥{target:,.0f}）")
            st.progress(1.0)
            st.info("已解锁，等待完成！")

    st.markdown("### 已完成心愿")
    if finished.empty:
        st.info("暂无已完成的心愿。")
    else:
        for _, row in finished.iterrows():
            title = row["title"]
            target = row["target_amount"]
            st.success(f"✅ {title} 已完成！（目标：¥{target:,.0f}）")
