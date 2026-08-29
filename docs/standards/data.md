# Data Standards

## violation 形态
```json
{ "rule": "durability/spec-coordinates", "severity": "high", "line": 12, "message": "file-path coordinate in spec: src/store.js" }
```
- severity: high = 破坏 launch 耐久门禁/契约缺失；low = 格式不齐（如缺一个推荐字段）

## 规则清单（v1 种子，见 CONTEXT.md durability gate）
1. `context-md/entry-format`（low）：`## <term>` 条目缺 定义:/边界:/已解决的歧义: 任一行
2. `durability/spec-coordinates`（high）：`.omc/specs/**/*.md` 出现路径坐标（含 `/` 且含 `.` 或以 `/` 结尾的 token；CJK 邻接豁免——继承 F-0008 教训）；`<!-- origin-fragment -->` 行内标记豁免
3. `claude-md/sections`（high）：CLAUDE.md 缺少六个必需节（项目约定/架构原则/规范索引/决策记录/共享背景/Agent 指南）
