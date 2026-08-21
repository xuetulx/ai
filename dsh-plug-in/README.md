# DSH Plugin Batch Installer

> DeepSeek Harness (DSH) 插件一键批量安装脚本，基于社区推荐清单整理。

## 简介

DeepSeek Harness 开源后采用「一切皆插件」设计哲学，官方本体只提供骨架，真正的战斗力全在插件里。本仓库提供一键批量安装脚本，帮你快速把社区推荐的高质量插件装齐。

- **核心档 9 个**：基础能力补齐 + 发现入口 + 用量监控
- **进阶档 15 个**：体验增强 + 进阶玩法
- 共 **24 个**推荐插件，按优先级排序安装

## 文件说明

| 文件 | 说明 |
|------|------|
| `install-dsh-plugins.sh` | 主脚本（Bash，适用于 Git Bash / WSL / Linux / macOS） |
| `install-dsh-plugins.bat` | Windows 双击启动器（自动查找 Git Bash 并调用主脚本） |
| `guard.bat` | 插件监控工具启动器（扫描 / 冲突检测 / 一键启停） |
| `dsh-plugin-guard/` | DSH 插件冲突监控器（详见其 README） |

## 前置要求

1. **Node.js**（用于运行 DSH）
2. **DeepSeek Harness** 已安装：
   ```bash
   npm install -g @deepseek-ai/dsh
   ```
3. **Git Bash**（Windows 用户需要，用于运行 `.sh` 脚本）
4. 启动 Web UI 时务必加 `--patch` 参数，否则部分插件和技能不生效：
   ```bash
   npx @deepseek-ai/dsh web --patch
   ```

## 快速开始

### 方式一：Bash 脚本（推荐）

```bash
# 安装核心推荐插件（9 个）
./install-dsh-plugins.sh

# 全量安装（核心 + 进阶，共 24 个）
./install-dsh-plugins.sh --full

# 指定 profile + 免确认
./install-dsh-plugins.sh --full --profile dev --yes

# 仅预览清单，不安装
./install-dsh-plugins.sh --list
```

### 方式二：Windows 双击运行

直接双击 `install-dsh-plugins.bat`，或在命令行带参数运行：

```
install-dsh-plugins.bat --full --yes
```

`.bat` 启动器会自动通过以下方式查找 Git Bash：
1. PATH 环境变量中的 `bash.exe`
2. 从 `git.exe` 安装路径推导（`Git\cmd\git.exe` -> `Git\bin\bash.exe`）
3. 遍历常见安装目录（Program Files、Scoop、LocalAppData 等）

## 命令参数

| 参数 | 说明 |
|------|------|
| `--full` | 安装全部 24 个推荐插件（核心 + 进阶） |
| `--profile <name>` | 指定 DSH profile（默认 `web`） |
| `--list` | 仅打印插件清单，不执行安装 |
| `--yes` | 跳过确认提示，直接安装 |
| `--skip-check` | 跳过 `dsh` 命令环境检查 |
| `--help` | 查看帮助 |

## 插件清单

### 核心档（第一梯队）

| # | 插件 | 作用 |
|---|------|------|
| 1 | dshmarket | 可视化插件市场（设置页搜索 / 一键安装） |
| 2 | dsh-find-plugin | 会话内搜索插件（对话里让 Agent 找插件） |
| 3 | dsh-web-ui | 界面全家桶（任务看板 / Git 图谱 / Token 统计 / 皮肤中心） |
| 4 | modlens | 视觉插件，给纯文本模型装眼睛（OCR / 版面 / 语义 JSON） |
| 5 | dsh-at-file | 输入框 `@` 引用工作区文件 |
| 6 | dsh-paste-input | 支持 Ctrl+V 粘贴 / 拖拽文件 |
| 7 | dsh-office | 读写 docx / pdf / pptx / xlsx 文档 |
| 8 | dsh-browser-panel | 内嵌浏览器，Agent 可操作网页 |
| 9 | dsh-usage | Token 用量 / 缓存命中率 / 余额查询 |

### 进阶档（体验增强 + 进阶玩法）

