---
trigger: on_quality
priority: high
version: 1.1
last_updated: 2026-07-15
---

# 07 质量保障体系

> **适用范围**：多工具兼容、反模式检查、文件修剪、CI 验证、批量回滚、Claude Code/Skills 专属规范。
>
> **前置依赖**：`01_core_behavior.md`
>
> **来源**：AgentAI v2.3 §24~§28 + §21；AI_RULES v3.1 §23；Cursor Rules 2026 最佳实践；Anthropic Skills 仓库

---

## 1. 多工具兼容层

> AGENTS.md 开放标准，60,000+ 项目采用

### 1.1 推荐策略：单一源 + 多适配

| 格式 | 路径 | 读取工具 |
|------|------|---------|
| **AGENTS.md** | 仓库根目录（支持嵌套） | Codex、Cursor、Copilot、Gemini CLI、Aider 等 25+ 工具 |
| **CLAUDE.md** | 根目录 + `~/.claude/` + 嵌套 | Claude Code 专用 |
| **.cursor/rules/*.mdc** | `.cursor/rules/` | Cursor 专用 |
| **SKILL.md** | `~/.claude/skills/<name>/` | Claude 任务级技能 |
| **.github/copilot-instructions.md** | `.github/` | GitHub Copilot |

**推荐方案**：

1. `[DO]` 以 `AGENTS.md` 为**单一真实源**
2. `[DO]` `CLAUDE.md` 为薄适配层，通过 `@AGENTS.md` 引入
3. `[DO]` Cursor glob 作用域规则在 `.cursor/rules/*.mdc` 中保持与 AGENTS.md 一致
4. `[BLOCK]` 不在多个文件中重复维护相同内容

### 1.2 AGENTS.md 六大核心领域

编写或更新 AGENTS.md 时，应覆盖以下六个领域（按优先级排序）：

**1. 构建与运行命令（最重要，放最前面）**

```markdown
## Build & Run
- Install deps: `pnpm install`
- Dev server: `pnpm dev` (port 3000)
- Production build: `pnpm build`
- Lint: `pnpm lint`
```

**2. 测试指令**

```markdown
## Testing
- All tests: `pnpm test`
- Single file: `pnpm test -- tests/auth.test.ts`
- With coverage: `pnpm test -- --coverage`
```

**3. 项目结构**

```markdown
## Structure
src/
├── api/       # 路由处理
├── services/  # 业务逻辑
├── models/    # 数据模型
└── utils/     # 共享工具
```

**4. 代码风格（只写与语言默认不同的规则）**

```markdown
## Code Style
- TypeScript strict mode; 禁止 `any`
- 函数组件，不用 class 组件
- 命名导出，不用默认导出
```

**5. Git 工作流**

```markdown
## Git Workflow
- 分支命名: `feature/`, `fix/`, `chore/`
- 提交消息: Conventional Commits
- 提交前检查: `pnpm test && pnpm lint`
```

**6. 边界（三级体系）**

```markdown
## Boundaries
- Always: [安全操作清单]
- Ask: [需确认的操作清单]
- Never: [禁止操作清单]
```

### 1.3 文件大小建议

1. `[DO]` 根目录 AGENTS.md 建议 **150~250 行**（约 4~8 KB）
2. `[DO]` 单个子目录 AGENTS.md 建议 **30~80 行**
3. `[DO]` 总 token 消耗控制在 **8K~12K tokens** 以内
4. `[BLOCK]` 避免超过 **32 KB**（Codex 默认上限）
5. `[DO]` 长文档使用链接引用，不内联全部内容

---

## 2. 反模式清单（v1.1 扩展至 15 项）

> GitHub 2,500+ 仓库分析 + Augment Code / Vercel 评估 + Cursor 2026 最佳实践

| # | 反模式 | 问题 | 修正方案 |
|---|--------|------|---------|
| 1 | **小说式指令** | 大段散文，Agent 难以提取 | 用**命令 + 代码块**替代段落文字 |
| 2 | **规则膨胀** | 超 500 行，上下文溢出，任务完成度 ↓30% | 保持 150~250 行，详细内容用链接引用 |
| 3 | **重复维护** | 同一规则在 AGENTS.md、CLAUDE.md、.cursor/rules 中各写一份 | AGENTS.md 为单一源，其他文件引用 |
| 4 | **模糊命令** | 「运行测试」而非精确命令 | 使用**精确命令 + 完整参数** |
| 5 | **缺少边界** | 没有 Always/Never 清单 | 添加三级边界体系，写边界而非偏好 |
| 6 | **过期不修剪** | 项目演进但指令不更新 | 每次重大变更后审查（建议加入 PR 模板） |
| 7 | **纯文字无代码** | 描述风格但不给示例 | 至少一个真实代码示例 |
| 8 | **忽视层级** | 单体仓库只有一个根文件 | 每个子包放独立 AGENTS.md |
| 9 | **安全规则缺失** | 没有敏感文件处理规则 | 使用 `05_security.md` 分级表 |
| 10 | **过度约束** | 每条都标 BLOCK，Agent 无法工作 | 区分 BLOCK/ASK/DO，给合理自主空间 |
| 11 | **无验证步骤** | 不定义「完成」标准 | 使用目标驱动执行 + 验证闭环 |
| 12 | **忽略工具差异** | .gitignore ≠ AI 忽略 | 配置专门 AI 排除文件 |
| 13 | **混淆 AGENTS.md 与 CLAUDE.md**（v1.1 新增） | 把 Claude 专属指令放入 AGENTS.md，导致其他工具误读 | AGENTS.md 只放跨工具通用内容，专属工具放各自文件 |
| 14 | **Always 模式滥用**（v1.1 新增） | .mdc 规则全部设为 Always，耗尽 token 预算 | 安全/边界用 Always（≤30 行），其余用 Agent Requested + globs |
| 15 | **写偏好而非边界**（v1.1 新增） | "优先用函数组件"对 AI 无效 | 改为"禁止使用 class 组件"或使用示例展示约定 |

---

## 3. 文件精简与定期修剪

> 膨胀的指令文件可使 Agent 任务完成度下降 30%

### 3.1 修剪触发条件

1. `[DO]` 文件超过 **300 行**时触发修剪审查
2. `[DO]` 每次项目重大架构变更后触发
3. `[DO]` 每季度定期审查一次

### 3.2 修剪流程

```
[DO]  1. 统计当前文件行数和各节占比
[DO]  2. 识别可外链内容 → 移至 docs/ 并留链接
[DO]  3. 删除已被工具默认行为覆盖的规则
[DO]  4. 合并重复规则
[DO]  5. 验证精简后不影响行为正确性
[ASK] 6. 精简结果需用户确认后应用
```

### 3.3 精简原则

1. **命令 > 描述**：`pnpm test` 优于「运行测试框架」
2. **代码 > 文字**：一个示例优于三段解释
3. **差异 > 全量**：只写与默认不同的规则
4. **链接 > 内联**：详细内容放 docs/，指令文件只保留核心

---

## 4. CI 验证建议

### 4.1 自动化检查

1. `[DO]` **文件存在性**：验证 `AGENTS.md` 存在于仓库根目录
2. `[DO]` **行数检查**：警告超过 300 行的指令文件
3. `[DO]` **敏感信息扫描**：检查指令文件中是否意外包含密钥
4. `[DO]` **链接有效性**：验证引用的外部链接和内部路径
5. `[DO]` **PR 模板集成**：「本次变更是否需要同步更新 AGENTS.md / CLAUDE.md？」

### 4.2 示例 CI 脚本

```yaml
# .github/workflows/agents-md-check.yml
name: AGENTS.md Quality Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check AGENTS.md exists
        run: |
          if [ ! -f AGENTS.md ]; then
            echo "::warning::AGENTS.md not found"
            exit 1
          fi
      - name: Check line count
        run: |
          LINES=$(wc -l < AGENTS.md)
          if [ "$LINES" -gt 300 ]; then
            echo "::warning::AGENTS.md has $LINES lines (recommended: 150-250)"
          fi
      - name: Scan for secrets
        run: |
          if grep -iE '(password|secret|token|api_key)\s*[:=]' AGENTS.md; then
            echo "::error::Potential secrets found in AGENTS.md"
            exit 1
          fi
```

---

## 5. 批量操作回滚机制

1. `[DO]` 批量修改前自动创建 Git 提交点或文件备份
2. `[DO]` 批量操作失败时立即停止，报告已执行操作和失败位置
3. `[DO]` 提供回滚方案
4. `[DO]` 删除操作优先"移动到回收站/临时目录"而非永久删除

---

## 6. Claude Code 专属规范

> 参考：Claude Code Best Practices

### 6.1 计划模式（Plan Mode）

1. `[DO]` 复杂任务必须先进入 plan mode 探索再执行
2. `[DO]` plan mode 只读不修改
3. `[DO]` 用户确认计划后再退出 plan mode
4. `[DO]` 简单任务可直接执行
5. `[BLOCK]` plan mode 中不得通过 MCP/hooks 间接修改文件

### 6.2 上下文窗口管理

1. `[DO]` 批量读取前评估 token 消耗
2. `[DO]` 大文件（>10MB）优先分页/分段读取
3. `[DO]` 批量读取 ≥20 个文件时告知用户
4. `[DO]` 长会话定期回顾核心目标

### 6.3 Skills 与 Hooks

1. `[DO]` 领域知识封装为 Skill 文件（`.claude/skills/`），按需加载
2. `[DO]` 关键动作配置为 Hook（如编辑后运行 linter）
3. `[DO]` CLAUDE.md 保持简洁，定期修剪

### 6.4 .claude/ 目录管理

`.claude/` 目录存放 Claude Code 的 CLAUDE.md、skills、hooks、settings 等配置：

| 子目录/文件 | 用途 | AI 操作权限 |
|------------|------|-----------|
| `CLAUDE.md` | 全局指令文件 | `[BLOCK]` 不得修改（除非用户明确要求且二次确认） |
| `CLAUDE.local.md` | 个人本地指令 | `[BLOCK]` 不得修改 |
| `.claude/skills/` | Skill 文件目录 | `[DO]` 可读取；`[ASK]` 修改/删除 |
| `.claude/settings.json` | Hooks 与配置 | `[BLOCK]` 不得修改 |
| `.claude/hooks/` | Hook 脚本 | `[BLOCK]` 不得修改 |

### 6.4 验证闭环

1. `[DO]` 提供可运行的验证手段（测试/构建/截图对比）
2. `[DO]` 展示证据（测试输出/命令结果）而非仅断言成功
3. `[DO]` 重要操作用子代理进行对抗性审查

---

## 附录 A：快速参考模板（v1.1 更新）

### A.1 新项目 AGENTS.md 最小模板（5 分钟上手）

```markdown
# AGENTS.md

## Project Overview
[项目名称] — [一句话描述]
Tech stack: [语言] [框架] [数据库] [其他关键依赖]

## Build & Run
- Install: `[包管理器] install`
- Dev: `[启动命令]`
- Build: `[构建命令]`
- Test: `[测试命令]`
- Lint: `[lint 命令]`

## Code Style
- [与语言默认不同的关键规则 1]
- [与语言默认不同的关键规则 2]
```[语言]
// 一个真实代码示例（比三段文字描述更有效）
```

## Boundaries
- Always: [安全操作清单 + 验证命令]
- Ask: [需确认的操作清单]
- Never: [禁止操作清单，越具体越好]

## Verification
- Pre-commit: `[lint cmd] && [test cmd]`
- 所有修改必须通过 lint（零警告）和 test（全通过）
```

### A.2 Cursor .mdc 安全规则模板

```markdown
---
description: "全局安全边界规则"
alwaysApply: true
enabled: true
---

# Global Safety Boundaries

## Never
- 不得修改 `.cursor/rules/` 目录下的任何文件
- 不得读取 `.env`、`*.pem`、`*.key`、`credentials.*`
- 不得在项目根目录之外创建/修改文件
- 禁止 `rm -rf` 等递归强制删除（`tmp/` 除外）
- 不得修改 `generated/`、`vendor/`、`node_modules/` 目录

## Always
- 修改代码后运行 `[项目 lint 命令]`
- 创建新文件后验证路径正确性
```
