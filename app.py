import streamlit as st
import db.db as db   # 导入整个 db 模块

# 初始化数据库
db.init_db()

st.set_page_config(page_title="心愿Flow", layout="wide")

st.title("欢迎来到心愿Flow\n记录每一步努力 点亮每一个心愿 🌟")
st.markdown("""
在这里，每一个日常的坚持，都是通往心愿的坚实步伐。  
通过考勤和习惯打卡，您将见证自己的成长与蜕变。  
让我们一起，将每一天的努力，转化为实现梦想的力量。  

请选择左侧导航栏，探索您的专属管理工具：
- 📊 仪表盘：展示资金池与心愿进度
- 🗓️ 考勤打卡：配置收入来源并打卡
- 💪 习惯打卡：完成习惯并获取奖励
- 🌟 心愿单：添加与查看心愿目标
""")
