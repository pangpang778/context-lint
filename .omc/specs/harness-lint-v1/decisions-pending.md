# Decisions Pending — harness-lint-v1（C5 已裁决存档）

> Run 4 C5 人工裁决记录（2026-08-29）。三条均不阻塞合并。

## D1. --json 下内部错误的表面
- 选项: stderr（现状） vs 折叠进 JSON payload {items, errors}
- **裁决: 保留 stderr** —— 维持"stdout 永远是纯 violation JSON"的管道友好不变量。agent 建议，人批准。

## D2. GBK/遗留编码文件
- 选项: 拒绝为 internal error（现状） vs 自动转码 UTF-8
- **裁决: 保持拒绝** —— 永不猜测编码；中文 Windows 场景如需支持，走显式 --encoding 参数（Run 3+ 评估）。process.md 已补 UTF-8-only 政策行。

## D3. 覆盖率门禁
- 选项: 现状（seam/回归定向测试，52 条） vs pytest --cov 80% 地板
- **裁决: 延后** —— 记为 follow-on；等规则数量翻倍后再上覆盖率地板，避免过早指标化。
