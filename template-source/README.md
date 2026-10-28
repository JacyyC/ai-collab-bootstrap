---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# <PROJECT-NAME>

> 本仓库是长期维护模板 v4。实例化时填写项目定位与已验证能力，删除本提示；业务事实尚未产生时保持草稿，不把模板骨架当成交付能力。

## 项目定位

<服务谁、解决什么问题、当前边界。>

## 当前可用能力

<仅写代码、配置、测试或实际运行证明的能力，以及限制。>

## 目录

- `project/`：实际业务代码、测试、配置与[产品文档](project/docs/index.md)。
- `workspace/`：工作项、交接、技术事实、规划与治理工具；不复制业务代码。
- [AGENTS](AGENTS.md)：人类与 AI 工作协议；`开发日志.md` 为人工专用。

## 日常使用

接手读 AGENTS、[WORK](workspace/docs/WORK.md)和当前工作项。小任务用一页 README，复杂任务才拆范围、计划、过程与证据；没有变更的事实不重复同步。

```bash
python3 workspace/scripts/maintain.py --new V1-01 --title "第一项工作"
python3 workspace/scripts/maintain.py --checkpoint V1-01
```

新建命令只生成待填写范围和 AC 的规划项，不代替范围确认。检查点刷新视图、运行完整结构检查并记录工具实际结果；业务验收仍需真实测试。只读审查使用 `python3 workspace/scripts/maintain.py --check`。

## 按需入口

- [工作项管理](workspace/docs/work-items/README.md)、[文档导航](workspace/docs/README.md)；
- [已验证架构](workspace/docs/framework/current/v1.md)；[目标骨架](workspace/docs/framework/target/v1.md)、[路线骨架](workspace/docs/ROADMAP.md)、[长期决策](workspace/docs/decisions/README.md)按实际需要采用；
- [历史](workspace/docs/HISTORY.md)、[文档政策](workspace/docs/DOCUMENTATION_POLICY.md)、[记录格式](workspace/docs/DOCUMENT_LIFECYCLE.md)。

初始化按项目真实目录保留、重命名或删除空的 backend/frontend；现有项目可保留原代码布局，由 README 明确项目区边界。默认 Current 用一页，内容增长后按职责拆分；目标、路线和 ADR 没有事实时不填虚构内容。
