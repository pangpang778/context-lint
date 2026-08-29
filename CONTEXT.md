# Glossary

## rule（规则）
- 定义: 一条可执行的 lint 检查，输入 harness 文件的文本，输出零或多个 violation。
- 边界: 规则只读；规则自身崩溃 ≠ violation（是内部错误，exit 2）。
- 已解决的歧义: 与 sy check 的 audit rule 同构，但作用对象是 markdown 散文而非文件图。

## violation（违规）
- 定义: 一条被规则确认的格式/纪律偏差，含 rule、severity、line、message。
- 边界: severity high = 破坏 harness 契约（如 spec 里出现文件路径坐标）；low = 格式不齐。
- 已解决的歧义: violation ≠ drift（drift 是文件系统 vs 声明的偏差，violation 是文件内容 vs 格式契约的偏差）。

## durability gate（耐久门禁）
- 定义: launch 协议规定 spec/tickets 禁止文件路径与行号坐标——context-lint 把这条人工门禁机械化。
- 边界: 只检查 .omc/specs/**/*.md；例外（带 origin 注明的原型片段）通过行内标记 `<!-- origin-fragment -->` 豁免。
- 已解决的歧义: 这是对 launch 协议中人工门禁的机械化，规则语义以 launch.md 为准。
