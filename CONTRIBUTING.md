# 贡献指南

感谢你愿意让心愿 Flow 变得更好。

1. Fork 仓库并从 `main` 创建主题分支。
2. 保持改动聚焦；界面文字使用简体中文，数据库访问集中在 `db/db.py`。
3. 运行 `python -m unittest discover -s tests -v`，确保测试通过。
4. 提交清楚说明「为什么」的 commit，并在 PR 中描述行为变化和验证方式。

请不要提交 `db/wishflow.sqlite3`、虚拟环境、密钥或个人数据。较大的功能改动建议先创建 issue 讨论。
