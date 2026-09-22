from __future__ import annotations

from html import escape
import streamlit as st


LINE_STICKERS = """
<div class="line-stickers" aria-hidden="true">
  <svg viewBox="0 0 64 64"><path d="M32 7l5 18 18 5-18 5-5 18-5-18-18-5 18-5z"/><circle cx="48" cy="14" r="4"/></svg>
  <svg viewBox="0 0 92 58"><path d="M7 13h78v32H7zM18 13v32M74 13v32M28 23h36M28 33h22"/><path d="M7 19l11 7M7 39l11-7M85 19l-11 7M85 39l-11-7"/></svg>
  <svg viewBox="0 0 68 64"><path d="M18 39V28a16 16 0 0132 0v11M18 37h-5v12h10V37m32 0h-5v12h10V37"/><path d="M28 52c3 5 9 6 14 2"/></svg>
</div>
"""


def apply_theme() -> None:
    st.markdown("""
    <style>
    #MainMenu, footer{visibility:hidden}
    .stApp{background:#fbfbff;background-image:linear-gradient(135deg,rgba(151,183,242,.14) 1px,transparent 1px),linear-gradient(45deg,rgba(246,181,194,.12) 1px,transparent 1px);background-size:25px 25px}
    .block-container{max-width:1180px;padding-top:2.3rem;padding-bottom:4rem}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#eef5ff 0%,#faf3fb 100%);border-right:1px solid #b7caed}[data-testid="stSidebar"] *{color:#3d4c70!important}
    h1,h2,h3{font-family:ui-rounded,"PingFang SC",sans-serif!important;letter-spacing:-.035em}h1{font-size:2.7rem!important;color:#3d4c70!important}h2{color:#3d4c70!important}
    .stButton button{border-radius:999px!important;border:1.5px solid #6c84bd!important;background:#7895d4!important;color:#fff!important;font-weight:650!important;box-shadow:3px 3px 0 #c9d8f3!important;transition:transform .16s,box-shadow .16s}.stButton button:hover{transform:translate(-1px,-2px);box-shadow:5px 5px 0 #c9d8f3!important;background:#6682c4!important}
    .stTextInput input,.stNumberInput input,[data-baseweb="select"]>div{border-radius:12px!important;border:1px solid #bdcdea!important;background:#fff!important}
    [data-testid="stMetric"]{background:rgba(255,255,255,.92)!important;border:1px solid #adc2ea!important;border-radius:18px!important;padding:16px!important;box-shadow:4px 5px 0 #e6eefc!important}[data-testid="stMetricLabel"]{color:#6c7c9b!important;font-weight:700}.stProgress>div>div>div{background:#f29aaf!important}
    [data-testid="stExpander"]{background:#fff;border:1px solid #c7d5ee;border-radius:16px;overflow:hidden}.stAlert{border-radius:14px!important;border:1px solid #c7d5ee!important}
    .paper-banner{background:linear-gradient(105deg,#fff 0%,#f7fbff 72%,#fff6fa 100%);border:1.5px solid #829bd0;border-radius:22px;padding:24px 145px 24px 28px;margin:0 0 1.5rem;box-shadow:7px 8px 0 #dce8fa;position:relative;overflow:hidden}.paper-banner p{margin:5px 0 0;color:#6d7891}.sticker-note{background:#fff7e9;border-left:4px solid #f2ae77;padding:12px 15px;color:#6a5b58;font-size:.92rem;border-radius:0 10px 10px 0}.habit-card{background:#fff;border:1px solid #bfd0ee;border-radius:15px;padding:16px 18px;margin:10px 0;box-shadow:3px 4px 0 #eef3fd}
    .line-stickers{position:absolute;right:24px;top:18px;display:flex;align-items:center;gap:4px;transform:rotate(5deg)}.line-stickers svg{width:42px;height:42px;fill:none;stroke:#8ca7df;stroke-width:2.3;stroke-linecap:round;stroke-linejoin:round}.line-stickers svg:nth-child(2){width:62px;stroke:#ee9bb0}.line-stickers svg:nth-child(3){stroke:#f2ae77}
    .flow-map{display:flex;gap:8px;align-items:center;margin:8px 0 28px;overflow-x:auto;padding-bottom:5px}.flow-step{white-space:nowrap;border:1px solid #c4d1ea;border-radius:999px;background:#fff;padding:9px 13px;color:#8a96aa;font-size:.84rem}.flow-step:after{content:'→';margin-left:12px;color:#a4b5d3}.flow-step:last-child:after{content:'';margin:0}.flow-step b{font-size:.7rem;margin-right:6px;color:#7895d4}.flow-step.done{border-color:#7895d4;color:#3d4c70;background:#eef4ff}.flow-step.done b{color:#f18da5}
    .stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{border-radius:999px;background:#edf2fc;padding:8px 16px}.stTabs [aria-selected="true"]{background:#7895d4!important;color:#fff!important}
    @media(max-width:680px){.paper-banner{padding-right:25px;padding-top:72px}.line-stickers{left:22px;right:auto;top:17px}}
    </style>
    """, unsafe_allow_html=True)


def intro(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="paper-banner"><h1>{title}</h1><p>{subtitle}</p>{LINE_STICKERS}</div>', unsafe_allow_html=True)


def sidebar(user_id: str) -> None:
    with st.sidebar:
        st.markdown(LINE_STICKERS, unsafe_allow_html=True)
        st.markdown("<div style='height:64px'></div>", unsafe_allow_html=True)
        st.markdown("## 个人首页\n心愿 Flow")
        st.caption("把日常的完成，留成温柔的轨迹。")
        st.caption(f"你好，{escape(user_id)}。今天也为自己完成一点。")
        st.divider()
        if st.button("切换使用者", use_container_width=True):
            st.session_state.user_id = ""
            st.rerun()
