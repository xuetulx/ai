---
version: 1.0
last_updated: 2026-08-20
---

# Trae Configuration

> 将 `ai-rules/rules-HOOK-skill-Agent-docs/` 中的内容按 Trae IDE 正确格式重新组织存放。Skills 已同步部署到全局 `~/.trae-cn/skills/`，并注册到 `~/.trae-cn/skill-config.json`。

---

## 一、目录结构

```
trae-configuration/
│
├── skills/                              ← Trae Skill 格式（已部署到全局）
│   ├── skill-code-review/SKILL.md
│   ├── skill-security-review/SKILL.md
│   └── skill-git-workflow/SKILL.md
│
├── rules/                               ← MDC 规则格式（行业通用）
│   ├── 00-hard-boundaries.mdc           (Always：全局硬边界)
│   ├── 01-py-coding.mdc                 (按需：**/*.py)
│   ├── 02-git-rules.mdc                 (按需)
│   └── 03-engineering.mdc               (按需：src/**)
│
├── hooks/                               ← Hook 配置（程序级硬约束）
│   ├── hook-backup-before-edit.md       (PreToolUse)
│   ├── hook-block-sensitive-files.md    (PreToolUse)
│   ├── hook-block-git-manipulation.md   (PreToolUse)
│   ├── hook-block-hardcoded-secrets.md  (PostToolUse)
│   └── hook-auto-audit-log.md           (PostToolUse)
│
├── agents/                              ← 子 Agent 定义
│   ├── agent-verify.md                  (独立验证)
│   └── agent-file-sync.md              (文件同步)
│
└── README.md                           (本说明)
```

---

## 二、Trae 格式适配说明

### 2.1 Skills（已部署到全局）

Trae 原生支持 Skills，存放路径：`~/.trae-cn/skills/<name>/SKILL.md`

**适配内容**：
- 添加 `name` 字段（必需，与文件夹同名）
- 添加 `description` 字段（必需，详细描述触发场景）
- 添加 `license: MIT` 字段
- `skill-git-workflow` 额外添加 `allowed-tools: Bash`

**全局部署位置**：
- `~/.trae-cn/skills/skill-code-review/SKILL.md`
- `~/.trae-cn/skills/skill-security-review/SKILL.md`
- `~/.trae-cn/skills/skill-git-workflow/SKILL.md`

**注册位置**：`~/.trae-cn/skill-config.json` → `managedSkills` 段，状态为 `user_upload`。

### 2.2 Rules（MDC 格式）

Trae IDE 不原生提供用户级 Rules 目录。此处采用 Cursor 兼容的 `.mdc` 格式（行业通用），保留 `description`、`globs`、`alwaysApply`、`enabled` 字段，并补充 `name` 字段。

> **如需在 Trae 中加载**：可作为 Skill 内容封装进 Skill，或通过项目级 `.cursorrules` / `AGENTS.md` 加载。

### 2.3 Hooks（程序级硬约束）

Trae IDE 不原生支持用户级 Hook（不同于 Claude Code）。Hook 配置文件仅作为：
- **配置参考**：每个 Hook 文件附带 Trae 风格 `settings.json` JSON 配置块
- **降级方案**：当无 Hook 支持时，通过 Rule 的 `[BLOCK]` 表达式实现等效约束

### 2.4 Agents（子代理定义）

Trae 通过 `Task` 工具调度子 Agent（如 `general_purpose_task`、`search` 等子代理类型）。每个 Agent 文件包含：
- 标准职责定义
- 调度示例（参考 Trae Task 工具用法）

---

## 三、与源目录的映射关系

