# VERSION LOG

> DSH Desktop 版本变更日志
> 格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.4.1 - 日志/缓存目录收口（log/ 与 cache/）] - 2026-09-01

### Added

* **运行时目录统一收口**：`app_config` 新增 `LOG_DIR_NAME`/`CACHE_DIR_NAME` 常量与 `app_base_dir()`/`app_log_dir()`/`app_cache_dir()`；`dsh_core` 移除本地 `_app_base_dir`，改引用 `app_config.app_base_dir`
* **运行日志自动落盘**：每次启动自动写入 `log/dsh-run-YYYYmmdd-HHMMSS.log`（GUI 日志区与 DSH 子进程输出同步落盘），关闭窗口时正常关闭文件句柄
* **导出默认路径绑定**：日志导出默认保存到应用日志文件夹 `log/`（仍可在弹窗中改选其他位置）

### Changed

* `main_window._export_log` 默认目录：用户桌面 → 应用日志文件夹 `log/`
* 散落根目录的 `dsh-usage-boot.log` 归入 `log/`；新增 `cache/` 缓存文件夹
* `app_config.APP_VERSION` → 1.4.1

### Technical

* 备份：`app_config.py`/`dsh_core.py`/`main_window.py` → `.bak`
* `.gitignore` 追加 `log/`、`cache/`
* 验证：`py_compile` 通过

## [1.4.0 - 插件指纹感知弹窗（有改动才弹，无改动直接启动）] - 2026-09-01

### Added

* **插件指纹机制**：每次启动（点"开启服务"）扫描 `dsh-Plugin/` 下所有含 `package.json` 的插件，并对其目录名 + 递归文件树内容计算 sha256 指纹（跳过 `node_modules`/`.git`/`dist` 等生成目录），与上次保存的指纹比对：
  * **无改动** → 不弹窗，直接启动，日志提示"N 个插件无改动，直接启动"（含未安装数）
  * **有改动**（新增/移除插件、改 `package.json`、改插件内规则/代码文件）→ 弹出 `PluginScanDialog` 让用户勾选注册，确认或跳过都记录新指纹，下次无新改动不再弹
* 新增 `dsh_core` 函数：`compute_plugin_fingerprint` / `plugins_changed` / `save_plugin_fingerprint` / `_read_plugin_fingerprint` / `_plugin_state_file`
* 指纹状态文件：`$DSH_HOME/dsh-desktop/plugin-state.json`（跟随 DSH_HOME，不污染便携应用目录；删除该文件可强制下次启动重新弹窗）

### Changed

* `main.py`/`main_window.py` 的 `_on_start()`：由"只要有插件就每次弹窗"改为"指纹有改动才弹窗"
* `app_config.APP_VERSION` → 1.4.0

### Technical

* 验证：`py_compile` 通过；指纹幂等性验证（同目录两次计算一致）；改动规则文件后指纹变化可触发弹窗；EXE 冒烟测试（启动 6s 无崩溃）
* 备份：`dsh_core.py`/`main_window.py`/`app_config.py`/`README.md` 及全部模块头部改动 → 各自 `.bak`
* **打包**：2026-09-01 17:22 用 `DSH-Desktop.spec` 打包 v1.4.0 并归位到 `DSH-Desktop/` 根目录（与 `dsh-Plugin/` 同级，保证便携插件扫描路径正确）；旧 EXE 备份为 `DSH-Desktop.exe.bak`
* 文档同步：README.md / main.py / 各模块头部 / VERSION_LOG 全部更新至 v1.4.0
* 插件文档：参考 dsh-market 结构为其余 5 个插件（guard/hardbound/gitops/engineering/rules）统一 README——补齐 Install 命令、DSH Desktop 便携生效说明、CLI/DSH 命令/更新规则/管理标记/目录结构，修正 guard 过时安装路径（`dsh-plug-in/` → `dsh-Plugin/`）；各 README 原稿备份为 `README.md.bak`

## [1.3.11 - 新增 3 个规则插件（hardbound/gitops/engineering，多插件共存协议）] - 2026-09-01

### Added

* **`dsh-Plugin/dsh-plugin-hardbound/`（v1.0.0，零依赖）**：全局硬边界 + 核心行为原则 → `$DSH_HOME/AGENTS.md`：
  * `rules/00_hard_boundaries.md`（源自 `ai-configuration/02-RULE/Always/00-hard-boundaries.mdc`）：[BLOCK]/[ASK]/[DO] 三级 + 验证命令
  * `rules/01_core_behavior.md`（源自 `ai-rules/GeneralRules/01_core_behavior.md`）：边界优先、三级权限、行为五原则、验证闭环、合规清单
* **`dsh-Plugin/dsh-plugin-gitops/`（v1.0.0，零依赖）**：Git 操作规范 + Git-MCP 网络排查要点：
  * `rules/01_git_rules.md`（源自 `02-git-rules.mdc`）：分支/提交/工作流规范 + 安全红线
  * `rules/02_git_mcp_troubleshooting.md`（源自 `06-MCP/`，精简要点版）：三板斧 + 诊断命令 + 修复模板 + 踩坑清单
* **`dsh-Plugin/dsh-plugin-engineering/`（v1.0.0，零依赖）**：工程质量 + Python 编码 + HOOK 机制文字化：
  * `rules/01_engineering.md`（源自 `03-engineering.mdc`）
  * `rules/02_py_coding.md`（源自 `01-py-coding.mdc`）
  * `rules/03_hooks_textual.md`（源自 `01-HOOK/` 5 个 Hook 的文字化表达）

### Changed

* **多插件共存协议（核心升级）**：3 个新插件 + 既有 `dsh-plugin-rules` 可同时挂载写同一个 `AGENTS.md` 互不覆盖：
  * 管理块按插件 id 稳定排序（`dsh-plugin-engineering` < `dsh-plugin-gitops` < `dsh-plugin-hardbound` < `dsh-plugin-rules`），任意插件先 sync 结果一致 → 幂等成立
  * 用户区保留：仅剥离 `dsh-plugin-*` 管理块，其余内容原样保留
  * 各自独立备份名（`AGENTS.md.pre-plugin-<id>.bak`），首次接管各备份一次