| # | 插件 | 作用 |
|---|------|------|
| 10 | DSH-better-sidebar | 侧边栏工作台（文件树 / 终端 / Git / 子代理） |
| 11 | dsh-TUI | Claude Code 风格全屏终端 |
| 12 | dsh-vision-toolkit | 视觉进阶（图片问答 / 长截图 OCR / UI 还原） |
| 13 | dsh-genui | 回复里直接渲染图表 / 表格 / 组件 |
| 14 | dsh-turn-rewind | 一键回退到上一步 |
| 15 | dsh-message-edit | 编辑已发消息 / 重新生成 |
| 16 | dsh-chat-import | 聊天记录无损导入（Cursor / ChatGPT / Gemini 等） |
| 17 | dsh_workflow | 多 Agent 工作流（成本追踪 / 中断恢复 / 权限） |
| 18 | dsh-memory-evolve | 跨会话长期记忆 |
| 19 | dsh-llm-fallbacks | 模型故障自动切换备用模型 |
| 20 | dsh-deep-whale | 鲸鱼娘皮肤系列 |
| 21 | dsh-agent-teams | 多 Agent 团队协作（需本机 git 读权限） |
| 22 | dsh-plan-execute | 双模型路由（规划用推理 / 执行用经济模型） |
| 23 | dsh-context-doctor | 上下文 Token 账单分析 / 裁剪建议 |
| 24 | dsh-browser | 操控真实 Chrome（保留登录态和 Cookie） |

### 未自动安装（需手动处理）

| 插件 | 原因 | 手动方式 |
|------|------|----------|
| dsh-anchored-standard | 属于 preset，非标准插件 | 参考仓库说明手动复制 preset 文件 |
| deepseek-harness-desktop | 桌面版安装包 | 去 [Releases](https://github.com/anywhere-labs/deepseek-harness-desktop/releases) 下载 |
| dsh-poison-guard | 供应链安全扫描工具 | `npm install -g dsh-poison-guard` |

## 插件监控工具（dsh-plugin-guard）

本目录附带 **DSH 插件冲突监控器**，用于排查插件间冲突与启动失败问题：

```bat
guard.bat status              :: 查看插件状态概览
guard.bat scan                :: 扫描所有插件
guard.bat check               :: 检测冲突与启动风险
guard.bat disable <id>        :: 一键禁用插件
guard.bat enable  <id>        :: 一键启用插件
```

- 可识别重复挂载、double-mount、已知风险插件（如缺 `vaultPath` 的 Obsidian Memory、依赖外部 IM 的 AWiki）
- 启停操作自动备份 `cordis.patch.yml`，重启 DSH 后生效
- 详见 `dsh-plugin-guard/README.md`

## 安装顺序建议

```
第 1 步：dshmarket + dsh-find-plugin（发现入口）
第 2 步：dsh-web-ui + dsh-anchored-standard（界面 + 性能，最立竿见影）
第 3 步：ModLens + dsh-at-file + dsh-paste-input（基础能力）
第 4 步：按需加装：better-sidebar / TUI / 桌面版 / 工作流 / 迁移类
```

## 注意事项

1. **ModLens 必须锁版本号**：脚本中已锁定 `@3.17.2`，DSH 更新频繁，不锁版本容易遇到 breaking change
2. **`--patch` 参数**：启动 Web UI 时必须加此参数，否则很多插件和技能不生效
3. **别贪多**：一次装 3~5 个够用，装多了模型会「变笨」（所有 Agent 工具的共识）
4. **安全第一**：插件能力 = 电脑权限，装前看 Star、更新时间、Issues，官方组织优先
5. **GitHub 仓库类插件**：部分插件为 GitHub 仓库形式，需要本机可访问 GitHub

## 安装后

- 若 `dsh web` 正在运行，请重启并带上 `--patch` 参数
- 浏览器硬刷新（`Ctrl+Shift+R`）让插件 UI 生效
- 部分插件热插拔即时生效，个别需要重启服务

## 相关链接

- [DeepSeek Harness 官方仓库](https://github.com/deepseek-ai/deepseek-harness)
- [DSH 插件 GitHub Topic](https://github.com/topics/dsh-plugin)
- [Oh-My-DSH 插件聚合目录](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin)

## License

MIT
