---
description: "Hook 层说明 - 程序级硬约束，不可遗漏"
version: 1.0
last_updated: 2026-07-28
---

# 01-HOOK：程序级硬约束

> **定位**：这些不是"提醒"，而是"拦截"。Hook 在 I/O 层面拦截违规操作，AI 无法绕过。

## 为什么放在第一位

规则（Rule）是文字提醒——密度高时会漏。Hook 是程序拦截——不漏、零步骤、无感知。

## Hook 清单（5 项）

| # | Hook 名称 | 拦截内容 | 来源 |
|---|----------|---------|------|
| 1 | backup-before-edit | 对任何现有文件执行 replace_in_file/write_to_file(覆盖) 前，自动创建 .bak 备份 | 02 §3.3 |
| 2 | block-sensitive-files | 拦截对 *.pem, *.key, *.cert, credentials.*, token* 的读取 | 01 §2.1, 05 §1.1 |
| 3 | block-git-manipulation | 拦截直接读写 .git/ 目录的操作 | 01 §2.1, 04 §1 |
| 4 | block-hardcoded-secrets | 扫描代码变更，拦截硬编码密码/密钥/Token | 06 §5, 05 §4.2 |
| 5 | auto-audit-log | 每次文件修改后自动追加 .ai_audit.log | 04 §5.2 |

## 配置方式

各平台 Hook 机制：
- **Claude Code**：`.claude/settings.json` → hooks → `PostToolUse` / `PreToolUse`
- **Cursor**：不支持原生 Hook，通过 Rules 中 `[BLOCK]` 模拟
- **Codex / Copilot**：通过 AGENTS.md 中的 Never 边界表达

## 优先级

Hook 层优先级高于所有 Rule——Hook 拦截的操作，Rule 无需再声明。
