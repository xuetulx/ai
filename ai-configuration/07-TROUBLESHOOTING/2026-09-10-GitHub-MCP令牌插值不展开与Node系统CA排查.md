---
title: "GitHub MCP 报 Bad credentials：CodeBuddy 不展开 mcp.json 的 ${VAR} 插值（附 Node 系统 CA 坑）"
date: 2026-09-10
status: resolved
category: mcp-config
tags: [github, mcp, codebuddy, environment-variable, token, node, use-system-ca, watt-toolkit]
related:
  - "ai-configuration/06-MCP/Git-MCP-网络连接失败排查与修复.md"
  - "ai-configuration/07-TROUBLESHOOTING/2026-09-01-GitHub推送WattToolkit加速排查.md"
---

# GitHub MCP 报 Bad credentials：CodeBuddy 不展开 `mcp.json` 的 `${VAR}` 插值

> **适用场景**：CodeBuddy 中 GitHub MCP 报 `Bad credentials`（HTTP 401），
> 但本机 `git` 能推送、Watt Toolkit 加速正常、token 也确认真实有效。
>
> **结论先行**：根因不是网络、也不是代理，而是
> **CodeBuddy 当前版本不会展开 `mcp.json` 里 `env` 的 `${VAR}` 插值**，
> MCP 子进程拿到的是**字面量字符串** `${GITHUB_PERSONAL_ACCESS_TOKEN}`，GitHub 自然回 401。
>
> **修复思路**：**删掉 `env` 里的 token 键**，让 MCP 子进程**直接继承主进程的环境变量**，
> 绕开不生效的插值；同时保留 `NODE_OPTIONS=--use-system-ca`（Node 必须信任 Watt Toolkit 的本地 CA）。

---

## 1. 现象

```text
GitHub MCP → Bad credentials (401)
```

命令行直连 GitHub API 却是好的，`git push` 也正常 —— 典型「看起来像网络/代理问题，实为配置问题」。

---

## 2. 先排除三个「看起来像」的方向

| 检查项 | 命令 / 依据 | 实测结果 | 结论 |
|---|---|---|---|
| Watt Toolkit 加速 | `tasklist \| findstr /I "steam"` + `netstat -ano \| findstr ":443"` | `Steam++.Accelerator.exe` 监听 `0.0.0.0:443` | ✅ 正常 |
| hosts 劫持 | `findstr /I github C:\Windows\System32\drivers\etc\hosts` | `127.0.0.1 api.github.com` | ✅ 已生效 |
| GitHub Token 有效性 | 直连 `api.github.com/user` | `200`，`login=xuetulx` | ✅ **token 本身有效** |
| npm 源 | `npm config get registry` | 官方源（未走国内镜像） | ⚠️ 仅影响 `npx` 拉包速度 |

> 三层（网络/加速/hosts/token）全部正常，因此 **401 与网络无关**，问题在「token 如何传到子进程」。

---

## 3. 根因定位：`${VAR}` 插值不展开

**关键判别实验**：拿一个**用完全相同 `${VAR}` 写法**的 MCP 做对照 —— CNB MCP。

```text
CNB MCP（env 用 ${CNB_API_TOKEN}） → 401 "not logged in"
而 CNB_API_TOKEN 环境变量明明存在
```

**两个 MCP 全部 401** ⇒ 只能是 **插值没生效**：

- CodeBuddy 当前版本**不会展开** `mcp.json` 中 `env` 的 `${VAR}`
- 子进程收到的是**字面量** `${GITHUB_PERSONAL_ACCESS_TOKEN}`（而不是 token 值）
- GitHub 校验该字面量 → `Bad credentials`（401）

> 这是**配置语义问题**，与网络、代理、证书、token 是否有效**全部无关**。

---

## 4. 顺带挖出的隐藏坑：Node 与 Watt Toolkit 的自签 CA

Watt Toolkit 的本地 443 反代使用**自签 CA**。`.NET/PowerShell` 走系统证书库能通，
**Node 默认只信任 Mozilla CA，不认它**：

```powershell
node                     # → fetch failed           （Node 不信任 Watt 自签 CA）
node --use-system-ca     # → HTTP_STATUS=200        （读取系统证书库后正常）
```

结论：**`NODE_OPTIONS=--use-system-ca` 是必需的**（Node 需读取系统证书库以信任 Watt Toolkit 的 CA）。
另外实测 `registry.npmmirror.com` 可用（HTTP 200），可用于加速 `npx` 拉包。

