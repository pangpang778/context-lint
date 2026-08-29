# Process Standards

## 流程
- conventional commit；main 直推；门禁 `pytest`（或 `python -m pytest`）全绿
- 新规则 = 新模块 + 注册表登记 + 测试 + docs/standards/data.md 清单同步（四处缺一不可）

## 与 shipyard 的关系
- 本工具机械化 launch 的耐久门禁与 harness 格式契约；发现的规则缺口回灌 shipyard-log 的 findings
- 与 sy check 分工：sy 管文件图（存在性/指针），context-lint 管散文内容（格式/纪律）
