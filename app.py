import db.db as db   # 导入整个 db 模块
import streamlit as st
import re
st.set_page_config(page_title="心愿Flow", page_icon="⭐", layout="wide")

# 可选：隐藏默认菜单与页脚
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# 初始化数据库
db.init_db()

# 可选：通过 URL 参数 ?rebuild=1 触发一次性重建数据库（用于云端迁移老库结构）
try:
    params = st.query_params  # streamlit>=1.50
    if params.get("rebuild") == "1":
        db.init_db(force_rebuild=True)
except Exception:
    pass

if "user_id" not in st.session_state:
    st.title("🔑 欢迎登录心愿Flow")
    st.markdown("请输入用户名以开始您的私人心愿单：")
    username = st.text_input("用户名").strip()
    if st.button("登录"):
        # 基础校验：非空、长度、字符集（中英文、数字、下划线、短横）
        if not username:
            st.error("请输入有效的用户名（不可为空）")
        elif len(username) > 30:
            st.error("用户名过长（请控制在 30 个字符以内）")
        elif not re.match(r"^[\u4e00-\u9fa5A-Za-z0-9_\-]{1,30}$", username):
            st.error("用户名仅支持中英文、数字、下划线与短横线")
        else:
            st.session_state["user_id"] = username
            st.success(f"欢迎，{username}！您的专属心愿之旅已开启。")
            st.rerun()
    st.stop()

 # 侧边栏：当前用户与退出登录
with st.sidebar:
    st.markdown(f"当前用户：**{st.session_state['user_id']}**")
    if st.button("退出登录 / 切换用户"):
        # 只清理登录态即可；如有其它缓存键可在此一并清理
        if "user_id" in st.session_state:
            del st.session_state["user_id"]
        st.rerun()

st.title("心愿Flow")
st.subheader("以打卡汇聚心愿预算，让目标有节奏地靠近")
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
