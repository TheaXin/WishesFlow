from datetime import date
from html import escape

import streamlit as st
from db.db import WishFlowError, add_habit, connection, record_habit_checkin
from ui import apply_theme, intro, sidebar

apply_theme()
if not st.session_state.get("user_id"): st.switch_page("home.py")
user_id = st.session_state.user_id
sidebar(user_id)
intro("习惯打卡", "把微小而重复的选择，变成可积累的奖励。")

with st.expander("＋ 新增习惯", expanded=False):
    with st.form("new_habit", clear_on_submit=True):
        title = st.text_input("习惯名称", placeholder="例如：阅读 20 分钟")
        reward = st.number_input("完成奖励", min_value=1.0, step=1.0)
        if st.form_submit_button("保存习惯", type="primary"):
            try:
                add_habit(user_id, title, reward)
                st.rerun()
            except WishFlowError as error:
                st.error(str(error))
when = st.date_input("选择日期", value=date.today(), max_value=date.today())
with connection() as conn:
    habits = conn.execute("SELECT id, title, reward_amount FROM habit_task WHERE user_id=? AND active=1 ORDER BY id DESC", (user_id,)).fetchall()
if not habits:
    st.info("添加第一个习惯，让今天有一个小小的完成感。")
for item in habits:
    left, right = st.columns([4, 1])
    left.markdown(f"**{escape(item['title'])}**  \\n完成一次，获得 ¥{item['reward_amount']:,.0f}")
    if right.button("完成", key=f"habit-{item['id']}", use_container_width=True):
        try:
            record_habit_checkin(user_id, item['id'], when)
            st.success(f"已记录「{item['title']}」。")
        except WishFlowError as error:
            st.caption(str(error))