* `dsh-plugin-rules` 的 `lib/core.js` 同步升级为多插件共存版（此前单插件逻辑无法与多插件共存）

### Technical

* 验证：`node --check` 12 个 JS 文件全部通过；lint 0 错误（仅 markdownlint 样式警告）；临时 DSH_HOME 全场景测试通过（三插件共存、用户区保留、幂等 noop、块排序稳定）
* 规则为自包含拷贝，换新环境随插件目录直接可用；`main.py` 未改动（1.3.10），无需重新打包 EXE

## [1.3.10 - 新增 dsh-plugin-rules 规则插件] - 2026-09-01

### Added

* **`dsh-Plugin/dsh-plugin-rules/`（v1.0.0，零依赖）**：将 `ai-rules/split/` 规则集（文件操作 18 条 + 编程规范 11 条，29 md）生成为 DSH 插件：
  * 原理：DSH 内置 `dsh-agent-instructions` 自动加载 `$DSH_HOME/AGENTS.md`，插件启动时（延迟 3s 后台）将 `rules/` 目录规则合并写入该文件，全部会话生效
  * 特性：保留用户区（管理标记之前内容原样保留）、首次接管自动备份 `AGENTS.md.pre-plugin-rules.bak`（幂等）、内容哈希无变化不写文件、扫描容错、失败不阻塞启动
  * CLI：`node lib/cli.js status|sync|list|check`（支持 `--dry-run`/`--dsh-home`/`--rules-dir`）
  * DSH 内 `/rules` 命令查看同步状态
* 验证：`node --check` 3 文件通过；临时 DSH_HOME 全场景测试通过（首次写入 77.5KB/29 规则、幂等 noop、用户区保留、备份触发、check 完整性）；真实 `~/.dsh` dry-run 确认 79.0KB 且未写文件
* `main.py` 未改动（1.3.9），无需重新打包 EXE

### Technical

* 插件 id `plugin-rules`，与 guard 同构（package.json `dsh.bundle.patch` + cordis.patch.yml + dsh.plugin.json）
* 规则为自包含拷贝（源 `ai-rules/split/`），换新环境随插件目录直接可用

## \[1.3.9 - 模块化重构：单文件 main.py 拆分为功能模块] - 2026-09-01

### Changed

* **将 1968 行单文件 `main.py` 拆分为 7 个模块，按职责解耦、便于维护**：

  | 文件 | 职责 |
  |---|---|
  | `main.py` | 入口：创建 Tk + 主窗口 + Splash（仅 ~30 行） |
  | `app_config.py` | 全局常量：标题/版本/端口/插件目录/版本检查消息前缀 |
  | `win_sweeper.py` | `WindowSweeper` 窗口清道夫（stdlib ctypes，独立可测） |
  | `dsh_core.py` | DSH 服务核心：node/dsh 定位、插件扫描注册、启动命令、端口/PID 管理、`DSHController` |
  | `ui_widgets.py` | UI 通用组件：颜色/渐变/圆角绘制、`build_rounded_card`、`RoundButton`、`SplashScreen` |
  | `dialogs.py` | `PluginScanDialog` 便携插件管理弹窗 |
  | `main_window.py` | `DSHDesktopApp` 主窗口（GUI 布局、事件、消息队列、版本感知） |

* 依赖单向、无循环：`app_config` ← `ui_widgets` ← `dialogs` ← `main_window`；`app_config` ← `win_sweeper` ← `dsh_core` ← `main_window`
* 行为零变更：所有函数/类原样搬运，仅调整 import；`APP_VERSION` 1.3.8 → 1.3.9
* `DSH-Desktop.spec` 无需改动：PyInstaller 自动分析 import 收集同级模块

### Technical

* 备份 `main.py` → `main.py.bak.v1.3.8`（重写前 v1.3.8 状态；`main.py.bak.v1.3.7` 为更早回滚点）
* 全模块 `py_compile` 通过；lint 0 诊断；import 冒烟 + GUI 构建/销毁测试通过
* 重新打包：PyInstaller `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`

## \[1.3.8 - 终端区移到按钮下方 + 压缩顶部空白] - 2026-09-01

### Changed

* **嵌入式终端区移到"打开DSH"按钮下方**（布局顺序 v1.3.5 的 `banner → status_card → log(fixed 320px) → actions` 改回 `banner → status_card → actions → log`），更符合"按钮 → 输出"的操作直觉：

  * 去掉 `terminal_frame` 的固定 `height=320` 与 `pack_propagate(False)`，改 `pack(fill="both", expand=True)`——终端区自动填充窗口剩余空间，窗口缩放时随动伸缩
  * `inner` 同步去掉 `pack_propagate(False)`，保证随外层展开
  * `log_box`（ScrolledText `height=14`）保留作为最小高度下限，expand 填充

* **去掉标题下边的空白部分**：

  * 顶部品牌横幅 `banner` 高度 96 → 64，`_draw_banner` 各元素坐标上移（竖条 30-66 → 14-50、标题 y34 → 14、副标题 y62 → 44、版本号 y30 → 14、端口 y66 → 44），标题下方不再留约 34px 空白
  * 状态卡片高度 116 → 96，`pady=(14,4) → (6,2)`，row2 `pady=(12,0) → (6,0)`
  * 按钮区 `pady=(10,4) → (2,6)`
  * `minsize(520, 760) → (520, 680)`（终端区自适应后不再需要大最小高度）

* `APP_VERSION` 1.3.7 → 1.3.8

### Fixed（说明性，非本版代码变更）

