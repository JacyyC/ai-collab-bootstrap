# AI 协作 · 长期维护工作区

一个中文 Agent Skill，为需要多轮迭代、交接和事实追溯的项目建立、更新或整理协作工作区。已有代码和产品说明保留原布局，工作范围、下一步和验证依据放在 `workspace/`。

## 它与模板的关系

本仓库发布的是 **Skill + 内置模板**。Skill 告诉 Agent 何时新建、更新或整理工作区；模板提供工作协议、单页工作项和实际检查工具。安装 Skill 后，再由 Agent 按项目事实实例化工作区。这里的 README 是产品介绍，[模板 README](template-source/README.md)中的占位符则留给使用者填写。

- 默认单页工作项；复杂任务才拆 Spec、Plan、Log、Evidence，兼容 Schema 2/3。
- 一个维护入口检查工作项、派生视图、文档和链接，记录实际工具结果。
- 不自动提交、部署或代替业务验收；普通阅读和一次性问答无需安装工作区。
- 一份通用 Skill 支持不同客户端，接入差异仅涉及安装、触发和协议入口。

## 安装

Python **3.10+**，工具仅用标准库。Git 用于差异检查和开发回归；无 Git 的目标项目会明确报告相应检查未运行。不需要 API Key 或附加服务。

在本仓库根目录执行，目标填客户端实际识别的 **skills 父目录**：

```bash
python3 scripts/install_skill.py --destination /path/to/your/skills
python3 scripts/install_skill.py --destination /path/to/your/skills --write
```

第一条预览，第二条安装整个 `ai-collab-bootstrap/`；已有同名目录时拒绝覆盖。无需把模板仓整体放进目标项目，也不要只复制 SKILL.md。

Codex、Claude Code、Cursor、GitHub Copilot、Gemini CLI、Windsurf、Cline、OpenCode 与其他客户端的路径、调用和版本边界见 **[主流 Agent 接入说明](skills/ai-collab-bootstrap/references/agent-setup.md)**。本仓库不自动安装到你的全局环境；接入文档不代表已在每个客户端实际验证。

## 使用

Codex 可显式调用：

```text
使用 $ai-collab-bootstrap，为这个已有项目建立长期维护工作区。
保留 src/、tests/ 和已有产品文档，先识别用户改动，再补必要入口和工具。
```

Claude Code 可用 `/ai-collab-bootstrap`。其他客户端按接入说明触发；未支持自动发现时，让 Agent 读取整个 Skill 的 SKILL.md 再执行。

```text
使用 ai-collab-bootstrap，只读检查现有工作区并报告缺口，不新建或修改文件。
```

无冲突的新目录可以先复制骨架：

```bash
python3 skills/ai-collab-bootstrap/scripts/bootstrap.py --target /path/to/project
python3 skills/ai-collab-bootstrap/scripts/bootstrap.py --target /path/to/project --write
```

脚本默认预览，检查清单和所有目标冲突后才写入。遇到现有 README 或工作区时交给 Skill 合并；不使用覆盖参数。复制后由 Agent 填写项目定位、日期与真实事实，再使用 **目标项目** 的工具：

```bash
python3 workspace/scripts/maintain.py --new TASK-01 --title "整理项目入口"
python3 workspace/scripts/maintain.py --check
python3 workspace/scripts/maintain.py --checkpoint TASK-01
```

`--new` 只产生 planned 项；明确范围和 AC 后才能实施。业务测试按实际变化运行，结构检查不能证明业务完成。

## 仓库结构与维护

```text
skills/ai-collab-bootstrap/   可独立安装：入口、规则、接入说明、脚本、模板发行件
template-source/             模板与治理工具的唯一权威源
scripts/                    本仓库安装、同步、校验与分发测试
docs/                       维护、验证与来源说明
```

仓库根目录只维护 Skill、模板源和分发工具。`workspace/` 位于模板内部，由 Skill 安装到目标项目使用；本仓库不建立工作项、交接记录或检查点。

修改模板后，在本仓库运行：

```bash
python3 scripts/sync_templates.py --write
python3 scripts/validate_repo.py
python3 -B -m unittest discover -s template-source/workspace/scripts/tests -v
python3 -B -m unittest discover -s scripts/tests -v
```

只修改用户项目时，不执行模板发行和全套仓库回归。详情见 [贡献说明](CONTRIBUTING.md)、[验证边界](docs/VALIDATION.md)与[来源说明](docs/PROVENANCE.md)。源码与 Skill 采用 [MIT](LICENSE) 许可。
