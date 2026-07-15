---
trigger: on_git_operation
priority: high
version: 1.3
last_updated: 2026-07-15T15:30
---

# 04 版本控制与工程规范

> **适用范围**：Git 操作、分支管理、提交规范、审计日志、版本管理、依赖镜像源、Token 预算管理。
>
> **前置依赖**：`01_core_behavior.md`
>
> **来源**：AgentAI_项目文件操作规则 v2.3 §10 + §12 + §19.4；AI_RULES v3.1 §13；AGENTS.md 文件大小建议

---

## 1. Git 操作约束

1. `[BLOCK]` 禁止直接读写 `.git/` 目录下的任何文件
2. `[DO]` 通过 git 命令间接操作版本控制（`git status`、`git diff`）
3. `[ASK]` 执行 `git commit`、`git push`、`git reset` 等写操作前必须确认
4. `[BLOCK]` 禁止 `git push --force`、`git reset --hard`（除非用户明确要求并二次确认）
5. `[DO]` **每次修改内容必须在新建分支上提交**，不得直接在 main/master/develop 上 commit

---

## 2. 分支管理规则

### 2.1 核心原则

1. `[DO]` 每次修改任务必须先创建新分支
2. `[BLOCK]` 禁止在 `main`/`master`/`develop`/`release/*` 上直接 commit
3. `[DO]` 原有分支仅用于读取代码、理解项目结构

### 2.2 分支命名

```
<type>/<description>
```

| 组成 | 说明 | 示例 |
|------|------|------|
| `type` | Conventional Commits 类型 | `feat`、`fix`、`docs`、`refactor` |
| `description` | 小写 + 连字符 | `add-radar-filter`、`fix-cache-bug` |

- 格式：`feat/add-user-auth`、`fix/null-pointer-crash`
- 可加日期前缀：`ai/20260701_fix-cache-bug`

### 2.3 标准工作流

```
[DO] 1. 确认当前分支 → git branch --show-current
[DO] 2. 记录原分支名
[DO] 3. 创建新分支 → git checkout -b feat/<任务描述>
[DO] 4. 在新分支上修改
[DO] 5. git add + git commit（Conventional Commits）
[ASK] 6. 询问用户是否推送或合并
[DO] 7. 根据指示切回原分支或保持
```

### 2.4 禁止操作

1. `[BLOCK]` 在 main/master/develop 上直接 `git commit`
2. `[BLOCK]` 未经确认执行 `git merge`/`git rebase` 到原分支
3. `[BLOCK]` 未经确认删除任何分支
4. `[DO]` 任务完成后提醒用户当前分支和未合并分支 — **强制步骤**，已纳入 `01_core_behavior.md` 验证闭环步骤 10

---

## 3. 提交消息规范

### 3.1 格式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 3.2 类型定义

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/辅助工具 |
| `ci` | CI/CD 配置 |
| `build` | 构建系统/外部依赖 |
| `revert` | 回退提交 |

### 3.3 破坏性变更

在类型/作用域后加 `!` 或 footer 写 `BREAKING CHANGE:`。

---

## 4. AI 生成文件的版本管理

1. `[DO]` 重要文件保留历史版本，语义化版本号（v1.0、v1.1、v2.0）
   - 主版本号：重大改动、结构调整
   - 次版本号：功能新增、内容扩充
   - 修订号：文字修正、格式调整、bug 修复
2. `[DO]` 规则文件命名格式：`AgentAI_项目文件操作规则_v{主版本}.{次版本}.md`
3. `[DO]` 配套规范同步命名：`AI_RULES_编程参考规范_v{主版本}.{次版本}.md`
4. `[DO]` 旧版本保留至少一个历史版本，或归档到 `docs/history/`

---

## 5. 审计日志与可追溯（v1.2 强化）

> **v1.2 重要变更**：审计日志和版本日志已纳入 `01_core_behavior.md` 原则 5「验证闭环」标准流程的强制步骤（步骤 5 和步骤 6）。以下为详细规范。

### 5.1 操作记录 `[DO]`

1. 每次文件操作后说明操作了哪些文件
2. 重要修改说明变更差异和理由
3. 批量操作给出汇总
4. **上述说明同时写入 `.ai_audit.log` 审计日志**，不在会话回复中口头带过

### 5.2 审计日志规范 `[DO]` — 验证闭环强制步骤

> 对应 `01_core_behavior.md` 原则 5 标准验证流程第 5 步

1. **触发时机**：每次代码/文件创建、修改、删除操作完成后**必须立即**追加审计记录，不允许跳过或延期
2. 审计日志字段：时间戳、操作类型（创建/修改/删除）、完整路径、变更摘要、验证结果
3. 审计日志文件：项目根目录 `.ai_audit.log`
4. 格式：每条记录以分隔线 `====...====` 分隔，`[日期时间] | 操作: xxx | 结果: xxx` 开头
5. 审计日志不得被 AI 自行修改或删除（仅追加）