* **"截图不好用"根因解释**：v1.3.6 的窗口清道夫按"新出现即隐藏"一刀切，截图工具（Win+Shift+S / 微信 / QQ 等）按快捷键时创建的无标题取景遮罩窗口会被当成新窗口隐藏，导致截图取景框一闪即没。v1.3.7 已加 `GetClassNameW == "ConsoleWindowClass"` 类名过滤修复——截图遮罩类名非 Console，机制上不可能被隐藏。本版沿用该逻辑，重新打包后验证即可。

### Technical

* 备份 `main.py` → `main.py.bak.v1.3.7`（修改前 v1.3.7 状态）

* Python `py_compile` 语法检查通过；lint 0 诊断

* 重新打包：PyInstaller `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`

## \[1.3.7 - 窗口清道夫误隐藏浏览器修复（类名过滤 + 时间窗）] - 2026-09-01

### Fixed

* **修复 v1.3.6 窗口清道夫误隐藏 Edge 浏览器窗口（导致"网页打不开"）**：

  * 根因：v1.3.6 按"DSH 启动后是否新出现的窗口"一刀切。用户点"打开DSH"
    → `os.startfile` 新开 Edge 浏览器窗口（HWND 不在基线里）→ 被 sweeper 当成
    "新出现的窗口"隐藏。日志实锤：`已隐藏 HWND=18059A 标题='无标题 - 用户配置 1 - Microsoft Edge'`

  * 修复1（**类名过滤**）：`_run` 中新增 `GetClassNameW` 检查，**只有窗口类名
    恰好为 `ConsoleWindowClass`（Windows 控制台黑窗）才会被隐藏**。浏览器
    （Chrome_WidgetWin_1）、IDE、资源管理器等非控制台窗口从机制上不可能被隐藏。

  * 修复2（**时间窗**）：扫描只在 DSH 启动后 **30 秒** 内有效（`MAX_ACTIVE_SECONDS`），
    超时自动退出。DSH 运行期间用户手动打开的 cmd / powershell 控制台窗口不会被误隐藏，
    也避免后台线程长期空转。

  * 双重保险：`ConsoleWindowClass` 类名 && HWND 不在基线 && PID 非自己 &&
    IsWindowVisible && 顶层窗口，五个条件全部满足才会隐藏。

### Changed

* `APP_VERSION` 1.3.6 → 1.3.7

### Technical

* Python `py_compile` 语法检查通过；lint 0 诊断

* 重新打包：PyInstaller `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`

## \[1.3.6 - 嵌入式终端 + 窗口清道夫] - 2026-09-01

### Added

* **WindowSweeper 窗口清道夫（stdlib ctypes + user32.dll，零三方依赖）**：

  * 根因：v1.3.4 / v1.3.5 都只能管"直接子进程"。DSH node.exe 内部 `child_process.spawn('cmd.exe', ...)` 用于打印 banner / Doctor 报告，会在桌面弹出独立的控制台窗口。CREATE_NO_WINDOW / DETACHED_PROCESS 都管不到孙进程。

  * 原理：DSH Popen **之前** 用 `EnumWindows + IsWindowVisible + GetAncestor(GA_ROOT) + GetWindowThreadProcessId` 枚举所有当前可见顶层窗口 HWND，作为基线。启动后台线程每 250ms 扫描一次，凡 DSH 启动后**新出现**的可见顶层窗口（PID 非 DSH Desktop 自己）一律 `ShowWindow(SW_HIDE)` 自动隐藏。

  * 安全边界：
     - 只隐藏 DSH 启动后**新出现**的窗口，不动用户在 DSH 启动前已开的 cmd / powershell / 浏览器 / IDE 等
     - DSH Desktop 自己的 GUI 窗口通过 PID 排除，绝不会被隐藏
     - 只对**当前可见**窗口操作（IsWindowVisible=True），已隐藏的窗口不动
     - 仅作用于**顶层**窗口（GetAncestor GA_ROOT），子控件不碰

  * 接入点：`DSHController.start()` 在 `_start_worker` 前 `sweeper.snapshot_baseline()`；`_start_worker` 内 Popen 后 `sweeper.start()`；`stop()` / Popen 失败时 `sweeper.stop()` 释放资源

  * 日志：在 GUI 终端区实时显示隐藏事件（带窗口标题），如 `[sweeper] 已隐藏 HWND=1A2B3C 标题='C:\WINDOWS\System32\cmd.exe'`

* **GUI 嵌入式终端视觉升级**：

  * log_box 高度 200 → 320（v1.3.6 的视觉中心）
  * 加深色外边框 + 顶部装饰条（红/黄/绿圆点 + "DSH 终端（嵌入式）"标题）
  * 字体 Consolas 9 → 10；加 `padx=8 pady=6 spacing1=1 spacing3=2` 行间距与内边距
  * 让 GUI 内这块区域看起来像真"终端"被嵌入，配合窗口清道夫让用户感受不到任何独立黑窗

### Changed

* 窗口高度 720 → 800，`minsize` 680 → 760（容纳加大的嵌入式终端区）

* `APP_VERSION` 1.3.5 → 1.3.6

### Technical

* 备份 `main.py` → `main.py.bak.v1.3.5`（修改前 v1.3.5 状态）

* Python AST / `py_compile` 语法检查通过；lint 0 诊断

* 重新打包：PyInstaller `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`

## \[1.3.5 - 终端输出区上移到"开启服务"按钮上方] - 2026-09-01

### Changed

* **GUI 布局重构**：原顺序 `banner → status_card → actions(按钮) → log(expand, 最底部)`；
  改为 `banner → status_card → log(fixed, 200px) → actions`。即把"终端输出"区
  移到"开启服务"按钮正上方，即使后台仍偶有独立 cmd 弹窗，DSH 进程的核心
  stdout/stderr 已在 GUI 内可视，不需频繁切换焦点

* **窗口尺寸**：高度 `650 → 720`，最小高度 `600 → 680`（容纳新位置上的终端区）

* **`_build_log` 由 expand 改为 fixed**：固定高度 200px，`pack_propagate(False)` 锁定
  避免被下方 button 区挤压变形；标题 `运行日志 → 终端输出（DSH 实时日志）`

