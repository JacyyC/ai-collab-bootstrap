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
