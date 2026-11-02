# 贡献说明

先阅读 [仓库协议](AGENTS.md)与 [README](README.md)。修改范围明确后直接实施，变更原因和验证结果写入提交说明或 PR，不创建仓库工作区。

- Skill 行为：修改 `skills/ai-collab-bootstrap/SKILL.md` 与实际需要的规则/引用。
- 模板与用户项目工具：只修改 `template-source/`，再运行 `python3 scripts/sync_templates.py --write`。禁止反向同步或手改生成副本。
- Agent 接入：更新 [接入说明](skills/ai-collab-bootstrap/references/agent-setup.md)中的对应条目与官方来源；区分文档核对、自动化验证和真实客户端测试。

工作记录规则变化时，按下表核对覆盖范围，修改实际受影响处；细则集中维护，其他入口只保留执行所需短规则和链接，不复制整套合同。

| 层次 | 核对位置 |
|---|---|
| 内容归属与文件合同 | `template-source/workspace/docs/DOCUMENTATION_POLICY.md`、`DOCUMENT_LIFECYCLE.md` |
| 日常接手与执行 | `template-source/AGENTS.md`、`workspace/README.md`、`workspace/docs/WORK.md` |
| 实例化后的记录提示 | `template-source/workspace/templates/work-item/` 的 README、Spec、Plan、Log、Evidence；`maintain.py` 的无模板回退入口 |
| Skill 新建、更新、整理与审查 | `skills/ai-collab-bootstrap/SKILL.md`、`classification-rules.md`、`consistency-check.md` |
| 工具、回归与发行 | `workspace_views.py`、相关行为测试；同步生成并核对 `skills/ai-collab-bootstrap/templates/`，不手改副本 |

表内省略的 `workspace/` 工具路径均位于 `template-source/`。根仓库不运行用户项目工作项流程；现有用户项目升级需按其实际入口和工具合并，不因本仓库模板更新而自动生效。

提交前运行 README 列出的结构校验和相关回归。新测试验证可观察行为，例如冲突时不写入、只读不改文件、旧记录可读；避免仅比对文案。若修改发行件，再验证重复生成没有变化。

用户项目日常修改不承担 Skill 仓库的发行检查。真实工作记录和人工日志不得进入模板。未获明确授权不推送或公开发布。