* `APP_VERSION` 1.3.4 → 1.3.5

### Technical

* 验证：lint 0 诊断通过；AST 解析通过

* 重新打包：PyInstaller `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`

## \[1.3.4 - 弹窗二重根因修复（旧版命中 + DETACHED_PROCESS 误用）] - 2026-09-01

### Fixed

* **根治"命中 npx 缓存旧版 dsh（rc.7）导致闪弹窗"**：

  * 根因：`find_dsh_entry_path()` 对 npx 缓存目录按 `os.listdir` 顺序遍历、不校验版本，一旦全局 npm 目录缺包就回退命中 `_npx` 缓存里的旧版 `0.1.0-rc.7`；rc.7 不支持官方 `--no-open`（启动日志实锤：`error: unknown option '--no-open'`），会默认自动打开浏览器 → spawn `start`/cmd → 弹黑窗

  * 修复：新增 `_parse_version_key()` semver 解析 + `_MIN_DSH_VERSION = "0.1.0-rc.8"` 下限校验，低于 rc.8 的入口一律跳过；多候选（全局 / npx 缓存 / 本地 node_modules）改为**按版本降序取最新**，避免命中顺序不稳定

* **修复"DETACHED_PROCESS 导致孙进程反而开黑窗"**：

  * 根因：v1.3.4 主 node.exe 用 `CREATE_NO_WINDOW | DETACHED_PROCESS`，DETACHED_PROCESS 仅作用于**直接子进程**（node 完全失去控制台）；node 内部再 spawn cmd/start/guard.bat 等控制台程序时（父进程无控制台），Windows 会自动分配**可见新控制台** → 闪黑窗，与"阻止子孙进程开黑窗"的初衷相反

  * 修复：`_start_worker` 改回仅 `CREATE_NO_WINDOW`（detach=False），更新 `_win_no_console_flags` docstring 纠正语义认知；短命令与长驻进程统一 detach=False

* **修复"打开DSH"按钮弹窗**：`_on_open` 在 Windows 下改用 `os.startfile(DSH_URL)` 直接 ShellExecute 打开默认浏览器，不经 `webbrowser` 的 cmd 中转路径

### Changed

* `APP_VERSION` 1.3.3 → 1.3.4

* `DSH-Desktop.spec` 维持 `console=False`（窗口化 EXE，无主控制台窗口）；源码态 `python main.py` 运行时 python.exe 自带控制台窗口属正常现象，无法由代码隐藏，请使用打包 EXE

### Technical

* 备份 `main.py` → `main.py.bak.v1.3.4`（修改前 v1.3.3 状态）

* Python AST / `py_compile` 语法检查通过；lint 0 诊断

* 重新打包：PyInstaller `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`

## \[1.3.3 - cmd 弹窗彻底根治 + 卡顿防护强化] - 2026-09-01

### Fixed

* **彻底根治"运行后弹出 cmd 命令窗口"**（v1.2.5 的 AllocConsole 方案本质缺陷）：

  * 根因：v1.2.5 `_ensure_hidden_console()` 在 PyInstaller `console=False` 窗口化 EXE 下调用 `AllocConsole()`，Windows 创建可见控制台后再 `ShowWindow(SW_HIDE)`，两者之间存在不可消除的竞态时间窗口，必然闪烁

  * 修复：PyInstaller `DSH-Desktop.spec` 改为 `console=True`，让 Windows loader 在 EXE 进入 `main()` **之前**就预分配好控制台（时机最早、无竞态）；程序启动后立即 `ShowWindow(SW_HIDE)` 隐藏，子进程 `CREATE_NO_WINDOW` 继承该隐藏控制台，node → cmd 全部孙进程 attach 到同一个隐藏控制台，彻底不弹窗

  * `_ensure_hidden_console()` → 重命名为 `_hide_console_on_console_exe()`，仅做 `GetConsoleWindow() + ShowWindow(SW_HIDE)`，不 AllocConsole、不 FreeConsole；源码态 `python main.py` 时跳过隐藏（保留用户终端）

* **强化卡顿防护**：

  * `_version_worker` 的 `queue.put()` 改为 `put_nowait()` + `queue.Full` 丢弃，消除所有后台线程可能因队列满而阻塞的路径

  * `stop()` 中 `subprocess.run(taskkill)` 补上 `timeout=10`，防止 taskkill 进程挂起导致关闭操作卡死

### Changed

* `APP_VERSION` 1.3.2 → 1.3.3

* `DSH-Desktop.spec` `console=False` → `console=True`（v1.3.3 核心变更，**需重新 PyInstaller 打包**后生效）

### Technical

* Python AST 语法检查通过

* 无残留 `AllocConsole` / `_ensure_hidden_console` 代码引用（仅版本历史注释保留）

* 重新打包前需先把 `DSH-Desktop.spec` 的 `console=True` 确认无误，再执行 PyInstaller

## \[1.3.2 - 启动日志洪峰修复] - 2026-08-31

### Fixed

* **修复"开启服务后软件容易卡死"**（DSH 启动日志洪峰拖垮 GUI）：

  * 根因：`_read_output` 线程将 DSH 输出逐行入队无界 `queue.Queue()`，`_drain_queue` 每 100ms 最多取 300 条、**每条单独** **`_log()`**（Text.insert + 行数检查 + delete + `see("end")` 滚动重绘）。首次启动 pnpm 下载依赖时可上万行/秒 → 100ms 内 300 次 Text 重绘 → 主线程假死；输出超速时队列无限积压、内存膨胀

  * 修复 1：`_msg_queue` 改有界队列 `maxsize=5000`，`_on_subprocess_output` 改 `put_nowait` + `queue.Full` 丢弃（防内存膨胀）

  * 修复 2：`_drain_queue` 改为批量收集（每轮 ≤200 条）后经新增 `_log_lines()` **一次 insert + 一次行数裁剪 + 一次 see** 写入，UI 重绘次数从 300/100ms 降到 ≤2/100ms

