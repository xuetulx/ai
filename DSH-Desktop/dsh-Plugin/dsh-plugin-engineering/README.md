# dsh-plugin-engineering

DSH 工程质量插件：把**工程质量规范**、**Python 编码规范**与 **HOOK 机制文字化**同步为 DSH 全局 `AGENTS.md`，作为工程级开发场景的按需基线。

## Install

```bash
dsh plugin --profile web add link:<本插件绝对路径>
```

注册后随 DSH 启动自动同步规则到 `$DSH_HOME/AGENTS.md`，无需手动操作。

### 在 DSH Desktop 中自动生效（便携插件）

把本插件目录放进 `DSH-Desktop/dsh-Plugin/` 后，DSH Desktop 点"开启服务"会自动扫描识别。规则类插件即使不弹窗注册，也会随服务自动执行规则同步（管理块标记 `dsh-plugin-engineering`），弹窗勾选仅用于显式注册。

## 内容

| 文件 | 来源 | 说明 |
|---|---|---|
| `rules/01_engineering.md` | `ai-configuration/02-RULE/Agent-Requested/03-engineering.mdc` | 模块化/输出结构/测试配套/资源限制/依赖安全 |
| `rules/02_py_coding.md` | `ai-configuration/02-RULE/Agent-Requested/01-py-coding.mdc` | Python 行为原则/文件头/排版/命名/注释 |
| `rules/03_hooks_textual.md` | `ai-configuration/01-HOOK/`（5 个 Hook 文字化） | 备份/敏感文件/.git 拦截/硬编码/审计日志的等效 Rule 表达 |

> DSH 无 Hook 机制，`03_hooks_textual.md` 把程序级 Hook 转成 `[BLOCK]`/`[DO]` 规则，由 AI 自觉执行。

## 工作原理

与 dsh-plugin-hardbound 相同：启动时把 `rules/` 合并进 `$DSH_HOME/AGENTS.md`，管理标记 `dsh-plugin-engineering`，多插件共存、幂等同步、首次接管备份。

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

DSH 内发送 `/engineering` 查看同步状态与规则清单。

### 更新规则

替换 `rules/` 目录下的 md 文件后执行 `node lib/cli.js sync`（或重启 DSH 服务自动同步）。

## 管理标记

生成的 `AGENTS.md` 结构：

```markdown
<用户自定义区（原样保留）>

<!-- ===== dsh-plugin-engineering MANAGED SECTION (do not edit) ===== -->
...规则区（每次同步重建）...
<!-- ===== end dsh-plugin-engineering ===== -->
```

两个标记之间的内容每次同步重建，**请勿手改**；标记之前为用户区。

## 目录结构

```
dsh-plugin-engineering/
├── package.json          # name=dsh-plugin-engineering, dsh.bundle.patch
├── cordis.patch.yml      # 挂载行 plugin-engineering
├── dsh.plugin.json       # 插件清单
├── README.md
├── rules/                # 规则源（自包含）
└── lib/
    ├── index.js          # DSH 宿主插件（启动同步 + /engineering 命令）
    ├── core.js           # 核心：合并 / 同步 / 状态（零依赖）
    └── cli.js            # 命令行入口
```

## 版本

- 1.0.0 (2026-09-01)：初始版本，多插件共存协议。
