---
trigger: always_on
priority: high
version: 1.2
last_updated: 2026-07-15
---

# AI 规则总索引 v1.2

> **设计目标**：模块化拆分，按需检索，减少 Agent 每次任务需加载的 token 量。本索引文件控制在 ~160 行以内，Agent 启动时仅加载本索引。
>
> **来源**：基于 `AgentAI_项目文件操作规则_v2.3.md` 和 `AI_RULES_编程参考规范_v3.1.md` 拆分、去重、优化。融合 GitHub 2,500+ 仓库分析、AGENTS.md 开放标准、Cursor .mdc 最新格式、Anthropic Skills 仓库等社区最佳实践。
>
> **使用方式**：Agent 启动时仅加载本索引。根据任务类型通过路由表按需读取对应子文件，控制单次 token 消耗在 8K~12K 以内。

---

## 规则文件清单

| 文件 | 方向 | 适用场景 | 预估行数 | Token 估算 |
|------|------|---------|---------|-----------|
| [01_core_behavior.md](./01_core_behavior.md) | **核心行为** | 所有任务（必读） | ~150 | ~2K |
| [02_file_operations.md](./02_file_operations.md) | **文件操作** | 创建/读取/修改/删除文件、目录管理、批量操作 | ~220 | ~3K |
| [03_coding_standards.md](./03_coding_standards.md) | **代码编写** | 编写代码、命名、注释、分语言规范、验证闭环 | ~200 | ~3K |
| [04_version_control.md](./04_version_control.md) | **版本控制** | Git 操作、分支管理、提交规范、审计日志 | ~150 | ~2K |
| [05_security.md](./05_security.md) | **安全规范** | 敏感信息、代码安全、Agentic AI 安全、MCP 安全 | ~250 | ~4K |
| [06_engineering.md](./06_engineering.md) | **工程质量** | 代码质量、测试、脚本安全、AI 输出约束、依赖管理 | ~200 | ~3K |
| [07_quality.md](./07_quality.md) | **质量保障** | 多工具兼容、Cursor .mdc 格式、反模式、文件修剪、CI 验证 | ~200 | ~3K |

> **Token 预算提示**：典型任务（路由命中 2~3 个文件）消耗约 6K~10K tokens，符合 AGENTS.md 推荐范围。

---

## 快速路由表

根据任务类型，读取对应文件组合：

| 任务类型 | 必读文件 | 可选文件 |
|---------|---------|---------|
| **任何任务** | `01_core_behavior.md` | — |
| **文件操作**（创建/修改/删除） | `01` + `02` | `05`（涉及敏感文件时） |
| **编写代码** | `01` + `03` | `06`（工程级代码时）、`05`（涉及安全编码时） |
| **Git 操作** | `01` + `04` | — |
| **安全相关** | `01` + `05` | `06`（代码安全编码时） |
| **测试相关** | `01` + `06`（§3 测试规范） | `05`（安全测试时） |
| **CI/CD 操作** | `01` + `04` + `05`（§14 CI/CD 安全） | `07`（CI 验证时） |
| **MCP 工具调用** | `01` + `05`（§6 MCP 安全） | `07`（多工具兼容时） |
| **配置 AI 指令文件** | `01` + `02` + `07` | `03`（涉及代码风格配置时） |
| **Monorepo/多 Agent** | `01` + `07`（§1 多工具兼容） | `05`（§11 多代理安全） |
| **全面审查/大型任务** | `01` + 全部子文件 | — |

---

## 术语定义