* 备份 `main.py` → `main.py.bak.v1.3.2`（修改前 v1.3.0 状态）

### Technical

* `APP_VERSION` → `1.3.2`；`py_compile` 通过；lint 0 诊断

* 重新打包：PyInstaller 6.22.2 `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`（12,644,762B），复制到根目录发布版；旧根目录 EXE 备份 → `DSH-Desktop.exe.bak.v1.3.0`，`dist/DSH-Desktop.exe.bak.v1.3.2` 为上一轮产物备份；warn 无关键缺失；EXE 启动存活测试 OK（8s alive, clean stop）

## \[1.3.0 EXE 打包] - 2026-08-31

### Technical

* PyInstaller 6.22.2 / Python 3.14.5 重新打包 `dist/DSH-Desktop.exe`（`--onefile --windowed --clean`），`APP_VERSION=1.3.0`（对应含 1.3.1 依赖修复后的 dsh-market node\_modules 环境）

* 打包前备份旧 EXE → `dist/DSH-Desktop.exe.bak.v1.3.0`（12636089B，v1.2.5）；产物 12644129B

* 验证：`py_compile` OK；warn 文件仅 POSIX 可选模块缺失（Windows 下正常）；EXE 启动存活测试 OK（8s 后进程存活，正常关闭）

* 注意：便携插件不内嵌 EXE；frozen 态 `_app_base_dir()` = EXE 所在目录，**发布时 EXE 需与** **`dsh-Plugin/`** **同级摆放**（放 `DSH-Desktop/` 根目录），否则双击 `dist/` 下 EXE 时便携插件扫描指向不存在的 `dist/dsh-Plugin/`，guard/market 不会自动注册

* 瘦身：删除 `build/`（15.7MB PyInstaller 缓存）与 `__pycache__/`（0.1MB）；`dist/` 保留 `DSH-Desktop.exe` 与备份 `.bak.v1.0.9`/`.bak.v1.3.0` 作回滚点。便携性核查：`dsh-Plugin/` 无绝对路径硬编码，源码态 `python main.py` 复制到新机器即用

* 发布版 EXE 归位：`dist/DSH-Desktop.exe` → `DSH-Desktop/` 根目录（与 `dsh-Plugin/` 同级），frozen 态 `_app_base_dir()` = 根目录，便携插件扫描自动命中 `dsh-Plugin/`；至此"复制整个 DSH-Desktop 文件夹到新机器 → 点开启服务 → 弹窗默认勾选 guard+market → 注册并启动"的换新环境流程在源码态与打包态下均成立

## \[1.3.0 - 便携插件机制] - 2026-08-31

### Added

* **便携插件机制**：`DSH-Desktop/dsh-Plugin/` 下归置便携插件源，随文件夹便携迁移，换新环境由启动器自动注册

  * 新增 `dsh-market` 源到 `dsh-Plugin/dsh-market/`（从 node\_modules/dshmarket\@1.15.0 已构建产物拷贝，2MB，lib/client/cordis.patch.yml 齐全）

  * web profile 的 `dshmarket` 依赖由 npm 包 `^1.15.0` 改为 `link:d:/3.aidata/ai/DSH-Desktop/dsh-Plugin/dsh-market`（备份 package.json → `.bak.market-link`），`--dump-config` 确认 `dsh-market` 行仍正确挂载

* **启动器"便携插件管理"弹窗**（main.py v1.3.0）：

  * 点"开启服务"时弹出 `PluginScanDialog`，扫描 `dsh-Plugin/` 下所有含 package.json 的子目录，显示名称/版本/已安装状态

  * 默认勾选 `DEFAULT_LOCAL_PLUGINS = [dsh-plugin-guard, dsh-market]`（已安装项也默认勾选，re-add 幂等）

  * 确认后随服务启动自动 `dsh plugin --profile web add link:<path>` 注册到 web profile；跳过/取消 = 不注册直接启动

  * 注册在后台线程执行（不阻塞 UI），失败不阻断启动（仅日志告警）；隐藏控制台不弹黑窗

### Changed

* `DSHController.start()` / `_start_worker()` 新增 `pending_plugins` 参数，Popen 前先注册所选插件

* `_on_start()` 先弹插件管理窗，把所选传给 `controller.start()`

### Technical

* 备份 `main.py` → `main.py.bak`（49768B）；`py_compile` 通过；`scan_local_plugins()` 功能验证 OK（识别 dsh-market/dsh-plugin-guard 两项，installed/default\_on 均正确）

* 新增函数：`_app_base_dir` / `_local_plugins_root` / `_dsh_home` / `_profile_dir` / `_read_profile_deps` / `scan_local_plugins` / `register_local_plugin`

* dsh-market 选"拷贝已构建产物"而非 git clone：其有 `prepare: npm run build`（需 TS 工具链），拷贝产物零构建依赖，最契合"换环境自动装"目标

* **独立代码审查修复（subagent fork）**：

  * P1-1：`_app_base_dir()` 新增 frozen 检测（PyInstaller onefile 态用 `sys.executable` 目录而非 `__file__`→`_MEIPASS`），`_local_plugins_root` 与 `find_dsh_entry_path` 第 3 步统一改用它，否则打包 EXE 下便携插件功能完全失效

  * P1-2：`scan_local_plugins()` 把整个目录解析+类型校验包进 try/except（单个坏目录不拖垮扫描）；字段类型校验（name/version/description 非 str 时回退/兜底）防 UI `[:60]` 崩溃；`PluginScanDialog.__init__` 用 try 包住，异常时必 destroy+grab\_release，杜绝幽灵窗口持 grab 卡死主窗口；grab\_set 移到 \_build\_ui 成功之后

  * P2-1：`register_local_plugin` 改 Popen+communicate(timeout=60)，超时 taskkill /F /T 树杀孙进程，加 stdin=DEVNULL 防 pnpm 交互挂起

  * P2-2：包名正则校验（`^[A-Za-z0-9][A-Za-z0-9._@/-]*$`）防路径穿越

  * P2-4：`start()` 传 pending 时 tuple 快照防竞态

  * P2-5：扫描为空时跳过弹窗直接启动

  * P2-7：弹窗底部加"注册将执行插件安装脚本，仅勾选可信插件"安全提示

