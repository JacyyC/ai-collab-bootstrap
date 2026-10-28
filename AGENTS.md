# Skill 仓库开发约定

本仓库发布 `ai-collab-bootstrap`。根目录维护 Skill、模板源、分发工具和使用说明；不创建项目工作区、工作项或检查点。

- 先读根 README，核对 Git 状态，只处理当前任务范围，保留用户与协作者改动。
- `skills/ai-collab-bootstrap/` 是可安装 Skill；`template-source/` 是模板权威源，发行模板只用 `python3 scripts/sync_templates.py --write` 生成。
- 用户项目的工作协议位于 template-source/AGENTS.md；仅在修改模板时按需读取，不把用户项目流程套到本仓库。
- 完成前运行 README 中适用的校验与回归，将变更原因和真实验证结果写入提交说明或 PR。没有实际运行的检查不能写通过。
- 个人开发日志如已存在，保持原样且不进入发行或提交；密钥、私人数据与缓存不进入仓库。
- Git 提交、历史重建、推送、发布和部署依用户授权执行；提交使用简洁具体的中文说明，无需工作项编号。
