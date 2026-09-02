# dsh-plugin-gitops

DSH GitOps 插件：把**Git 操作规范**与 **Git-MCP 网络排查要点**同步为 DSH 全局 `AGENTS.md`，作为版本控制场景的按需基线。

## Install

```bash
dsh plugin --profile web add link:<本插件绝对路径>
```

注册后随 DSH 启动自动同步规则到 `$DSH_HOME/AGENTS.md`，无需手动操作。

### 在 DSH Desktop 中自动生效（便携插件）

把本插件目录放进 `DSH-Desktop/dsh-Plugin/` 后，DSH Desktop 点"开启服务"会自动扫描识别。规则类插件即使不弹窗注册，也会随服务自动执行规则同步（管理块标记 `dsh-plugin-gitops`），弹窗勾选仅用于显式注册。

## 内容

| 文件 | 来源 | 说明 |
|---|---|---|
| `rules/01_git_rules.md` | `ai-configuration/02-RULE/Agent-Requested/02-git-rules.mdc` | Git 分支/提交/工作流规范 + 安全红线 |
| `rules/02_git_mcp_troubleshooting.md` | `ai-configuration/06-MCP/Git-MCP-网络连接失败排查与修复.md`（精简要点） | MCP 网络失败三板斧 + 诊断命令 + 修复模板 + 踩坑清单 + Watt Toolkit 加速模式 |

> 完整版排查文档仍在 `ai-configuration/06-MCP/`，本插件注入的是精简要点（避免占用 token 预算）。

## 工作原理

与 dsh-plugin-hardbound 相同：启动时把 `rules/` 合并进 `$DSH_HOME/AGENTS.md`，管理标记 `dsh-plugin-gitops`，多插件共存、幂等同步、首次接管备份。

## 用法

### CLI（无需 DSH 即可用）

```bash
node lib/cli.js status                # 查看状态
node lib/cli.js sync --dry-run        # 预览将写入内容（不写文件）
node lib/cli.js sync                  # 同步规则到 $DSH_HOME/AGENTS.md
node lib/cli.js check                 # 完整性检查
node lib/cli.js sync --dsh-home <path>   # 指定 DSH home（测试）
```

### DSH 命令

DSH 内发送 `/gitops` 查看同步状态与规则清单。

### 更新规则

替换 `rules/` 目录下的 md 文件后执行 `node lib/cli.js sync`（或重启 DSH 服务自动同步）。

## 管理标记

生成的 `AGENTS.md` 结构：

```markdown
<用户自定义区（原样保留）>

<!-- ===== dsh-plugin-gitops MANAGED SECTION (do not edit) ===== -->
...规则区（每次同步重建）...
<!-- ===== end dsh-plugin-gitops ===== -->
```

两个标记之间的内容每次同步重建，**请勿手改**；标记之前为用户区。

## 目录结构

```
dsh-plugin-gitops/
├── package.json          # name=dsh-plugin-gitops, dsh.bundle.patch
├── cordis.patch.yml      # 挂载行 plugin-gitops
├── dsh.plugin.json       # 插件清单
├── README.md
├── rules/                # 规则源（自包含）
└── lib/
    ├── index.js          # DSH 宿主插件（启动同步 + /gitops 命令）
    ├── core.js           # 核心：合并 / 同步 / 状态（零依赖）
    └── cli.js            # 命令行入口
```

## 版本

- 1.0.1 (2026-09-01)：`rules/02_git_mcp_troubleshooting.md` 新增 §4 Watt Toolkit（Steam++）加速模式要点（git push Connection reset 场景）
- 1.0.0 (2026-09-01)：初始版本，多插件共存协议。
