# dsh-plugin-guard 新环境完整搭建 SOP

> 目标：在一台**全新环境**上，从零复现「DSH 插件冲突监控 + 一键启停」工具的全部过程。
> 本文档是踩坑实录 + 操作手册，按顺序执行即可，无需重新摸索。

---

## 0. 背景（为什么要做这个工具）

DSH（DeepSeek Harness）web 启动时曾连续崩溃：

| 报错 | 根因 | 处置 |
| --- | --- | --- |
| `ui-obsidian-memory: Cannot read properties of undefined (reading 'vaultPath')` | 插件缺 `config.vaultPath` 配置 | 在 profile 的 `cordis.patch.yml` 禁用该插件 |
| `@awiki/im-core-node: IM operation failed internally` | AWiki 依赖 IM Core 外部服务，初始化失败中断 webServer | 禁用 awiki / awiki-provider / awiki-summary-provider |

由此产生需求：**做一个插件，能扫描插件树、识别冲突/启动风险，并一键启停插件**，避免每次手动改 YAML、避免盲试。

---

## 1. 前置条件（新环境检查清单）

```bash
node -v                 # 需要 Node.js >= 18
npm i -g @deepseek-ai/dsh   # 安装 DSH（如未装）
dsh --version           # 确认可用
```

- 目标 profile 目录：`~/.dsh/profiles/web`（Windows: `C:\Users\<用户名>\.dsh\profiles\web`）
- profile 结构（正常状态应有）：
  - `package.json`（含 `dsh.profile.bundles` 数组）
  - `cordis.patch.yml`（profile 自身补丁层，启停就是改这里）
  - `node_modules/`（各 bundle 包，内含各自的 `cordis.patch.yml`）
  - `pnpm-workspace.yaml` / `pnpm-lock.yaml`

---

## 2. 文件清单（复制本目录即可复用）

工具本体就是 `dsh-plug-in/dsh-plugin-guard/` 这一个目录 + 根目录的 `guard.bat`：

```text
dsh-plug-in/
├── guard.bat                      # Windows 启动器（推荐日常用）
└── dsh-plugin-guard/
    ├── package.json               # npm 包描述；dsh.bundle.patch 指向 cordis.patch.yml
    ├── cordis.patch.yml           # bundle 补丁层：挂载 plugin-guard 插件行
    ├── dsh.plugin.json            # 插件清单（entry.name 必须与 lib/index.js 导出的 name 一致）
    ├── bin/guard.js               # npm bin 入口（转发到 lib/cli.js）
    ├── lib/
    │   ├── core.js                # 核心逻辑（零外部依赖）：扫描/检测/启停/迷你 YAML 解析
    │   ├── cli.js                 # 命令行入口（status/scan/check/list/disable/enable）
    │   └── index.js               # DSH 宿主插件入口（启动自动告警 + /guard 命令）
    └── README.md                  # 使用文档
```

**零外部依赖**（只用 Node 内置 `fs/path/os`），拷贝即可运行，无需 `npm install`。

---

## 3. 核心文件要点

### 3.1 `package.json`

```json
{
  "name": "dsh-plugin-guard",
  "version": "1.0.0",
  "type": "commonjs",
  "main": "lib/index.js",
  "bin": { "dsh-plugin-guard": "bin/guard.js" },
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

`dsh.bundle.patch` 是关键：告诉 DSH 这个包作为 bundle 时，用哪个文件作为插件行补丁。

### 3.2 `cordis.patch.yml`（bundle 补丁层）

```yaml
# 挂载 plugin-guard 插件行；id 必须与 lib/index.js 导出的 name 一致
- insert:
    - id: plugin-guard
      name: 'dsh-plugin-guard'
```

### 3.3 `dsh.plugin.json`

```json
{ "name": "dsh-plugin-guard", "version": "1.0.0",
  "entry": { "name": "dsh-plugin-guard" },
  "client": { "platform": "web" } }
