---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# 项目实际代码与文件区

`project/` 保存业务代码、测试、配置、运行资产和稳定产品文档。工作状态、候选设计、交接和治理工具保存在 `workspace/`。

backend/frontend 为可删除的目录占位；按真实项目边界保留或重命名。现有成熟代码布局可以保留原位置，在根 README 明确责任，不为了采用模板强制移动。

稳定产品说明进入 [docs](docs/index.md)，实际能力或运维改变后更新；架构事实同步对应 Current。构建产物、依赖、缓存、密钥和本地数据不提交。
