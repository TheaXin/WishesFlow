import streamlit as st
from db.db import get_conn
from datetime import date

st.title("💪 习惯打卡")
st.caption(f"当前用户: {st.session_state['user_id']}")

# ------------------------
# 获取当前用户ID
# ------------------------
user_id = st.session_state["user_id"]

# ------------------------
# 读取习惯任务
# ------------------------
conn = get_conn()
rows = conn.execute(
    "SELECT id, title, reward_amount FROM habit_task WHERE user_id = ?", (
        user_id,)
).fetchall()

# ------------------------
# 习惯任务展示与管理
# ------------------------
if not rows:
    st.info("暂无习惯任务，请先添加。")
    with st.form("habit_form_empty"):
        habit_title = st.text_input("习惯名称（如 健身/背单词）")
        reward_amount = st.number_input("奖励金额", min_value=1.0, step=1.0)
        submitted = st.form_submit_button("添加习惯")
        if submitted and habit_title.strip():
            conn.execute(
                "INSERT INTO habit_task (title, reward_amount, user_id) VALUES (?, ?, ?)",
                (habit_title, reward_amount, user_id)
            )
            conn.commit()
            conn.close()
            st.success(f"习惯任务【{habit_title}】已添加")
            st.rerun()
else:
    # 展示习惯任务表格
    st.subheader("习惯任务列表")
    import pandas as pd
    df = pd.DataFrame(rows, columns=["ID", "习惯名称", "奖励金额"])
    st.table(df[["习惯名称", "奖励金额"]])

    # 添加新习惯任务
    with st.expander("➕ 添加新的习惯任务"):
        with st.form("habit_form_add"):
            habit_title = st.text_input(
                "习惯名称（如 健身/背单词）", key="add_habit_title")
            reward_amount = st.number_input(
                "奖励金额", min_value=1.0, step=1.0, key="add_reward_amount")
            submitted = st.form_submit_button("添加习惯")
            if submitted and habit_title.strip():
                conn.execute(
                    "INSERT INTO habit_task (title, reward_amount, user_id) VALUES (?, ?, ?)",
                    (habit_title, reward_amount, user_id)
                )
                conn.commit()
                st.success(f"习惯任务【{habit_title}】已添加")
                st.rerun()

    # 编辑或删除习惯任务
    with st.expander("📝 编辑或删除习惯任务"):
        habit_options = {f"{title} (¥{reward_amount:.0f})": (
            task_id, title, reward_amount) for task_id, title, reward_amount in rows}
        selected = st.selectbox("选择要编辑的习惯", list(habit_options.keys()))
        selected_id, selected_title, selected_reward = habit_options[selected]
        new_title = st.text_input(
            "习惯名称", value=selected_title, key="edit_habit_title")
        new_reward = st.number_input("奖励金额", min_value=1.0, step=1.0, value=float(
            selected_reward), key="edit_reward_amount")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存修改"):
                if new_title.strip():
                    conn.execute(
                        "UPDATE habit_task SET title=?, reward_amount=? WHERE id=? AND user_id=?",
                        (new_title, new_reward, selected_id, user_id)
                    )
                    conn.commit()
                    st.success("修改已保存")
                    st.rerun()
        with col2:
            if st.button("删除习惯", type="secondary"):
                # 仅删除习惯任务，不删除 habit_checkin 表中的历史记录
                conn.execute(
                    "DELETE FROM habit_task WHERE id=? AND user_id=?",
                    (selected_id, user_id)
                )
                conn.commit()
                st.warning(f"已删除习惯【{selected_title}】")
                st.rerun()

    # ------------------------
    # 习惯打卡
    # ------------------------
    st.subheader("完成习惯打卡")
    selected_date = st.date_input("选择打卡日期", value=date.today())
    for task_id, title, reward_amount in rows:
        st.write(f"{title} (奖励 ¥{reward_amount:.0f})")
        if st.button(f"完成打卡 - {title}", key=f"checkin_{task_id}"):
            # Check if already checked in for the selected date
            existing = conn.execute(
                "SELECT 1 FROM habit_checkin WHERE task_id = ? AND date = ? AND user_id = ?",
                (task_id, selected_date.isoformat(), user_id)
            ).fetchone()
            if existing:
                st.info("该日期已完成打卡")
            else:
                conn.execute(
                    "INSERT INTO habit_checkin (task_id, date, reward_amount, user_id) VALUES (?, ?, ?, ?)",
                    (task_id, selected_date.isoformat(), reward_amount, user_id)
                )
                conn.commit()
                st.success(f"打卡成功！完成【{title}】，奖励 ¥{reward_amount:.0f}")

    # ------------------------
    # 当日打卡记录
    # ------------------------
    st.subheader("当日打卡记录")
    checkins = conn.execute(
        "SELECT hc.id, ht.title, hc.reward_amount FROM habit_checkin hc "
        "JOIN habit_task ht ON hc.task_id = ht.id "
        "WHERE hc.date = ? AND hc.user_id = ?",
        (selected_date.isoformat(), user_id)
    ).fetchall()
    for checkin_id, title, reward_amount in checkins:
        st.write(f"{title} (奖励 ¥{reward_amount:.0f})")
        if st.button(f"删除打卡记录 - {title}", key=f"delete_checkin_{checkin_id}"):
            conn.execute(
                "DELETE FROM habit_checkin WHERE id = ? AND user_id = ?",
                (checkin_id, user_id)
            )
            conn.commit()
            st.rerun()
conn.close()
