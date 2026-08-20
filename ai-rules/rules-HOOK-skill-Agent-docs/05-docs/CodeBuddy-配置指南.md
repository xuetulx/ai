---
version: 1.0
last_updated: 2026-07-28
---

# CodeBuddy 用户级配置指南

> **适用场景**：将 AI Rules 五层架构（HOOK+RULE+SKILL+AGENT）部署到 CodeBuddy 用户级目录，实现跨项目复用。

---

## 一、架构总览

```
源目录（维护源）                        目标目录（C:\Users\<用户名>\.codebuddy\）
─────────────────────────────────      ─────────────────────────────────────
01-HOOK/*.md              ──映射──▶   settings.json（Hooks 配置）
02-RULE/Always/*.mdc       ──映射──▶   rules/00-hard-boundaries.md
02-RULE/Agent-Requested/*.mdc ──映射─▶  rules/01-py-coding.md
                                       rules/02-git-rules.md
                                       rules/03-engineering.md
03-SKILL/*/SKILL.md        ──映射──▶   skills/<name>/SKILL.md
04-AGENT/*.md              ──映射──▶   agents/<name>.md
```

### 层级说明

| 层 | 加载机制 | Token 消耗 | 遗漏风险 |
|----|---------|:---:|:---:|
| **Hook（settings.json）** | PreToolUse/PostToolUse 程序拦截 | 0（不占上下文） | **零** |
| **Rule（Always）** | 每次会话强制加载 | ≤1K | 极低 |
| **Rule（按需）** | glob 匹配时加载 | ≤2K/个 | 低 |
| **Skill** | AI 自动匹配 description 或手动 `/skill` 调用 | ≤2K/次 | 中 |
| **Agent** | 主 Agent 通过 `Task` 工具调度 | 0（独立上下文） | 低 |

---

## 二、前置条件

- CodeBuddy IDE 已安装
- 确认用户主目录路径：`echo $env:USERPROFILE`（PowerShell）或 `echo ~`（Bash）
- 确认 `.codebuddy/` 目录存在（首次使用会自动创建）

---

## 三、目录结构

```
C:\Users\<用户名>\.codebuddy\
│
├── settings.json            ← Hook 配置（程序级硬约束）
│
├── rules/                   ← Rule 规则文件
│   ├── 00-hard-boundaries.md    （Always：全局硬边界）
│   ├── 01-py-coding.md          （按需：**/*.py）
│   ├── 02-git-rules.md          （按需）
│   └── 03-engineering.md        （按需：src/**）
│
├── skills/                  ← Skill 技能文件
│   ├── code-review/
│   │   └── SKILL.md
│   ├── security-review/
│   │   └── SKILL.md
│   └── git-workflow/
│       └── SKILL.md
│
└── agents/                  ← Agent 子代理定义
    ├── agent-verify.md          （独立验证）
    └── agent-file-sync.md       （文件同步）
```

---

## 四、配置步骤

### 步骤 1：创建目录结构

```powershell
# PowerShell（Windows）
$base = "$env:USERPROFILE\.codebuddy"
mkdir -Force "$base\rules"
mkdir -Force "$base\skills\code-review"
mkdir -Force "$base\skills\security-review"
mkdir -Force "$base\skills\git-workflow"
mkdir -Force "$base\agents"
```

### 步骤 2：部署 settings.json（Hooks）

创建 `%USERPROFILE%\.codebuddy\settings.json`：

