# Git/GitHub MCP 网络连接失败：快速排查要点

> 来源：ai-configuration/06-MCP/Git-MCP-网络连接失败排查与修复.md（完整版见 ai-configuration/06-MCP/）
> 适用：AI 工具中 Git 类 MCP（server-git / server-github）报「网络连接失败 / fetch failed」

## 0. 结论（必读）

**MCP 子进程（node/npx）不自动继承系统代理**。国内环境绝大多数「网络连接失败」
不是超时，而是 **TLS 证书验证失败**（代理 MITM 替换证书，node 默认只信任 Mozilla CA）。

> ⚠️ 核心区分：`git` 命令能访问 ≠ `node` 能访问。git 代理与 node 代理是**两套独立配置**。

修复三板斧（三选一或组合）：
1. `env` 注入 `HTTP_PROXY` / `HTTPS_PROXY`（node 不读系统代理）
2. 证书错误（`UNABLE_TO_VERIFY_LEAF_SIGNATURE`）→ `NODE_OPTIONS: --use-system-ca`（Node ≥ 22.9）
3. 仍不行 → `--tls-reject-unauthorized=0`（**仅本地调试，不安全，不推荐**）

## 1. 诊断命令（按顺序执行）

```powershell
# ① 验证 node 链路（最重要）
node -e "fetch('https://api.github.com').then(r=>console.log('NODE OK:', r.status)).catch(e=>console.error('NODE FAIL:', e.cause?.code || e.message))"

# ② 查看系统代理端口（Clash Verge 常为 127.0.0.1:7897）
(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyServer

# ③ 带代理 + 系统 CA 重测
$env:HTTP_PROXY="http://127.0.0.1:7897"; $env:HTTPS_PROXY="http://127.0.0.1:7897"
node --use-system-ca -e "fetch('https://api.github.com').then(r=>console.log('NODE OK:', r.status)).catch(e=>console.error('NODE FAIL:', e.cause?.code || e.message))"

# ④ 验证 git 链路（排除 git 层问题）
git ls-remote https://github.com/octocat/Hello-World.git HEAD
```

| 输出 | 结论 |
|---|---|
| `NODE OK: 200` | node 直连正常，问题在别处 |
| `NODE FAIL: fetch failed` | 网络不通 → 需要代理 |
| `NODE FAIL: UNABLE_TO_VERIFY_LEAF_SIGNATURE` | **证书问题** → `--use-system-ca` |
| `NODE FAIL: ENOTFOUND` | DNS 解析失败 |

## 2. 修复模板（.mcp.json）

> 改前先备份 `Copy-Item .mcp.json .mcp.json.bak`；Windows 路径必须正斜杠 `D:/code/repo`；JSON 末尾不能多逗号。

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

- 代理端口换成实际端口（Clash Verge 默认 7897，Clash for Windows 默认 7890）
- 私有仓库必须配 token（scope ≥ repo），用环境变量引用，**禁止硬编码 token 入库**
- 改完必须**重载 MCP / 完全重启客户端**（旧子进程持旧环境变量）

## 3. 踩坑清单

| # | 坑 | 说明 |
|---|---|---|
| 1 | 以为浏览器能访问 = node 能访问 | node 子进程不自动继承系统代理 |
| 2 | 只配 git 代理 | git ≠ node，两套独立配置 |
| 3 | 只加 --use-system-ca 不加代理 | TUN 干扰仍直连失败，必须组合 |
| 4 | Windows 路径写反斜杠 | JSON 内必须 `D:/code/repo` |
| 5 | mcp.json 末尾多逗号 | 进程直接挂掉，界面笼统报网络失败 |
| 6 | 改完不重载 MCP | 旧子进程持旧环境变量，配置不生效 |
| 7 | token 没配/scope 不全 | 私有仓库 401 |
| 8 | 防火墙/杀软拦截 node.exe | Windows 安全软件拦截出站 |

## 4. `git push` 直连报 `Connection reset`（Watt Toolkit 场景）

> 完整版见 `ai-configuration/06-MCP/...` §7；实战见 `ai-configuration/07-TROUBLESHOOTING/2026-09-01-GitHub推送WattToolkit加速排查.md`

**先判定加速方案再动手**：

| 方案 | 原理 | git 是否配代理 | 判定命令 |
|---|---|---|---|
| Watt Toolkit（Steam++） | hosts 劫持 + 本地 80/443 透明转发 | **不配**，直连即走加速 | `findstr /I github C:\Windows\System32\drivers\etc\hosts` + `tasklist \| findstr /I "watt steam"` |
| Clash 类代理 | 独立端口（7890/7897） | 需要 `http.proxy` | `netstat -ano \| findstr "7897 7890"` |

要点：

1. Watt Toolkit 场景：确认 hosts 有 `127.0.0.1 github.com` + `Steam++.Accelerator.exe` 监听 80/443 → **直接 `git push`，禁止配代理**
2. 代理端口不能拿来就用：先 `netstat` 查监听，`CONNECT 405` = 不是 HTTP 代理（禁止沿用）
3. Clash 场景用一次性参数：`git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push`（不写回全局 config）
