---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# Workspace

这里保存长期维护所需的当前工作、范围、计划、验证、交接与技术决策。实际代码和稳定产品使用说明进入 [project](../project/README.md)。

日常接手只读根 [AGENTS](../AGENTS.md)、[WORK](docs/WORK.md)和所选工作项 README。需要浏览结构、建立稳定说明或修改治理时再读[导航](docs/README.md)、[政策](docs/DOCUMENTATION_POLICY.md)与[生命周期](docs/DOCUMENT_LIFECYCLE.md)。

状态与下一步以工作项 YAML 为准；受控视图由工具生成。Schema 4 单页记录是默认，复杂内容按需拆分；Schema 2/3 历史不批量改写。

执行中新授权和返修安排回流现有范围/计划，实际结果进入验证记录；README 保留当前入口，历史依据按阶段/批次定位。拆分前按[内容归属](docs/DOCUMENTATION_POLICY.md#现行约定与历史依据)判断独立保存价值。

工作项、检查点和只读检查统一使用 `workspace/scripts/maintain.py`；[模板](templates/work-item/README.md)保留必需信息而不要求空的计划、日志和证据文件。人工开发日志不由 AI 维护。
