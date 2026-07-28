---
version: 1.0
last_updated: 2026-07-28
---

# AI Rules 分层架构 v1.0

> **之前**：8 个文件 ~2500 行全部 always_applied → 密度过高，关键约束被淹没
> **现在**：按「是否会遗漏」分层 → HOOK 拦截不可遗漏的，RULE 放可遗漏的

---

## 快速导航

```
rules-HOOK-skill-Agent-docs/
│
├── 01-HOOK/              ← 程序级硬约束（不可遗漏）
│   ├── hook-backup-before-edit.md       修改前强制备份
│   ├── hook-block-sensitive-files.md    拦截读取敏感文件
│   ├── hook-block-git-manipulation.md   拦截直接操作 .git/
│   ├── hook-block-hardcoded-secrets.md  扫描硬编码密钥
│   └── hook-auto-audit-log.md           自动追加审计日志
│
├── 02-RULE/              ← 文字提醒（可能被忽略，但覆盖全面）
│   ├── Always/
│   │   └── 00-hard-boundaries.mdc       极简边界清单（≤30行）
│   └── Agent-Requested/
│       ├── 01-py-coding.mdc             Python 编码规范
│       ├── 02-git-rules.mdc             Git 操作规范
│       └── 03-engineering.mdc           工程质量规范
│
├── 03-SKILL/             ← 领域知识（低频场景，手动触发）
│   ├── skill-code-review/               代码审查
│   ├── skill-security-review/           安全审查
│   └── skill-git-workflow/              Git 操作
│
├── 04-AGENT/             ← 隔离执行（独立进程，防验证偏见）
│   ├── agent-verify.md                  代码验证 Agent
│   └── agent-file-sync.md               文件同步 Agent
│
└── 05-docs/              ← 历史归档 + 配置指南
    ├── CodeBuddy-配置指南.md              CodeBuddy 用户级部署指南
    └── archived/                         原始 8 个规则文件
```

---

## 层级对比

| 层 | 遗漏可能性 | 加载时机 | 适用内容 |
|----|:---:|------|---------|
| **HOOK** | **不会漏** ✅ | 每次 I/O 自动拦截 | 禁止读密钥、修改前备份、拦截 .git 操作 |
| **RULE (Always)** | 极少漏 | 每次会话 | [BLOCK]/[ASK]/[DO] 三级清单 |
| **RULE (Agent Requested)** | 按需漏 | 匹配 glob 时 | Python 规范、Git 规范、工程规范 |
| **SKILL** | 需手动触发 | 用户调用 | 安全审查、代码审查、完整 Git 工作流 |
| **AGENT** | 需调度启动 | 主 Agent 调度 | 独立验证、文件同步 |

---

## 关键原则

1. **Hook 覆盖 Rule**：Hook 已拦截的，Rule 不再重复声明
2. **Always 极简**：≤30 行，仅放绝对不能漏的硬边界
3. **Agent Requested + globs**：代码规范类全部精确匹配文件类型
4. **Skill 低频场景**：安全/审查/工作流，手动触发不浪费 token
5. **Agent 隔离执行**：验证类任务独立运行，避免自我偏见

---

## Token 预算

| 层级 | 加载条件 | Token 估算 |
|------|---------|-----------|
| HOOK | 不占上下文（程序级） | 0 |
| RULE (Always) | 每次会话 | ≤1K |
| RULE (Agent Requested) | 匹配 glob 时 | ≤2K/个 |
| SKILL | 手动触发 | ≤2K/个 |
| AGENT | 调度启动 | 不占主 Agent 上下文 |

**对比原方案**：之前 2500 行 ≈ 8K+ Token 每次必加载
**现在**：Always 层 ≤1K Token，其余按需。

---

## 参考标准

- OWASP GenAI Security Project — genai.owasp.org
- AGENTS.md 开放标准 — agents.md（60,000+ 项目）
- Cursor Rules 2026 — docs.cursor.com/context/rules-for-ai
- Claude Code Best Practices — code.claude.com/docs/en/best-practices
- Conventional Commits — conventionalcommits.org
