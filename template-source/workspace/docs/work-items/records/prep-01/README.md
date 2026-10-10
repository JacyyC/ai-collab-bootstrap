---
schema_version: 4
document_status: active
last_updated: 2026-10-10
id: PREP-01
title: "准备可独立安装的公开 Skill 发布候选"
status: completed
updated_at: 2026-10-10T16:21+08:00
next_action: 由维护者确认版权人、许可证和 GitHub 信息后按发布清单继续
closed_at: 2026-10-10
branch: "none"
head: none
---

# PREP-01：准备公开 Skill 发布候选

## 目标与边界

将用户指定的副本整理为独立可安装的 ai-collab-bootstrap 发布候选，保留治理合同和工具回归，补文档、安装入口、CI 和公开审查；原目录保持不变。本项不安装到用户环境、不创建 GitHub 远程、不提交、推送或发布，不代替维护者确认版权。

## 验收条件

- AC-01：技能结构有效，相对引用与单向模板同步检查通过。
- AC-02：原有 30 项工具回归通过，隔离安装和初始化能运行；预览及冲突保护不改用户文件。
- AC-03：审查后的副本秘密扫描无命中，原目录内容和 Git 状态不变，发布限制和授权决定如实记录。

## 必要背景与交接

公开 skill 放在 skills/，template-source/ 是权威模板，发行副本通过白名单生成。个人档案保留在审查环境，未进入公开包。主目录和 skill 各有 MIT 草案，待维护者确认署名与权利；没有正式许可证或远程提交。

## 文档影响

调整发行默认目录与回归固定路径；现有模板规则保持不变。公开仓库说明在外层 README 和 docs/，不复制进模板。

## 验证

| AC | 状态 | 方法或命令 | 结果或证据 | 限制 |
|---|---|---|---|---|
| AC-01 | passed | scripts/validate_repo.py；官方 quick_validate.py | 技能结构、38 文件模板清单、源/发行检查和全仓本地引用均通过 | 不证明模型行为 |
| AC-02 | passed | unittest discover（源工具与 scripts/tests） | 原 30 项回归与 7 项安装/初始化实测均通过；预览与冲突保护、独立检查点链路成功 | 未执行跨客户端或模型行为实测 |
| AC-03 | passed | Gitleaks 8.30.1 dir --redact；SHA-256 与 Git 状态比较 | 副本零命中；原 107 文件哈希与 Git 状态完全相同；外层 docs/ 记录授权决定与限制 | 不证明所有著作权归属；只审查新快照 |

<!-- maintenance-check:start -->
## 工具检查

检查时间：2026-10-10T16:18:50+08:00

仅记录本次工具执行的结构、链接与 Git 检查；不代表业务 AC 通过。

| 检查 | 状态 | 本次结果 |
|---|---|---|
| 工作项与派生视图 | passed | 1 个工作项，3 个派生视图 |
| 文档结构与全部本地链接 | passed | 17 个稳定文档，66 个链接和锚点 |
| git diff --check | not_run | N/A：根目录没有 Git 仓库，未验证差异空白 |

<!-- maintenance-check:end -->
