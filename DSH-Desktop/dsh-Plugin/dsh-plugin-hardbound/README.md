# dsh-plugin-hardbound

DSH 硬边界插件：把**全局硬边界**与**核心行为原则**同步为 DSH 全局 `AGENTS.md`，作为每个会话的必读基线。

## Install

```bash
dsh plugin --profile web add link:<本插件绝对路径>
```

注册后随 DSH 启动自动同步规则到 `$DSH_HOME/AGENTS.md`，无需手动操作。

### 在 DSH Desktop 中自动生效（便携插件）

把本插件目录放进 `DSH-Desktop/dsh-Plugin/` 后，DSH Desktop 点"开启服务"会自动扫描识别。规则类插件即使不弹窗注册，也会随服务自动执行规则同步（管理块标记 `dsh-plugin-hardbound`），弹窗勾选仅用于显式注册。

## 内容

| 文件 | 来源 | 说明 |
|---|---|---|
| `rules/00_hard_boundaries.md` | `ai-configuration/02-RULE/Always/00-hard-boundaries.mdc` | 硬边界：[BLOCK]/[ASK]/[DO] 三级 + 验证命令 |
| `rules/01_core_behavior.md` | `ai-rules/GeneralRules/01_core_behavior.md` | 边界优先、三级权限、行为五原则、验证闭环、合规清单 |

## 工作原理

DSH 内置 `@deepseek-ai/dsh-agent-instructions` 会自动加载 `$DSH_HOME/AGENTS.md`（默认 `~/.dsh/AGENTS.md`）。
插件启动时（延迟 3 秒）把 `rules/` 合并进该文件，用管理标记夹住规则区：

```
<!-- ===== dsh-plugin-hardbound MANAGED SECTION (do not edit) ===== -->
...规则区（每次同步重建）...
<!-- ===== end dsh-plugin-hardbound ===== -->
```

特性：
- **多插件共存**：识别任意 `dsh-plugin-*` 管理块，只重建自己的块，其他插件块与用户区原样保留，多个规则插件可同时挂载互不覆盖
- **首次接管备份**：`AGENTS.md.pre-plugin-hardbound.bak`（幂等，仅一次）
- **幂等同步**：内容哈希无变化不写文件
- **安全**：同步失败仅告警，不阻塞 DSH 启动

## 用法

### CLI（无需 DSH 即可用）

```bash
node lib/cli.js status                # 查看规则与 AGENTS.md 状态
node lib/cli.js sync --dry-run        # 预览将写入内容（不写文件）
node lib/cli.js sync                  # 同步规则到 $DSH_HOME/AGENTS.md
node lib/cli.js check                 # 完整性检查
node lib/cli.js sync --dsh-home <path>   # 指定 DSH home（测试）
```

### DSH 命令

DSH 内发送 `/hardbound` 查看同步状态与规则清单。

### 更新规则

替换 `rules/` 目录下的 md 文件后执行 `node lib/cli.js sync`（或重启 DSH 服务自动同步）。

## 管理标记

生成的 `AGENTS.md` 结构：

```markdown
<用户自定义区（原样保留）>

<!-- ===== dsh-plugin-hardbound MANAGED SECTION (do not edit) ===== -->
...规则区（每次同步重建）...
<!-- ===== end dsh-plugin-hardbound ===== -->
```

两个标记之间的内容每次同步重建，**请勿手改**；标记之前为用户区。

## 目录结构

```
dsh-plugin-hardbound/
├── package.json          # name=dsh-plugin-hardbound, dsh.bundle.patch
├── cordis.patch.yml      # 挂载行 plugin-hardbound
├── dsh.plugin.json       # 插件清单
├── README.md
├── rules/                # 规则源（自包含）
└── lib/
    ├── index.js          # DSH 宿主插件（启动同步 + /hardbound 命令）
    ├── core.js           # 核心：合并 / 同步 / 状态（零依赖）
    └── cli.js            # 命令行入口
```

## 版本

- 1.0.0 (2026-09-01)：初始版本，多插件共存协议。
