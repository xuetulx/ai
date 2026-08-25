# VERSION LOG

> DSH Desktop 版本变更日志
> 格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.6] - 2026-08-25

### Added
- 打包支持：新增 `build.bat` 一键打包脚本与 `DSH-Desktop.spec`（PyInstaller 配置）
- 打包参数：`--onefile`（单文件）、`--windowed`（无控制台）、`--clean`（清理缓存）
- 产物：`dist/DSH-Desktop.exe`，双击即用、无需 Python 环境，可分发

### Technical
- PyInstaller 6.22.2 已安装于 Python 3.14 环境
- spec 排除 numpy/pandas/matplotlib 等无关大包，减小体积

## [1.0.5] - 2026-08-25

### Fixed
- **find_pids_by_port 修复**：用户实测发现 netstat 解析在中文 Windows 下返回空列表
  - 根因：中文 Windows 的 `netstat` 输出状态字为本地化字符串（`LISTENING` → `侦听`），导致 `parts[-1].upper() != "LISTENING"` 把所有行过滤掉
  - 修复：改用 **PowerShell `Get-NetTCPConnection -LocalPort 3080 -State Listen`**（Windows 8+ 内置，跨语言稳定）
  - 兜底：netstat 解析同时接受 `LISTENING` 和 `侦听`

## [1.0.4] - 2026-08-25

### Added
- **外部实例强制关闭能力**——针对用户反馈"检测到外部实例但关闭按钮禁用"
- `find_pids_by_port()`：通过 `netstat -ano -p TCP` 查找占用 3080 端口的 LISTENING 进程
- `kill_pids(pids)`：对每个 PID 执行 `taskkill /F /T` 终止进程树
- 状态刷新：外部实例状态下"关闭服务"按钮恢复为可用（红色）
- `_on_stop` 重写为三分支：
  1. 本控制器进程 → 直接 stop
  2. 外部实例 → 二次确认弹窗列出 PID → kill_pids → 等待端口释放（最多 3 秒）
  3. 都没跑 → 仅日志

## [1.0.3] - 2026-08-25

### Added
- 端口探测：`port_in_use()` 通过 socket 连接检测 3080 端口是否被占用
- 启动前端口检测：端口被占用时返回 `PORT_BUSY`，UI 弹窗提示"可能已有 DSH 实例"，询问是否直接打开浏览器
- 外部实例识别：状态栏支持"运行中（外部实例）"——非本应用启动但端口有服务时正确显示
- 进程退出提示：子进程异常退出（rc≠0）时日志明确提示退出码与 EADDRINUSE 排查方向
- 关闭服务对外部实例给出引导（提示手动结束占用进程）

### Fixed
- 日志区行数上限 1000 行（超出删除最早 100 行），防止错误日志刷屏导致 UI 卡顿
- 日志队列每轮限流 300 条

### Verified
- 实测诊断确认：用户机器上 3080 端口已被 PID 14712 (node) 占用，导致"开启服务"触发 EADDRINUSE 秒崩
- 端口探测/空闲端口/PORT_BUSY/无死锁 4 项测试全 PASS

## [1.0.2] - 2026-08-25

### Fixed
- **彻底修复点击"开启服务"后界面未响应的真正根因**
  - 根因：`threading.Lock` 为**非可重入锁**，`start()` 在 `with self._lock` 内调用 `self.is_running` property（内部再次加锁）→ 主线程**自锁死锁** → 消息循环停摆 → 窗口"未响应"
  - 修复：改用 `threading.RLock`（可重入锁）；`start()` 锁内直接检查字段，不再嵌套调用 property
- 子进程输出回调改为 `queue.Queue` + 主线程 `after` 轮询，彻底消除 tkinter 跨线程调用风险
- `stop()` 简化：不再拒绝"启动中"关闭，进程存在即终止，退出清理更可靠
- 退出逻辑统一：运行中或启动中关闭窗口均先尝试 stop 再退出

### Verified
- 回归测试 7 项全 PASS（start/stop 无死锁、二次点击防护、状态属性、消息队列收发、回调）
- `start()` 实测 4.8ms 返回，UI 不再阻塞

## [1.0.1] - 2026-08-25

### Fixed
- 修复点击"开启服务"后界面卡死（未响应）的问题
  - 根因 1：Windows 上 `npx` 为 `npx.cmd` 批处理，`Popen` 直接执行失败/异常，改经 `cmd /c` 包装
  - 根因 2：npx 首次运行需交互确认安装包，`-y` 参数自动跳过确认
  - 根因 3：启动逻辑原在主线程同步执行，阻塞 tkinter 消息循环；改为后台线程执行，UI 永不卡死
- 新增"启动中"状态（琥珀色指示灯 + 按钮禁用），刷新间隔缩短至 500ms
- 子进程输出按 `\r`/`\n` 分段，单行截断 500 字符，避免下载进度条刷屏
- 关闭服务在"启动中"时给出提示；退出窗口时同样处理启动中状态

## [1.0.0] - 2026-08-25

### Added
- GUI 窗口（tkinter），含标题、状态卡片、三个功能按钮、运行日志区
- 开启服务：后台执行 `npx @deepseek-ai/dsh web --no-open`
- 关闭服务：Windows 下 `taskkill /F /T /PID <pid>` 终止进程树
- 打开DSH：`webbrowser.open("http://127.0.0.1:3080")`
- 状态自检：每秒刷新服务运行状态，按钮可用性自动切换
- 子进程输出捕获：后台线程读取 stdout/stderr 并实时显示在日志区
- 退出保护：服务运行时关闭窗口会弹窗确认
- 无控制台窗口：使用 `subprocess.CREATE_NO_WINDOW` 避免弹出黑色 CMD 窗口

### Technical
- 仅依赖 Python 3.8+ 标准库
- 零第三方依赖
- PyInstaller 打包说明已附带
