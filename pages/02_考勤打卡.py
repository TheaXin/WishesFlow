import streamlit as st
from db.db import get_conn
import datetime

st.title("🗓️ 考勤打卡")

# ------------------------
# 收入来源管理（内嵌表单）
# ------------------------
st.subheader("收入来源配置")

conn = get_conn()
rows = conn.execute("SELECT id, title, daily_amount FROM income").fetchall()
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
                    "INSERT INTO income (title, daily_amount) VALUES (?, ?)",
                    (title, daily_amount)
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
                        "UPDATE income SET title = ?, daily_amount = ? WHERE id = ?",
                        (new_title, new_amount, id_)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"收入来源【{new_title}】已更新")
                    st.experimental_rerun()
else:
    with st.form("income_form"):
        title = st.text_input("收入名称（如 基本工资）")
        daily_amount = st.number_input("每日金额", min_value=0.0, step=10.0)
        submitted = st.form_submit_button("添加收入来源")

        if submitted and title.strip():
            conn = get_conn()
            conn.execute(
                "INSERT INTO income (title, daily_amount) VALUES (?, ?)",
                (title, daily_amount)
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
            "SELECT 1 FROM attendance WHERE income_id = ? AND date = ?",
            (income_id, selected_date.isoformat())
        ).fetchone()
        if existing:
            if selected_date == today:
                st.info("今日已完成打卡")
            else:
                st.info("该日期已打卡")
        else:
            conn.execute(
                "INSERT INTO attendance (income_id, date, earned_amount) VALUES (?,?,?)",
                (income_id, selected_date.isoformat(), daily_amount)
            )
            conn.commit()
            st.success(f"打卡成功！已获得 ¥{daily_amount:.0f} 来自【{title}】")
        conn.close()
else:
    st.warning("请先配置至少一个收入来源。")
