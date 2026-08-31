---
description: "Git/GitHub MCP 在 AI 工具中报『网络连接失败』的完整排查与修复指南（含诊断命令、配置片段、验证脚本）"
version: 1.0
last_updated: 2026-08-31
---

# Git/GitHub MCP 网络连接失败：排查与修复指南

> **适用场景**：AI 工具（CodeBuddy / Claude Code / Cursor 等）中，Git 类 MCP 服务器
> （`@modelcontextprotocol/server-git` / `@modelcontextprotocol/server-github`）
> 报「网络连接失败 / 连接失败 / fetch failed / connect timeout」。
>
> **本文档可直接粘贴给任何 AI 工具作为上下文**，或在本地按步骤执行。

---

## 0. 先说结论（必读）

**MCP 子进程（node/npx）不自动继承系统代理**。国内环境绝大多数「网络连接失败」
不是 AI 客户端问题，而是 **npx 启动的 MCP 子进程访问 GitHub API 失败**，且失败原因
**不是超时，而是 TLS 证书验证失败**（Clash/V2Ray 等代理对 GitHub 做 MITM 替换证书，
node 默认只信任 Mozilla CA，不认代理根证书）。

> ⚠️ **核心区分**：`git` 命令能访问 ≠ `node` 能访问。git 的代理与 node 的代理是
> **两套独立配置**。git 正常不代表 MCP 正常。

修复三板斧（三选一或组合）：

1. `env` 注入 `HTTP_PROXY` / `HTTPS_PROXY`（node 不读系统代理，必须显式给）
2. 若报证书错误（`UNABLE_TO_VERIFY_LEAF_SIGNATURE` / `SELF_SIGNED_CERT_IN_CHAIN`）：
   加 `NODE_OPTIONS: --use-system-ca`（需 Node ≥ 22.9，让 node 信任 Windows 系统证书库，
   其中已装代理根证书）
3. 若前两者不行：`NODE_OPTIONS: --use-system-ca` 改为 `--tls-reject-unauthorized=0`（**仅本地调试用，不安全，不推荐**）

---

## 1. 故障分层（先定位是哪个环节）

| 环节 | 说明 | 判断方法 |
|---|---|---|
| A. AI 客户端 ↔ MCP 服务 | stdio 本机管道，几乎不会网络失败 | 终端手动跑 MCP 命令 |
| B. MCP 服务 → GitHub API | **最高发**：node 走代理/证书问题 | 终端手动跑 MCP 命令看真实报错 |
| C. git 命令 → GitHub | git 自身的代理配置 | `git ls-remote` |
| D. 浏览器 → GitHub | 系统代理/TUN | 浏览器直接访问 |

**快速区分**：

- 终端手动运行 MCP 命令也网络报错 → **问题在 B 层**（代理/证书/token），处理 `env` 代理
- 终端运行 MCP 正常，AI 工具仍失败 → 问题在 A 层（客户端配置、传输协议 stdio/SSE、版本兼容），重载 MCP / 重启客户端

---

## 2. 诊断步骤（按顺序执行）

### 步骤 1：验证 node 链路（最重要，直接复现 MCP 报错）

```powershell
# Windows PowerShell
node -e "fetch('https://api.github.com').then(r=>console.log('NODE OK:', r.status)).catch(e=>console.error('NODE FAIL:', e.cause?.code || e.message))"
```

预期结果与结论：

| 输出 | 结论 |
|---|---|
| `NODE OK: 200` | node 直连正常，问题在别处 |
| `NODE FAIL: fetch failed` | 网络不通 → 需要代理 |
| `NODE FAIL: UNABLE_TO_VERIFY_LEAF_SIGNATURE` | **证书问题** → `--use-system-ca`（代理 MITM） |
| `NODE FAIL: ENOTFOUND` | DNS 解析失败 → DNS/代理 |

### 步骤 2：验证代理链路（找到你的代理端口）

```powershell
# 查看 Windows 系统代理设置（Clash Verge 常显示 127.0.0.1:7897）
(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyServer

# 查看 git 代理（注意：git 代理 ≠ node 代理）
git config --global --get http.proxy
git config --global --get https.proxy
```

