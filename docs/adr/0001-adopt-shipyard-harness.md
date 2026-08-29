# ADR-0001: Adopt the shipyard harness

- 状态: accepted ｜ 日期: 2026-08-29 ｜ 置信度: high

## 背景
本项目是 shipyard 生态的 markdown 纪律 linter（机械化 launch 的耐久门禁），同时是 Run 4 dogfood 载体（首个 Python 项目，验证 harness 的栈可移植性）。

## 决策
采用 shipyard harness；design-system 因无 UI 跳过；Python 3.12+ pytest 零第三方运行时依赖。

## 理由
- 机械化"spec 禁坐标"这条人工门禁，是 Run 1-3 反馈回路的自然延伸
- 换栈验证：harness 的 5 载体应当与实现语言无关

## 后果
- 继承 sy check 的教训（F-0008 CJK 误报）：路径类规则必须处理 CJK 邻接
- pytest 依赖需 dev 安装（`pip install pytest`），运行时零依赖不变