* 修复后验证：`py_compile` 通过；scan 功能 OK；坏 package.json（数组/坏字段类型）容错验证 PASS（坏 dict 跳过、坏字段兜底为目录名/空串且类型安全）

## \[1.3.1 - 便携插件依赖修复] - 2026-08-31

### Fixed

* **修复 v1.3.0 便携插件机制导致 DSH web 服务无法启动**（开启服务后 3080 端口无监听，`node bin.js web --no-open` 启动即崩溃 `ERR_MODULE_NOT_FOUND`）：

  * 根因 1：web profile 的 `dshmarket` 依赖为 `link:` 指向 `dsh-Plugin/dsh-market`，但该目录 `node_modules` 为空，`lib/net.js` 无法解析 `undici`（已装：`npm install --omit=dev --ignore-scripts`，undici + js-yaml 共 3 包）

  * 根因 2（修复后暴露）：link 场景下 peer 依赖 `@deepseek-ai/dsh-settings` / `@deepseek-ai/schemastery` / `@deepseek-ai/cordis` 无法从 dsh-market 目录向上解析（已装：`npm install --no-save` 三个 peer 依赖，293 包；未写入 package.json）

* 验证：`node bin.js web --no-open` 启动成功，输出 `dsh web: http://127.0.0.1:3080`，进程 20s 存活，仅 SQLite ExperimentalWarning；`dsh-plugin-guard` 正常加载（5 条冲突 WARNING 为提示性，非致命）

### Note

* 便携插件依赖以 node\_modules 随包携带；因使用 `--no-save`，package.json 未记录新增依赖，便携迁移后若需重建请执行：`npm install --omit=dev --ignore-scripts && npm install @deepseek-ai/dsh-settings @deepseek-ai/schemastery @deepseek-ai/cordis --no-save`

## \[插件补装完成 - dsh-plugin-guard] - 2026-08-31

### Fixed

* **补齐 dsh-plugin-guard（v1.3.0）缺失的安装状态**（此前的导入后被禁用/回滚，遗留 `node_modules` 链接缺失 + bundles 列表缺失）：

  * 命令：`dsh plugin --profile web add link:d:/3.aidata/ai/DSH-Desktop/dsh-Plugin/dsh-plugin-guard`（pnpm 11.22.0，Done in 1.4s）

  * `node_modules/dsh-plugin-guard` SymbolicLink → 本地 checkout 已建立；`package.json` bundles 数组已追加 `dsh-plugin-guard`（reconcile 自动完成）

  * 验证：`dsh --profile web --dump-config` 输出含 `- id: plugin-guard / name: dsh-plugin-guard`，已挂载进启动树；14 个声明依赖全部在 node\_modules 中（pnpm 清理的 -14 为上次中断尝试的孤儿包）

  * 注：此前记录"需带 `--patch` 才生效"系不完整安装状态下的权宜说法；bundle 层现由 profile 启动自动应用，重启 dsh web 进程即可生效

## \[DSH Doctor 弹窗隐藏 - 方案C] - 2026-08-31

### Fixed

* **定位弹窗根因**：cmd 弹窗来源为 Windows 计划任务 `DSH Doctor Supervisor`（2026-08-31 14:55:44 注册，登录触发），执行 `C:\Users\Administrator\AppData\Local\DSH Doctor\supervisor.cmd` → node `@linxin666/dsh-doctor` v0.3.6 supervisor（DSH 事务性救援组件，新装/UI 更新时默认注册用户级计划任务）；与 EXE、插件导入无关（禁用 guard 后仍弹、恢复到导入前 package.json 仍弹）

* **方案 C 实施（保留救援功能 + 隐藏窗口）**：

  1. 备份 `supervisor.cmd` → `supervisor.cmd.bak.20260831`
  2. 新建 `supervisor_hidden.vbs`（`WScript.Shell.Run` 以 0=隐藏窗口 启动 `supervisor.cmd`，不等待）
  3. 计划任务动作由「cmd 直接执行 supervisor.cmd」改为「`wscript.exe "...supervisor_hidden.vbs"`」（`Set-ScheduledTask`，规避 schtasks 引号转义坑）
  4. 验证：`schtasks /run` 手动触发 → Last Result = 0（此前为 1 失败）；node 守护进程驻留，救援功能正常保留

* **注意**：若 DSH 更新重写 `supervisor.cmd`，VBS 包装不受影响；若 DSH 重新注册计划任务动作为 cmd 直调，可按上述步骤重建（VBS 隐藏启动器 + `Set-ScheduledTask` 改动作，步骤见 `.ai_audit.log` 2026-08-31 15:05 记录）

## \[插件导入] - 2026-08-31

### Added

* **将** **`DSH-Desktop/dsh-Plugin/dsh-plugin-guard`（v1.3.0）导入 web profile**：

  * 命令：`dsh plugin --profile web add link:d:/3.aidata/ai/DSH-Desktop/dsh-Plugin/dsh-plugin-guard`（pnpm 11.22.0，Done in 8.9s）

  * 导入前备份 profile `package.json` → `package.json.bak.import-20260831`

  * 验证：`dsh plugin list` 显示 `dsh-plugin-guard@link:d:/...`；`package.json` dependencies + bundle 数组已含该包；`node_modules/dsh-plugin-guard` link 建立，版本 1.3.0 与源一致

  * 插件 CLI 可用：`node lib/cli.js status` → 已启用 140 / 已禁用 33，扫描出 5 个 WARN（tool-subagent/tool-subagent-fork 多 id 挂载、better-sidebar double-mount），无 critical

  * 注：DSH web 启动需带 `--patch` 插件方生效（见 DEPLOY\_SOP）

