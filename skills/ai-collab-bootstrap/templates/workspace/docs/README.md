---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# Workspace 导航与登记

日常接手从根 [AGENTS](../../AGENTS.md)、[WORK](WORK.md)和所选工作项 README 开始；本页在找说明或改变文档结构时使用，不列入每次任务的固定阅读。

## 按需阅读

| 问题 | 入口 |
|---|---|
| 工作范围、步骤、验证与下一步 | 工作项 README；有独立 Spec/Plan/Evidence 时按链接读取 |
| 新建、状态或字段规则 | [Lifecycle](DOCUMENT_LIFECYCLE.md) |
| 文档内容归属 | [Policy](DOCUMENTATION_POLICY.md) |
| 架构与未来差异 | [Framework](framework/README.md) |
| 规划、历史与长期选择 | [Roadmap](ROADMAP.md)、[HISTORY](HISTORY.md)、[ADR](decisions/README.md) |

## 稳定文件登记表

路径相对于仓库根目录。登记源维护职责与事实入口；新增/移动/废弃稳定正文时同步本表和直接链接。目录登记覆盖其职责内文件，动态工作项与人工日志不逐文件登记。

| 路径 | 权威职责 | 读者 / 时机 | 事实源 |
|---|---|---|---|
| `README.md` | 项目定位、已验证能力、日常入口 | 使用者；首次进入或定位变化 | 代码、配置与验证 |
| `AGENTS.md` | 执行协议与权限边界 | 贡献者/AI；接手 | 用户约定、Policy/Lifecycle |
| `project/README.md` | 业务区边界 | 开发者；目录调整 | 实际布局 |
| `project/docs/index.md` | 稳定产品文档导航 | 使用者；找使用/开发/运维说明 | 稳定产品页 |
| `workspace/README.md` | 工作区入口 | 维护者；认识工作区 | 治理与导航 |
| `workspace/docs/README.md` | 导航与稳定文件登记 | 维护者；找正文或新增/移动稳定页 | 登记与文件树 |
| `workspace/docs/DOCUMENTATION_POLICY.md` | 内容归属与同步 | 贡献者；内容边界或政策变化 | 用户治理约定 |
| `workspace/docs/DOCUMENT_LIFECYCLE.md` | 记录格式与检查合同 | 贡献者；字段/状态/模板变化 | Schema与工具 |
| `workspace/docs/WORK.md` | 当前工作投影 | 接手者；日常 | 工作项YAML |
| `workspace/docs/HISTORY.md` | 终态索引 | 审计者；查历史 | 工作项YAML |
| `workspace/docs/ROADMAP.md` | 未来成果路线骨架 | 规划者；有实际目标时 | 已接受范围 |
| `workspace/docs/work-items/README.md` | 工作项管理投影 | 维护者；选项/查历史 | 工作项YAML |
| `workspace/docs/framework/README.md` | 架构导航与分层 | 维护者；架构问题 | Current/Target |
| `workspace/docs/framework/current/v1.md` | 单页已验证架构骨架 | 开发者；技术事实变化 | 实现与验证 |
| `workspace/docs/framework/target/v1.md` | 可选目标骨架 | 规划者；已接受未来差异 | 范围与采用门槛 |
| `workspace/docs/decisions/` | 长期决策与模板 | 维护者；有长期选择时 | 已接受决定 |
| `workspace/templates/work-item/` | 单页及可选分文件模板 | 贡献者；创建或拆分记录 | Lifecycle |
| `workspace/scripts/` | 统一维护、校验、发行及效果比较工具 | 维护者；检查点/模板变更 | 实际执行结果 |

## 动态记录与工具

`work-items/records/<id>/` 永久保存每项工作，单页是默认；分文件与项内 archive 按内容需要建立。终态正文默认冻结，纠错留日期与依据；人工开发日志不纳入 AI 维护。

- [单页模板](../templates/work-item/README.md)，可选 [Spec](../templates/work-item/spec.md)、[Plan](../templates/work-item/plan.md)、[Log](../templates/work-item/log.md)、[Evidence](../templates/work-item/evidence.md)。
- [统一入口](../scripts/maintain.py)：`--new ID --title 标题`、`--checkpoint ID`、`--check`。
- [视图工具](../scripts/workspace_views.py)、[健康检查](../scripts/document_health_check.py)、[链接检查](../scripts/check_markdown_links.py)保留独立入口，日常不重复调用。
- [发行同步](../scripts/sync_skill_templates.py)：仅模板维护时 `--write` / `--check`；实例化项目不增加此步骤。
- [效果比较](../scripts/benchmark_maintenance.py)与 `workspace/scripts/tests/`：仅治理/工具变化时运行，使用隔离场景，不成为每项业务工作的必跑流程。
