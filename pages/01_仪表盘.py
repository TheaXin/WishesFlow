from html import escape

import pandas as pd
import streamlit as st

from db.db import connection, pool_summary
from ui import apply_theme, intro, sidebar

apply_theme()
if not st.session_state.get("user_id"):
    st.switch_page("home.py")
user_id = st.session_state.user_id
sidebar(user_id)
summary = pool_summary(user_id)

intro("仪表盘", "把每一次完成，留成一条正在向前的线。")
a, b, c, d = st.columns(4)
a.metric("可用心愿金", f"¥ {summary['balance']:,.0f}")
b.metric("考勤累计", f"¥ {summary['attendance']:,.0f}")
c.metric("习惯累计", f"¥ {summary['habits']:,.0f}")
d.metric("已为心愿预留", f"¥ {summary['reserved']:,.0f}")

with connection() as conn:
    trend = pd.read_sql_query("""
        SELECT date AS 日期, SUM(amount) AS 当日累计 FROM (
          SELECT date, earned_amount AS amount FROM attendance WHERE user_id = ?
          UNION ALL SELECT date, reward_amount FROM habit_checkin WHERE user_id = ?
        ) GROUP BY date ORDER BY date
    """, conn, params=(user_id, user_id))
    wishes = pd.read_sql_query("""
        SELECT title AS 心愿, target_amount AS 目标, status AS 状态, priority AS 优先级
        FROM wishlist WHERE user_id = ? ORDER BY status, priority, id
    """, conn, params=(user_id,))

left, right = st.columns([1.25, 1])
with left:
    st.subheader("行动积累趋势")
    if trend.empty:
        st.info("完成一次考勤或习惯打卡后，这里会出现趋势。")
    else:
        trend["累计心愿金"] = trend["当日累计"].cumsum()
        st.line_chart(trend.set_index("日期")[["累计心愿金"]], color="#7895d4")
with right:
    st.subheader("我的心愿")
    if wishes.empty:
        st.info("去「心愿单」写下第一个想实现的目标。")
    else:
        labels = {"active": "积累中", "unlocked": "已解锁", "completed": "已完成"}
        for _, wish in wishes.iterrows():
            progress = min(summary["balance"] / wish["目标"], 1.0) if wish["状态"] == "active" else 1.0
            st.write(f"**{escape(wish['心愿'])}** · ¥{wish['目标']:,.0f} · {labels[wish['状态']]}")
            st.progress(progress)
