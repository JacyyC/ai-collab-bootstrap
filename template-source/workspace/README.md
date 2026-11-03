---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# Workspace

项目日常接手从根 [AGENTS](../AGENTS.md)、[WORK](docs/WORK.md)和所选工作项开始。稳定产品/架构知识、源码与测试沿用根 [README](../README.md)链接的实际位置。

- [WORK](docs/WORK.md)：规划与活动；[HISTORY](docs/HISTORY.md)：终态，按需查询。两者只从工作项状态源派生。
- [Policy](docs/DOCUMENTATION_POLICY.md)：内容放哪里；[Lifecycle](docs/DOCUMENT_LIFECYCLE.md)：字段、拆分、验证与流转；[Layout](docs/PROJECT_LAYOUT.md)：运行文件归位、命名与迁移。
- [单页模板](templates/work-item/README.md)默认使用；复杂时按需采用本地 Spec/Plan/Log/Evidence 库存，不默认创建五份正文。

统一工具为 `python3 workspace/scripts/maintain.py --check/--checkpoint ID/--new ID --title 标题`。具体参数分别调用，不把此行当作一个 shell 命令。项目不运行模板仓发行同步，也不依赖全局 Skill 才能日常维护。

同一维护入口还提供显式字段更新、分类原件导入和真实章节链接，参数与边界见 [Lifecycle](docs/DOCUMENT_LIFECYCLE.md#机械字段、附件与链接)。正文保持任务内容，复杂部分按需拆开；原始失败与适用结果从本地入口进入。

首次接入、对齐或版本升级时再使用 Skill；新规则需真正合并到本地读取链、生成链和工具，记录实际采纳范围。