| 源文件（`ai-rules/rules-HOOK-skill-Agent-docs/`） | 目标文件（`trae-configuration/`） | 全局部署 |
|---|---|:---:|
| `01-HOOK/hook-backup-before-edit.md` | `hooks/hook-backup-before-edit.md` | — |
| `01-HOOK/hook-block-sensitive-files.md` | `hooks/hook-block-sensitive-files.md` | — |
| `01-HOOK/hook-block-git-manipulation.md` | `hooks/hook-block-git-manipulation.md` | — |
| `01-HOOK/hook-block-hardcoded-secrets.md` | `hooks/hook-block-hardcoded-secrets.md` | — |
| `01-HOOK/hook-auto-audit-log.md` | `hooks/hook-auto-audit-log.md` | — |
| `02-RULE/Always/00-hard-boundaries.mdc` | `rules/00-hard-boundaries.mdc` | — |
| `02-RULE/Agent-Requested/01-py-coding.mdc` | `rules/01-py-coding.mdc` | — |
| `02-RULE/Agent-Requested/02-git-rules.mdc` | `rules/02-git-rules.mdc` | — |
| `02-RULE/Agent-Requested/03-engineering.mdc` | `rules/03-engineering.mdc` | — |
| `03-SKILL/skill-code-review/SKILL.md` | `skills/skill-code-review/SKILL.md` | ✅ `~/.trae-cn/skills/` |
| `03-SKILL/skill-security-review/SKILL.md` | `skills/skill-security-review/SKILL.md` | ✅ `~/.trae-cn/skills/` |
| `03-SKILL/skill-git-workflow/SKILL.md` | `skills/skill-git-workflow/SKILL.md` | ✅ `~/.trae-cn/skills/` |
| `04-AGENT/agent-verify.md` | `agents/agent-verify.md` | — |
| `04-AGENT/agent-file-sync.md` | `agents/agent-file-sync.md` | — |

---

## 四、Trae 全局部署详情

### 4.1 部署目标

```
C:\Users\<用户名>\.trae-cn\
├── skills\
│   ├── skill-code-review\SKILL.md      ← 新增
│   ├── skill-security-review\SKILL.md ← 新增
│   └── skill-git-workflow\SKILL.md     ← 新增
└── skill-config.json                   ← 修改：注册 3 个新 skill
```

### 4.2 skill-config.json 注册项

```json
{
  "managedSkills": {
    "skill-code-review": "user_upload",
    "skill-security-review": "user_upload",
    "skill-git-workflow": "user_upload",
    ...
  }
}
```

---

## 五、为什么 Rules / Hooks / Agents 不部署到全局

| 层级 | Trae 原生支持 | 原因 |
|------|:---:|------|
| **Skills** | ✅ | `~/.trae-cn/skills/` 为 Trae 官方 Skill 目录 |
| **Rules** | ❌ | Trae 无用户级 Rules 目录（仅 Skill 一种扩展机制） |
| **Hooks** | ❌ | Trae 无用户级 Hook 机制（不同于 Claude Code 的 `.claude/settings.json`） |
| **Agents** | ❌ | Trae 通过 `Task` 工具内置调度，无独立 Agent 配置目录 |

> Rules / Hooks / Agents 保留在项目级 `trae-configuration/` 作为参考与降级方案。如需生效，可在项目根目录创建 `AGENTS.md` 引用相关文件，或将其内容封装为 Skill。

---

## 六、验证

### 6.1 验证 Skills 全局部署

```powershell
# 确认 3 个新 Skill 已部署
Get-ChildItem "$env:USERPROFILE\.trae-cn\skills\skill-*" -Recurse -File | Select-Object FullName
```

预期输出：3 个 SKILL.md 文件路径。

### 6.2 验证 skill-config.json 注册

```powershell
# 查看 managedSkills 字段
Get-Content "$env:USERPROFILE\.trae-cn\skill-config.json" | ConvertFrom-Json | Select-Object -Expand managedSkills
```

预期包含：`skill-code-review`、`skill-security-review`、`skill-git-workflow`。

### 6.3 验证项目级配置完整性

```powershell
Get-ChildItem "trae-configuration" -Recurse -File | Select-Object FullName, Length | Format-Table -AutoSize
```

---

## 七、参考标准

- [Trae IDE Skills 文档](https://www.trae.cn/)
- [Cursor Rules 2026 格式](https://docs.cursor.com/context/rules-for-ai)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [AGENTS.md 开放标准](https://agents.md/)
- [Conventional Commits](https://conventionalcommits.org)
