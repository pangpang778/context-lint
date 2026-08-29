# Mission Brief — Run 4 (C1)

## Objective
Build **context-lint** v1: a Python CLI that mechanically enforces the shipyard harness's markdown discipline. Three rule groups (see docs/standards/data.md 种子清单):
1. `context-md/entry-format` — CONTEXT.md 条目格式
2. `durability/spec-coordinates` — .omc/specs/**/*.md 禁止文件路径坐标（机械化 launch 耐久门禁；CJK 邻接豁免，`<!-- origin-fragment -->` 行内豁免）
3. `claude-md/sections` — CLAUDE.md 六必需节

## Scope boundary
- Python ≥3.12 标准库 only（运行时零第三方依赖；测试用 pytest，dev 依赖）
- CLI：`python -m context_lint [--root <dir>] [--json]`，退出码 0/1/2
- 违规形态 `{rule, severity, line, message}`（docs/standards/data.md）

## Non-goals
- 自动修复（--fix）、sy check 的文件图规则（存在性/指针）、配置文件

## Run-4 特殊说明
- 首个 Python dogfood：验证 harness 栈可移植性
- 继承 sy check 教训（F-0008）：路径规则必须处理 CJK 邻接
- 不得 git commit/push——orchestrator 在检查点之间统一提交
