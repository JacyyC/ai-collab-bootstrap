# AI 协作 · 长期维护工作区

一个中文 Agent Skill，为长期维护的软件项目建立、更新或整理 AI 协作工作区：把实际代码与产品说明留在原布局，把范围、交接和验证证据放在 `workspace/`。

**适合**已经需要多轮迭代、工作交接和事实追溯的项目。**普通阅读、一次性问答和微小修改**无需引入完整工作区。它不是生产监控、自动运维或无人值守部署工具。

## 能提供什么

- 三条路径：新建协作工作区、原地修补既有工作区、在授权范围内整理混合文档。
- Schema 4 默认单页工作项；复杂任务才拆 Spec、Plan、Log、Evidence，保留 Schema 2/3 读取兼容。
- 可执行 Python 检查工具：工作项状态与依赖、派生视图、本地 Markdown 链接、检查点证据。
- 随 skill 携带独立模板，不依赖作者电脑路径，不自动提交、推送或部署。

这些工具检查的是文档结构，不能证明业务验收完成，也不能保证模型一定按说明行动。详见 [验证与边界](docs/VALIDATION.md)。

## 环境和安装

Python **3.10+**。运行工具仅使用标准库；Git 用于仓库检查和回归测试，无 Git 项目会明确报告相应检查未运行。没有网络服务、API Key 或额外 Python 包依赖；调用模型的费用取决于使用的客户端。

从本仓库根目录执行，目标填为你的客户端实际使用的 skill 目录：

```bash
python3 scripts/install_skill.py --destination /path/to/your/skills
python3 scripts/install_skill.py --destination /path/to/your/skills --write
```

第一条只预览；第二条复制完整 `ai-collab-bootstrap/`。已有同名目录时拒绝覆盖，安装前检查目标客户端的发现路径。Codex 常见本地位置是 `${CODEX_HOME:-$HOME/.codex}/skills`；路径支持以所用客户端版本为准。支持项目技能目录的客户端也可将目标设为目标项目的技能目录。Trae 可使用项目的 `.trae/skills`，但本次未在 Trae 中验证自动发现行为。

也可以手工完整复制 [skills/ai-collab-bootstrap](skills/ai-collab-bootstrap/)，保留全部相对路径。安装脚本不修改客户端配置。

## 调用示例

```text
使用 $ai-collab-bootstrap，给这个已有项目添加长期协作工作区。
保留 src/、tests/ 和现有代码布局，先核对用户改动，只补必要入口和工具。
```

```text
使用 $ai-collab-bootstrap，只检查现有工作区并报告缺口，不创建或改写文件。
```

```text
使用 $ai-collab-bootstrap，将 docs/ 中已确认属于开发过程的文档归位，
保留 API 手册和人工日志，修复受影响引用并执行实际项目检查。
```

首次创建也可使用 [bootstrap 脚本](skills/ai-collab-bootstrap/scripts/bootstrap.py)预览和安全复制骨架；它保留既有代码目录，遇到任何模板目标冲突就停止，更新与迁移由 skill 按项目事实处理。

```bash
python3 skills/ai-collab-bootstrap/scripts/bootstrap.py --target /path/to/project
python3 skills/ai-collab-bootstrap/scripts/bootstrap.py --target /path/to/project --write
```

复制后让 Agent 填写项目定位、日期和已验证事实，再使用目标项目的工具：

```bash
python3 workspace/scripts/maintain.py --new TASK-01 --title "整理项目入口"
python3 workspace/scripts/maintain.py --check
python3 workspace/scripts/maintain.py --checkpoint TASK-01
```

新建项只处于规划状态；必须明确范围与验收条件后才实施，不能把骨架当作已完成成果。

## 仓库与维护

```text
skills/ai-collab-bootstrap/  可安装 skill（规则、UI 元数据、脚本、模板发行件）
template-source/           模板与 Python 工具权威源
scripts/                   安装和仓库校验入口
docs/                      验证、发布与授权说明
.github/workflows/         自动检查配置
```

维护模板后运行：

```bash
python3 -m unittest discover -s template-source/workspace/scripts/tests -t template-source/workspace/scripts -v
python3 template-source/workspace/scripts/sync_skill_templates.py --write --destination skills/ai-collab-bootstrap/templates
python3 scripts/validate_repo.py
python3 -m unittest discover -s scripts/tests -v
```

生成命令只复制白名单文件，排除真实工作项、人工日志、私人数据和缓存。`template-source/README.md` 的项目占位符必须保留：它是供用户实例化的模板，不是本仓库介绍。不要反向同步发行副本。贡献方法见 [CONTRIBUTING](CONTRIBUTING.md)。

## 发布状态和许可

当前是 **v0.1.0 发布候选**，已完成本地结构、工具回归和隔离安装验证；尚未在 GitHub 执行 CI，也未完成跨客户端或独立模型行为测试。

源码、文档和可安装 skill 采用 [MIT 许可证](LICENSE)，版权署名 JacyyC。维护者已确认公开及授权权利。发布记录见 [发布清单](docs/RELEASE_CHECKLIST.md)和 [来源与授权](docs/PROVENANCE.md)。
