---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# 工作项管理入口

本页按规划、活动与终态浏览工作项。状态源是 `records/<稳定小写id>/README.md` YAML，受控区由工具生成，不在这里维护正文副本。

<!-- workspace-view:start -->
## 规划项

| 优先级 | ID | 下一动作 | 入口 |
|---|---|---|---|

当前没有规划工作项。

## 活动项

| 优先级 | ID | 状态 | Stage | 下一动作 | 入口 |
|---|---|---|---|---|---|

当前没有活动工作项。

## 历史项

| 终态日期 | ID | 结果 | 入口 |
|---|---|---|---|
| 2026-10-10 | PREP-01 | completed | [PREP-01](records/prep-01/README.md) |
<!-- workspace-view:end -->

## 维护

日常接手从 [WORK](../WORK.md)进入当前项。新建用 `python3 workspace/scripts/maintain.py --new ID --title 标题`；填写实际范围与 AC 后实施，在检查点运行 `--checkpoint ID`。单页记录足够时不创建空的分文件。

原有 Schema 2/3 保持兼容，历史查 [HISTORY](../HISTORY.md)。[格式细则](../DOCUMENT_LIFECYCLE.md)仅在字段或规则问题时读取。
