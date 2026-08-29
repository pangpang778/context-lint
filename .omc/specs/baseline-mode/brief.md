# Mission Brief — baseline-mode (C1, Run 5 F2)

## Objective
`--baseline <file>` 与 `--baseline-generate`：存量违规冻结、只拦新增——linter 落地既有仓库的标准采用模式。

## 语义
- `--baseline-generate`：跑全量规则，把当前全部 violation 写入指定基线文件（JSON：`{ "version": 1, "generatedAt": ISO, "violations": [{rule, file, message}] }`），exit 0
- `--baseline <file>`：当前 run 的每条 violation 计算指纹 `sha1(rule + relpath + message)`，与基线比对：命中 = 存量（不计入 exit 1，stdout 中标记 `[baseline]` 前缀）；未命中 = 新增（计入 exit 1）
- `--json`：`{ "violations": [...], "baseline": { "matched": N, "new": M } }`
- relpath 用相对 `--root` 的 posix 斜杠路径（跨平台稳定）

## Pre-approved seams
- S1 指纹函数（纯：violation → fingerprint string）
- S2 基线读写（JSON 加载/生成；损坏基线 → exit 2）
- S3 比对过滤 + CLI 集成（generate 与 compare 两模式、exit 语义）
- S4 e2e（基线命中/新增/无基线退化 = 全量计违规）

## Non-goals
- 自动修基线（手工 --baseline-generate 重建）、按行号指纹（行号漂移）、多基线合并

## Ticket 期望
3 张垂直切片：T1 指纹+基线 IO（纯/IO）、T2 比对过滤+CLI 两模式、T3 e2e+README。串行（共享 CLI 面）。
