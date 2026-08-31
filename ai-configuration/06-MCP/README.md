---
description: "MCP 服务器配置层 - 文件操作类 MCP 服务器说明与配置片段"
version: 1.0
last_updated: 2026-08-25
---

# 06-MCP：文件操作 MCP 服务器

> **定位**：存放与「AI 文件操作」相关的 MCP 服务器配置说明与可复制片段。
> 适用于 Claude Code / CodeBuddy（`.mcp.json`）与 DSH（`dsh-mcp-client` 插件实例）。

## 已配置 MCP 服务器（项目级 .mcp.json）

| 服务器 | 包 | 用途 | 依赖 |
|---|---|---|---|
| CNB MCP Server | `@cnbcool/mcp-server` | CNB 云服务 | — |
| GitHub | `@modelcontextprotocol/server-github` | GitHub API | `GITHUB_PERSONAL_ACCESS_TOKEN` |

## 推荐：文件操作 MCP（Filesystem Server）

官方文件系统 MCP，提供 20+ 文件操作工具（read_file / write_file / edit_file / move_file / delete_file / search_files / directory_tree 等），支持目录白名单隔离。

### Claude Code / CodeBuddy 格式（追加到 .mcp.json）

```json
{
  "mcpServers": {
    "filesystem": {
      "autoApprove": [],
      "timeout": 60000,
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "D:/3.aidata"
      ],
      "type": "stdio",
      "disabled": false
    }
  }
}
```

> `args` 中每个路径 = 一个授权目录（白名单）。**安全建议**：只授权需要 AI 操作的项目目录，
> 不要授权 `C:\` / `D:\` 根目录、`~/.ssh`、`.aws` 等敏感区域。

### DSH 格式（写入 `~/.dsh/profiles/<profile>/cordis.patch.yml`）

```yaml
- id: mcp-filesystem
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: fs
    transport: stdio
    command: npx
    args: ['-y', '@modelcontextprotocol/server-filesystem', 'D:/3.aidata']
    toolCallTimeoutMs: 60000
```

工具名形如 `mcp__fs__read_file`、`mcp__fs__edit_file`；修改配置触发 HMR 热重连，无需重启。

## 参考

- 官方仓库: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- npm: https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem
