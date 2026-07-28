# AI 规则体系版本日志

---

## v1.0 (2026-07-01)

### 初始版本

1. **核心行为原则**（01_core_behavior.md）
   - 边界优先原则
   - 三级权限体系（BLOCK/ASK/DO）
   - AI Agent 行为四原则（思考、简单、精确、目标）
   - 12 项合规检查清单

2. **文件操作规则**（02_file_operations.md）
   - 文件读取/创建/修改/删除规则
   - 目录结构规则
   - 批量操作规则
   - 临时文件与缓存规则
   - 产物输出规则

3. **代码编写规范**（03_coding_standards.md）
   - 前置检索规范
   - 代码输出强制规则
   - 通用编码规范
   - 分语言特殊规则（Python、JS/TS、Go、Shell）
   - 提交消息规范（Conventional Commits）

4. **版本控制与工程规范**（04_version_control.md）
   - Git 操作约束
   - 分支管理规则
   - 提交消息规范
   - AI 生成文件的版本管理
   - 审计日志与可追溯

5. **安全规范**（05_security.md）
   - 敏感信息保护
   - AI 指令文件安全保护
   - 上下文泄露防护
   - 代码安全编码规范
   - Agentic AI 安全风险防护（OWASP Top 10）
   - MCP 安全规范

6. **工程质量与工具链**（06_engineering.md）
   - 工程级代码质量
   - AI 输出约束
   - 测试配套规范
   - 依赖与供应链安全
   - 安全合规编码
   - 资源限制

7. **质量保障体系**（07_quality.md）
   - 多工具兼容层
   - 反模式清单（12 项）
   - 文件精简与定期修剪
   - CI 验证建议
   - 批量操作回滚机制
   - Claude Code 专属规范

### 参考标准

- OWASP GenAI Security Project
- AGENTS.md 开放标准（LF/AAIF 托管）
- Karpathy Skills（github.com/forrestchang/andrej-karpathy-skills）
- Agent Rules（github.com/steipete/agent-rules）
- Cursor Rules 最新格式
- Claude Code Best Practices
- Conventional Commits
- Google Style Guides

---

## v1.1 (2026-07-15)

### 新增功能

1. **Cursor .mdc 格式支持**（全体系）
   - `00_master_index.md`：新增跨工具格式对照表，添加 Cursor `.mdc` 文件格式说明
   - `02_file_operations.md`：新增 §2.1.1 `.mdc` 文件创建规范，包含 YAML frontmatter 模板和四种激活模式
   - `03_coding_standards.md`：新增 §7 Cursor .mdc 规则编写规范，包含格式模板和 glob 模式最佳实践
   - `04_version_control.md`：新增 §7 Token 预算与规则文件管理，包含 `.mdc` 文件的行数和 Token 限制

2. **Monorepo/多 Agent 场景支持**（v1.1 重点）
   - `00_master_index.md`：新增 Monorepo 场景建议，展示子目录 `AGENTS.md` 的职责隔离模式
   - `05_security.md`：新增 §11 多代理与 Monorepo 安全边界，包含代理间信任边界和职责隔离示例
   - `07_quality.md`：扩展反模式清单至 15 项，新增混淆 AGENTS.md 与 CLAUDE.md、Always 模式滥用、写偏好而非边界等反模式

3. **验证闭环体系**（v1.1 核心新增）
   - `01_core_behavior.md`：新增原则 5「验证闭环」，包含标准验证流程和 16 项合规检查清单
   - `03_coding_standards.md`：新增 §2.4 验证闭环要求，包含验证检查表
   - `07_quality.md`：新增反模式「无验证步骤」，强调目标驱动执行 + 验证闭环

4. **Anthropic Skills 仓库安全实践**（v1.1 新增）
   - `05_security.md`：新增 §11.3 Anthropic Skills 仓库安全实践，包含 Skills 文件的独立安全审查要求
   - `07_quality.md`：新增 Claude Code Skills 与 Hooks 管理规范

5. **工具链配置参考**（v1.1 新增）
   - `06_engineering.md`：新增 §8 工具链配置参考，包含推荐项目工具链文件结构和 `.cursor/rules/` 文件组织建议

### 改进优化

1. **Token 预算管理**（全体系）
   - `00_master_index.md`：新增 Token 预算管理章节，包含各层级文件的行数和 Token 限制
   - `04_version_control.md`：新增 Token 预算限制表和规则文件提交检查清单

2. **安全规范增强**
   - `05_security.md`：扩展敏感文件分级表，新增输出列；新增 Unicode/Markdown 注入防护；新增测试文件安全审查；新增 CI/CD 安全章节

3. **反模式清单扩展**
   - `07_quality.md`：从 12 项扩展至 15 项，新增 3 项 v1.1 专属反模式

4. **分语言规则扩展**
   - `03_coding_standards.md`：新增 C/C++、Java、CAPL/CANoe、MATLAB、Markdown 等语言的特殊规则

5. **依赖镜像源策略**
   - `04_version_control.md`：新增各语言默认镜像源表，包含 Python、Node.js、Go、Rust、Java 的多个镜像源

### 文档完善

1. **README.md**：新增完整的项目说明文档
2. **VERSION_LOG.md**：新增版本迭代日志文件（本文件）

---

## v1.2 (2026-07-15)

### 改进优化 — 审计日志与版本日志强制化

1. **验证闭环流程强化**（`01_core_behavior.md`）
   - 标准验证流程新增第 5 步「追加审计日志到 `.ai_audit.log`」
   - 标准验证流程新增第 6 步「更新相关 `VERSION_LOG.md`」
   - 原有第 5 步「汇总验证结果」顺延为第 7 步
   - 审计日志和版本日志从可选 `[DO]` 升级为验证闭环强制步骤

2. **编码规范验证检查表同步**（`03_coding_standards.md`）
   - 验证检查表新增 2 项：审计日志已追加、版本日志已更新

3. **版本控制规则细化**（`04_version_control.md`）
   - §5 审计日志与可追溯重写：明确触发时机、字段格式、文件路径
   - 审计日志规范标注为「验证闭环强制步骤」
   - 版本迭代日志标注为「验证闭环强制步骤」
   - 新增子模块独立维护 `VERSION_LOG.md` 说明

### 同步副本

- `rule/.codebuddy/rules/core-behavior/RULE.mdc` — 验证闭环流程同步更新
- `rule/.codebuddy/rules/coding-standards/RULE.mdc` — 验证检查表同步更新
- `rule/.trae/01_core_behavior.md` — 验证闭环流程同步更新
- `rule/.trae/03_coding_standards.md` — 验证检查表同步更新

---

## v1.3 (2026-07-15)

### 同步副本 — Trae IDE 全局规则全量同步

