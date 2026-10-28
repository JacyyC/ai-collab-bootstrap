# 主流 Agent 接入

核对日期：2026-10-28。这里区分 **安装 Skill** 与 **让工具加载项目协议**：Skill 用于初始化、升级或整理；安装后的用户项目以根 AGENTS.md 为唯一协议。接入只做一次，不成为每轮工作的额外步骤。

## 选择客户端

所有目标都是 skills 的父目录，安装后应出现 `ai-collab-bootstrap/SKILL.md`、两份规则、scripts/、references/ 与 templates/。整个 Skill 不依赖本仓库位置。

| 工具 | 项目级 / 个人级目录 | 调用与边界 |
|---|---|---|
| Codex CLI / App | 本地 Codex 常用 `~/.codex/skills/`，自定义环境为 `$CODEX_HOME/skills/`；其他发现目录依版本文档确认 | `$ai-collab-bootstrap`；本项目此前用 Codex 代理读取 Skill 实测，未宣称本轮完成全局自动发现测试 |
| Claude Code | `.claude/skills/` / `~/.claude/skills/` | `/ai-collab-bootstrap`，也可按 description 自动选择；项目协议用薄 CLAUDE.md 引入 |
| Cursor | `.agents/skills/` 或 `.cursor/skills/`；个人 `~/.agents/skills/` 或 `~/.cursor/skills/` | Agent 中自然语言点名，按当前版本 Skills 列表确认；官方还列有 Claude/Codex 目录兼容 |
| GitHub Copilot | 项目 `.github/skills/`、`.claude/skills/` 或 `.agents/skills/`；个人 `~/.copilot/skills/` 或 `~/.agents/skills/` | 按使用界面支持情况选择；IDE、CLI、coding agent 支持面不同，不把网页聊天视为本地执行环境 |
| Gemini CLI | `.gemini/skills/` 或 `.agents/skills/`；个人 `~/.gemini/skills/` 或 `~/.agents/skills/` | 自然语言点名；按 CLI 的 Skills 管理与激活提示操作，可能需要批准加载 |
| Windsurf / Cascade | 传统项目目录 `.windsurf/skills/`，个人 `~/.codeium/windsurf/skills/` | 当前官方入口已转向 Devin Desktop，新文档使用 `.devin/skills/` 并兼容旧路径；按实际产品版本选择 |
| Cline | `.cline/skills/` / `~/.cline/skills/` | Skills 设置中确认启用，使用自然语言触发；不同版本可能需要开启该功能 |
| OpenCode | 常见项目 `.opencode/skills/`、个人 `~/.config/opencode/skills/` | 原生路径本轮未完成官方页面核实；先按当前官方文档确认，否则使用下方通用方式 |
| Roo Code | 本页不预设 Skill 原生目录 | 可在项目 Rules 中要求读取 Skill；是否原生发现目录依安装版本确认 |
| TRAE | 官方提供 SKILL.md 的 Skills 管理能力 | 在客户端 Skills 设置中按当前版本导入完整目录；本仓库本身不需要 .trae 包装，未做 TRAE 自动发现实测 |
| ZCode / 其他 Agent | 产品名可能对应不同工具，不预设隐藏目录 | 未确认具体官网与版本时，用通用读取方式；支持 SKILL.md 后再按其官方目录安装 |

以上是接入说明与本地分发验证，**不代表每个客户端都已实际运行**。已核实官方目录的条目来自文末来源；未核实或产品不明确的条目明确保留限制，不猜测调用命令。

## 安装一次

从维护仓库根目录运行，例如 Claude Code 项目级安装：

```bash
python3 scripts/install_skill.py --destination /path/to/project/.claude/skills
python3 scripts/install_skill.py --destination /path/to/project/.claude/skills --write
```

Codex 个人级安装示例：

```bash
python3 scripts/install_skill.py --destination ~/.codex/skills --write
```