```

### 3.4 `lib/index.js`（宿主插件）

- 导出 `{ name: 'plugin-guard', apply(ctx), inject: [] }`
- `apply` 内 `ctx.effect` 延迟 3 秒后执行扫描：有问题输出 `[dsh-plugin-guard] 检测到 N 个插件冲突/风险项`，无问题输出检查通过
- 若命令系统存在，注册 `/guard` 命令查看状态

### 3.5 `lib/core.js`（核心，理解这 4 个函数即可）

| 函数 | 职责 |
| --- | --- |
| `scanPlugins(profile)` | 读 profile 的 `package.json` 拿 `bundles` → 逐个读 `node_modules/<包>/cordis.patch.yml` → 解析 `insert` 行汇总插件清单 → 再用 profile 自身 `cordis.patch.yml` 做禁用/配置覆盖 |
| `runChecks(scan)` | 4 类检测：duplicate-id（critical）、double-mount（warning）、known-risk（按内置规则表）、config-orphan（info） |
| `setPluginEnabled(profile, id, enabled)` | 安全编辑 profile 的 `cordis.patch.yml`：自动备份 `.guard.bak`；行级编辑保留用户注释；纯禁用条目整条删除 |
| `parseYaml(text)` | 手写迷你 YAML 解析器（递归 `parseBlock`），支持数组/对象/嵌套/注释/`!!js` 表达式原样保留 |

- `normalizeBundleName`：统一 `github:owner/repo#branch`、`git+https://...git`、`link:/abs/path`、`npm:name` 各种来源格式为包名，才能定位 `node_modules/<包名>/cordis.patch.yml`
- 内置宿主 bundle 白名单：`@deepseek-ai/dsh-base`、`@deepseek-ai/dsh-web-app` 不在 node_modules，扫描时跳过不报错

### 3.6 内置风险规则（可在 core.js 的 `RISK_RULES` 扩展）

| 插件 | 风险 | 级别 |
| --- | --- | --- |
| `ui-obsidian-memory` | 缺 `config.vaultPath` 启动崩溃 | critical |
| `awiki` 系列 | 依赖 IM 外部服务，失败中断 webServer | warning |
| `better-sidebar` | 与 `@linxin666/dsh-web-ui-all` 聚合包 double-mount | warning |

### 3.7 `guard.bat`（Windows 启动器要点）

- `chcp 65001` 切 UTF-8；**注释必须用英文**（cmd 下中文 UTF-8 注释会乱码）
- 结尾用 `if %RC% EQU 0 goto :ok` 结构处理退出码（cmd 的 if 括号块容易出错）
- 用法：`guard.bat status|scan|check|list|disable <id>|enable <id> [--profile <name>]`

---

## 4. 从零搭建步骤（新环境操作序列）

### 步骤 1：创建目录与文件

把 `dsh-plug-in/dsh-plugin-guard/` 整个目录复制到新环境（或按第 3 节逐文件创建），放在任意位置，例如：

```bash
mkdir -p ~/tools/dsh-plugin-guard && cp -r dsh-plugin-guard/* ~/tools/dsh-plugin-guard/
```

### 步骤 2：先跑 CLI 验证（不依赖 DSH，随时可用）

```bash
cd ~/tools/dsh-plugin-guard
node lib/cli.js status                 # 概览：已启用/已禁用数量 + 潜在问题
node lib/cli.js scan                   # 全部插件清单（来源、状态）
node lib/cli.js check                  # 冲突与启动风险（有 critical 退出码 2）
node lib/cli.js list                   # 仅 id（# 前缀 = 已禁用）
node lib/cli.js disable <插件id>        # 一键禁用
node lib/cli.js enable  <插件id>        # 一键启用
node lib/cli.js --profile <名字> ...    # 指定其他 profile
```

### 步骤 3：作为 DSH 插件安装（启动时自动告警，可选）

```bash
# 正确写法：link: 后跟真实绝对路径，【不要带尖括号】
dsh plugin --profile web add link:d:/3.aidata/ai/dsh-plug-in/dsh-plugin-guard
```

> ⚠️ 常见错误：把文档示例 `link:<绝对路径>` 的尖括号一起复制进命令，DSH 会直接报
> `dsh: pnpm failed in profile directory ...`，且会连带触发 profile 全量依赖解析。

### 步骤 4：启动 DSH 验证

```bash
# web 启动必须带 --patch，否则插件/技能不生效
npx @deepseek-ai/dsh web --patch
```

- 启动日志应出现 `[dsh-plugin-guard] 插件树检查通过`（无风险时）
- 验证服务：`curl -I http://127.0.0.1:3080` 应返回 `HTTP/1.1 200`
- 聊天中可发送 `/guard` 查看插件状态

### 步骤 5：一键启停往返验证

```bash
guard.bat disable ui-obsidian-memory     # 禁用 → cordis.patch.yml.guard.bak 自动备份
guard.bat status                         # 确认 DISABLED
guard.bat enable  ui-obsidian-memory     # 启用 → 条目被移除/恢复
guard.bat status                         # 确认 enabled
```

---

## 5. 新环境最容易踩的坑（务必先看）