| 术语 | 精确定义 |
|------|---------|
| **项目根目录** | Agent AI 当前会话绑定的工作目录，所有相对路径以此为基准。 |
| **授权目录** | 用户明确授权的额外可操作目录（绝对路径），与项目根目录权限等同。 |
| **AI 指令文件** | `.claude/`、`.cursor/rules/*.mdc`、`CLAUDE.md`、`AGENTS.md` 等 AI 行为配置文件。 |
| **`.mdc` 文件** | Cursor 2026 年推荐的新规则格式（替代 `.cursorrules`），支持 YAML frontmatter + glob 模式。详见 [Cursor Rules Guide](https://docs.cursor.com/context/rules-for-ai)。 |
| **Agent 生成文件** | 由 AI 主动创建的文件，包括代码、文档、配置、产物等。 |
| **用户原始文件** | 项目中已存在的、由用户或团队创建维护的文件。 |
| **受保护文件** | `02_file_operations.md` §2.3 列出的关键文件，修改必须走副本确认流程。 |
| **临时文件** | AI 为完成任务临时创建的中间文件，任务结束后应清理。 |
| **产物文件** | AI 任务的最终输出文件，如生成的报告、代码、图片等。 |
| **批量操作** | ≥ 3 个文件删除 / ≥ 5 个文件修改 / ≥ 10 个文件创建 / ≥ 5 个新目录。 |
| **三级边界** | `Always`([DO]) / `Ask`([ASK]) / `Never`([BLOCK]) 行为分类体系，源自 AGENTS.md 开放标准。 |
| **验证闭环** | 每次代码修改后必须通过可运行的验证（测试/构建/lint），形成「修改 → 验证 → 确认」闭环。 |
| **Token 预算** | 单次 Agent 加载的规则文件 token 消耗上限：推荐 8K~12K，最大 32KB（Codex 默认上限）。 |

---

## 跨工具指令文件格式对照

| 格式 | 路径 | 工具 | 特点 |
|------|------|------|------|
| **AGENTS.md** | 仓库根目录（支持嵌套） | Codex、Cursor、Copilot、Gemini CLI、Aider 等 25+ 工具 | 跨工具通用标准（OpenAI 2025.8 推出，LF/AAIF 托管） |
| **CLAUDE.md** | 根目录 + `~/.claude/` + 嵌套 | Claude Code 专用 | 支持 `@AGENTS.md` 引用共享内容 |
| **`.cursor/rules/*.mdc`** | `.cursor/rules/` | Cursor 专用（2026 推荐格式） | YAML frontmatter + glob 作用域 + 4 种激活模式 |
| **SKILL.md** | `.claude/skills/<name>/` | Claude 生态 | 任务级领域技能，按需加载 |
| **`.github/copilot-instructions.md`** | `.github/` | GitHub Copilot 专用 | GitHub 原生集成 |

> **迁移提示**：Cursor 已弃用根目录 `.cursorrules`，请迁移至 `.cursor/rules/*.mdc`。详见 [Cursor 官方迁移指南](https://docs.cursor.com/context/rules-for-ai#migrating-from-cursorrules)。

---

## 跨文件冲突裁决规则

当子文件之间规则冲突时，按以下优先级裁决：

| 优先级 | 规则类型 | 说明 |
|--------|---------|------|
| **P0** | `[BLOCK]` 安全禁止 | 安全底线，任何情况下不得违反 |
| **P1** | 用户明确指令 | 用户在会话中明确给出的指令，覆盖自动化规则 |
| **P2** | 文件操作规则（`02`） | 文件读写/创建/删除场景优先 |
| **P3** | 代码编写规则（`03`） | 代码风格/质量/格式场景优先 |
| **P4** | 项目已有风格 | 修改已有文件时，保持原有风格优先于全局规范 |

**总原则**：安全优先 > 用户确认 > 自主执行。更严格的规则覆盖更宽松的规则。

### 关键交叉场景裁决表

| 场景 | 裁决结果 |
|------|---------|
| 修改已有代码的缩进 | 保持原风格（P4 > P3）。不得因全局规则而重格式化 |
| 创建新代码文件 | 使用 `03` 的 4 空格缩进（P3 适用） |
| 产物写入 dist/ vs output/ | 优先 `output/`（`02` 优先），`dist/` 仅当构建系统要求时 |
| 删除 3 个用户文件 | 必须走 `[ASK]` 流程（`02` 优先），先列清单确认 |
| .env 文件读取 | 可读取但不得输出明文（安全 P0 覆盖） |

---

## 越界操作拦截响应模板

当检测到越界操作时，AI 必须暂停并提示用户：

```
⚠️ 【越界操作警告】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  操作类型: <写入/安装/删除/执行>
  目标路径: <路径>
  原始命令: <命令>

  请选择:
  [Y] 确认继续（不推荐）
  [N] 取消操作（默认）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 用户未响应时的默认行为

| 越界类型 | 默认行为 |
|---------|---------|
| 安装类越界（含 `-g`/`--global`） | 自动移除全局标志，改为本地安装 |
| 文件操作越界（路径超出白名单） | 拒绝执行 |
| 删除类越界（涉及非临时目录） | 拒绝执行 |
| 系统命令越界（`sudo`、`chmod 777`） | 拒绝执行 |

---

## 指令文件层级优先级

当多个指令文件同时存在时：

1. **就近原则**：距离被编辑文件最近的指令文件优先。子目录 `AGENTS.md` 覆盖根目录同名文件
2. **用户覆盖**：用户的直接提示词覆盖所有文件中的指令
3. **层级合并**（Claude Code）：`~/.claude/CLAUDE.md`（用户级）→ 项目根 `CLAUDE.md`（项目级）→ 子目录 `CLAUDE.md`（模块级）。三层合并，冲突以更具体（更近）的为准
4. **跨工具兼容**：`AGENTS.md` 为通用源，`CLAUDE.md` 通过 `@AGENTS.md` 引用，`.cursor/rules/*.mdc` 通过 `glob` 作用域精确匹配
5. **规则文件版本化**：历史版本用版本号命名（`_v1.0.md`），旧版本归档至 `docs/history/`

### Monorepo 场景建议

```
monorepo/
├── AGENTS.md                    # 全局共享：技术栈、约定、边界
├── frontend/
│   └── AGENTS.md                # 前端 Agent："你只管 UI，不要碰 /backend"
├── backend/
│   └── AGENTS.md                # 后端 Agent：专属职责与边界
└── infra/
    └── AGENTS.md                # 基础设施 Agent："apply 前要审批"
```

> **职责隔离**：子目录 `AGENTS.md` 使用 `Never: 修改 /backend/ 目录` 等硬边界语句限定 Agent 操作域。

---

## Token 预算管理

| 层级 | 文件 | 行数限制 | Token 限制 |
|------|------|---------|-----------|
| 索引 | `00_master_index.md` | ≤ 200 行 | ≤ 3K |
| 子文件 | `01~07_*.md` | ≤ 300 行 | ≤ 5K |
| 项目指令 | `AGENTS.md`（根目录） | 150~250 行 | 4K~8K |
| 子目录指令 | `子目录/AGENTS.md` | 30~80 行 | 1K~2K |
| Agent 总加载 | 一次典型任务 | — | **8K~12K**（推荐上限） |

> **触发修剪阈值**：任何子文件超过 300 行、AGENTS.md 超过 250 行时，触发 `07_quality.md` §3 的修剪流程。

---

**生效时间**：2026-07-15
**版本**：v1.1（新增 Cursor .mdc 格式对照、Monorepo 场景、Token 预算管理、验证闭环术语）
**子文件总数**：7 个
**参考标准**：
- OWASP GenAI Security Project — genai.owasp.org
- AGENTS.md 开放标准 — agents.md（LF/AAIF 托管，60,000+ 项目）
- Karpathy Skills — github.com/forrestchang/andrej-karpathy-skills（158k+ stars）
- Anthropic Skills 仓库 — github.com/anthropics/skills（138k+ stars, 2026.5）
- Agent Rules — github.com/steipete/agent-rules
- Cursor Rules 最新格式 — docs.cursor.com/context/rules-for-ai
- Claude Code Best Practices — code.claude.com/docs/en/best-practices
- Conventional Commits — conventionalcommits.org
- Google Style Guides — google.github.io/styleguide