---

## 5. 修复：重配 `~/.codebuddy/mcp.json`

> 路径：`C:\Users\Administrator\.codebuddy\mcp.json`
> 备份：`mcp.json.bak-20260910`（回滚即用备份覆盖回去）

### 5.1 改动要点

1. **删掉** `env.GITHUB_PERSONAL_ACCESS_TOKEN` 键
   → 改由 MCP 子进程**继承 CodeBuddy 主进程环境变量**（已证实主进程存在该变量），**绕开不生效的插值**
2. **保留** `NODE_OPTIONS: "--use-system-ca"` → 信任 Watt Toolkit 的本地 CA（必需）
3. **新增** `npm_config_registry: "https://registry.npmmirror.com"` → 加速 `npx` 拉包

### 5.2 修复后的 GitHub 条目

```json
"GitHub": {
  "autoApprove": [],
  "timeout": 60000,
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github@2025.4.8"],
  "env": {
    "NODE_OPTIONS": "--use-system-ca",
    "npm_config_registry": "https://registry.npmmirror.com"
  },
  "type": "stdio",
  "disabled": false
}
```

### 5.3 校验

- JSON 合法（能被解析）
- **无任何硬编码 token** 入库
- lint 0 错误

---

## 6. 生效条件（必须）

**新配置必须重启 CodeBuddy（或在 MCP 面板断开重连 `GitHub`）才生效**。
修改后立即重试仍是旧报错，是因为旧 MCP 子进程仍持有旧的字面量 token —— 属正常现象。

---

## 7. 纠正一个方向：Watt Toolkit 不能配成 HTTP 代理

- Watt Toolkit 走 **hosts + 本地 443 反代**模式，**没有** `1080`/`7890`/`7897` 这类代理端口（实测只监听 443）
- 因此写 `HTTPS_PROXY=...` 指向它是**无效的**
- 它正常工作只依赖两件事，无需再配代理：
  1. **hosts 劫持**（已有 hook `ensure-watt-accelerator.sh` 在会话启动/每次 GitHub MCP 调用前自动保活）
  2. **Node 信任它的 CA**（即 `--use-system-ca`）

> 反面教训：不要给这个环境画蛇添足地配 `HTTP_PROXY`。

---

## 8. 连带发现：CNB MCP 同因故障

CNB MCP 报 401「not logged in」的**根因完全相同**（同样是不展开 `${CNB_API_TOKEN}` 插值）。
本次仅按授权范围处理 GitHub；CNB 修复方式与上完全一致（删 token 键 → 继承主进程 env）。

---

## 9. 可复用经验清单

1. **MCP 报 401/认证错时，先分清「token 无效」还是「token 没传到」**：
   直连 API 验证 token 有效性（`api.github.com/user`），有效则问题在传递链路。
2. **`${VAR}` 插值不可假定的能力**：同一个 MCP 框架里用两个 MCP 对照（同写法是否都 401），即可判定「是否展开插值」。
3. **CodeBuddy 当前不展开 `mcp.json` 的 `env` 插值** → 需要密钥类变量时，**删键让子进程继承主进程环境变量**（更稳，也不必把密钥写进配置）。
4. **Node 走透明加速/自签 CA 反代时，必须 `NODE_OPTIONS=--use-system-ca`**（`fetch failed` 的典型真因）。
5. **`--use-system-ca` 与「配代理」是两件事**：Watt Toolkit 透明加速模式只需前者，**不需要** `HTTP_PROXY`。
6. **改了 MCP 配置必须重启客户端**，否则旧子进程继续用旧环境变量，会误判「修复无效」。
7. **配置改动前先备份** `mcp.json` → `mcp.json.bak-<日期>`，并确保 `mcp.json` 里**不出现明文 token**。

---

## 10. 关联文档

- `ai-configuration/06-MCP/Git-MCP-网络连接失败排查与修复.md` — 网络/证书层完整指南（Clash + Watt Toolkit 两套方案）
- `ai-configuration/07-TROUBLESHOOTING/2026-09-01-GitHub推送WattToolkit加速排查.md` — `git push` 网络排查实战
- `ai-configuration/02-RULE/Agent-Requested/04-git-mcp-troubleshooting.mdc` — 按需加载的规则版要点
