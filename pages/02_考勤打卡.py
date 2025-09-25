import streamlit as st
from db.db import get_conn
import datetime

st.caption(f"当前用户: {st.session_state['user_id']}")
st.title("🗓️ 考勤打卡")

user_id = st.session_state["user_id"]

# ------------------------
# 收入来源管理（内嵌表单）
# ------------------------
st.subheader("收入来源配置")

conn = get_conn()
rows = conn.execute(
    "SELECT id, title, daily_amount FROM income WHERE user_id = ?", (user_id,)).fetchall()
conn.close()

if rows:
    st.table(rows)

    with st.expander("添加新的收入来源"):
        with st.form("income_form_add"):
            title = st.text_input("收入名称（如 基本工资）")
            daily_amount = st.number_input("每日金额", min_value=0.0, step=10.0)
            submitted = st.form_submit_button("添加收入来源")
            if submitted and title.strip():
                conn = get_conn()
                conn.execute(
                    "INSERT INTO income (title, daily_amount, user_id) VALUES (?, ?, ?)",
                    (title, daily_amount, user_id)
                )
                conn.commit()
                conn.close()
                st.success(f"收入来源【{title}】已添加")
                st.experimental_rerun()

    with st.expander("编辑现有收入来源"):
        edited_id = st.selectbox(
            "选择要编辑的收入来源", rows, format_func=lambda r: f"{r[1]} (¥{r[2]:.0f}/天)")
        if edited_id:
            id_, old_title, old_amount = edited_id
            with st.form("income_form_edit"):
                new_title = st.text_input("收入名称", value=old_title)
                new_amount = st.number_input(
                    "每日金额", min_value=0.0, step=10.0, value=old_amount)
                submitted_edit = st.form_submit_button("保存修改")
                if submitted_edit and new_title.strip():
                    conn = get_conn()
                    conn.execute(
                        "UPDATE income SET title = ?, daily_amount = ? WHERE id = ? AND user_id = ?",
                        (new_title, new_amount, id_, user_id)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"收入来源【{new_title}】已更新")
                    st.experimental_rerun()

    with st.expander("删除收入来源"):
        delete_id = st.selectbox(
            "选择要删除的收入来源", rows, format_func=lambda r: f"{r[1]} (¥{r[2]:.0f}/天)", key="delete_income_select")
        if st.button("删除收入来源"):
            conn = get_conn()
            conn.execute(
                "DELETE FROM income WHERE id = ? AND user_id = ?",
                (delete_id[0], user_id)
            )
            conn.commit()
            conn.close()
            st.success(f"收入来源【{delete_id[1]}】已删除")
            st.experimental_rerun()
else:
    with st.form("income_form"):
        title = st.text_input("收入名称（如 基本工资）")
        daily_amount = st.number_input("每日金额", min_value=0.0, step=10.0)
        submitted = st.form_submit_button("添加收入来源")

        if submitted and title.strip():
            conn = get_conn()
            conn.execute(
                "INSERT INTO income (title, daily_amount, user_id) VALUES (?, ?, ?)",
                (title, daily_amount, user_id)
            )
            conn.commit()
            conn.close()
            st.success(f"收入来源【{title}】已添加")
            st.experimental_rerun()

# ------------------------
# 考勤打卡
# ------------------------
st.subheader("今日打卡")
if rows:
    selected = st.selectbox(
        "选择收入来源", rows, format_func=lambda r: f"{r[1]} (¥{r[2]:.0f}/天)")
    today = datetime.date.today()
    selected_date = st.date_input("选择打卡日期", value=today)
    if st.button("立即打卡"):
        income_id, title, daily_amount = selected
        conn = get_conn()
        existing = conn.execute(
            "SELECT 1 FROM attendance WHERE income_id = ? AND date = ? AND user_id = ?",
            (income_id, selected_date.isoformat(), user_id)
        ).fetchone()
        if existing:
            if selected_date == today:
                st.info("今日已完成打卡")
            else:
                st.info("该日期已打卡")
        else:
            conn.execute(
                "INSERT INTO attendance (income_id, date, earned_amount, user_id) VALUES (?,?,?,?)",
                (income_id, selected_date.isoformat(), daily_amount, user_id)
            )
            conn.commit()
            st.success(f"打卡成功！已获得 ¥{daily_amount:.0f} 来自【{title}】")
        conn.close()

    with st.expander("删除打卡记录"):
        del_income = st.selectbox(
            "选择收入来源", rows, format_func=lambda r: f"{r[1]} (¥{r[2]:.0f}/天)", key="del_attendance_income_select")
        del_date = st.date_input(
            "选择打卡日期", value=today, key="del_attendance_date")
        if st.button("删除打卡记录"):
            conn = get_conn()
            conn.execute(
                "DELETE FROM attendance WHERE income_id = ? AND date = ? AND user_id = ?",
                (del_income[0], del_date.isoformat(), user_id)
            )
            conn.commit()
            conn.close()
            st.success(f"已删除 {del_date} 来自【{del_income[1]}】的打卡记录")
            st.experimental_rerun()
else:
    st.warning("请先配置至少一个收入来源。")