**注意**：如果系统代理开关是关的（`ProxyEnable: 0`）但 git/浏览器都能访问，
说明在用 **TUN 模式**（虚拟网卡接管流量）。此时 node 直连会被透明代理干扰，
更需要显式 `HTTP_PROXY` + `--use-system-ca` 组合。

### 步骤 3：带代理 + 系统 CA 重测 node（修复验证）

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
$env:NO_PROXY="localhost,127.0.0.1"
node --use-system-ca -e "fetch('https://api.github.com').then(r=>console.log('NODE OK:', r.status)).catch(e=>console.error('NODE FAIL:', e.cause?.code || e.message))"
```

- `NODE OK: 200` → 修复方案确认有效，直接改 `.mcp.json`
- 仍失败 → 检查代理端口是否正确、代理是否真的在运行

### 步骤 4：验证 git 链路（排除 C 层）

```bash
git ls-remote https://github.com/octocat/Hello-World.git HEAD
```

失败则先修 git 网络（`git config --global http.proxy http://127.0.0.1:7897`）。

---

## 3. 修复：修改 `.mcp.json`

> ⚠️ **修改前先备份**：`Copy-Item .mcp.json .mcp.json.bak`
> ⚠️ **Windows 路径必须用正斜杠**：`D:/code/repo`，不能写 `D:\code\repo`
> ⚠️ **JSON 末尾不能多逗号**，否则 MCP 进程直接崩溃

### 3.1 `server-github`（GitHub API 版，走 npx 的 stdio 服务）

```json
{
  "mcpServers": {
    "GitHub": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "NODE_OPTIONS": "--use-system-ca",
        "HTTP_PROXY": "http://127.0.0.1:7897",
        "HTTPS_PROXY": "http://127.0.0.1:7897",
        "NO_PROXY": "localhost,127.0.0.1",
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      },
      "type": "stdio",
      "disabled": false
    }
  }
}
```

- 代理端口换成你本地实际端口（Clash Verge 默认 `7897`，Clash for Windows 默认 `7890`）
- 访问私有仓库必须配 token，scope 至少勾 `repo`；`${GITHUB_PERSONAL_ACCESS_TOKEN}` 是环境变量引用，**禁止硬编码 token 入库**

### 3.2 `server-git`（本地 git 命令版）

```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git", "D:/code/myrepo"],
      "env": {
        "NODE_OPTIONS": "--use-system-ca",
        "HTTP_PROXY": "http://127.0.0.1:7897",
        "HTTPS_PROXY": "http://127.0.0.1:7897",
        "NO_PROXY": "localhost,127.0.0.1"
      },
      "type": "stdio",
      "disabled": false
    }
  }
}
```

> 仓库路径必须用**绝对路径**（`D:/code/myrepo`），不要用 `.` 相对路径。

### 3.3 改完必须做的事

1. **重载 MCP / 完全重启 AI 客户端**（不是重启会话窗口——旧进程还持有旧环境变量）
2. 如果客户端仍报失败，用下面的验证脚本确认配置本身没问题

---

## 4. 验证：完整 MCP 握手 + 真实工具调用

> 与 AI 客户端完全相同的调用路径：`initialize` → `notifications/initialized` → `tools/call`。
> 以下脚本验证 **server-github 包已缓存时的入口**；若报 ENOENT，先 `npx -y @modelcontextprotocol/server-github` 下载一次，
> 或用 `npx.cmd` 代替。包入口路径按你实际缓存目录调整。

