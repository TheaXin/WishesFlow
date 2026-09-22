import streamlit as st

from db.db import init_db
from ui import apply_theme

st.set_page_config(page_title="个人首页 · 心愿 Flow", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
init_db()
apply_theme()

page = st.navigation(
    {
        "我的心愿": [
            st.Page("home.py", title="个人首页", default=True),
            st.Page("pages/01_仪表盘.py", title="仪表盘"),
        ],
        "行动": [
            st.Page("pages/02_考勤打卡.py", title="考勤打卡"),
            st.Page("pages/03_习惯打卡.py", title="习惯打卡"),
            st.Page("pages/04_心愿单.py", title="心愿单"),
        ],
    }
)
page.run()
