# 20_wiki（LLM-WIKI 引擎运行时域）
* **定位**：由 `InternalKnowledgeEngine` 自动管理的知识图谱存储根目录（对应后端配置 `vault_root`）。
* **规则**：自动化流水线**仅允许写入 `debug/`**；人工审核后在 Obsidian 中直接将卡片拖拽至 `release/` 或 `gold/`（全局逻辑 ID 引用确保零断链）。
