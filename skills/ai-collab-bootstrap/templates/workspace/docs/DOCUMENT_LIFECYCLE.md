---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# Workspace 文档生命周期

本文件定义工作记录与检查合同；内容归属见 [Policy](DOCUMENTATION_POLICY.md)，执行权限见根 [AGENTS](../../AGENTS.md)。

## 记录与状态

工作项永久位于 `workspace/docs/work-items/records/<小写稳定-id>/`，不随状态搬目录。状态为 `planned`、`ready`、`active`、`blocked`、`paused`、`completed`、`cancelled`。完成和取消均有关闭日期及可复核依据；非终态不带关闭日期。

README YAML 是状态源，WORK、HISTORY 和工作项管理页仅为派生视图。小项在 README 保存目标/边界、AC、必要决定、验证与限制；内容较多时分别拆 Spec、Plan、Log、Evidence。没有内容时不预建空文件，不增加“选轻量还是完整”的问答。

## Schema 4

新建项使用 Schema 4。README 必需字段为 `schema_version`、`document_status`、`last_updated`、`id`、`title`、`status`、`updated_at`、`next_action`；终态另有 `closed_at`。

| 字段或内容 | 合同 |
|---|---|
| id | 大写语义 ID，如 `V1-01`、`DOCS-01`；目录为对应小写；不得复用 |
| priority | 可省略，默认 P2；值为 P0 至 P3 |
| stage | 无分阶段时为空/null；非空时引用 Plan 或 README“计划”内实际定义的 Stage ID |
| depends_on / blocked_by | 可省略，默认空；依赖须存在且无循环，外部门禁用 G-* |
| spec / plan | 可省略；默认内容在 README，分文件时链接实际正文；共享 Spec 可引用 records 下另一已登记项的 spec.md |
| head / branch / created_at | 新建工具自动记录；head 是工作或 Stage 起点基线，检查点不得覆盖。没有 Git 时明确 none |
| labels / framework_scope | 可省略，按检索需要填写 |
| next_action | 只在 YAML 维护一次；终态说明结束后的动作或无后续动作，不复制到快照/交接表 |

范围、AC、决定和验证是实际内容，不由生成器替人确认。planned 项可保留待明确内容；实施前填写实际目标和验收条件，不能用真实活动/终态项的占位符冒充完成。

验证记录可在 README“验证”或独立 Evidence，使用 `AC-01` 等编号、实际命令/证据、`passed`/`failed`/`not_run`/`pending` 状态及限制。工具只运行结构检查，不验证证据叙述真实性；completed 所有已声明验收条件有通过依据，不能有明示未通过条件或只有空文件、全部 pending。同一 AC 有重试记录时，以最后一条为当前结论，保留历史失败。取消说明原因、验证到哪里和未覆盖范围。

## 按需拆分与影响

范围复杂时建立 Spec，跨阶段实施时建立 Plan；过程或证据妨碍接手阅读时才拆 Log/Evidence。范围、实施步骤与结果分别维护，避免重复权威正文。

Schema 4 Plan 可声明 `impact_schema: 2`（省略时按新格式处理），文档影响只列实际受影响页面、处置和原因；无影响写“无”。计划中的 Stage ID 如 V1-01A，README 当前 Stage 必须能定位到定义。共享 Spec 不意味着实施上依赖其所属工作项，依赖字段只表达实际前置成果。

## 历史兼容

Schema 2/3 保持原文件和字段合同，终态默认冻结，不批量升级。Schema 2 的 base_head 继续兼容；Schema 3 使用 head、Plan impact_schema: 1 和原十类 DOC-* 影响矩阵。新任务使用 Schema 4，旧活动项只有需要实质改造时才迁移，记录原因。

历史终态有 Evidence；明确 archived 的 Legacy 可保留 source.md.txt 及局限。新格式的内嵌证据不用于静默删除旧证据文件。

## 检查点

1. 实施前明确范围与 AC；多阶段项当前只推进一个明确 Stage。
2. 普通实施按需留下重要决定或阻塞，不逐命令写日志。
3. 可交接点、暂停或完成时，更新当前状态、必要背景、实际验证及限制，并同步发生变化的稳定事实。
4. 执行 `python3 workspace/scripts/maintain.py --checkpoint <ID>`，一次刷新视图、检查工作项/文档/链接和 Git diff，并记录工具本次结果。失败先修复或保持未完成，如实交接。

只读审查用 `python3 workspace/scripts/maintain.py --check`，不写视图或记录。新建用 `--new <ID> --title <标题>`，只生成单页规划项及机械字段。工具不提交、不重置、不自动改业务完成状态；工具检查块不作为业务 AC 证据。对终态执行检查点只更新派生视图和输出结果，不修改已冻结正文。

Stage 是可验证实施单元，与 Git 提交独立。未授权提交时保留真实未提交范围；授权后按任务范围提交，不为回填提交自身哈希另建提交。

## 稳定文件与架构

稳定页有 document_status 与 last_updated，只有事实成立才作为 active 权威；draft 可保留模板提示。历史废弃/替代正文声明替代入口或原因。

Current 默认一页，先说明覆盖、已验证能力和限制；需要时拆 Technology、Components、Flows、Data Integration、Verification。Target、ADR、Roadmap 在产生已接受目标或长期决策时建立；没有需求时不填假事实，也不要求这些可选目录存在。删除可选骨架须同时修复链接和登记。

新增/移动/删除稳定页时更新登记与入口，完整检查覆盖真实链接、孤立页与状态。跨仓检查仅在实际跨仓变更时触发，不规定无条件“两仓每周检查”或每次人工三路径走读。

## 模板维护

本仓库的 template-source/ 是模板源，skills/ai-collab-bootstrap/templates/ 是发行副本；实例化项目只有自己的工作区，不维护这一对源与副本。模板规则或工具变化后运行回归，再执行模板维护仓根目录的 `python3 scripts/sync_templates.py --write` 和 `--check`。这是模板发行操作，不是实例化项目日常任务的额外步骤；不得复制真实工作项、用户文档、人工日志和私人数据。
