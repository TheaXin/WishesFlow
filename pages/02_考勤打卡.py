from datetime import date
import streamlit as st
from db.db import WishFlowError, add_income, connection, record_attendance
from ui import apply_theme, intro, sidebar

apply_theme()
if not st.session_state.get("user_id"): st.switch_page("home.py")
user_id = st.session_state.user_id
sidebar(user_id)
intro("考勤打卡", "把规律的投入，转换为看得见的心愿预算。")

with st.expander("＋ 新增收入来源", expanded=False):
    with st.form("new_income", clear_on_submit=True):
        title = st.text_input("名称", placeholder="例如：全职工作")
        amount = st.number_input("每次打卡计入", min_value=0.01, step=10.0)
        if st.form_submit_button("保存来源", type="primary"):
            try:
                add_income(user_id, title, amount)
                st.rerun()
            except WishFlowError as error:
                st.error(str(error))
with connection() as conn:
    incomes = conn.execute("SELECT id, title, daily_amount FROM income WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
if not incomes:
    st.info("先新增一个收入来源，再开始打卡。")
    st.stop()

# Keep IDs as options so identically named sources never overwrite each other.
options = {r['id']: r for r in incomes}
selected_id = st.selectbox("选择收入来源", list(options), format_func=lambda key: f"{options[key]['title']} · ¥{options[key]['daily_amount']:,.2f}/次 · 来源 #{key}")
selected = options[selected_id]
when = st.date_input("打卡日期", value=date.today(), max_value=date.today())
if st.button("完成考勤打卡", type="primary"):
    try:
        amount = record_attendance(user_id, selected['id'], when)
        st.success(f"已为「{selected['title']}」积累 ¥{amount:,.2f}。")
    except WishFlowError as error:
        st.warning(str(error))