```json
{
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "write_to_file|replace_in_file",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python -c \"import os, sys, json; data = json.load(sys.stdin); fp = data.get('tool_input', {}).get('filePath', ''); bn = os.path.basename(fp).lower(); (os.path.exists(fp) and not fp.endswith('.bak') and not bn.endswith('.log') and bn not in ('version_log.md', 'changelog.md') and __import__('shutil').copy2(fp, fp + '.bak') or None)\""
                    }
                ]
            },
            {
                "matcher": "read_file",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python -c \"import sys, json; p = json.load(sys.stdin).get('tool_input',{}).get('filePath',''); exit(2 if any(p.endswith(x) for x in ('.pem','.key','.cert','credentials.','token')) else 0)\""
                    }
                ]
            },
            {
                "matcher": "delete_file",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python -c \"import sys, json; fp = json.load(sys.stdin).get('tool_input',{}).get('filePath',''); print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'ask', 'permissionDecisionReason': 'Delete backup file? Confirm the new file is verified first.'}})) if fp.endswith('.bak') else None\""
                    }
                ]
            }
        ],
        "PostToolUse": [
            {
                "matcher": "write_to_file|replace_in_file|delete_file",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python -c \"import json, sys, os; from datetime import datetime; d = json.load(sys.stdin); op = d.get('tool_name','?'); fp = d.get('tool_input',{}).get('filePath','?'); ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S'); print(f'==== {ts} | 操作: {op} | 路径: {fp} | 结果: OK ====\\n', file=open(os.path.join(os.path.dirname(fp) if os.path.dirname(fp) else '.', '.ai_audit.log'), 'a'))\""
                    }
                ]
            },
            {
                "matcher": "write_to_file|replace_in_file",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python -c \"import sys, json, os; d = json.load(sys.stdin); fp = d.get('tool_input',{}).get('filePath',''); bak = fp + '.bak'; print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'systemMessage': 'Backup ' + bak + ' exists. You may delete it after confirming the changes are correct.', 'additionalContext': 'A backup file ' + bak + ' was created before editing. After the user confirms the change is correct, ask whether to delete this .bak backup.'}})) if os.path.exists(bak) else None\""
                    }
                ]
            }
        ]
    }
}
```

各 Hook 功能：

| Hook | 类型 | 功能 |
|------|------|------|
| backup-before-edit | PreToolUse | 修改/覆写已存在文件前自动创建 `.bak` 备份（追加式文件 `*.log`、`VERSION_LOG.md`、`CHANGELOG.md` 除外） |
| block-sensitive-files | PreToolUse | 拦截读取 `*.pem`、`*.key`、`*.cert`、`credentials.*`、`token*` |
| confirm-backup-delete | PreToolUse | 删除 `.bak` 文件前弹权限确认框（`permissionDecision: ask`），确认新文件无误后才放行 |
| auto-audit-log | PostToolUse | 每次文件修改后追加审计日志到 `.ai_audit.log` |
| backup-cleanup-prompt | PostToolUse | 修改完成后若存在 `.bak` 备份，提示用户确认后清理 |

### 步骤 3：部署 Rules

#### 3.1 `rules/00-hard-boundaries.md`（Always）

```markdown
# 全局硬边界

## Never [BLOCK]
1. 禁止在项目根目录/授权目录之外创建/修改/删除文件
2. 禁止删除或覆盖用户原始文件不先创建 .bak 备份
3. 禁止读取 *.pem, *.key, *.cert, credentials.*, token*
4. 禁止直接读写 .git/ 目录内部文件（用 git 命令代替）
5. 禁止硬编码密钥/密码/Token（用环境变量）
6. 禁止创建不含语义化版本号的生产代码文件
7. 禁止对任何现有文件执行 replace_in_file / write_to_file(覆盖) 而不先创建备份
   例外：追加式文件（*.log、VERSION_LOG.md、CHANGELOG.md）只追加不覆盖，无需备份

## Ask First [ASK]
1. 修改/删除受保护文件
2. 覆盖用户已有源代码文件
3. 读取 .env / .env.* 环境变量文件
4. 批量删除 >= 3 个文件
5. 修改构建配置/CI/CD 配置

## Always Do [DO]
1. 修改代码后立即运行 linter，展示验证结果
2. 每次文件操作后追加 .ai_audit.log 审计日志
3. 实质性变更后更新 VERSION_LOG.md
```

#### 3.2 `rules/01-py-coding.md`（按需：`**/*.py`）

