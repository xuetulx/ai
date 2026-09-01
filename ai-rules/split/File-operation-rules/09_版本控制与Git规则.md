## 10. 版本控制与 Git 规则

### 10.1 Git 操作约束

1. `[BLOCK]` 禁止直接读写 `.git/` 目录下的任何文件
2. `[DO]` 通过 git 命令间接操作版本控制（如 `git status`、`git diff`）
3. `[ASK]` 执行 `git commit`、`git push`、`git reset` 等写操作前必须确认
4. `[BLOCK]` 禁止执行 `git push --force`、`git reset --hard` 等破坏性操作（除非用户明确要求并二次确认）
5. `[DO]` **每次修改内容提交前，必须在新建分支上进行**，不得直接在原有分支（如 `main`、`master`、`develop`）上 commit

### 10.2 提交消息规范

1. `[DO]` Git 提交消息遵循 Conventional Commits 规范
   - 格式：`<type>(<scope>): <description>`
   - 类型：`feat` / `fix` / `docs` / `refactor` / `test` / `chore` / `style`
2. `[DO]` 提交消息使用中文或英文，保持项目既有风格一致

### 10.3 AI 生成文件的版本管理

1. `[DO]` 重要文件修改保留历史版本，使用版本号命名（v1.0、v1.1、v2.0）
2. `[DO]` 版本号规则（语义化版本）：
   - 主版本号：重大改动、结构调整
   - 次版本号：功能新增、内容扩充
   - 修订号：文字修正、格式调整、bug 修复
3. `[DO]` 修改记录可写入文件头部或单独的变更日志
4. `[DO]` 本规则文件编辑后生成新版本时，文件名必须包含版本号，与文档内部版本号保持一致。
5. `[DO]` 命名格式：`AgentAI_项目文件操作规则_v{主版本}.{次版本}.md`
   - 示例：`AgentAI_项目文件操作规则_v2.1.md`、`AgentAI_项目文件操作规则_v2.2.md`
6. `[DO]` 旧版本文件应保留至少一个历史版本用于追溯，或归档到 `docs/history/` 目录。
7. `[DO]` 配套规范（如 AI_RULES_编程参考规范）同步遵循相同命名规则：`AI_RULES_编程参考规范_v{主版本}.{次版本}.md`。

### 10.4 分支管理规则（v2.0 新增）

#### 10.4.1 核心原则

1. `[DO]` **AI 每次执行文件修改任务，必须先创建新分支，再在新分支上提交**。
2. `[BLOCK]` **禁止在原有分支（`main`、`master`、`develop`、`release/*`）上直接 commit 任何修改**。
3. `[DO]` 原有分支仅用于读取代码、理解项目结构，不做任何写操作。

#### 10.4.2 分支命名规范

```
<type>/<description>
```

| 组成部分 | 说明 | 示例 |
|---------|------|------|
| `type` | 对应 Conventional Commits 类型 | `feat`、`fix`、`docs`、`refactor` |
| `description` | 简短描述，小写字母 + 连字符 | `add-radar-filter`、`fix-cache-bug` |

- `[DO]` 格式：`feat/add-user-auth`、`fix/null-pointer-crash`、`docs/update-api-readme`
- `[DO]` 必要时可加日期前缀避免重名：`ai/20260701_fix-cache-bug`

#### 10.4.3 标准工作流

```
[DO] 1. 确认当前分支 → git branch --show-current
[DO] 2. 记录原分支名（如 main / develop），确保任务结束后可切回
[DO] 3. 从原分支创建新分支 → git checkout -b feat/<任务描述>
[DO] 4. 在新分支上进行文件修改
[DO] 5. git add + git commit（遵循 Conventional Commits）
[ASK] 6. 询问用户是否推送或合并（git push / PR / merge）
[DO] 7. 用户决定后，根据指示切回原分支或保持当前分支
```

#### 10.4.4 禁止操作

1. `[BLOCK]` 在 `main` / `master` / `develop` 分支上直接执行 `git commit`
2. `[BLOCK]` 未经用户确认执行 `git merge`、`git rebase` 到原分支
3. `[BLOCK]` 未经用户确认删除任何分支（包括 AI 自己创建的分支）
4. `[DO]` 任务完成后提醒用户：当前所在分支、是否有未合并的分支

### 10.5 GitHub 网络代理排查要点（v1.9 新增）

> **适用**：`git push`/`git fetch` 到 GitHub 报 `Connection reset` / `Couldn't connect to server`。
> 完整排查文档：`ai-configuration/06-MCP/Git-MCP-网络连接失败排查与修复.md` §7
> 实战记录：`ai-configuration/07-TROUBLESHOOTING/2026-09-01-GitHub推送WattToolkit加速排查.md`

1. `[DO]` **先判定加速方案再动手**：`Connection reset` ≠ 没配代理
   - **Watt Toolkit（Steam++）**：hosts 劫持 + 本地 80/443 透明转发，git 不配代理直连即走加速
     - 判定：`findstr /I github C:\Windows\System32\drivers\etc\hosts` 有 `127.0.0.1 github.com`，且 `tasklist | findstr /I "watt steam"` 有 `Steam++.Accelerator.exe`
   - **Clash 类代理**：独立代理端口（7890/7897），git 需显式配 `http.proxy`
     - 判定：`netstat -ano | findstr "7897 7890"` 有监听
2. `[BLOCK]` Watt Toolkit 场景**禁止**给 git 配 `http.proxy`（会绕过加速器反而失败）
3. `[BLOCK]` 代理端口报 `CONNECT 405` = 不是 HTTP 代理（如 clash-verge-service 管理端口），禁止沿用
4. `[DO]` Clash 场景用一次性参数临时代理，不写回全局 config：
   `git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push`
5. `[ASK]` 需持久化代理时，询问用户后再 `git config --global http.proxy`