## \[1.2.5 恢复 - 弹窗根治最终方案] - 2026-08-31

### Technical

* **用户实测反馈 v1.0.9 无 cmd 弹窗**（截图），经 git 对比确认 v1.0.9 与 v1.1.0 启动逻辑一致，弹窗根因系 npm `@deepseek-ai/dsh` 包升级后内部 spawn 行为变化（运行时下载，非 EXE 内嵌）

* 备份 v1.0.9：`main.py.bak.v1.0.9`（git acb4167 提取）+ `dist/DSH-Desktop.exe.bak.v1.0.9`（24065152B 一致）

* **选定方案 B**：从 `main.py.bak.v1.2.5` 恢复 v1.2.5 弹窗根治代码（`_ensure_hidden_console` + 直接 node 单进程启动 `find_dsh_entry_path` + `build_hidden_startupinfo` 兜底，`APP_VERSION = "1.2.5"`）

* 验证：read\_lints 0 错误、py\_compile OK

* PyInstaller 6.22.2 / Python 3.14.5 / onefile + windowed 重新打包 `dist/DSH-Desktop.exe`；EXE 启动存活测试 OK（6s 后进程存活，正常关闭）

* **清除 v1.1.0 及之后的所有备份**（18 个，含 main.py.bak.v1.1.0~~v1.2.5、README.md.bak.v1.1.0/v1.2.5、VERSION\_LOG.md.bak.v1.2.5、DSH-Desktop.exe.bak.v1.1.0~~v1.2.5/repack-v1.1.0）；保留 v1.0.9 及之前的备份（main.py.bak、README.md.bak、.ai\_audit.log.bak、main.py.bak.v1.0.9、DSH-Desktop.exe.bak.v1.0.9）

## \[1.1.0] - 2026-08-31

### Added

* **版本感知**：启动时后台查询 npm 上 `@deepseek-ai/dsh` 的 latest 版本（`npm view ... version`，8s 超时静默失败），状态卡片显示"DSH 官方版本：vX.X.X（npm latest）"

  * 查询结果经 `_msg_queue` 特殊前缀消息回传主线程，遵循项目既有线程安全模式，不触碰 tkinter

* README 新增"与官方 CLI 对齐"小节，引用官方 npm dist-tag：`latest` = `0.1.1-rc.2`（master 分支 `0.1.2-alpha.2`）

### Changed

* **对齐官方 deepseek-ai/deepseek-harness 最新 CLI 变更**：

  * 确认 `dsh web` ≡ `dsh --profile web`（官方硬编码保留别名，两种写法等价）

  * 确认 `--no-open` 为**官方正式参数**（官方自 v0.1.0-rc.8 起本机启动默认自动打开浏览器；`--host 0.0.0.0` 被官方显式禁止，防 RCE 暴露到局域网）

  * 本工具固定 `127.0.0.1:3080` + `--no-open`，符合官方安全基线，杜绝双浏览器窗口（v1.0.8 移除 `--no-open` 属误判，v1.0.9 恢复正确，本版以官方源码再次复核确认）

* 模块 docstring 补充官方 CLI 对齐说明

* **版本查询兼容修复**：Windows 上 `npm` 为 `npm.cmd`，`subprocess.run` 直接执行失败（与 npx 同因），改为 `cmd /c npm view ...` 包装；实测返回 `0.1.1-rc.2`

* README 功能表新增"版本感知"行；开启服务命令标注 `-y` 参数

### Technical

* 修改前已备份 `main.py.bak` / `README.md.bak`

* 验证：read\_lints 0 错误、py\_compile OK

* `APP_VERSION` 升至 1.1.0

## \[1.0.9] - 2026-08-25

### Changed

* **回退恢复** **`--no-open`** **启动参数**（用户实测：移除该参数后 dsh 自动打开浏览器，与"打开DSH"按钮重复 → 出现两个浏览器窗口）

  * 恢复 `DSH_EXTRA_ARGS = ["--no-open"]` 常量与 `build_start_command()` 中的展开

  * 行为回到 v1.0.5：启动服务不自动打开浏览器，仅通过应用内"打开DSH"按钮访问，杜绝双窗口

* README 功能表同步恢复 `--no-open`，保持文档与代码一致

### Technical

* 修改前已备份 `main.py.bak`（23883B）

* 验证：read\_lints 0 错误、py\_compile OK

* `APP_VERSION` 升至 1.0.9（历史版本 1.0.8 记录保留）

* 重新打包 `dist/DSH-Desktop.exe`

## \[1.0.8] - 2026-08-25

### Changed

* **移除** **`--no-open`** **启动参数**（B\_00 前置检索复核结论：官方 CLI 文档 v0.1.0-rc.7 无此参数）

  * `DSH_EXTRA_ARGS` 常量删除，`build_start_command()` 恢复为官方标准命令 `npx -y @deepseek-ai/dsh web`

  * 启动后 dsh 会自动打开浏览器（与应用内"打开DSH"按钮行为一致，无需担心功能缺失）

* 同步更新模块 docstring 中的命令说明

### Technical

* 修改前已备份 `main.py.bak`（23964B）

* 验证：read\_lints 0 错误、py\_compile OK

* `APP_VERSION` 同步升至 1.0.8

* 已用 PyInstaller 6.22.2 重新打包 `dist/DSH-Desktop.exe`（--onefile --windowed --clean）

## \[1.0.7] - 2026-08-25

### Fixed

* README.md 与实际状态严重脱节，一次性对齐到 v1.0.5：

  * 版本号 `v1.0.0` → `v1.0.5`

  * 移除启动命令中的 `--no-open`（官方 CLI 文档 v0.1.0-rc.7 无此参数，按 B\_00 前置检索复核结论修正）

  * 删除"方式一：双击 build.bat"打包指引（build.bat 已随清理删除）

  * 移除 `pyinstaller DSH-Desktop.spec` 指引（spec 已删除），仅保留命令行打包方式

  * 补充 v1.0.4 新增的外部实例识别与强制关闭说明

