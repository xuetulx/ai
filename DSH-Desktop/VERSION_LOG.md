# VERSION LOG

> DSH Desktop 版本变更日志
> 格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.3.2 - 启动日志洪峰修复] - 2026-08-31

### Fixed
- **修复"开启服务后软件容易卡死"**（DSH 启动日志洪峰拖垮 GUI）：
  - 根因：`_read_output` 线程将 DSH 输出逐行入队无界 `queue.Queue()`，`_drain_queue` 每 100ms 最多取 300 条、**每条单独 `_log()`**（Text.insert + 行数检查 + delete + `see("end")` 滚动重绘）。首次启动 pnpm 下载依赖时可上万行/秒 → 100ms 内 300 次 Text 重绘 → 主线程假死；输出超速时队列无限积压、内存膨胀
  - 修复 1：`_msg_queue` 改有界队列 `maxsize=5000`，`_on_subprocess_output` 改 `put_nowait` + `queue.Full` 丢弃（防内存膨胀）
  - 修复 2：`_drain_queue` 改为批量收集（每轮 ≤200 条）后经新增 `_log_lines()` **一次 insert + 一次行数裁剪 + 一次 see** 写入，UI 重绘次数从 300/100ms 降到 ≤2/100ms
- 备份 `main.py` → `main.py.bak.v1.3.2`（修改前 v1.3.0 状态）

### Technical
- `APP_VERSION` → `1.3.2`；`py_compile` 通过；lint 0 诊断
- 重新打包：PyInstaller 6.22.2 `--onefile --windowed --clean` → `dist/DSH-Desktop.exe`（12,644,762B），复制到根目录发布版；旧根目录 EXE 备份 → `DSH-Desktop.exe.bak.v1.3.0`，`dist/DSH-Desktop.exe.bak.v1.3.2` 为上一轮产物备份；warn 无关键缺失；EXE 启动存活测试 OK（8s alive, clean stop）

## [1.3.0 EXE 打包] - 2026-08-31

### Technical
- PyInstaller 6.22.2 / Python 3.14.5 重新打包 `dist/DSH-Desktop.exe`（`--onefile --windowed --clean`），`APP_VERSION=1.3.0`（对应含 1.3.1 依赖修复后的 dsh-market node_modules 环境）
- 打包前备份旧 EXE → `dist/DSH-Desktop.exe.bak.v1.3.0`（12636089B，v1.2.5）；产物 12644129B
- 验证：`py_compile` OK；warn 文件仅 POSIX 可选模块缺失（Windows 下正常）；EXE 启动存活测试 OK（8s 后进程存活，正常关闭）
- 注意：便携插件不内嵌 EXE；frozen 态 `_app_base_dir()` = EXE 所在目录，**发布时 EXE 需与 `dsh-Plugin/` 同级摆放**（放 `DSH-Desktop/` 根目录），否则双击 `dist/` 下 EXE 时便携插件扫描指向不存在的 `dist/dsh-Plugin/`，guard/market 不会自动注册
- 瘦身：删除 `build/`（15.7MB PyInstaller 缓存）与 `__pycache__/`（0.1MB）；`dist/` 保留 `DSH-Desktop.exe` 与备份 `.bak.v1.0.9`/`.bak.v1.3.0` 作回滚点。便携性核查：`dsh-Plugin/` 无绝对路径硬编码，源码态 `python main.py` 复制到新机器即用
- 发布版 EXE 归位：`dist/DSH-Desktop.exe` → `DSH-Desktop/` 根目录（与 `dsh-Plugin/` 同级），frozen 态 `_app_base_dir()` = 根目录，便携插件扫描自动命中 `dsh-Plugin/`；至此"复制整个 DSH-Desktop 文件夹到新机器 → 点开启服务 → 弹窗默认勾选 guard+market → 注册并启动"的换新环境流程在源码态与打包态下均成立

## [1.3.0 - 便携插件机制] - 2026-08-31

### Added
- **便携插件机制**：`DSH-Desktop/dsh-Plugin/` 下归置便携插件源，随文件夹便携迁移，换新环境由启动器自动注册
  - 新增 `dsh-market` 源到 `dsh-Plugin/dsh-market/`（从 node_modules/dshmarket@1.15.0 已构建产物拷贝，2MB，lib/client/cordis.patch.yml 齐全）
  - web profile 的 `dshmarket` 依赖由 npm 包 `^1.15.0` 改为 `link:d:/3.aidata/ai/DSH-Desktop/dsh-Plugin/dsh-market`（备份 package.json → `.bak.market-link`），`--dump-config` 确认 `dsh-market` 行仍正确挂载
