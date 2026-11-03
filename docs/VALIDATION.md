# 验证与边界

本仓库验证模板结构与派生视图、工具行为、可携带安装和骨架初始化。仓库校验只读，不需要根目录工作区或工作项；项目维护工具与工作项模板仅存在于待安装的模板中。

```bash
python3 scripts/validate_repo.py
python3 -B -m unittest discover -s template-source/workspace/scripts/tests -v
python3 -B -m unittest discover -s scripts/tests -v
```

验证采用临时目录：安装前后核对文件、冲突时不覆盖、模板完整性失败时不写入、无 Git 明确不适用、单页任务/旧格式/验收缺失按合同处理。仓库校验还会报告误放在根目录的 workspace/，不擅自删除其中内容。结构检查不能证明模型一定遵循说明或代替业务测试。

主流工具的安装位置来自各自官方资料或明确标注的待核对信息。未逐一登录、安装或操作各厂商客户端；自动发现、账号差异和客户端版本仍需在使用环境确认。接入说明只在安装或排查加载时读取。CI 配置随仓库提供，远端是否通过以实际运行结果为准。

2026-10-29 本地实测：31 项模板治理回归与 10 项安装、分发和仓库回归全部通过；Skill Creator 校验、38 文件发行同步、Python 语法和本地 Markdown 链接检查通过。根目录无需 workspace/ 即可完成校验，安装后的项目仍可生成自己的工作区并运行检查点。

## 2026-11-01 文件组织规则

本地实际运行：

- `python3 -B -m unittest discover -s template-source/workspace/scripts/tests -v`：41 项通过，其中新增 10 项文件组织行为回归。
- `python3 -B -m unittest discover -s scripts/tests -v`：10 项安装、初始化和仓库回归通过。
- `python3 scripts/validate_repo.py`：模板源、独立发行件、Python 3.10 语法、本地链接与锚点及 Git 差异检查通过。
- `python3 scripts/sync_templates.py --write` / `--check`：39 个白名单文件一致；再次生成更新 0 个文件。
- Skill Creator `quick_validate.py`：Skill 基本结构通过。

新增回归通过真实维护入口验证未跟踪散乱记录被拒绝、失败检查不移动或删除原文件、标准正文和专题的 README 入口、专题命名、参考式链接、原始产物入口，以及旧格式、关闭项和 archive 的兼容保护。示例代码、注释、未使用的链接定义与工具检查块不能充当专题入口。

布局规则约束非终态、非归档的 Schema 4 工作项，不为统一命名改写历史。工具不判断专题是否值得拆分、内容是否重复或用途说明是否充分；这些仍由执行者审查。本次没有运行真实模型执行行为测试，回归结果不能证明 Agent 一定遵循文件创建纪律。

## 2026-11-02 现行约定回流与分类附件

更新范围覆盖项目 AGENTS、Policy/Lifecycle、日常导航、五份工作项模板与无模板回退入口、Skill 入口/分类/审查规则和发行副本。贡献说明增加规则变更覆盖表，便于核对相关入口；细则仍集中在 Policy/Lifecycle。已有项目和已安装 Skill 不随本仓库更新自动升级，本次未修改项目2的工作项或运行工具。

本地实际运行：

- 模板治理回归 `python3 -B -m unittest discover -s template-source/workspace/scripts/tests -v`：47 项通过，新增 6 项分类附件行为回归。
- 安装、初始化和仓库回归 `python3 -B -m unittest discover -s scripts/tests -v`：10 项通过。
- `python3 scripts/validate_repo.py`：源模板与独立发行件、Python 3.10 语法、本地链接和锚点、Git 差异检查通过。
- `python3 scripts/sync_templates.py --write` / `--check`：39 个白名单文件一致，重复生成更新 0 个文件；Skill Creator `quick_validate.py` 通过。

新增行为覆盖散放机器结果、未分类附件和非法分类目录的只读拒绝；从 README 链接的 Evidence 进入批次附件；授权原件和历史失败内容保持不变；示例/注释/工具检查块不能充当附件入口；终态机器结果不被新规则迁移。

回流是否充分、历史授权与现行边界是否一致、技术证据是否适用由执行者读取核对，不使用标题关键词、文件数量或正文匹配做语义门禁。没有运行真实模型执行行为测试，未宣称模型遵循或业务质量通过。

## 2026-11-03 运行文件分类、命名与版本

新增 `PROJECT_LAYOUT.md` 作为创建前归属、目录内分类、技术栈命名、实际版本边界与检查点审查的规则正文。根/项目 README 保存实际目录职责；项目 AGENTS、Workspace/WORK/导航、Policy/Lifecycle、五份工作项模板、无模板回退提示与 Skill 新建/更新/分类/审查入口联动引用，发行白名单纳入新规则。贡献说明补充覆盖核对位置与各模板职责，避免只更新入口而遗漏实例化提示。

参考项目仅作只读核对，确认测试层次、业务职责与工作项命名混合，以及测试支持和跨测试文件导入需要在迁移时修复；本次未移动该项目文件。通用规则按职责、模块/包/服务边界、既有技术栈约定和版本/生命周期判断，覆盖源码、测试、工具、配置、资源及生成文件；不固化参考项目的目录、工作编号、语言命名或版本号。规则区分并存合同版本、迁移序列、发布验收套件与普通迭代，不要求按每轮执行复制整套源码和测试。

本地实际运行：

- `python3 -B -m unittest discover -s template-source/workspace/scripts/tests -v`：47 项通过。
- `python3 -B -m unittest discover -s scripts/tests -v`：10 项通过，覆盖安装、初始化与仓库只读校验。
- `python3 scripts/validate_repo.py`：源模板与独立发行件、Python 3.10 语法、本地链接/锚点与 Git 差异检查通过。
- `python3 scripts/sync_templates.py --write` / `--check`：40 个白名单文件一致，重复生成更新 0 个文件；Skill Creator `quick_validate.py` 通过。

本次调整规则、导航与生成提示，未新增仅比对文案的测试或按目录文件数、文件名关键词判定代码职责的门禁。现有工具检查不自动证明项目代码分类、版本隔离或运行行为正确；需由执行者读取实现并核对新增、改名、未跟踪及任务内已提交文件，测试迁移还需检查收集范围。本次未运行真实模型守约测试或参考项目迁移验收；已安装 Skill 和已有项目需按更新流程合并规则后才生效。
