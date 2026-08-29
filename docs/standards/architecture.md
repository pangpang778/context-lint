# Architecture Standards

## 模块边界
- `context_lint/cli.py`：argparse 入口 + 退出码（0/1/2），不含规则逻辑
- `context_lint/engine.py`：规则注册表 + 运行器（规则失败 ≠ violation，异常 → exit 2）
- `context_lint/rules/`：每条规则一个模块（context_md.py、durability.py、claude_md.py）
- 规则间禁止互相 import——为什么：规则独立可关停、可测试

## 错误处理
- violation 统一形态 `{rule, severity, line, message}`；CLI 输出人类可读行 + `--json`
- 文件读取失败 → 该文件记一条 internal-error 并继续（不中断整批）——为什么：lint 全量优先于单文件成败

## 依赖方向
- cli → engine → rules，严格单向
