# Mission Brief — inline-ignore (C1, Run 5)

## Objective
为 context-lint 增加**行内豁免**机制：被标记的行免除 violation。标记 = 该行末尾（或独立 preceding 行）的注释 `<!-- context-lint:ignore -->`（可带规则 ID 列表：`<!-- context-lint:ignore rule1,rule2 -->`）；裸标记豁免该行全部规则。作用范围：规则 1-3（context-md 条目按被违反行豁免；durability 按 token 所在行；claude-md 按节首行）。

## Scope boundary
- `--json` 输出每规则增加 `suppressed` 计数（被豁免的 violation 数）
- 退出码不变（豁免的 violation 不计入 exit 1）
- 测试：S1 匹配器（纯函数：行+标记 → 豁免的规则 ID 集）、S2 引擎集成（过滤后计数 + suppressed 统计）、S3 端到端（含豁免样例夹具）

## Non-goals
- 文件级整体忽略、块范围忽略（区间）、--fix、baseline（下一个功能）

## Pre-approved seams
- S1 匹配器（纯）
- S2 引擎集成（engine.py 过滤 + suppressed 计数）
- S3 e2e（pytest 集成 + 夹具仓库）

## Non-goals 补充
- 不改变任何既有规则的判定语义（只做豁免层）

## Ticket 期望
2-3 张垂直切片：T1 匹配器+测试、T2 引擎+CLI 集成+文档、（可选 T3 e2e 夹具）。共享面少，可并行或串行由拆票判断。