```markdown
# Python 代码编写规范

## 核心规则
- 遵循 PEP 8 + Google Python Style Guide
- 使用 `with` 管理文件/连接，类型注解
- 所有输入校验：空值、越界、类型错误
- 文件/IO/网络全部加异常捕获
- 优先使用标准库，最小化第三方依赖

## 命名
- 常量: UPPER_CASE, 变量/函数: snake_case, 类: PascalCase
- 私有变量前缀 `_`, 布尔谓词前缀 `is_`/`has_`

## 代码结构
- 单函数 ≤ 80 行，嵌套 ≤ 3 层
- 导入分组: 标准库 → 第三方 → 本地，组间空行

## 文件头（强制）
```python
"""
模块用途
版本: v1.0
创建时间: YYYY-MM-DD
作者: AI
修改记录: ...
"""
```

## 验证
- 代码修改后运行 `ruff check .` 零警告通过
```

#### 3.3 `rules/02-git-rules.md`（按需）

```markdown
# Git 操作规范

## 分支
- 每次修改在新建分支上进行，禁止在 main/master/develop 上 commit
- 分支命名: `<type>/<description>`，如 `feat/add-auth`

## 提交
- Conventional Commits: `type(scope): description`
- 类型: feat/fix/docs/refactor/perf/test/chore

## 禁止
- 禁止 `push --force`、`reset --hard`
- 禁止未经确认的 merge/rebase
- 禁止删除未合并分支
```

#### 3.4 `rules/03-engineering.md`（按需：`src/**`）

```markdown
# 工程质量规范

## 模块化
- 单一职责，分层隔离（数据/计算/输出/工具）
- 复用优先，禁止复制粘贴

## 性能
- 大数据优先迭代器
- 频繁字符串拼接用缓冲容器
- 批量 IO 代替单条读写

## 日志
- 分级: DEBUG/INFO/WARN/ERROR/FATAL
- 含时间戳、模块名、关键参数
- 生产代码移除 print

## 测试
- 正常流程 + 边界 + 异常输入
- 可直接运行验证

## 依赖安全
- 禁止安装未验证的第三方依赖
- 优先使用项目已有依赖
- 新增依赖告知：包名、版本、用途、协议
```

### 步骤 4：部署 Skills

#### 4.1 `skills/code-review/SKILL.md`

```markdown
---
name: code-review
description: "代码审查：审查代码质量、安全性、健壮性和性能。当用户请求代码审查、review、检查代码时使用。"
---

# 代码审查工作流

## 审查维度
1. **正确性**：逻辑是否准确，边界是否覆盖
2. **安全性**：注入漏洞、敏感信息泄露、权限校验
3. **健壮性**：异常处理、空值校验、资源释放
4. **性能**：算法复杂度、内存占用、IO 效率
5. **可维护性**：命名规范、注释完整、模块化

## 输出格式
```
问题: <问题描述>
严重度: [严重/中等/轻微]
文件: <文件路径>:<行号>
建议: <修复方案>
```
```

#### 4.2 `skills/security-review/SKILL.md`

```markdown
---
name: security-review
description: "安全审查：检查代码中的敏感信息、注入漏洞、Agentic AI 安全风险。当用户请求安全检查、安全审查、security review 时使用。"
---

# 安全审查工作流

## 检查清单
- [ ] 硬编码密钥/密码/Token
- [ ] SQL/命令注入漏洞
- [ ] XSS/路径穿越
- [ ] 不安全的反序列化
- [ ] 错误信息泄露内部路径
- [ ] 日志记录敏感数据
- [ ] 第三方依赖已知漏洞

## 输出格式
```
风险等级: [高/中/低]
位置: <文件路径>:<行号>
描述: <风险说明>
修复建议: <具体方案>
```
```

#### 4.3 `skills/git-workflow/SKILL.md`