- **启动器"便携插件管理"弹窗**（main.py v1.3.0）：
  - 点"开启服务"时弹出 `PluginScanDialog`，扫描 `dsh-Plugin/` 下所有含 package.json 的子目录，显示名称/版本/已安装状态
  - 默认勾选 `DEFAULT_LOCAL_PLUGINS = [dsh-plugin-guard, dsh-market]`（已安装项也默认勾选，re-add 幂等）
  - 确认后随服务启动自动 `dsh plugin --profile web add link:<path>` 注册到 web profile；跳过/取消 = 不注册直接启动
  - 注册在后台线程执行（不阻塞 UI），失败不阻断启动（仅日志告警）；隐藏控制台不弹黑窗

### Changed
- `DSHController.start()` / `_start_worker()` 新增 `pending_plugins` 参数，Popen 前先注册所选插件
- `_on_start()` 先弹插件管理窗，把所选传给 `controller.start()`

### Technical
- 备份 `main.py` → `main.py.bak`（49768B）；`py_compile` 通过；`scan_local_plugins()` 功能验证 OK（识别 dsh-market/dsh-plugin-guard 两项，installed/default_on 均正确）
- 新增函数：`_app_base_dir` / `_local_plugins_root` / `_dsh_home` / `_profile_dir` / `_read_profile_deps` / `scan_local_plugins` / `register_local_plugin`
- dsh-market 选"拷贝已构建产物"而非 git clone：其有 `prepare: npm run build`（需 TS 工具链），拷贝产物零构建依赖，最契合"换环境自动装"目标
- **独立代码审查修复（subagent fork）**：
  - P1-1：`_app_base_dir()` 新增 frozen 检测（PyInstaller onefile 态用 `sys.executable` 目录而非 `__file__`→`_MEIPASS`），`_local_plugins_root` 与 `find_dsh_entry_path` 第 3 步统一改用它，否则打包 EXE 下便携插件功能完全失效
  - P1-2：`scan_local_plugins()` 把整个目录解析+类型校验包进 try/except（单个坏目录不拖垮扫描）；字段类型校验（name/version/description 非 str 时回退/兜底）防 UI `[:60]` 崩溃；`PluginScanDialog.__init__` 用 try 包住，异常时必 destroy+grab_release，杜绝幽灵窗口持 grab 卡死主窗口；grab_set 移到 _build_ui 成功之后
  - P2-1：`register_local_plugin` 改 Popen+communicate(timeout=60)，超时 taskkill /F /T 树杀孙进程，加 stdin=DEVNULL 防 pnpm 交互挂起
  - P2-2：包名正则校验（`^[A-Za-z0-9][A-Za-z0-9._@/-]*$`）防路径穿越
  - P2-4：`start()` 传 pending 时 tuple 快照防竞态
  - P2-5：扫描为空时跳过弹窗直接启动
  - P2-7：弹窗底部加"注册将执行插件安装脚本，仅勾选可信插件"安全提示
- 修复后验证：`py_compile` 通过；scan 功能 OK；坏 package.json（数组/坏字段类型）容错验证 PASS（坏 dict 跳过、坏字段兜底为目录名/空串且类型安全）

## [1.3.1 - 便携插件依赖修复] - 2026-08-31

### Fixed
- **修复 v1.3.0 便携插件机制导致 DSH web 服务无法启动**（开启服务后 3080 端口无监听，`node bin.js web --no-open` 启动即崩溃 `ERR_MODULE_NOT_FOUND`）：
  - 根因 1：web profile 的 `dshmarket` 依赖为 `link:` 指向 `dsh-Plugin/dsh-market`，但该目录 `node_modules` 为空，`lib/net.js` 无法解析 `undici`（已装：`npm install --omit=dev --ignore-scripts`，undici + js-yaml 共 3 包）
  - 根因 2（修复后暴露）：link 场景下 peer 依赖 `@deepseek-ai/dsh-settings` / `@deepseek-ai/schemastery` / `@deepseek-ai/cordis` 无法从 dsh-market 目录向上解析（已装：`npm install --no-save` 三个 peer 依赖，293 包；未写入 package.json）
- 验证：`node bin.js web --no-open` 启动成功，输出 `dsh web: http://127.0.0.1:3080`，进程 20s 存活，仅 SQLite ExperimentalWarning；`dsh-plugin-guard` 正常加载（5 条冲突 WARNING 为提示性，非致命）

### Note
- 便携插件依赖以 node_modules 随包携带；因使用 `--no-save`，package.json 未记录新增依赖，便携迁移后若需重建请执行：`npm install --omit=dev --ignore-scripts && npm install @deepseek-ai/dsh-settings @deepseek-ai/schemastery @deepseek-ai/cordis --no-save`

## [插件补装完成 - dsh-plugin-guard] - 2026-08-31

