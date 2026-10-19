# 心愿 Flow ✦

把日常行动换成可见进度的本地心愿管理工具。你可以记录考勤与习惯打卡，将积累的「心愿金」用于解锁并完成真正想实现的事。

- [体验在线网页版](https://redcowork.xiaohongshu.com/f/vfujzmifp4/)
- [查看产品介绍与交互演示](product-site/index.html)

本仓库目前包含可运行的 Streamlit + SQLite 本地版，以及 `product-site/` 静态介绍与交互演示页。RedCowork 上的在线网页版是独立实现；其最新源码尚未归档到本仓库，因此不要把 `product-site/` 误认为在线网页版的完整源码。

## 功能

- 多使用者本地资料：昵称仅存于当前浏览器会话，数据按使用者隔离。
- 考勤打卡：为工作、接单或其他稳定投入设置每次累积金额。
- 习惯打卡：把阅读、运动、学习等重复行动转成奖励。
- 心愿单：设置目标与优先级；余额足够后解锁，完成后资金会持续记为已使用。
- 仪表盘：查看累计来源、可用余额及每日积累趋势。

## 快速开始

需要 Python 3.10 或更高版本。

```bash
git clone https://github.com/TheaXin/WishesFlow.git
cd WishesFlow
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

在浏览器打开终端显示的地址（通常为 `http://localhost:8501`）。macOS 用户也可以双击 `启动心愿Flow.command`。

## 数据与隐私

所有业务数据保存在本机的 `db/wishflow.sqlite3`，不会上传到任何服务器。该数据库已被 Git 忽略；请自行备份它以保留记录。此项目目前没有登录、云同步或加密功能，因此不建议录入敏感个人信息。

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

项目以 Streamlit 构建界面，SQLite 负责本地持久化。核心记账规则集中在 `db/db.py`，页面只处理交互展示，便于测试和维护。

## 静态介绍页部署

`product-site/` 不需要构建或后端。进入该目录运行 `python3 -m http.server 8000`，打开 `http://localhost:8000`；部署时把该目录里的 `index.html`、`styles.css` 和 `script.js` 一起上传到任意静态站点服务即可。仓库的 GitHub Pages 工作流会在推送到 `main` 后自动发布这个演示页。页内“打开网页版”按钮指向上方 RedCowork 版本。

Streamlit 本地版依赖 SQLite，不应直接作为无持久化存储的静态网站部署。若部署到服务器，需另外设计持久化、用户隔离、备份与访问控制。

## 参与贡献

欢迎提交 issue 和 pull request。提交前请阅读 [贡献指南](CONTRIBUTING.md)、遵守[行为准则](CODE_OF_CONDUCT.md)，并运行测试。安全问题请勿公开提交，参见 [安全政策](SECURITY.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。
