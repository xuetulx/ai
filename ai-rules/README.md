# ai-rules 权威源声明

> **建立日期**：2026-10-12（DSH 全局配置自审第 2 步）
> **本文件的作用**：消除"同一批规则三代并存、无权威声明"的冲突（自审发现 P1-①）。

## 唯一权威源

```
GeneralRules\00_master_index.md
GeneralRules\01_core_behavior.md
GeneralRules\02_file_operations.md
GeneralRules\03_coding_standards.md
GeneralRules\04_version_control.md
GeneralRules\05_security.md
GeneralRules\06_engineering.md
GeneralRules\07_quality.md
```

**`GeneralRules\` 是唯一有效规则源。** 其中：
- `00_master_index.md` = 总索引与路由表
- `01~07` = 按需加载的子文件（**01 为必读**）
- `VERSION_LOG.md` = 版本日志（追加型）
- `.ai_audit.log` = 操作审计日志（追加型）

## 已归档（历史，勿引用）

| 归档路径 | 原位置 | 说明 |
|---|---|---|
| `archive\merge\` | `merge\` | 上一代**整本**规则：`AgentAI_项目文件操作规则_v2.2.md`、`AI_RULES_编程参考规范_v3.1.md` |
| `archive\split\` | `split\` | 更早的**切片**规则：`File-operation-rules\00~17`、`Programming-specifications\B_00~B_10` |

**归档原因**：三者内容覆盖同一批规则，**没有任何文件声明谁是权威版**；照旧版本执行会与 `GeneralRules\` 直接冲突
（典型：批量删除阈值、受保护文件清单、commit type 集合在各版本取值不同）。

**权威性替代关系（执行时请改用右侧）**：

| 旧文件里的路径 | 现应引用 |
|---|---|
| `merge\AgentAI_项目文件操作规则_v2.2.md` | `GeneralRules\01_core_behavior.md` + `02_file_operations.md` |
| `merge\AI_RULES_编程参考规范_v3.1.md` | `GeneralRules\03_coding_standards.md` + `05_security.md` + `06_engineering.md` |
| `split\File-operation-rules\*.md` | `GeneralRules\01` + `02` + `04` |
| `split\Programming-specifications\*.md` | `GeneralRules\03` + `05` + `06` + `07` |

## 与全局 AGENTS.md 的关系

`$DSH_HOME\AGENTS.md`（全局规则，每个新会话自动加载）与本 `GeneralRules\` 是**两份并存但已对齐**的规则：

- 全局 AGENTS.md = **常驻**层（体积受预算约束，只放边界与路由）；
- `GeneralRules\` = **按需**层（长内容、分语言规范、审查清单）。

**对齐状态（2026-10-12）**：批量删除门槛、凭证黑名单、受保护文件清单、commit type、分支保护名
五处取值已统一，详见 `GeneralRules\VERSION_LOG.md` 当日条目。**再出现分歧时，以全局 AGENTS.md 为准**
（它是唯一会被自动加载的一份），并立即回写本目录。

## 归档目录内文件的开头标记

`archive\merge\` 与 `archive\split\` 下每个 `.md` 的开头已加：

```
> ⚠️ 历史归档（2026-10-12）：本文件不是权威规则源，请勿引用或据此执行。
> 权威源：..\..\GeneralRules\。归档原因见 ..\..\README.md。
```
