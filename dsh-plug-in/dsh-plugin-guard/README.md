# dsh-plugin-guard

DSH 插件冲突监控器：检测插件间冲突与启动风险，一键启停插件。
对齐上游 [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) 的插件系统机制（bundle patch 层、双锚点 bundle 解析、`patchReload` 热重载）。

## 功能

1. **扫描** — 列出 profile 中所有已挂载插件、包来源、启用/禁用状态
2. **冲突检测** — 自动识别：
   - 重复挂载（同一插件 id 被多个 bundle 插入）
   - double-mount（同一包被多个 id 挂载，重复注册路由风险）
   - 已知风险插件（需特殊配置/外部服务，如 `ui-obsidian-memory` 缺 `vaultPath`、AWiki 依赖 IM）
   - 配置覆盖引用了未启用插件
3. **一键启停** — `disable <id>` / `enable <id>`，安全编辑 profile 的 `cordis.patch.yml`（自动备份 `.guard.bak`），依据 profile 的 `patchReload` 提示热重载或重启

## 与上游 DSH 机制对齐的更新（v1.3）

- **双锚点 bundle 解析**：`findBundleDir` 先查 profile 的 `node_modules`，再从 dsh 安装目录解析内置 bundle（`@deepseek-ai/dsh-base`、`@deepseek-ai/dsh-web-app`、`@deepseek-ai/dsh-headless`），不再跳过内置 bundle
- **patch 文件名动态化**：patch 文件路径读取 bundle manifest 的 `dsh.bundle.patch` 字段（如 `./cordis.patch.yml`），不再硬编码
- **`patchReload` 感知**：读取 profile manifest 的 `dsh.profile.patchReload`（默认 `live` 热重载），CLI 与宿主插件据此显示"即时生效"或"需重启"提示
- **home 级 patch 层**：扫描并应用 `$DSH_HOME/cordis.patch.yml`（优先级高于 profile 自身层），对齐上游 home patch 机制
- **`workspace:` 协议支持**：bundle 名支持 pnpm `workspace:` 前缀解析

## 目录结构

```
dsh-plugin-guard/
├── package.json         # npm 包描述（dsh.bundle.patch 指向 cordis.patch.yml）
├── cordis.patch.yml     # bundle 补丁层（挂载 plugin-guard 行）
├── dsh.plugin.json      # 插件清单
├── bin/guard.js         # npm bin 入口
└── lib/
    ├── core.js          # 核心：扫描 / 检测 / 启停（零依赖）
    ├── cli.js           # 命令行入口
    └── index.js         # DSH 宿主插件（启动时自动检测告警）
```

## 用法

### 方式一：命令行工具（推荐，DSH 崩溃时也能用）

直接在 `dsh-plug-in/` 下运行 `guard.bat`，或手动执行：

```bash
node dsh-plugin-guard/lib/cli.js status              # 概览状态
node dsh-plugin-guard/lib/cli.js scan                # 扫描全部插件
node dsh-plugin-guard/lib/cli.js check               # 冲突与启动风险检测
node dsh-plugin-guard/lib/cli.js list                # 仅列出插件 id
node dsh-plugin-guard/lib/cli.js disable <id>        # 一键禁用
node dsh-plugin-guard/lib/cli.js enable  <id>        # 一键启用
node dsh-plugin-guard/lib/cli.js --profile <name>    # 指定 profile（默认 web）
```

Windows 快捷方式：

```bat
guard.bat check
guard.bat disable ui-obsidian-memory
guard.bat enable  ui-obsidian-memory
```

### 方式二：作为 DSH 插件安装（启动时自动检测）

```bash
# 注意：link: 后面必须写真实绝对路径，不要保留尖括号
dsh plugin --profile web add link:d:/3.aidata/ai/dsh-plug-in/dsh-plugin-guard
```

安装后每次启动 DSH，`plugin-guard` 插件会自动扫描插件树：
- 无问题 → 输出 `[dsh-plugin-guard] 插件树检查通过`
- 有问题 → 输出 `[dsh-plugin-guard] 检测到 N 个插件冲突/风险项` 及明细

若命令系统可用，还可在聊天中发送 `/guard` 查看状态。

## 已识别的风险插件

| 插件 id | 风险 | 处理 |
| --- | --- | --- |
| `ui-obsidian-memory` | 需要 `config.vaultPath`，缺失时启动崩溃 | 未配置时建议禁用 |
| `awiki` / `awiki-provider` / `awiki-summary-provider` | 依赖 IM Core 外部服务，初始化失败会中断 webServer | 不使用 AWiki 时建议禁用 |
| `better-sidebar` / `web-ui-better-sidebar` | 与聚合包 double-mount，重复注册 `/sidebar/api` 导致整树启动失败 | 确保聚合包在前且 !!js 防护生效 |

## 一键启停原理

`disable <id>` 会在 profile 的 `cordis.patch.yml` 中追加（或更新）：

```yaml
- id: <插件id>
  disabled: true
```

`enable <id>` 会移除该条目。每次修改前自动备份到 `cordis.patch.yml.guard.bak`。
生效方式取决于 profile 的 `dsh.profile.patchReload`：

- `live`（默认）— 热重载，修改后即时生效，无需重启
- `startup` — 需重启 DSH 才生效

## 注意事项

- 修改 `cordis.patch.yml` 前自动备份，如操作失误可用备份恢复
- 内置宿主 bundle（`@deepseek-ai/dsh-base` 等）从 dsh 安装目录解析，无需也不应安装到 profile 的 node_modules
- 聚合包（如 `@linxin666/dsh-web-ui-all`）挂载多个 id 是正常设计，不视为冲突
- home 级用户 patch（`$DSH_HOME/cordis.patch.yml`）优先级高于 profile 自身层，扫描结果中带 `homePatchFile` 标记
