# Data Standards

## violation 形态
```json
{ "rule": "durability/spec-coordinates", "severity": "high", "line": 12, "message": "file-path coordinate in spec: src/store.js" }
```
- severity: high = 破坏 launch 耐久门禁/契约缺失；low = 格式不齐（如缺一个推荐字段）

## 规则清单（v1 种子，见 CONTEXT.md durability gate）
1. `context-md/entry-format`（low）：`## <term>` 条目缺 定义:/边界:/已解决的歧义: 任一行
2. `durability/spec-coordinates`（high）：`.omc/specs/**/*.md` 出现路径坐标——token 的最末 `/` 分隔段含 `.`，或 token 以 `/` 结尾（`src/store.js`、`path/to/` 是坐标；含 `/` 但其末段无 `.` 的规则标识如 `context-md/entry-format` 不是）；CJK 邻接豁免（相邻或内含 CJK——继承 F-0008 教训）；`<!-- origin-fragment -->` 行内标记豁免

> 勘误（来自 C2 裁决 #1）：上一版把坐标谓词写成「含 `/` 且含 `.`」，会误伤含 `/` 但末段无扩展名的规则标识（`context-md/entry-format` 等）。本版改为「最末 `/` 分隔段含 `.`，或以 `/` 结尾」，保证真实文件路径与目录地址被捕获、规则标识被豁免。实施该规则的 spec 同步此勘误。
3. `claude-md/sections`（high）：CLAUDE.md 缺少六个必需节（项目约定/架构原则/规范索引/决策记录/共享背景/Agent 指南）