```markdown
---
name: git-workflow
description: "Git 工作流：处理分支创建、提交、推送、合并等版本控制操作。当用户要求 git 操作、提交代码、创建分支、推送时使用。"
---

# Git 工作流

## 标准流程
1. 确认当前分支: `git branch --show-current`
2. 创建新分支: `git checkout -b <type>/<desc>`
3. 提交: `git add . && git commit -m "<type>: <desc>"`
4. 推送: `git push -u origin <branch>`

## 分支命名
- feat/<描述>, fix/<描述>, docs/<描述>
- refactor/<描述>, test/<描述>, chore/<描述>

## 提交格式
`<type>[optional scope]: <description>`
```

### 步骤 5：部署 Agents

#### 5.1 `agents/agent-verify.md`

```markdown
# 独立验证 Agent

## 职责
每次代码修改后独立执行 lint + test，避免主 Agent 的自我验证偏见。

## 验证步骤
1. 读取被修改文件列表
2. 运行 linter: `ruff check` / `eslint` / `golangci-lint`
3. 运行相关测试
4. 汇总结果，标注通过/失败项
5. 有失败项时给出修复建议

## 边界
- 只读验证，不修改任何文件
- 不假设代码意图，仅报告客观结果
```

#### 5.2 `agents/agent-file-sync.md`

```markdown
# 文件同步 Agent

## 职责
将原文件变更同步到目标文件时，按 diff 比例选择局部补丁或全量覆写策略。

## 处理流程
1. 对原文件与目标文件做全文差异比对
2. 计算改动占比 = 变更行数 / 总行数
3. 改动占比 < 70%: 局部补丁更新
4. 改动占比 >= 70%: 全量覆写
5. 禁止无 diff 直接全量覆写

## 边界
- 仅同步被请求的文件
- 不修改未变更内容
```

---

## 五、验证配置

### 5.1 验证目录结构

```powershell
Get-ChildItem -Recurse -File "$env:USERPROFILE\.codebuddy\rules","$env:USERPROFILE\.codebuddy\skills","$env:USERPROFILE\.codebuddy\agents","$env:USERPROFILE\.codebuddy\settings.json" | Select-Object FullName, Length | Format-Table -AutoSize
```

预期输出：

```
FullName                                          Length
--------                                          ------
C:\Users\...\.codebuddy\rules\00-hard-boundaries.md  1200
C:\Users\...\.codebuddy\rules\01-py-coding.md        1200
C:\Users\...\.codebuddy\rules\02-git-rules.md         800
C:\Users\...\.codebuddy\rules\03-engineering.md      1000
C:\Users\...\.codebuddy\skills\code-review\SKILL.md   ...
C:\Users\...\.codebuddy\skills\security-review\SKILL.md ...
C:\Users\...\.codebuddy\skills\git-workflow\SKILL.md  ...
C:\Users\...\.codebuddy\agents\agent-verify.md        ...
C:\Users\...\.codebuddy\agents\agent-file-sync.md     ...
C:\Users\...\.codebuddy\settings.json                 ...
```

### 5.2 验证 Token 预算

| 层级 | 文件数 | 总大小 |
|------|:---:|:---:|
| Rule (Always) | 1 | ~1.2KB |
| Rule (按需) | 3 | ~3KB |
| Skill | 3 | ~5KB |
| Agent | 2 | ~3KB |
| **总计（按需加载，排除 Hook）** | — | **~4KB** |

> **对比**：原方案 8 个 Always 规则 ~86KB（~10K+ tokens），新方案 Always 层仅 ~1.2KB。

---

## 六、旧规则迁移

如果已存在旧的规则文件，执行以下步骤：

### 6.1 备份旧规则

```powershell
# 创建归档目录
mkdir -Force "$env:USERPROFILE\.codebuddy\rules-archived"

# 移动旧规则到归档目录（非删除）
Move-Item "$env:USERPROFILE\.codebuddy\rules\ai-rules-*" "$env:USERPROFILE\.codebuddy\rules-archived\" -Force
```

### 6.2 确认清理结果

```powershell
# 确认 rules/ 下仅保留新规则
Get-ChildItem "$env:USERPROFILE\.codebuddy\rules" -File | Select-Object Name
```

---

