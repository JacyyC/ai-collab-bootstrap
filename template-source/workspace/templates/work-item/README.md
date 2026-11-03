---
schema_version: 4
document_status: active
last_updated: YYYY-MM-DD
id: <WORK-ID>
title: <TITLE>
status: planned
updated_at: YYYY-MM-DDTHH:MM+08:00
next_action: 明确目标与验收条件
---

# <WORK-ID>：<TITLE>

## 目标与边界

<说明用户成果、当前有效范围与约束、授权依据和非目标；实施前填写。>

## 验收条件

- AC-01：<可观察且可验证的结果。>

## 必要背景与交接

<仅保存影响接手的决定、阻塞、未提交范围和验证缺口；没有则写无。不重复 YAML 状态或下一步。>

## 文档影响

无。

## 验证

| AC | 状态 | 方法或命令 | 结果或证据 | 限制 |
|---|---|---|---|---|
| AC-01 | pending | 未运行 | 尚无结果 | <未覆盖范围> |

运行代码、测试与脚本按 `workspace/docs/PROJECT_LAYOUT.md` 进入所属模块并在模块内分类、命名和区分实际兼容版本，本页引用实现。检查点前核对任务内新增、改名与未跟踪文件及临时代码去向，验证区简述实际审查结果。

新授权、范围和返修安排更新现有范围/计划章节，实际结果进入验证章节；不追加多份“最新授权/当前技术门”。内容较多时按 `workspace/docs/DOCUMENTATION_POLICY.md` 回流 Spec/Plan/Log/Evidence，本页保留当前入口。仅需独立保存、引用或复核的附件按 `workspace/docs/DOCUMENT_LIFECYCLE.md` 分类、命名和登记。状态与下一步只维护 YAML；工具检查点块不代替业务验收。
