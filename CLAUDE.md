# context-lint — Agent & Human Shipyard

## 项目约定
- Python ≥ 3.12，pytest 测试，零第三方运行时依赖（标准库 only）
- CLI 入口 `context_lint/cli.py`（argparse），包 `context_lint/`
- 命名：模块 snake_case，类 PascalCase，测试 `tests/test_*.py`
- 提交：conventional commits

## 架构原则
- 规则数据驱动：每条 lint 规则一个纯函数（输入文本/树，输出 violation 列表），注册进注册表
- 只读审计：linter 绝不修改被检文件
- 退出码契约：0 = 干净，1 = 有 violation，2 = 用法/内部错误

## 规范索引（全文在 docs/standards/）
- 架构规范: docs/standards/architecture.md
- 数据规范: docs/standards/data.md
- 流程规范: docs/standards/process.md

## 决策记录（全文在 docs/adr/，此处只列 load-bearing 的）
- ADR-0001: adopt shipyard harness

## 共享背景
- 术语: CONTEXT.md ｜ 业务知识: docs/business/ ｜ 决策背景: docs/adr/

## Agent 指南
- 交付走 /oh-my-claudecode:launch；术语以 CONTEXT.md 为准；可复用能力沉淀到 .omc/skills/
- 本项目无 UI：design-system 载体不适用（drydock 跳过项）
- 教训继承（来自 sy check 的 F-0008）：路径类规则必须考虑 CJK 邻接与散文误报
