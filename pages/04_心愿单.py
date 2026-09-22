from html import escape
import streamlit as st
from db.db import WishFlowError, add_wish, complete_wish, connection, pool_summary, unlock_wish
from ui import apply_theme, intro, sidebar

apply_theme()
if not st.session_state.get("user_id"): st.switch_page("home.py")
user_id = st.session_state.user_id
sidebar(user_id)
funds = pool_summary(user_id)["balance"]
intro("心愿单", f"当前可用心愿金 ¥ {funds:,.0f}。先实现最想要的那个。")

with st.expander("＋ 写下一个新心愿", expanded=False):
    with st.form("new_wish", clear_on_submit=True):
        title = st.text_input("心愿名称", placeholder="例如：周末去海边")
        target = st.number_input("目标金额", min_value=1.0, step=100.0)
        priority = st.number_input("优先级（数字小的优先）", min_value=1, value=1)
        if st.form_submit_button("添加心愿", type="primary"):
            try:
                add_wish(user_id, title, target, priority)
                st.rerun()
            except WishFlowError as error:
                st.error(str(error))
with connection() as conn:
    wishes = conn.execute("SELECT * FROM wishlist WHERE user_id=? ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'unlocked' THEN 1 ELSE 2 END, priority, id", (user_id,)).fetchall()
if not wishes: st.info("还没有心愿。把想要的生活写下来，行动才有方向。")
for wish in wishes:
    progress = min(funds / wish['target_amount'], 1.0) if wish['status'] == 'active' else 1.0
    st.markdown(f"### {escape(wish['title'])}")
    st.caption(f"目标 ¥{wish['target_amount']:,.0f} · 优先级 {wish['priority']}")
    st.progress(progress, text=f"{progress:.0%} 已积累")
    if wish['status'] == 'active' and funds >= wish['target_amount']:
        if st.button("解锁这个心愿", key=f"unlock-{wish['id']}", type="primary"):
            try:
                unlock_wish(user_id, wish['id'])
                st.rerun()
            except WishFlowError as error:
                st.warning(str(error))
    elif wish['status'] == 'unlocked':
        if st.button("标记为已实现 ✦", key=f"complete-{wish['id']}"):
            try:
                complete_wish(user_id, wish['id'])
                st.rerun()
            except WishFlowError as error:
                st.warning(str(error))
    elif wish['status'] == 'completed': st.success("已实现，值得庆祝。")
