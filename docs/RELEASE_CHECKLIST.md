# v0.1.0 发布检查

## 已准备

- 可安装的 `skills/ai-collab-bootstrap/`，相对引用及完整模板。
- 中文 README、范围说明、调用示例、贡献方法和来源说明。
- 安全安装与初始化脚本：默认预览，明确 `--write` 后才写入，不覆盖冲突。
- 工具回归、模板漂移检查、技能元数据和本地链接检查入口。
- GitHub Actions 配置，最小只读仓库权限。
- 副本敏感扫描和原目录完整性核对，实测结果见验证说明。

## 公开前的维护者决定

- [x] 维护者确认有权公开源码与文档，采用 MIT，版权署名 JacyyC；已启用正式许可证。
- [x] 维护者授权在 `JacyyC/ai-collab-bootstrap` 公开发布；中文展示名为「AI 协作 · 长期维护工作区」。
- [x] 复核公开文件清单、安装入口、许可与文档；自动扫描不证明绝对无敏感内容。

## 执行发布时

- [x] 使用审查后的新快照，没有导入原 Git 历史。
- [x] 初始化独立 `main`，检查完整 diff；采用 JacyyC 的 GitHub noreply 提交邮箱。
- [x] 创建[公开仓库](https://github.com/JacyyC/ai-collab-bootstrap)，首次推送的 GitHub Actions 全部通过；详情见 [验证说明](VALIDATION.md)。
- 首版 tag / Release：`v0.1.0`，下载和公开状态以 [Releases](https://github.com/JacyyC/ai-collab-bootstrap/releases) 为准；发布说明包含验证范围和使用边界。

已启用私密漏洞报告。原始来源目录未修改，可安装包未安装到维护者的客户端环境。
