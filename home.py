from __future__ import annotations

import re
from html import escape
import streamlit as st

from db.db import WishFlowError, add_wish, connection, pool_summary
from ui import LINE_STICKERS, sidebar

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

if not st.session_state.user_id:
    _, main, _ = st.columns([1, 1.3, 1])
    with main:
        st.markdown(LINE_STICKERS, unsafe_allow_html=True)
        st.markdown("<div style='height:58px'></div>", unsafe_allow_html=True)
        st.markdown("# 心愿 Flow\n### 先从一件真正想实现的事开始。")
        name = st.text_input("怎么称呼你？", placeholder="输入昵称即可开始")
        if st.button("进入我的个人首页", type="primary", use_container_width=True):
            name = name.strip()
            if not re.fullmatch(r"[\u4e00-\u9fffA-Za-z0-9_-]{1,30}", name):
                st.error("昵称支持 1–30 个中英文、数字、下划线或短横线。")
            else:
                st.session_state.user_id = name
                st.rerun()
    st.stop()

user_id = st.session_state.user_id
sidebar(user_id)
with connection() as conn:
    wish_count = conn.execute("SELECT COUNT(*) FROM wishlist WHERE user_id = ?", (user_id,)).fetchone()[0]
    income_count = conn.execute("SELECT COUNT(*) FROM income WHERE user_id = ?", (user_id,)).fetchone()[0]
    habit_count = conn.execute("SELECT COUNT(*) FROM habit_task WHERE user_id = ? AND active = 1", (user_id,)).fetchone()[0]

st.markdown(f"<div class='paper-banner'><h1>{escape(user_id)} 的个人首页</h1><p>从一件想实现的事开始，把今天的完成留成你的进度。</p>{LINE_STICKERS}</div>", unsafe_allow_html=True)
flow = [("01", "设定心愿", wish_count > 0), ("02", "配置行动", income_count + habit_count > 0), ("03", "每日完成", False), ("04", "解锁实现", False)]
flow_html = "".join(f"<span class='flow-step {'done' if done else ''}'><b>{n}</b>{label}</span>" for n, label, done in flow)
st.markdown(f"<div class='flow-map'>{flow_html}</div>", unsafe_allow_html=True)

if wish_count == 0:
    st.markdown("## 你的下一步：设定第一个心愿")
    with st.form("first_wish", clear_on_submit=True):
        title = st.text_input("这次最想实现什么？", placeholder="例如：看一场演唱会")
        target = st.number_input("大约需要多少心愿金？", min_value=1.0, value=1500.0, step=100.0)
        if st.form_submit_button("保存心愿，继续下一步", type="primary"):
            try:
                add_wish(user_id, title, target, 1)
                st.rerun()
            except WishFlowError as error:
                st.error(str(error))
elif income_count + habit_count == 0:
    st.markdown("## 你的下一步：配置一个行动")
    left, right = st.columns(2)
    with left:
        st.markdown("<div class='habit-card'><b>从习惯开始</b><br><small>阅读、运动、学习或早睡，完成一次就为心愿加一笔。</small></div>", unsafe_allow_html=True)
        if st.button("添加第一个习惯", use_container_width=True): st.switch_page("pages/03_习惯打卡.py")
    with right:
        st.markdown("<div class='habit-card'><b>从稳定投入开始</b><br><small>把工作、接单或规律投入，记录为一笔心愿金。</small></div>", unsafe_allow_html=True)
        if st.button("配置收入来源", use_container_width=True): st.switch_page("pages/02_考勤打卡.py")
else:
    summary = pool_summary(user_id)
    st.markdown("## 今天的个人计划")
    a, b, c = st.columns([1, 1, 1.35])
    a.metric("可用心愿金", f"¥ {summary['balance']:,.0f}")
    b.metric("已配置行动", f"{income_count + habit_count} 项")
    with c:
        st.markdown("<div class='habit-card'><b>现在就去完成一次打卡</b><br><small>进度不是靠等待，而是由今天的一次完成开始。</small></div>", unsafe_allow_html=True)
        if st.button("去完成今日打卡", type="primary", use_container_width=True):
            st.switch_page("pages/03_习惯打卡.py" if habit_count else "pages/02_考勤打卡.py")

with st.expander("个人首页的使用路线"):
    st.markdown("**设定心愿** → **配置行动** → **每日完成** → **解锁实现**。每次回到这里，只需看清楚当前的下一步。")
