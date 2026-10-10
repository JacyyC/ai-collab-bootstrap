# 来源与授权

本仓库由维护者指定的长期维护模板与 `ai-collab-bootstrap` skill 副本整理而来。原始目录未修改；原 Git 历史未复制，公开仓库使用审查后的独立快照。

保留原有协议、分类规则、Schema 2/3 兼容逻辑、Schema 4 模板、维护工具与回归测试；原 `.trae/skills` 中 skill 移至公开 `skills/`。个人工具草稿、开发日志、历史工作项及首次实测报告不进入公开包。模板源和发行副本分别维护，发行副本由白名单单向生成。

本次新增仓库文档、安装/初始化辅助脚本、仓库校验和 CI 配置。本仓库运行脚本仅用 Python 标准库；未识别到携带的第三方字体、图片、二进制或 vendored 依赖。没有发现原有 `LICENSE`；自动扫描不能证明所有代码与文档的著作权归属。

CI 使用 GitHub 官方 checkout/setup-python Actions，以及 [Gitleaks](https://github.com/gitleaks/gitleaks) 8.30.1 容器扫描公开快照；这些工具按各自许可获取与执行，其代码或二进制没有放入本发布包。

维护者于 2026-10-10 确认有权公开源码和文档，同意采用 MIT，版权署名 JacyyC，并授权在 `JacyyC/ai-collab-bootstrap` 创建公开仓库。[根许可证](../LICENSE)与[安装包许可证](../skills/ai-collab-bootstrap/LICENSE)一致。

自动检查未独立核实著作权、雇佣或委托合同。以后如引入第三方内容，应保留其原许可证与版权声明。
