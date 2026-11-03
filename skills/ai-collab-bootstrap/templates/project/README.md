---
document_status: active
last_updated: YYYY-MM-DD
template_version: 4
governance_schema: 4
---

# 项目实际代码与文件区

`project/` 保存业务代码、测试、配置、运行资产和稳定产品文档。工作状态、候选设计、交接和治理工具保存在 `workspace/`。

backend/frontend 为可删除的目录占位；按真实项目边界保留或重命名。现有成熟代码布局可以保留原位置，在根 README 明确责任，不为了采用模板强制移动。

本页或根 README 链接的实际模块入口说明源码、测试、运行配置、项目工具、资源与产物的目录职责和必要命令，按真实内容维护，不预建所有类别。后续新增文件先找已有职责与实现，模块内部也按实际边界、层次、用途及版本分类，命名遵循所属技术栈；新增目录或改变职责时更新对应入口。创建、版本区分、临时代码处置与检查点审查见 [项目文件布局](../workspace/docs/PROJECT_LAYOUT.md)。

稳定产品说明进入 [docs](docs/index.md)，实际能力或运维改变后更新；架构事实同步对应 Current。构建产物、依赖、缓存、密钥和本地数据不提交。