| # | 坑 | 现象 | 解法 |
| --- | --- | --- | --- |
| 1 | **PowerShell ExecutionPolicy 拦截 npx.ps1** | 命令窗口一闪而过、服务没起来 | 用 `cmd /c "npx ..."` 子进程绕过，别直接用 PowerShell 调 npx |
| 2 | **内联命令 `$` 变量被外层 shell 吞掉** | PowerShell 里 `$` 变量展开为空 | 把复杂逻辑写成 `.ps1` 脚本再执行，别用超长内联命令 |
| 3 | **cmd 下 UTF-8 中文注释乱码** | `.bat` 里中文变成乱码 | `.bat` 注释一律用英文 |
| 4 | **cmd 的 `if ( )` 括号块语法** | bat 逻辑报错 | 用 `if %RC% EQU 0 goto :ok` 跳转结构 |
| 5 | **YAML 解析器缺陷** | 嵌套/`!!js` 解析错误 | 用递归 `parseBlock(start,end)` 按缩进切块，`!!js` 原样保留为字符串 |
| 6 | **double-mount 误报** | 聚合包挂多 id 被当成冲突 | 内置 bundle 白名单跳过；非 `insert` 顶层条目视为配置覆盖；double-mount 按**包名**聚合判断 |
| 7 | **enable 后残留空条目** | 启用后 `disabled: true` 行删了但 `- id:` 空壳还在 | 纯禁用条目（只有 id+disabled）整条删除，并清理尾随空行 |
| 8 | **并行命令竞态** | 同时跑 disable/enable 会误删别人的禁用条目 | **禁止并行**修改同一个 `cordis.patch.yml`，一次只跑一个启停命令 |
| 9 | **`link:<路径>` 尖括号占位符** | 直接复制示例报 `pnpm failed` | 去掉尖括号，写真实绝对路径：`link:d:/xxx/dsh-plugin-guard` |
| 10 | **pnpm `minimumReleaseAge` 拦截新发布包** | `ERR_PNPM_MINIMUM_RELEASE_AGE_VIOLATION`，一堆 `@linxin666/*` 被拒 | profile 目录建 `.npmrc`：`minimumReleaseAge=0`；或命令行 `pnpm --config.minimumReleaseAge=0 add ...` |
| 11 | **pnpm add link: 触发全量 registry 解析** | 网络抖动 `UND_ERR_DESTROYED`，下载 `eventsource-parser` 等失败 | 加 `--offline`；或手动在 `package.json` 写 `"dsh-plugin-guard": "link:d:/..."` 后 `pnpm install --no-frozen-lockfile` |

---

## 6. 真实环境验证结果（作为新环境的验收基准）

| 检查项 | 结果 |
| --- | --- |
| `scan` 插件条目数 | 35 个（web profile） |
| `status` 禁用状态 | 5 个（含 ui-obsidian-memory 等风险插件） |
| `check` double-mount | 检测准确（`better-sidebar` ↔ 聚合包） |
| disable → enable 往返 | 状态一致，`cordis.patch.yml` 无残留空条目 |
| 备份机制 | 每次修改前自动生成 `cordis.patch.yml.guard.bak`，曾用于恢复误删条目 |
| DSH web 启动 | 首页 `HTTP/1.1 200`，端口 3080 正常监听 |
| 代码质量 | `node --check` 通过，lint 0 问题 |

---

## 7. 日常操作速查

```bat
guard.bat status              :: 状态概览（最常用）
guard.bat check               :: 检测冲突/启动风险
guard.bat scan                :: 完整插件清单
guard.bat list                :: 仅插件 id
guard.bat disable <id>        :: 一键禁用（自动备份）
guard.bat enable  <id>        :: 一键启用
guard.bat --profile dev ...   :: 指定其他 profile
```

修改后需**重启 DSH**（`npx @deepseek-ai/dsh web --patch`）才生效。

---

## 8. 排障指引

1. **启动即崩溃** → `guard.bat check` 看 critical 项，逐个 `guard.bat disable <id>` 后重启
2. **网页打不开** → 看是否有 awiki 相关 IM 报错；禁用 awiki 系列再重启
3. **启停不生效** → 确认改的是 `~/.dsh/profiles/<profile>/cordis.patch.yml`；确认重启带 `--patch`
4. **误操作想恢复** → 把 `cordis.patch.yml.guard.bak` 复制回 `cordis.patch.yml`
5. **新插件想加进风险规则** → 编辑 `lib/core.js` 的 `RISK_RULES` 数组，加 `{ ids, pkg, reason, check }` 一条即可
