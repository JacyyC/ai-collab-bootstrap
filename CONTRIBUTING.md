# 贡献说明

先阅读 [仓库协议](AGENTS.md)与 [README](README.md)。修改范围明确后直接实施，变更原因和验证结果写入提交说明或 PR，不创建仓库工作区。

- Skill 行为：修改 `skills/ai-collab-bootstrap/SKILL.md` 与实际需要的规则/引用。
- 模板与用户项目工具：只修改 `template-source/`，再运行 `python3 scripts/sync_templates.py --write`。禁止反向同步或手改生成副本。
- Agent 接入：更新 [接入说明](skills/ai-collab-bootstrap/references/agent-setup.md)中的对应条目与官方来源；区分文档核对、自动化验证和真实客户端测试。

文件归属或工作记录规则变化时，按下表核对覆盖范围，修改实际受影响处；细则集中维护，其他入口只保留执行所需短规则和链接，不复制整套合同。

| 层次 | 核对位置 |
|---|---|
| 内容归属与文件合同 | `template-source/workspace/docs/DOCUMENTATION_POLICY.md`、`DOCUMENT_LIFECYCLE.md` |
| 修复深度、重评估、经验与验证复用 | Lifecycle 的按范围处理规则、Policy 的经验与证据归属；核对 AGENTS、五份模板与无模板回退提示 |
| 项目代码、内部分类、命名与版本 | `template-source/workspace/docs/PROJECT_LAYOUT.md`；根/模块 README 的实际职责入口与现存导航；不强制项目目录或全量登记表 |
| 日常接手与执行 | `template-source/AGENTS.md`、`workspace/README.md`、`workspace/docs/WORK.md` |
| 实例化后的记录提示 | `template-source/workspace/templates/work-item/` 的 README、Spec、Plan、Log、Evidence；`maintain.py` 的无模板回退入口 |
| Skill 新建、更新、整理与审查 | `skills/ai-collab-bootstrap/SKILL.md`、`classification-rules.md`、`consistency-check.md` |
| 工具、回归与发行 | `maintain.py`、`workspace_views.py`、`scripts/template_release.py` 白名单与相关行为测试；同步生成并核对 `skills/ai-collab-bootstrap/templates/`，不手改副本 |

项目布局规则重点核对日常 AGENTS、根/项目 README、Workspace/WORK/导航入口、五份工作项模板与 `maintain.py` 无模板回退提示，再核对 Skill 的共用边界、新建/更新路径、分类和审查规则。Spec 明确整理与兼容范围，Plan 安排分类、迁移和验证，Log 保存重要取舍，Evidence 保存实际审查与测试结果，单页 README 承担相同职责。仅修改实际受影响提示，不在五份模板复制完整规则；新增规则文件须进入发行白名单，并由原有入口链接。

用户提供的目录或文件用于核对问题，不能直接固化成所有项目必须遵循的目录树、语言命名或版本号。规则应给出按职责、所属边界、技术栈和生命周期选择的依据，示例与强制合同明确区分；覆盖核对也要确认没有因某个案例扩大适用范围或破坏项目已有约定。

修复验证规则以影响、风险和实际证据指导处理深度，细则集中在 Lifecycle/Policy，日常协议与模板仅保留对应职责的提醒。核对局部修复能保持轻量、复杂/复发/回退/高风险能扩大诊断、旧证据按依赖判断、经验有适用的落实位置；不得从单个案例引入统一失败次数、全量测试要求、新进度表或自动语义门禁。保留各项目已经明确的验收、授权与预算要求。

表内省略的 `workspace/` 工具路径均位于 `template-source/`。根仓库不运行用户项目工作项流程；现有用户项目升级需按其实际入口和工具合并，不因本仓库模板更新而自动生效。

提交前运行 README 列出的结构校验和相关回归。新测试验证可观察行为，例如冲突时不写入、只读不改文件、旧记录可读；避免仅比对文案。若修改发行件，再验证重复生成没有变化。

用户项目日常修改不承担 Skill 仓库的发行检查。真实工作记录和人工日志不得进入模板。未获明确授权不推送或公开发布。

## 生命周期与同步闭环

本仓根 AGENTS 管 Skill 维护，template-source/AGENTS 管用户项目日常；两者不互相覆盖。Skill 仅用于首次接入、对齐、升级及范围内必要迁移。三份规则分别维护内容归属、记录合同、运行文件方法；日常不全读，规则详情不重复到全部入口。五份工作项模板是本地库存，实际任务默认仅 README。

在上表基础上按实际影响核对：模板根/模块 README、AGENTS、Workspace/WORK/现存导航、三份规则、五模板及 maintain 正常/回退生成；再核对 Skill 的 description/三路径/分类/审查、接入说明与 agents/openai.yaml。根 README、根 AGENTS、来源/安全和验证说明只修改受影响职责；不为覆盖清单机械改写无关文件。变更传播的完整性由执行者审查，不使用正文关键词门禁。

源模板人工修改与 Skill/根说明人工同步后，运行根同步入口生成模板副本和 SHA-256 清单，再验证整个 Skill。脚本不自动更新人工说明、已安装 Skill 或用户项目。新增/退役资产同时调整 scripts/template_release.py 与行为回归；旧清单资产只有未定制时才由发行同步移除，不能将其用于覆盖实例化项目。未知文件保留并审查实际打包范围。

用户项目日常工具留在 template-source/workspace/scripts/；发行器、benchmark、回归及夹具留维护仓 scripts/、tests/，不复制到项目。可选知识模板位于 template-source/optional/，随 Skill 发行但不默认安装；五份工作项模板仍默认安装。历史管理页和独立 CLI 已存在时保留兼容。

Skill 包升级与项目升级分开：前者更换完整包，后者合并实际本地协议、模板、工具与读取入口，记录来源指纹/不可变修订和采纳范围。部分采纳与未知来源如实说明；不加新 Schema、全覆盖升级器或第二进度账本。没有额外授权不改全局安装、其他项目或客户端配置。

验证使用 README 的当前命令及 Skill Creator quick_validate；重复生成应更新 0 个资产。新建最小原生布局、无 Git/全局 Skill、复杂拆分、旧 Schema/人工区兼容、冲突与私有边界、源/发行漂移分别通过实际行为验证。远端 CI 与本地结果分开记录。
