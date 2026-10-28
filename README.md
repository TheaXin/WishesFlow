# 心愿 Flow ✦

把日常行动换成可见进度的本地心愿管理工具。你可以记录考勤与习惯打卡，将积累的「心愿金」用于解锁并完成真正想实现的事。

- [使用浏览器独立版](https://theaxin.github.io/WishesFlow/app/)
- [产品介绍与交互演示](https://theaxin.github.io/WishesFlow/)

旧的 [RedCowork 在线版本](https://redcowork.xiaohongshu.com/f/vfujzmifp4/) 是独立历史实现，其源码未归档在本仓库；该版本不属于本仓库的自动发布范围。现在的主要浏览器入口为上方 GitHub Pages 版本，源码位于 `product-site/app/`，与仓库同步发布。

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

本地 Streamlit 版的业务数据保存在运行电脑的 `db/wishflow.sqlite3`，本地版不会主动上传业务数据。该数据库已被 Git 忽略；请自行备份它以保留记录。此项目目前没有登录、云同步或加密功能，因此不建议录入敏感个人信息。

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

项目以 Streamlit 构建界面，SQLite 负责本地持久化。核心记账规则集中在 `db/db.py`，页面只处理交互展示，便于测试和维护。

## 参与贡献

欢迎提交 issue 和 pull request。提交前请阅读 [贡献指南](CONTRIBUTING.md)、遵守[行为准则](CODE_OF_CONDUCT.md)，并运行测试。安全问题请勿公开提交，参见 [安全政策](SECURITY.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。

## 三种入口与版本边界

| 入口 | 实现与用途 | 数据位置 |
| --- | --- | --- |
| 本地版 `app.py` | Python / Streamlit，完整本地工作流 | 运行电脑的 SQLite 文件 |
| 浏览器独立版 `product-site/app/` | 原生 HTML / CSS / JavaScript，可独立管理打卡与心愿 | 当前浏览器、当前网站来源的 localStorage |
| 产品展示页 `product-site/index.html` | 产品介绍与固定数据交互示意，入口链接至浏览器版 | 示意不保存数据 |

两个可用版本遵守同样的主要记账规则：项目每天一次打卡；考勤和习惯奖励汇入余额；预算足够才可解锁；已解锁和已实现心愿持续占用目标预算。浏览器版金额按整数分记录，支持项目创建、当天打卡、按优先级展示心愿、解锁及实现、最近 20 条记录、JSON 备份导出与恢复。

浏览器版当前是单一资料空间，没有本地版的昵称分区或每日趋势图，也不支持直接读取 SQLite。不同浏览器、设备、域名和端口之间数据独立；浏览器版与本地版不自动互通。清理网站数据或结束隐私浏览可能丢失记录；请定期导出备份。导入会先验证数据，经确认后替换浏览器版全部记录。项目不提供账号、云端业务数据存储或跨设备同步。

### 预览浏览器版

```bash
python3 -m http.server 8080 --directory product-site
```

访问 `http://localhost:8080/` 看产品展示，访问 `http://localhost:8080/app/` 使用独立应用。请通过 HTTP(S) 使用，不要直接双击 HTML 文件。线上使用 HTTPS，保证浏览器存储及唯一标识能力正常。

### GitHub 源码与线上同步

同一仓库维护展示页、本地应用与浏览器应用，不在其他平台单独维护一份演示代码。

`.github/workflows/pages.yml` 在 PR 上执行 Python 和 JavaScript 记账检查，在 `main` 推送或手动触发时，通过检查后构建并发布 `product-site/` 到 GitHub Pages。构建只包含静态网站，不上传 SQLite 或个人记录。`build.json` 与页面底部包含本次构建对应的 commit 链接；本地构建若有未提交修改会明确标注。

首次启用需在 GitHub 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。合并代码后在 Actions 确认发布成功，再以部署输出的 URL 为准。默认项目 Pages 路径预期为 `https://theaxin.github.io/WishesFlow/`，应用在其 `app/` 下；此地址尚需实际部署验证。源码更新与部署完成之间有构建时间差，失败时线上继续保留之前版本，可通过页脚 commit 对照。源码同步不等于用户数据同步。

本地检查：

```bash
python -m unittest discover -s tests -v
node --test tests/browser_core.test.cjs
python scripts/build_site.py
python -m http.server 8080 --directory site-dist
```

`site-dist/` 是生成目录，不作为源码提交。当前改动是否已发布，以 GitHub Actions 成功记录和线上页脚版本为准。