1. **Trae 全局规则同步**（`C:\Users\Administrator\.trae-cn\user_rules\`）
   - 从 `ai_rules/` 源全量同步至 Trae IDE 全局规则目录
   - 同步范围：8 个文件（00~07），总计约 +947 行
   - 00_master_index.md（v1.1→v1.2）：路由表/冲突裁决/越界模板/层级优先级/Token预算/Monorepo
   - 01_core_behavior.md（v1.1→v1.3）：三级边界对照表/边界优先级/验证闭环11步/16项合规检查
   - 02_file_operations.md（v1.1→v1.2）：.mdc规范/修改约束/删除安全机制/产物交付/缓存管理
   - 03_coding_standards.md（v1.1→v1.1）：开源许可/合规清单/C++/Java/.mdc规范/Prompt模板
   - 04_version_control.md（v1.1→v1.3）：禁止操作/审计日志强化/Token预算/提交检查/版本管理约束
   - 05_security.md（v1.1→v1.1）：错误处理/身份越权/MCP冲突裁决/Unicode注入/测试审查/Monorepo/CI/CD
   - 06_engineering.md（v1.1→v1.1）：工具链配置参考/推荐项目结构
   - 07_quality.md（v1.1→v1.1）：Skills与Hooks/.claude目录管理/验证闭环/附录模板

2. **审计日志初始化**（`.ai_audit.log`）
   - 新增项目根目录 `.ai_audit.log`，记录首次完整操作审计

### 同步副本历史

- `C:\Users\Administrator\.trae-cn\user_rules\` → 2026-07-15 全量同步（v1.2~v1.3 内容）

---

## v1.3.1 (2026-07-15)

### bug 修复 — 版本日志追加策略缺失

1. **版本日志追加策略明确化**（`04_version_control.md` §5.3）
   - 新增第 4 条「追加策略」：版本记录**必须追加到已有内容末尾**（时间正序），不得覆盖/替换/插入到已有记录之前
   - 明确若 `VERSION_LOG.md` 不存在则自动创建
   - 原第 4~6 条顺延为第 5~7 条

2. **验证闭环步骤 6 措辞修正**（`01_core_behavior.md`）
   - 从"更新 VERSION_LOG.md"改为"在已有内容末尾追加 VERSION_LOG.md 记录"
   - 补充"文件不存在则自动创建"

### 根因

审计日志（`.ai_audit.log`）规则已明确"仅追加"（`04_version_control.md` §5.2 第 5 条），但版本日志（`VERSION_LOG.md`）规则仅说"更新"，缺少明确的追加策略声明，导致历史版本记录可能被覆盖或插入到错误位置。

### 同步副本

- `C:\Users\Administrator\.trae-cn\user_rules\` → 2026-07-15 增量同步 v1.3.1 变更（2 个文件）
- `C:\Users\Administrator\.codebuddy\rules\` → 2026-07-15 增量同步 v1.3 变更（3 个 .mdc 文件：core-behavior, version-control, file-operations）

---

## v1.4 (2026-07-15)

### 新增功能 — 文件同步规则

1. **差异化文件同步机制**（`02_file_operations.md` §3.4）
   - **基础默认处理逻辑**：文件变更同步前必须对原文件与目标文件做全文 diff 比对，生成 diff 变更片段，仅对变动段落局部更新目标文件。禁止读写/输出未改动文本，大幅减少 token 消耗，杜绝 AI 篡改无变更内容。
   - **例外放行条件**：经判定两份文件改动内容占比 ≥ 70%、局部补丁无实际收益时，允许直接输出完整新版本从头覆写目标文件。需标注"改动占比 XX%，触发全量覆写例外"。
   - **约束红线**：`[BLOCK]` 无前置 diff 比对步骤，不得直接全量重写文件。任何情况下不得跳过 diff 生成直接执行全量覆盖。
   - 版本号 1.2 → 1.3

---

## v1.5 (2026-07-16)

### 改进优化 — 版本号强制体系

基于用户对版本追溯性的严格要求，将版本号相关规则从 `[DO]`（建议）升级为 `[BLOCK]`（强制禁止违反），建立三级联动版本控制体系：

1. **文件名强制含版本号**（`02_file_operations.md` §2.2）
   - 第 3 条从 `[DO]` 升级为 `[BLOCK]`：AI 生成的源代码/重要产物文件**必须**在文件名中包含语义化版本号
   - 禁止创建不含版本号的生产文件

2. **文件头强制含版本号**（`03_coding_standards.md` §2.1、§3.2）
   - 新增 §2.1 第 6 条 `[BLOCK]`：每个源代码文件头**必须**包含版本号和创建日期
   - §3.2 文件头注释模板增加版本号字段示例，标注为"强制必含"

3. **修改前强制备份**（`02_file_operations.md` §3.2）
   - AI 生成文件修改流程从「直接修改或创建新版本」升级为「先备份→递增版本号→修改→询问是否删旧版」
   - 新增第 5 步 `[ASK]`：修改完成后询问用户是否删除旧版本文件

4. **删除旧版本必须询问**（`04_version_control.md` §4、`01_core_behavior.md` §2.2）
   - `04_version_control.md` §4 第 1 条从 `[DO]` → `[BLOCK]`，第 5 条新增 `[ASK]`
   - `01_core_behavior.md` §2.1 新增第 9、10 条 `[BLOCK]`，§2.2 新增第 11 条 `[ASK]`

### 影响文件

- `01_core_behavior.md` — v1.3 → v1.4（新增 3 条版本相关约束）
- `02_file_operations.md` — v1.3 → v1.4（文件命名、修改流程强化）
- `03_coding_standards.md` — v1.1 → v1.2（文件头版本号强制要求）
- `04_version_control.md` — v1.3 → v1.4（版本管理升为 BLOCK/ASK 级）
- `00_master_index.md` — v1.2 → v1.3（版本号更新）

### 同步待办

- [ ] 同步至 Trae IDE 全局规则 `C:\Users\Administrator\.trae-cn\user_rules\`
- [ ] 同步至 CodeBuddy 全局规则
- [ ] 推送至 GitHub `ai-rules/GeneralRules`

---

## v1.6 (2026-07-16)

### 改进优化 — 备份前置强制化

基于 AI 在执行修改操作时跳过备份步骤的疏漏，将备份流程从 `[DO]`（流程建议）升级为 `[BLOCK]`（硬约束）：

1. **修改约束新增备份前置硬边界**（`02_file_operations.md` §3.3）
   - 新增第 0 条 `[BLOCK]`：禁止在未创建 `.bak` 备份文件的情况下对任何现有文件执行 `replace_in_file` 或 `write_to_file`（覆盖模式）
   - 强制四步流程：(a) 创建备份 (b) 验证备份完整性 (c) 方可执行修改 (d) 事后告知用户
   - 备份命名规范：`原文件名_v{版本号}.bak` 或 `原文件名_backup_{YYYYMMDD}.bak`

2. **核心行为同步**（`01_core_behavior.md` §2.1）
   - 新增第 11 条 `[BLOCK]`：禁止未创建 `.bak` 备份副本就执行文件修改（交叉引用 `02_file_operations.md` §3.3 第 0 条）

### 影响文件

- `02_file_operations.md` — v1.4 → v1.5（§3.3 新增备份前置硬边界）
- `01_core_behavior.md` — v1.4 → v1.5（§2.1 新增第 11 条 BLOCK）

### 同步待办

- [ ] 同步至 Trae IDE 全局规则 `C:\Users\Administrator\.trae-cn\user_rules\`
- [ ] 同步至 CodeBuddy 全局规则
- [ ] 推送至 GitHub `ai-rules/GeneralRules`

---

## v1.7 (2026-07-16)

### bug 修复 — 文件名版本号检查遗漏

**根因**：`01_core_behavior.md` §4 合规检查清单中「目录与命名」仅有一条模糊的"文件命名是否符合规范"，
未将文件名版本号列为显式检查项。Agent 执行时文件头版本号正确但文件名遗漏版本号（如 `盲区BK问题统计.py`
缺少 `_v2.2` 后缀），因为约束在陈述区但不在检查清单区，自检时漏掉。

**修复**：

1. **合规检查清单拆分**（`01_core_behavior.md` §4）
   - 「目录与命名」新增独立检查项：**文件名是否包含语义化版本号**（如 `_v1.0.py`）？（生产代码 `[BLOCK]` 强制）
   - 原模糊项"文件命名是否符合规范"保留为基础格式检查（小写/下划线/无中文空格）
   - 版本号 1.5 → 1.6

2. **验证闭环步骤 4 强化**（`01_core_behavior.md` §3）
   - 步骤 4 补充："新建源代码文件须验证文件名含语义化版本号"
   - 确保每次文件创建后自动触发文件名版本号自检

3. **编码规范验证检查表补充**（`03_coding_standards.md` §2.4）
   - 新增检查项：`[ ] 文件名包含语义化版本号（生产代码强制）`
   - 版本号 1.2 → 1.3

4. **总索引更新**（`00_master_index.md`）
   - 版本号 1.3 → 1.4

### 影响文件

- `01_core_behavior.md` — v1.5 → v1.6（§4 检查清单 + §3 验证步骤）
- `03_coding_standards.md` — v1.2 → v1.3（§2.4 验证检查表）
- `00_master_index.md` — v1.3 → v1.4（版本号更新）

### 同步待办

- [ ] 同步至 CodeBuddy 全局规则

---

## v1.8 (2026-07-21)

### 改进优化 — 最小化修改原则与原始功能保持升级为硬边界

将"只修改必要的部分"和"保持原始功能不变"相关规则从 `[DO]`（建议）或无标签升级为 `[BLOCK]`（硬边界）：

1. **核心行为原则升级**（`01_core_behavior.md` §3）
   - 原则 2「简单优先」：`[BLOCK]` 不加没被要求的功能
   - 原则 3「外科手术式修改」：4 项关键规则升级为 `[BLOCK]`
     - 不被要求就不「改进」相邻代码、注释或格式
     - 不重构没有问题的东西
     - 每一行变更都应能直接追溯到用户请求
     - 发现无关死代码，提一下——不要删
   - 版本号 v1.6 → v1.7

2. **文件修改约束升级**（`02_file_operations.md` §3.3）
   - #3：`[BLOCK]` 增量修改优先，保留原有逻辑，不做无关重构（原 `[DO]`）
   - #4：`[BLOCK]` 保留文件原有的注释和文档（原 `[DO]`）
   - #6：`[BLOCK]` 每行变更必须能追溯到用户请求——不做「顺手改进」（原 `[DO]`）
   - #7：`[BLOCK]` 发现无关问题提一下但不主动修改（原 `[DO]`）
   - 版本号 v1.5 → v1.6

3. **代码编写规范升级**（`03_coding_standards.md` §2.1）
   - #4：`[BLOCK]` 需求有风险先指出再修正，不能直接按错误需求写（原无标签）
   - 版本号 v1.3 → v1.4

4. **总索引更新**（`00_master_index.md`）
   - 版本号 v1.4 → v1.5

### 影响文件

- `00_master_index.md` — v1.4 → v1.5
- `01_core_behavior.md` — v1.6 → v1.7
- `02_file_operations.md` — v1.5 → v1.6
- `03_coding_standards.md` — v1.3 → v1.4

### 同步待办

- [ ] 同步至 CodeBuddy 全局规则

---

## 格式说明

### 版本号规则

- **主版本号**：重大改动、结构调整、不兼容变更
- **次版本号**：功能新增、内容扩充、向后兼容
- **修订号**：文字修正、格式调整、bug 修复

### 变更类型

| 类型 | 说明 |
|------|------|
| `新增功能` | 新的规则章节或功能模块 |
| `改进优化` | 现有规则的增强和优化 |
| `文档完善` | 文档、说明、示例的完善 |
| `bug 修复` | 规则中的错误或遗漏 |
| `重构` | 规则结构的重新组织 |
