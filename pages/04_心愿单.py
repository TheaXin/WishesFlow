import streamlit as st
from db.db import get_conn

st.title("🌟 心愿单")
st.caption(f"当前用户: {st.session_state['user_id']}")

# ------------------------
# 添加心愿
# ------------------------
with st.form("wish_form"):
    title = st.text_input("心愿名称（如 新电脑/旅游）")
    target_amount = st.number_input("目标金额", min_value=1.0, step=10.0)
    priority = st.number_input("优先级（数字越小越优先）", min_value=0, step=1)
    submitted = st.form_submit_button("添加心愿")

    if submitted and title.strip():
        conn = get_conn()
        conn.execute(
            "INSERT INTO wishlist (title, target_amount, priority, status, user_id) VALUES (?,?,?,?,?)",
            (title, target_amount, priority, 0, st.session_state["user_id"])
        )
        conn.commit()
        conn.close()
        st.success(f"心愿已添加：{title}")

# ------------------------
# 计算可用资金
# ------------------------
conn = get_conn()
attendance_sum = conn.execute("""
    SELECT IFNULL(SUM(i.daily_amount), 0)
    FROM attendance a
    JOIN income i ON a.income_id = i.id
    WHERE a.user_id = ?
""", (st.session_state["user_id"],)).fetchone()[0]

habit_sum = conn.execute("""
    SELECT IFNULL(SUM(h.reward_amount), 0)
    FROM habit_checkin hc
    JOIN habit_task h ON hc.task_id = h.id
    WHERE hc.user_id = ?
""", (st.session_state["user_id"],)).fetchone()[0]
available_funds = attendance_sum + habit_sum

# ------------------------
# 展示心愿
# ------------------------
st.subheader("我的心愿列表")
rows = conn.execute(
    "SELECT id, title, target_amount, priority, status FROM wishlist WHERE status IN (0,1) AND user_id = ? ORDER BY priority ASC, id ASC",
    (st.session_state["user_id"],)
).fetchall()
conn.close()

if rows:
    for wid, title, target, priority, status in rows:
        # 如果未解锁且目标金额小于等于可用资金，显示已满足解锁条件
        if status == 0 and target <= available_funds:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.success(
                    f"✅ {title} 已满足解锁条件！（目标 ¥{target:.0f}, 优先级 {priority}）")
            with col2:
                if st.button("完成心愿 ✅", key=f"complete_{wid}"):
                    conn = get_conn()
                    conn.execute(
                        "UPDATE wishlist SET status=2 WHERE id=? AND user_id=?",
                        (wid, st.session_state["user_id"])
                    )
                    conn.commit()
                    conn.close()
                    st.rerun()
        elif status == 1:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.success(f"✅ {title} 已解锁！（目标 ¥{target:.0f}, 优先级 {priority}）")
            with col2:
                # Complete wish button (use st.rerun)
                if st.button("完成心愿 ✅", key=f"complete_{wid}"):
                    conn = get_conn()
                    conn.execute(
                        "UPDATE wishlist SET status=2 WHERE id=? AND user_id=?",
                        (wid, st.session_state["user_id"])
                    )
                    conn.commit()
                    conn.close()
                    st.rerun()
            with col3:
                if st.button("编辑", key=f"edit_btn_{wid}"):
                    st.session_state[f"edit_mode_{wid}"] = True
            # Show edit form if requested
            if st.session_state.get(f"edit_mode_{wid}", False):
                with st.expander("编辑心愿", expanded=True):
                    edit_title = st.text_input(
                        "心愿名称", value=title, key=f"edit_title_{wid}")
                    edit_target = st.number_input(
                        "目标金额", min_value=1.0, step=10.0, value=float(target), key=f"edit_target_{wid}")
                    edit_priority = st.number_input(
                        "优先级", min_value=0, step=1, value=int(priority), key=f"edit_priority_{wid}")
                    save = st.button("保存修改", key=f"save_{wid}")
                    cancel = st.button("取消", key=f"cancel_{wid}")
                    if save and edit_title.strip():
                        conn = get_conn()
                        conn.execute(
                            "UPDATE wishlist SET title=?, target_amount=?, priority=? WHERE id=? AND user_id=?",
                            (edit_title, edit_target, edit_priority,
                             wid, st.session_state["user_id"])
                        )
                        conn.commit()
                        conn.close()
                        st.session_state.pop(f"edit_mode_{wid}", None)
                        st.rerun()
                    if cancel:
                        st.session_state.pop(f"edit_mode_{wid}", None)
                        st.rerun()
        else:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"**{title}** （目标 ¥{target:.0f}, 优先级 {priority}）")
            with col2:
                if st.button("编辑", key=f"edit_btn_{wid}"):
                    st.session_state[f"edit_mode_{wid}"] = True
            if st.session_state.get(f"edit_mode_{wid}", False):
                with st.expander("编辑心愿", expanded=True):
                    edit_title = st.text_input(
                        "心愿名称", value=title, key=f"edit_title_{wid}")
                    edit_target = st.number_input(
                        "目标金额", min_value=1.0, step=10.0, value=float(target), key=f"edit_target_{wid}")
                    edit_priority = st.number_input(
                        "优先级", min_value=0, step=1, value=int(priority), key=f"edit_priority_{wid}")
                    save = st.button("保存修改", key=f"save_{wid}")
                    cancel = st.button("取消", key=f"cancel_{wid}")
                    if save and edit_title.strip():
                        conn = get_conn()
                        conn.execute(
                            "UPDATE wishlist SET title=?, target_amount=?, priority=? WHERE id=? AND user_id=?",
                            (edit_title, edit_target, edit_priority,
                             wid, st.session_state["user_id"])
                        )
                        conn.commit()
                        conn.close()
                        st.session_state.pop(f"edit_mode_{wid}", None)
                        st.rerun()
                    if cancel:
                        st.session_state.pop(f"edit_mode_{wid}", None)
                        st.rerun()
else:
    st.info("还没有心愿，快去设定一个吧！")

# ------------------------
# 已完成心愿
# ------------------------
st.subheader("已完成心愿")
conn = get_conn()
completed_rows = conn.execute(
    "SELECT id, title, target_amount, priority FROM wishlist WHERE status=2 AND user_id = ? ORDER BY priority ASC, id ASC",
    (st.session_state["user_id"],)
).fetchall()
conn.close()

if completed_rows:
    for wid, title, target, priority in completed_rows:
        st.success(f"✅ {title} 已完成！（目标 ¥{target:.0f}, 优先级 {priority}）")
else:
    st.caption("暂无已完成的心愿。")