### 5.3 版本迭代日志 `[DO]` — 验证闭环强制步骤

> 对应 `01_core_behavior.md` 原则 5 标准验证流程第 6 步

1. **触发时机**：每次实质性变更完成后**必须立即**更新版本日志，不允许跳过或延期
2. **判断标准**：非临时文件、非纯格式修改即为实质性变更
3. 版本日志文件：项目根目录或子模块目录 `VERSION_LOG.md`
4. **追加策略**：新增版本记录**必须追加到已有内容末尾**（时间正序，v1.0 → v1.1 → v1.2 → ...），不得覆盖、替换或插入到已有记录之前。若 `VERSION_LOG.md` 不存在则自动创建
5. 记录格式：版本号（语义化版本）、日期、变更类型（新增功能/改进优化/bug 修复/文档完善）、变更摘要、影响文件列表
6. 版本号规则：主版本号（重大改动/结构调整）、次版本号（功能新增/内容扩充）、修订号（文字修正/格式调整/bug 修复）
7. **子模块独立维护**：如 `game/`、`scripts/` 等子目录有独立项目，各自维护独立 `VERSION_LOG.md`

---

## 6. 依赖镜像源策略

### 6.1 选择原则

1. `[DO]` 默认使用国内镜像加速
2. `[DO]` 优先级：可用性检测 → 响应最快者优先，失败自动切换
3. `[ASK]` 修改项目镜像配置文件前询问用户
4. `[DO]` 镜像超时时自动回退至官方源

### 6.2 各语言默认镜像源

| 语言 | 镜像源 URL | 提供商 |
|------|-----------|--------|
| **Python (pip)** | `https://pypi.tuna.tsinghua.edu.cn/simple` | 清华大学（默认首选） |
| | `http://mirrors.aliyun.com/pypi/simple/` | 阿里云 |
| | `https://mirrors.cloud.tencent.com/pypi/simple` | 腾讯云 |
| | `https://repo.huaweicloud.com/repository/pypi/simple` | 华为云 |
| **Node.js (npm)** | `https://registry.npmmirror.com` | 淘宝/NPMMirror |
| | `https://mirrors.tencent.com/npm/` | 腾讯云 |
| | `https://repo.huaweicloud.com/repository/npm/` | 华为云 |
| **Go (go mod)** | `https://goproxy.cn` | 七牛云 |
| **Rust (cargo)** | `https://mirrors.tuna.tsinghua.edu.cn/crates.io-index` | 清华大学 |
| **Java (Maven)** | `https://maven.aliyun.com/repository/public` | 阿里云 |

### 6.3 安装命令示例

```bash
# Python pip（默认清华源，无需询问）
pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple

# Node.js npm（默认 NPMMirror，无需询问）
npm install <package> --registry https://registry.npmmirror.com
```

---

## 7. Token 预算与规则文件管理（v1.1 新增）

> 来源：AGENTS.md 文件大小建议 + Vercel 2026 评估——膨胀的指令文件可使 Agent 任务完成度下降 30%

### 7.1 Token 预算限制

| 文件类型 | 最大行数 | 最大 Token | 触发修剪 |
|---------|---------|-----------|---------|
| 根目录 `AGENTS.md` | 250 行 | 8K | 超过 250 行 |
| 子目录 `AGENTS.md` | 80 行 | 2K | 超过 80 行 |
| `CLAUDE.md`（适配层） | 60 行 | 1.5K | 超过 80 行 |
| `.cursor/rules/*.mdc`（单文件） | 100 行 | 2.5K | 超过 150 行 |
| `ai_rules/` 子文件 | 300 行 | 5K | 超过 300 行 |

### 7.2 规则文件提交检查清单

每次修改规则文件后，在提交前验证：

```bash
# 1. 检查行数
wc -l AGENTS.md

# 2. 检查敏感信息泄露
grep -iE '(password|secret|token|api_key)\s*[:=]' AGENTS.md

# 3. 检查重复规则（与 .claude/、.cursor/ 对比）
diff <(grep -oP '\[BLOCK\].*' AGENTS.md | sort) \
     <(grep -oP '\[BLOCK\].*' CLAUDE.md | sort)
```

### 7.3 规则文件版本管理约束

1. `[DO]` 每次修改规则文件后，更新文件头部的 `version` 和 `last_updated` 字段 — **强制步骤**，已纳入 `01_core_behavior.md` 验证闭环步骤 7
2. `[DO]` 重大变更保留旧版本文件（加 `_v{旧版本}.md` 后缀或归档至 `docs/history/`）
3. `[DO]` 在 `VERSION_LOG.md` 记录变更摘要
4. `[BLOCK]` 不得删除或覆盖历史版本而不保留备份
