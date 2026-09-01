---
title: "GitHub 推送网络排查：Watt Toolkit（Steam++）加速模式实战"
date: 2026-09-01
status: resolved
category: network
tags: [github, git, watt-toolkit, steam++, proxy, network-troubleshooting]
related:
  - "ai-configuration/06-MCP/Git-MCP-网络连接失败排查与修复.md"
---

# GitHub 推送网络排查：Watt Toolkit（Steam++）加速模式实战

> **适用场景**：国内环境 `git push` / `git fetch` 到 GitHub 报
> `Failed to connect to github.com port 443: Connection reset`，
> 且本机使用 **Watt Toolkit（Steam++）** 加速 GitHub。
>
> **结论先行**：Watt Toolkit 加速模式是 **hosts 劫持 + 本地 80/443 透明转发**，
> git **不需要配置任何代理**，直连即可走加速。不要画蛇添足配 `http.proxy`。

---

## 1. 现象

```text
$ git push -u origin v1.4.1
fatal: unable to access 'https://github.com/...':
Failed to connect to github.com port 443 after 21055 ms:
Couldn't connect to server
```

或：

```text
error: Connection reset by peer
```

---

## 2. 诊断过程（2026-09-01 实战）

| # | 步骤 | 命令 | 结果 | 结论 |
|---|---|---|---|---|
| 1 | 系统代理设置 | `(Get-ItemProperty 'HKCU:\...\Internet Settings').ProxyServer` | `127.0.0.1:7897` | 注册表残留 Clash 端口 |
| 2 | 检查代理端口监听 | `netstat -ano \| findstr 7897` | 无监听 | **Clash 未运行** |
| 3 | git 代理配置 | `git config --get http.proxy` | 空 | git 是直连模式 |
| 4 | 带 Clash 代理重试 | `git -c http.proxy=http://127.0.0.1:7897 push` | 连接被拒 | 端口无监听必然失败 |
| 5 | 全端口扫描 | `netstat -ano \| findstr LISTENING` | 发现 `clash-verge-service` 监听 `33211` | 有可疑进程 |
| 6 | 试 33211 作 HTTP 代理 | `git -c http.proxy=http://127.0.0.1:33211 push` | `CONNECT 405 Method Not Allowed` | **33211 不是 HTTP 代理端口** |
| 7 | 查 hosts 劫持 | `findstr /I github C:\Windows\System32\drivers\etc\hosts` | github 域名全指向 `127.0.0.1` | **Watt Toolkit 加速生效** |
| 8 | 查加速进程监听 | `netstat -ano \| findstr ":443"` + `tasklist` | `Steam++.Accelerator.exe` 监听 `80`/`443` | 透明转发已就绪 |
| 9 | 直连重试 | `git push -u origin v1.4.1` | **成功** | Watt Toolkit 透明加速，无需代理 |

---

## 3. 关键识别方法

### 3.1 判断是否 Watt Toolkit 加速模式

```powershell
# ① hosts 是否劫持 github（加速生效标志）
findstr /I "github" C:\Windows\System32\drivers\etc\hosts
# 输出应看到：127.0.0.1 github.com / api.github.com / *.githubusercontent.com ...

# ② 加速进程是否在监听 80/443
netstat -ano | findstr ":80 " | findstr "LISTENING"
netstat -ano | findstr ":443" | findstr "LISTENING"
tasklist | findstr /I "watt steam"
# 看到 Steam++.Accelerator.exe（或 SteamTools 相关进程）监听 80/443 → 加速已启动
```

**满足 ① + ② 即可判定**：git 直连即可，`Connection reset` 通常说明加速服务
未启动（打开 Watt Toolkit 并开启"网络加速"）或 hosts 被还原。

### 3.2 判断是否 Clash 类代理模式

```powershell
# 代理端口有监听 + 系统代理开启
(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyEnable
(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyServer
netstat -ano | findstr "7897 7890"
```

Clash 类代理需要给 git 显式配代理：

```bash
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push
```

> ⚠️ 代理端口**不能拿来就用**：必须先确认端口有监听进程，且该进程是 HTTP 代理
> （不是任意监听端口）。用 `git push` 测一次，若报 `CONNECT 405` 说明该端口
> 不是 HTTP 代理。

---

## 4. 结论与要点

1. **`Connection reset`（直连被重置）≠ 没配代理**，先判断本机加速方案再动手。
2. **Watt Toolkit（Steam++）加速 = hosts 劫持 + 本地 80/443 透明转发**：
   - git/浏览器/命令行**全透明**，直连 443 即被加速器接管
   - **不要**给 git 配 `http.proxy`（会绕过加速器，反而失败）
3. **Clash 类代理 = 独立端口代理**：需要给 git/node 显式配代理
   （node 的 MCP 场景另见 `06-MCP/Git-MCP-网络连接失败排查与修复.md`）。
4. **端口有效性三查**：查监听（`netstat`）→ 查进程身份（`tasklist`）→ 实测
   （`git push` / `curl -x`）。`CONNECT 405` = 端口在但非 HTTP 代理。
5. **失败恢复顺序**：确认 Watt Toolkit 已启动并开启网络加速 → 确认 hosts 劫持
   存在 → 确认 `Steam++.Accelerator.exe` 监听 80/443 → 直连 `git push`。

---

## 5. 相关文档

- `ai-configuration/06-MCP/Git-MCP-网络连接失败排查与修复.md` — node/MCP 场景（Clash + 证书）
- `ai-rules/GeneralRules/04_version_control.md` §8 — GitHub 网络代理排查要点（规则版）
- `ai-rules/split/File-operation-rules/09_版本控制与Git规则.md` §10.5 — 分支/推送规范（规则版）
- `DSH-Desktop/dsh-Plugin/dsh-plugin-gitops/rules/02_git_mcp_troubleshooting.md` — 插件注入的精简要点