有自定义 CODEX_HOME 时使用该目录下的 skills。安装脚本仅复制完整目录，拒绝覆盖已有同名目录，不修改宿主权限或客户端配置。升级时保留原版本再替换，不合并两份不同版本。

不要求把同一份 Skill 同时装入所有兼容目录；每个客户端选择一个入口即可。自动发现未刷新时重载项目或新开会话，在 Skills 列表查 `ai-collab-bootstrap`。只把 Skill.md 粘贴到规则框会丢失配套模板。

## 项目协议只维护一份

完成初始化后，Codex 等支持 AGENTS.md 的工具直接使用根协议。对需要专用入口的工具，只加薄入口，不复制整套规则。

Claude Code 的 CLAUDE.md 示例：

```markdown
# 项目工作协议

@AGENTS.md
```

Gemini CLI 的 GEMINI.md 或编辑器项目 Rules 可写：

```text
开始修改前读取仓库根目录 AGENTS.md，并按其中的入口接手当前工作项。
```

Copilot 可在 `.github/copilot-instructions.md`、Cursor 可在项目 Rule、Cline/Roo/TRAE 可在项目规则界面加入同样指引。需要始终加载的规则时在客户端设置对应作用域。客户端是否原生读取 AGENTS.md、是否支持导入语法，以对应版本为准；不要把普通相对链接当成已保证自动执行。

模板结构检查允许 CLAUDE.md、GEMINI.md 等入口；链接错误仍会失败。增加薄入口不改变项目协议、验收或 Git 授权。

## 无原生 Skill 功能时

将整个 Skill 放在客户端可访问的普通目录，直接请求：

```text
读取 /path/to/ai-collab-bootstrap/SKILL.md，按它为当前项目建立必要工作区。
保持原代码布局，已有入口合并处理，不覆盖用户文件。配套模板在同目录 templates/。
```

这是显式读取，不等同于自动发现。Agent 需要能读写本地文件并运行 Python；仅能网页聊天而无仓库访问和命令执行的工具，只能给建议，不能执行模板初始化。

## 验证是否接上

1. 客户端能发现该名称，或显式读取 SKILL.md 并找到同目录 templates/。
2. 先让它只读检查一个项目；能区分实际运行、未运行与不适用。
3. 在临时目录初始化后，运行目标项目的 `python3 workspace/scripts/maintain.py --check`，并核对原文件未被覆盖。

本仓库回归自动验证安装、配套文件、冲突保护、初始化和 CLAUDE.md 兼容；厂商客户端自动发现需在相应客户端核对，不伪造这一层结果。

## 官方来源

- [Codex Skills](https://developers.openai.com/codex/skills/)：本轮请求返回 HTTP 403；Codex 常用个人目录与当前环境说明交叉核对，新增版本目录需使用者确认。
- [Claude Code Skills](https://code.claude.com/docs/en/skills)：本轮读取成功，包含 .claude/skills 和显式命令。
- [Claude Code Memory](https://code.claude.com/docs/en/memory)：项目协议导入方式。
- [Cursor Skills](https://cursor.com/docs/skills)：本轮读取成功，列有 .agents、.cursor 和兼容目录。
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills)：本轮读取成功，目录支持依使用界面而异。
- [Gemini CLI Skills](https://geminicli.com/docs/cli/skills/)：本轮读取成功，包含 .gemini 和 .agents。
- [Cascade Skills](https://docs.windsurf.com/windsurf/cascade/skills)：本轮跳转至 Devin Desktop，说明新旧目录兼容。
- [Cline Skills](https://docs.cline.bot/customization/skills.md)：本轮读取成功，列有工作区与全局目录。
- [OpenCode Skills](https://opencode.ai/docs/skills/)：本轮访问超时，原生发现仍需核对。
- [TRAE Skills](https://docs.trae.ai/ide/skills)：本轮读取成功，提供 SKILL.md 管理说明；不据此声称已完成客户端实测。

安装或加载有变化时，仅更新这里的对应条目；不分叉不同厂商的核心工作流程。