### Fixed
- **补齐 dsh-plugin-guard（v1.3.0）缺失的安装状态**（此前的导入后被禁用/回滚，遗留 `node_modules` 链接缺失 + bundles 列表缺失）：
  - 命令：`dsh plugin --profile web add link:d:/3.aidata/ai/DSH-Desktop/dsh-Plugin/dsh-plugin-guard`（pnpm 11.22.0，Done in 1.4s）
  - `node_modules/dsh-plugin-guard` SymbolicLink → 本地 checkout 已建立；`package.json` bundles 数组已追加 `dsh-plugin-guard`（reconcile 自动完成）
  - 验证：`dsh --profile web --dump-config` 输出含 `- id: plugin-guard / name: dsh-plugin-guard`，已挂载进启动树；14 个声明依赖全部在 node_modules 中（pnpm 清理的 -14 为上次中断尝试的孤儿包）
  - 注：此前记录"需带 `--patch` 才生效"系不完整安装状态下的权宜说法；bundle 层现由 profile 启动自动应用，重启 dsh web 进程即可生效

## [DSH Doctor 弹窗隐藏 - 方案C] - 2026-08-31

### Fixed
- **定位弹窗根因**：cmd 弹窗来源为 Windows 计划任务 `DSH Doctor Supervisor`（2026-08-31 14:55:44 注册，登录触发），执行 `C:\Users\Administrator\AppData\Local\DSH Doctor\supervisor.cmd` → node `@linxin666/dsh-doctor` v0.3.6 supervisor（DSH 事务性救援组件，新装/UI 更新时默认注册用户级计划任务）；与 EXE、插件导入无关（禁用 guard 后仍弹、恢复到导入前 package.json 仍弹）
- **方案 C 实施（保留救援功能 + 隐藏窗口）**：
  1. 备份 `supervisor.cmd` → `supervisor.cmd.bak.20260831`
  2. 新建 `supervisor_hidden.vbs`（`WScript.Shell.Run` 以 0=隐藏窗口 启动 `supervisor.cmd`，不等待）
  3. 计划任务动作由「cmd 直接执行 supervisor.cmd」改为「`wscript.exe "...supervisor_hidden.vbs"`」（`Set-ScheduledTask`，规避 schtasks 引号转义坑）
  4. 验证：`schtasks /run` 手动触发 → Last Result = 0（此前为 1 失败）；node 守护进程驻留，救援功能正常保留
- **注意**：若 DSH 更新重写 `supervisor.cmd`，VBS 包装不受影响；若 DSH 重新注册计划任务动作为 cmd 直调，可按上述步骤重建（VBS 隐藏启动器 + `Set-ScheduledTask` 改动作，步骤见 `.ai_audit.log` 2026-08-31 15:05 记录）

## [插件导入] - 2026-08-31

### Added
- **将 `DSH-Desktop/dsh-Plugin/dsh-plugin-guard`（v1.3.0）导入 web profile**：
  - 命令：`dsh plugin --profile web add link:d:/3.aidata/ai/DSH-Desktop/dsh-Plugin/dsh-plugin-guard`（pnpm 11.22.0，Done in 8.9s）
  - 导入前备份 profile `package.json` → `package.json.bak.import-20260831`
  - 验证：`dsh plugin list` 显示 `dsh-plugin-guard@link:d:/...`；`package.json` dependencies + bundle 数组已含该包；`node_modules/dsh-plugin-guard` link 建立，版本 1.3.0 与源一致
  - 插件 CLI 可用：`node lib/cli.js status` → 已启用 140 / 已禁用 33，扫描出 5 个 WARN（tool-subagent/tool-subagent-fork 多 id 挂载、better-sidebar double-mount），无 critical
  - 注：DSH web 启动需带 `--patch` 插件方生效（见 DEPLOY_SOP）

## [1.2.5 恢复 - 弹窗根治最终方案] - 2026-08-31

### Technical
- **用户实测反馈 v1.0.9 无 cmd 弹窗**（截图），经 git 对比确认 v1.0.9 与 v1.1.0 启动逻辑一致，弹窗根因系 npm `@deepseek-ai/dsh` 包升级后内部 spawn 行为变化（运行时下载，非 EXE 内嵌）
- 备份 v1.0.9：`main.py.bak.v1.0.9`（git acb4167 提取）+ `dist/DSH-Desktop.exe.bak.v1.0.9`（24065152B 一致）
- **选定方案 B**：从 `main.py.bak.v1.2.5` 恢复 v1.2.5 弹窗根治代码（`_ensure_hidden_console` + 直接 node 单进程启动 `find_dsh_entry_path` + `build_hidden_startupinfo` 兜底，`APP_VERSION = "1.2.5"`）
- 验证：read_lints 0 错误、py_compile OK
- PyInstaller 6.22.2 / Python 3.14.5 / onefile + windowed 重新打包 `dist/DSH-Desktop.exe`；EXE 启动存活测试 OK（6s 后进程存活，正常关闭）
- **清除 v1.1.0 及之后的所有备份**（18 个，含 main.py.bak.v1.1.0~v1.2.5、README.md.bak.v1.1.0/v1.2.5、VERSION_LOG.md.bak.v1.2.5、DSH-Desktop.exe.bak.v1.1.0~v1.2.5/repack-v1.1.0）；保留 v1.0.9 及之前的备份（main.py.bak、README.md.bak、.ai_audit.log.bak、main.py.bak.v1.0.9、DSH-Desktop.exe.bak.v1.0.9）