```powershell
node -e "const{spawn}=require('child_process');const c=spawn('node',['<NPM_CACHE>/_npx/<HASH>/node_modules/@modelcontextprotocol/server-github/dist/index.js'],{env:{...process.env,NODE_OPTIONS:'--use-system-ca',HTTP_PROXY:'http://127.0.0.1:7897',HTTPS_PROXY:'http://127.0.0.1:7897',NO_PROXY:'localhost,127.0.0.1'}});let buf='';c.stdout.on('data',d=>{buf+=d;let i;while((i=buf.indexOf('\n'))>=0){const l=buf.slice(0,i);buf=buf.slice(i+1);try{const m=JSON.parse(l);if(m.id===1){send(null,'notifications/initialized');send(2,'tools/call',{name:'search_repositories',arguments:{query:'repo:octocat/Hello-World'}});}if(m.id===2){const s=m.error?('ERROR: '+m.error.message):(m.result&&m.result.content&&m.result.content[0]?m.result.content[0].text.slice(0,200):'EMPTY');console.log('TOOL_RESULT: '+s.replace(/\n/g,' '));process.exit(0);}}catch(e){}}});function send(id,method,params){c.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n');}c.stderr.on('data',d=>{});send(1,'initialize',{protocolVersion:'2024-11-05',capabilities:{},clientInfo:{name:'t',version:'1'}});setTimeout(()=>{console.log('TIMEOUT');process.exit(1);},30000);"
```

**通过标准**：输出 `TOOL_RESULT: {"total_count": ...}` 且包含仓库数据 → 网络 + 协议 + token 三层全部正常。

---

## 5. 踩坑清单（高频原因）

| # | 坑 | 说明 |
|---|---|---|
| 1 | ❌ 以为浏览器能访问 = node 能访问 | **node 子进程不自动继承系统代理**，国内头号坑 |
| 2 | ❌ 只配 `git` 代理 | git 代理 ≠ node 代理，两套独立配置 |
| 3 | ❌ 只加 `--use-system-ca` 不加代理 | 证书对了但直连仍被 TUN 干扰，必须组合 |
| 4 | ❌ Windows 路径写反斜杠 | JSON 内必须 `D:/code/repo` 或 `D:\\code\\repo` |
| 5 | ❌ mcp.json 末尾多逗号 | JSON 非法，MCP 进程直接挂掉，界面笼统报网络失败 |
| 6 | ❌ 改完不重载 MCP | 配置不生效，旧子进程还持旧环境变量 |
| 7 | ❌ token 没配/scope 不全 | 私有仓库报 401，上层笼统提示网络失败 |
| 8 | ❌ 防火墙/杀软拦截 node.exe | Windows 安全软件拦截 node 出站，临时关闭测试 |

---

## 6. 实战案例（2026-08-31，本机已修复）

**现象**：CodeBuddy 中 GitHub MCP 报网络连接失败。

**诊断过程**：

| 测试 | 结果 | 结论 |
|---|---|---|
| `git ls-remote github.com` | ✅ 正常 | git 链路 OK |
| `node fetch api.github.com`（直连） | ❌ `UNABLE_TO_VERIFY_LEAF_SIGNATURE` | 证书问题 |
| `node fetch`（走代理 7897） | ❌ 同样证书错 | 代理 MITM 证书不被 node 默认 CA 信任 |
| `node --use-system-ca`（走代理） | ✅ 200 | 修复方案确认 |
| `curl -x 127.0.0.1:7897` | ❌ HTTP 000 | 确认走代理而非直连 |

**环境特征**：Clash Verge TUN 模式（`ProxyEnable: 0`，端口 `127.0.0.1:7897`），
Clash 根证书已装 Windows 系统证书库。

**修复**：`.mcp.json` 的 GitHub server `env` 加：

```json
"NODE_OPTIONS": "--use-system-ca",
"HTTP_PROXY": "http://127.0.0.1:7897",
"HTTPS_PROXY": "http://127.0.0.1:7897",
"NO_PROXY": "localhost,127.0.0.1"
```

**验证**：完整 MCP 握手（`github-mcp-server 0.6.2`）+ `search_repositories` 真实调用
返回 `octocat/Hello-World` → 三层全通。

---

## 7. 参考

- Node 系统 CA 支持：<https://nodejs.org/api/cli.html#--use-system-ca>（Node ≥ 22.9）
- MCP 官方 servers：<https://github.com/modelcontextprotocol/servers>
- server-github npm：<https://www.npmjs.com/package/@modelcontextprotocol/server-github>
- server-git npm：<https://www.npmjs.com/package/@modelcontextprotocol/server-git>
