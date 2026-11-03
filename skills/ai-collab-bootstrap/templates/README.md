---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# <PROJECT-NAME>

<说明项目服务谁、解决什么问题、当前已验证能力及限制。>

## 使用与目录

<链接实际安装、运行、测试、源码模块和稳定产品文档。保留既有布局，不要求创建 project/、backend/、frontend/ 或固定架构目录。>

`workspace/` 保存协作记录、项目内模板和维护工具；业务源码、测试与稳定知识沿用项目原位置。架构事实、已接受目标和候选设想注明身份，不用空骨架表示能力。

## 协作入口

首次接入、对齐或获取新版后升级使用 ai-collab-bootstrap；接入后的日常工作由本地 [AGENTS](AGENTS.md)、[WORK](workspace/docs/WORK.md)和所选工作项承接，无需每轮加载 Skill。

```bash
python3 workspace/scripts/maintain.py --new TASK-01 --title "明确的工作目标"
python3 workspace/scripts/maintain.py --check
python3 workspace/scripts/maintain.py --checkpoint TASK-01
```

新建仅产生 planned 单页，填写实际范围和 AC 后实施。复杂时使用项目内五份模板，按需拆分。工具检查不证明业务通过。

- [工作区说明](workspace/README.md)、[按需文档入口](workspace/docs/README.md)、[历史](workspace/docs/HISTORY.md)。
- [内容归属](workspace/docs/DOCUMENTATION_POLICY.md)、[记录合同](workspace/docs/DOCUMENT_LIFECYCLE.md)、[运行文件布局](workspace/docs/PROJECT_LAYOUT.md)。

升级已安装 Skill 不会升级本项目；需要合并本地协议、模板、工具和实际入口，并保留定制、用户改动与历史原件。新增或变更模块职责时维护实际模块入口，不逐文件维护第二份台账。
