import db.db as db   # 导入整个 db 模块
import streamlit as st
st.set_page_config(page_title="心愿Flow", layout="wide")

# 初始化数据库
db.init_db()

if "user_id" not in st.session_state:
    st.title("🔑 欢迎登录心愿Flow")
    st.markdown("请输入用户名以开始您的私人心愿单：")
    username = st.text_input("用户名")
    if st.button("登录"):
        if not username:
            st.error("请输入用户名")
        else:
            st.session_state["user_id"] = username
            st.success(f"欢迎，{username}！您的专属心愿之旅已开启。")
            st.experimental_rerun()
    st.stop()

st.title("🌟 心愿Flow — 让心愿照进现实 🌟")
st.markdown(f"您好，**{st.session_state['user_id']}** 🎉")
st.caption(f"当前用户: {st.session_state['user_id']}")
st.markdown("""
在这里，每一次坚持，都会化作点亮心愿的星光。  
打卡越多，心愿越近，让梦想一步步走进现实。  
从今天开始，让努力变得可见，让心愿触手可及。  

请选择左侧导航栏，探索您的专属管理工具：
- 📊 仪表盘：展示资金池与心愿进度
- 🗓️ 考勤打卡：配置收入来源并打卡
- 💪 习惯打卡：完成习惯并获取奖励
- 🌟 心愿单：添加与查看心愿目标
""")