### Technical

* 修改前已备份 `README.md.bak`（2276B）

## \[1.0.6] - 2026-08-25

### Added

* 打包支持：新增 `build.bat` 一键打包脚本与 `DSH-Desktop.spec`（PyInstaller 配置）

* 打包参数：`--onefile`（单文件）、`--windowed`（无控制台）、`--clean`（清理缓存）

* 产物：`dist/DSH-Desktop.exe`，双击即用、无需 Python 环境，可分发

### Technical

* PyInstaller 6.22.2 已安装于 Python 3.14 环境

* spec 排除 numpy/pandas/matplotlib 等无关大包，减小体积

## \[1.0.5] - 2026-08-25

### Fixed

* **find\_pids\_by\_port 修复**：用户实测发现 netstat 解析在中文 Windows 下返回空列表

  * 根因：中文 Windows 的 `netstat` 输出状态字为本地化字符串（`LISTENING` → `侦听`），导致 `parts[-1].upper() != "LISTENING"` 把所有行过滤掉

  * 修复：改用 **PowerShell** **`Get-NetTCPConnection -LocalPort 3080 -State Listen`**（Windows 8+ 内置，跨语言稳定）

  * 兜底：netstat 解析同时接受 `LISTENING` 和 `侦听`

## \[1.0.4] - 2026-08-25

### Added

* **外部实例强制关闭能力**——针对用户反馈"检测到外部实例但关闭按钮禁用"

* `find_pids_by_port()`：通过 `netstat -ano -p TCP` 查找占用 3080 端口的 LISTENING 进程

* `kill_pids(pids)`：对每个 PID 执行 `taskkill /F /T` 终止进程树

* 状态刷新：外部实例状态下"关闭服务"按钮恢复为可用（红色）

* `_on_stop` 重写为三分支：

  1. 本控制器进程 → 直接 stop
  2. 外部实例 → 二次确认弹窗列出 PID → kill\_pids → 等待端口释放（最多 3 秒）
  3. 都没跑 → 仅日志

## \[1.0.3] - 2026-08-25

### Added

* 端口探测：`port_in_use()` 通过 socket 连接检测 3080 端口是否被占用

* 启动前端口检测：端口被占用时返回 `PORT_BUSY`，UI 弹窗提示"可能已有 DSH 实例"，询问是否直接打开浏览器

* 外部实例识别：状态栏支持"运行中（外部实例）"——非本应用启动但端口有服务时正确显示

* 进程退出提示：子进程异常退出（rc≠0）时日志明确提示退出码与 EADDRINUSE 排查方向

* 关闭服务对外部实例给出引导（提示手动结束占用进程）

### Fixed

* 日志区行数上限 1000 行（超出删除最早 100 行），防止错误日志刷屏导致 UI 卡顿

* 日志队列每轮限流 300 条

### Verified

* 实测诊断确认：用户机器上 3080 端口已被 PID 14712 (node) 占用，导致"开启服务"触发 EADDRINUSE 秒崩

* 端口探测/空闲端口/PORT\_BUSY/无死锁 4 项测试全 PASS

## \[1.0.2] - 2026-08-25

### Fixed

* **彻底修复点击"开启服务"后界面未响应的真正根因**

  * 根因：`threading.Lock` 为**非可重入锁**，`start()` 在 `with self._lock` 内调用 `self.is_running` property（内部再次加锁）→ 主线程**自锁死锁** → 消息循环停摆 → 窗口"未响应"

  * 修复：改用 `threading.RLock`（可重入锁）；`start()` 锁内直接检查字段，不再嵌套调用 property

* 子进程输出回调改为 `queue.Queue` + 主线程 `after` 轮询，彻底消除 tkinter 跨线程调用风险

* `stop()` 简化：不再拒绝"启动中"关闭，进程存在即终止，退出清理更可靠

* 退出逻辑统一：运行中或启动中关闭窗口均先尝试 stop 再退出

### Verified

* 回归测试 7 项全 PASS（start/stop 无死锁、二次点击防护、状态属性、消息队列收发、回调）

* `start()` 实测 4.8ms 返回，UI 不再阻塞

## \[1.0.1] - 2026-08-25

### Fixed

* 修复点击"开启服务"后界面卡死（未响应）的问题

  * 根因 1：Windows 上 `npx` 为 `npx.cmd` 批处理，`Popen` 直接执行失败/异常，改经 `cmd /c` 包装

  * 根因 2：npx 首次运行需交互确认安装包，`-y` 参数自动跳过确认

  * 根因 3：启动逻辑原在主线程同步执行，阻塞 tkinter 消息循环；改为后台线程执行，UI 永不卡死

* 新增"启动中"状态（琥珀色指示灯 + 按钮禁用），刷新间隔缩短至 500ms

* 子进程输出按 `\r`/`\n` 分段，单行截断 500 字符，避免下载进度条刷屏

* 关闭服务在"启动中"时给出提示；退出窗口时同样处理启动中状态

## \[1.0.0] - 2026-08-25

### Added

* GUI 窗口（tkinter），含标题、状态卡片、三个功能按钮、运行日志区

* 开启服务：后台执行 `npx @deepseek-ai/dsh web --no-open`

* 关闭服务：Windows 下 `taskkill /F /T /PID <pid>` 终止进程树

* 打开DSH：`webbrowser.open("http://127.0.0.1:3080")`

* 状态自检：每秒刷新服务运行状态，按钮可用性自动切换

* 子进程输出捕获：后台线程读取 stdout/stderr 并实时显示在日志区

* 退出保护：服务运行时关闭窗口会弹窗确认

* 无控制台窗口：使用 `subprocess.CREATE_NO_WINDOW` 避免弹出黑色 CMD 窗口

### Technical

* 仅依赖 Python 3.8+ 标准库

* 零第三方依赖

* PyInstaller 打包说明已附带

