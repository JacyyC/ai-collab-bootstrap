# 贡献说明

先阅读 [仓库协议](AGENTS.md)与 [README](README.md)。修改范围明确后直接实施，变更原因和验证结果写入提交说明或 PR，不创建仓库工作区。

- Skill 行为：修改 `skills/ai-collab-bootstrap/SKILL.md` 与实际需要的规则/引用。
- 模板与用户项目工具：只修改 `template-source/`，再运行 `python3 scripts/sync_templates.py --write`。禁止反向同步或手改生成副本。
- Agent 接入：更新 [接入说明](skills/ai-collab-bootstrap/references/agent-setup.md)中的对应条目与官方来源；区分文档核对、自动化验证和真实客户端测试。

提交前运行 README 列出的结构校验和相关回归。新测试验证可观察行为，例如冲突时不写入、只读不改文件、旧记录可读；避免仅比对文案。若修改发行件，再验证重复生成没有变化。

用户项目日常修改不承担 Skill 仓库的发行检查。真实工作记录和人工日志不得进入模板。未获明确授权不推送或公开发布。
