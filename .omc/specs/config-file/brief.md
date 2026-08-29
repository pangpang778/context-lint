# Mission Brief — config-file (C1, Run 5 F3)

## Objective
`.context-lint.json`（root 可选配置）：
```json
{ "ignore": ["rule-id"], "severityOverrides": { "rule-id": "high" } }
```
- `ignore`：规则整体停用（不产生 violation，不进 --json）
- `severityOverrides`：改判某规则全部 violation 的 severity（high↔low）
- **exit 语义演进**：exit 1 当且仅当存在**非豁免且 severity=high** 的 violation；low 违规照常报告但不失败——这是 severity 机制的自然结论（契约变更，测试要更新）

## 继承的硬教训（sy check F-0008/F-0009 同款）
- 损坏 JSON → exit 2
- **未知规则 ID → exit 2 并报出 ID**（防拼写静默失效）

## Pre-approved seams
- S1 配置加载器（纯：root → config；缺文件=空配置；损坏→ConfigError）
- S2 引擎应用（纯：violations × config → 过滤/改判后集）
- S3 CLI 集成（check/fix 全部接配置；--json 反映改判后 severity）
- S4 e2e（含：ignore 生效、severity 改判生效、坏配置 exit 2、未知 ID exit 2、无配置=现状不变）

## Non-goals
- CLI 配置 flags、~ 全局配置、per-line ignore（已由 F1 覆盖）、新规则

## Ticket 期望
3 张串行：T1 加载器（纯）、T2 引擎+CLI 接线、T3 e2e+README。
