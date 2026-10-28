---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# 技术决策

模板尚未登记任何已接受 ADR。只有跨工作项、长期影响架构或迁移成本的决定才进入本目录；局部实施选择留在对应工作项 Log。

## 决策索引

| ID | 状态 | 标题 | 替代关系 |
|---|---|---|---|

## 新建决策

复制 [ADR 模板](ADR-0000-template.md)，分配下一个固定四位编号并在上表登记。

ADR 在 YAML 中使用 `decision_status: proposed|accepted|rejected|superseded`。只有用户可以作最终决定；被替代的 ADR 必须声明 `replaced_by`，不静默重写旧结论。