## 七、配置与源文件的映射关系

| 源文件（仓库维护） | 目标文件（用户级部署） |
|---|---|
| `01-HOOK/hook-backup-before-edit.md` | `settings.json` → PreToolUse（备份 + 删除确认 + 清理提示 3 个 hook） |
| `01-HOOK/hook-block-sensitive-files.md` | `settings.json` → PreToolUse |
| `01-HOOK/hook-auto-audit-log.md` | `settings.json` → PostToolUse |
| `02-RULE/Always/00-hard-boundaries.mdc` | `rules/00-hard-boundaries.md` |
| `02-RULE/Agent-Requested/01-py-coding.mdc` | `rules/01-py-coding.md` |
| `02-RULE/Agent-Requested/02-git-rules.mdc` | `rules/02-git-rules.md` |
| `02-RULE/Agent-Requested/03-engineering.mdc` | `rules/03-engineering.md` |
| `03-SKILL/skill-code-review/SKILL.md` | `skills/code-review/SKILL.md` |
| `03-SKILL/skill-security-review/SKILL.md` | `skills/security-review/SKILL.md` |
| `03-SKILL/skill-git-workflow/SKILL.md` | `skills/git-workflow/SKILL.md` |
| `04-AGENT/agent-verify.md` | `agents/agent-verify.md` |
| `04-AGENT/agent-file-sync.md` | `agents/agent-file-sync.md` |

---

## 八、同步策略

当源目录（`rules-HOOK-skill-Agent-docs/`）中的文件发生变更时，需同步到 `~/.codebuddy/`：

### 8.1 一键脚本（推荐）

```powershell
cd D:\3.aidata\ai\ai-rules\rules-HOOK-skill-Agent-docs
powershell -ExecutionPolicy Bypass -File .\deploy-codebuddy.ps1
```

脚本幂等可重复执行，完整流程：

1. 依赖检查（python 可用性）
2. 创建目录、复制 rules/skills/agents 共 9 个文件
3. 从 `settings.json.template`（单一事实源）生成 settings.json
4. 三重校验：JSON 合法性 → hooks 结构（matcher 齐全性）→ 源与部署 MD5 一致性
5. 输出部署清单

> **settings.json 配置变更流程**：修改 `settings.json.template`（仓库根目录）→ 运行脚本即同步生效。
> 模板是 hooks 配置的**单一事实源**，脚本与指南均不再内嵌 JSON 配置。

### 8.2 手动同步

1. **Hook 变更**：修改 `settings.json` 中的对应 Hook 定义
2. **Rule 变更**：覆盖 `rules/` 下对应文件（遵循 `agent-file-sync` Agent 的 diff 策略）
3. **Skill 变更**：覆盖 `skills/<name>/SKILL.md`
4. **Agent 变更**：覆盖 `agents/<name>.md`

### 8.3 注意事项（避免踩坑）

- `settings.json` 的 `matcher` 是正则表达式，**不要加引号**（如 `"write_to_file|replace_in_file"` 直接写，不可写成 `"\"write_to_file\""`）
- 敏感文件拦截必须用退出码 **2**（阻塞错误），`1` 仅表示非阻塞提示，无法真正拦截
- Skills/Agents 文件 frontmatter 需含 `name` 字段；源文件已内置，复制后无需修改
- 追加式文件（`*.log`、`VERSION_LOG.md`、`CHANGELOG.md`）只追加不覆盖，backup hook 会自动跳过备份
- 备份清理流程：修改完成后 `backup-cleanup-prompt` 会提示存在 `.bak`；删除 `.bak` 时 `confirm-backup-delete` 强制弹确认框（`permissionDecision: ask`），确认新文件无误后才允许删除

---

## 九、参考资料

- [CodeBuddy Rules 官方文档](https://www.codebuddy.ai/docs/zh/ide/User-guide/Overview)
- [AGENTS.md 开放标准](https://agents.md/)
- [Cursor Rules 2026 格式](https://docs.cursor.com/context/rules-for-ai)
- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
