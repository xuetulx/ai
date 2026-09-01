# dsh-plugin-rules

DSH 规则注入插件：将 `ai-rules/split` 规则集（文件操作 18 条 + 编程规范 11 条）同步为 DSH 全局 `AGENTS.md`，使所有会话自动加载规则。零外部依赖，自包含便携。

## Install

```bash
dsh plugin --profile web add link:<本插件绝对路径>
```

注册后随 DSH 启动自动同步规则到 `$DSH_HOME/AGENTS.md`，无需手动操作。

### 在 DSH Desktop 中自动生效（便携插件）

把本插件目录放进 `DSH-Desktop/dsh-Plugin/` 后，DSH Desktop 点"开启服务"会自动扫描识别。规则类插件即使不弹窗注册，也会随服务自动执行规则同步（管理块标记 `dsh-plugin-rules`），弹窗勾选仅用于显式注册。

## 原理

DSH 内置 `@deepseek-ai/dsh-agent-instructions` 会自动发现并加载：
- **用户全局**：`$DSH_HOME/AGENTS.md`（即 `~/.dsh/AGENTS.md`）
- **项目级**：从项目根到 cwd 逐级的 `AGENTS.md` / `CLAUDE.md` / `*.local.md`

本插件启动时（延迟 3s，后台线程）把 `rules/` 目录的规则合并写入 `$DSH_HOME/AGENTS.md`，DSH 加载后即对所有会话生效。

## 特性

- **保留用户区**：`AGENTS.md` 中"管理标记之前"的内容原样保留，不覆盖用户自定义
- **首次接管自动备份**：`~/.dsh/AGENTS.md.pre-plugin-rules.bak`（幂等，仅一次）
- **幂等同步**：内容哈希无变化不写文件
- **安全**：同步失败仅告警，不阻塞 DSH 启动；扫描容错（单坏文件不影响整体）
- **`/rules` 命令**：DSH 内查看同步状态与规则清单

## 结构

```
dsh-plugin-rules/
├── package.json          # name=dsh-plugin-rules, dsh.bundle.patch
├── cordis.patch.yml      # 挂载行 plugin-rules
├── dsh.plugin.json       # 插件清单
├── README.md
├── rules/                # 规则源（自包含，从 ai-rules/split 拷贝）
│   ├── File-operation-rules/      (18 条)
│   └── Programming-specifications/ (11 条)
└── lib/
    ├── index.js          # DSH 宿主插件（启动同步 + /rules 命令）
    ├── core.js           # 核心：扫描/合并/同步/状态（零依赖）
    └── cli.js            # 命令行入口
```

## 用法

### CLI（无需 DSH 即可用）

```bash
node lib/cli.js status                # 查看状态
node lib/cli.js sync --dry-run        # 预览将写入内容（不写文件）
node lib/cli.js sync                  # 执行同步（写 ~/.dsh/AGENTS.md）
node lib/cli.js list                  # 列出规则
node lib/cli.js check                 # 完整性检查
node lib/cli.js sync --dsh-home <path>   # 指定 DSH home（测试）
```

### 作为 DSH 插件（随服务自动执行）

见上文 Install。注册后 DSH 启动即自动同步规则，无需手动操作。

### 更新规则

替换 `rules/` 目录下的 md 文件后执行 `node lib/cli.js sync`（或重启 DSH 服务自动同步）。

## 管理标记

生成的 `AGENTS.md` 结构：

```markdown
<用户自定义区（原样保留）>

<!-- ===== dsh-plugin-rules MANAGED SECTION (do not edit) ===== -->
# DSH 规则集（自动生成，来源: ai-rules/split）
## rules/File-operation-rules/00_术语定义与核心原则.md
...
<!-- ===== end dsh-plugin-rules ===== -->
```

两个标记之间的内容每次同步重建，**请勿手改**；标记之前为用户区。

## 版本

- 1.0.0 (2026-09-01)：初始版本，多插件共存协议。