## [1.1.0] - 2026-08-31

### Added
- **版本感知**：启动时后台查询 npm 上 `@deepseek-ai/dsh` 的 latest 版本（`npm view ... version`，8s 超时静默失败），状态卡片显示"DSH 官方版本：vX.X.X（npm latest）"
  - 查询结果经 `_msg_queue` 特殊前缀消息回传主线程，遵循项目既有线程安全模式，不触碰 tkinter
- README 新增"与官方 CLI 对齐"小节，引用官方 npm dist-tag：`latest` = `0.1.1-rc.2`（master 分支 `0.1.2-alpha.2`）

### Changed
- **对齐官方 deepseek-ai/deepseek-harness 最新 CLI 变更**：
  - 确认 `dsh web` ≡ `dsh --profile web`（官方硬编码保留别名，两种写法等价）
  - 确认 `--no-open` 为**官方正式参数**（官方自 v0.1.0-rc.8 起本机启动默认自动打开浏览器；`--host 0.0.0.0` 被官方显式禁止，防 RCE 暴露到局域网）
  - 本工具固定 `127.0.0.1:3080` + `--no-open`，符合官方安全基线，杜绝双浏览器窗口（v1.0.8 移除 `--no-open` 属误判，v1.0.9 恢复正确，本版以官方源码再次复核确认）
- 模块 docstring 补充官方 CLI 对齐说明
- **版本查询兼容修复**：Windows 上 `npm` 为 `npm.cmd`，`subprocess.run` 直接执行失败（与 npx 同因），改为 `cmd /c npm view ...` 包装；实测返回 `0.1.1-rc.2`
- README 功能表新增"版本感知"行；开启服务命令标注 `-y` 参数

### Technical
- 修改前已备份 `main.py.bak` / `README.md.bak`
- 验证：read_lints 0 错误、py_compile OK
- `APP_VERSION` 升至 1.1.0

## [1.0.9] - 2026-08-25

### Changed
- **回退恢复 `--no-open` 启动参数**（用户实测：移除该参数后 dsh 自动打开浏览器，与"打开DSH"按钮重复 → 出现两个浏览器窗口）
  - 恢复 `DSH_EXTRA_ARGS = ["--no-open"]` 常量与 `build_start_command()` 中的展开
  - 行为回到 v1.0.5：启动服务不自动打开浏览器，仅通过应用内"打开DSH"按钮访问，杜绝双窗口
- README 功能表同步恢复 `--no-open`，保持文档与代码一致

### Technical
- 修改前已备份 `main.py.bak`（23883B）
- 验证：read_lints 0 错误、py_compile OK
- `APP_VERSION` 升至 1.0.9（历史版本 1.0.8 记录保留）
- 重新打包 `dist/DSH-Desktop.exe`

## [1.0.8] - 2026-08-25

### Changed
- **移除 `--no-open` 启动参数**（B_00 前置检索复核结论：官方 CLI 文档 v0.1.0-rc.7 无此参数）
  - `DSH_EXTRA_ARGS` 常量删除，`build_start_command()` 恢复为官方标准命令 `npx -y @deepseek-ai/dsh web`
  - 启动后 dsh 会自动打开浏览器（与应用内"打开DSH"按钮行为一致，无需担心功能缺失）
- 同步更新模块 docstring 中的命令说明

### Technical
- 修改前已备份 `main.py.bak`（23964B）
- 验证：read_lints 0 错误、py_compile OK
- `APP_VERSION` 同步升至 1.0.8
- 已用 PyInstaller 6.22.2 重新打包 `dist/DSH-Desktop.exe`（--onefile --windowed --clean）

## [1.0.7] - 2026-08-25

### Fixed
- README.md 与实际状态严重脱节，一次性对齐到 v1.0.5：
  - 版本号 `v1.0.0` → `v1.0.5`
  - 移除启动命令中的 `--no-open`（官方 CLI 文档 v0.1.0-rc.7 无此参数，按 B_00 前置检索复核结论修正）
  - 删除"方式一：双击 build.bat"打包指引（build.bat 已随清理删除）
  - 移除 `pyinstaller DSH-Desktop.spec` 指引（spec 已删除），仅保留命令行打包方式
  - 补充 v1.0.4 新增的外部实例识别与强制关闭说明

### Technical
- 修改前已备份 `README.md.bak`（2276B）

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
