---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# 按需文档入口

日常只需 [AGENTS](../../AGENTS.md)、[WORK](WORK.md)和所选工作项。新增正文在其直接入口提供链接及用途，不强制维护全量文件登记表。

| 问题 | 权威入口 |
|---|---|
| 项目定位、使用、模块职责与稳定知识 | 根 README 及实际模块/文档入口 |
| 当前范围、AC、下一步、阻塞与实际验证 | 工作项 README；拆分正文按其链接读取 |
| 内容归属、现行约定回流与证据复用 | [Policy](DOCUMENTATION_POLICY.md) |
| 字段、状态、文件组织、修复深度、验收与检查点 | [Lifecycle](DOCUMENT_LIFECYCLE.md) |
| 源码、测试、工具、配置、资源的归位与迁移 | [Layout](PROJECT_LAYOUT.md) |
| 规划与活动、终态历史 | [WORK](WORK.md)、[HISTORY](HISTORY.md) |

五份本地模板库存：[README](../templates/work-item/README.md)、[Spec](../templates/work-item/spec.md)、[Plan](../templates/work-item/plan.md)、[Log](../templates/work-item/log.md)、[Evidence](../templates/work-item/evidence.md)。实际任务默认只创建 README。

默认无需 project/docs、framework、Target、Roadmap、ADR 或第三管理页。已经有内容的说明按项目实际职责保留；需要新的长期目标或决定时，从当前项目约定或 Skill 随附可选模板建立。不得为了删空骨架删除用户事实。

`workspace/scripts/` 只承担项目本地协作检查。发行器、开发测试和结构 benchmark 属模板维护仓，不成为每项业务工作流程。旧项目自有导航、登记和工具可继续维护，升级时保护定制。
