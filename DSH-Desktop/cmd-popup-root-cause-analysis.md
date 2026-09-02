# DSH Desktop cmd 弹窗根因排查档案

> 创建时间：2026-09-01
> 版本：v1.2.5 → v1.3.3 → v1.3.4（最终定稿）
> 核心问题：PyInstaller 打包的 GUI 应用（DSH Desktop）启动 DSH 服务时弹出 cmd 黑窗
> 状态：✅ v1.3.4 已修复

***

## 问题描述

用户双击 `DSH-Desktop.exe`，点击"开启服务"按钮后：

1. DSH Desktop GUI 正常显示
2. 一个 cmd.exe 黑色命令窗口弹出（Windows Task Manager 可见）
3. cmd 窗口内容是 DSH node 进程的输出
4. 关闭 DSH Desktop 后 cmd 窗口也跟着消失

## 涉及文件

| 文件                 | 角色                                       |
| ------------------ | ---------------------------------------- |
| `DSH-Desktop.spec` | PyInstaller 打包配置（`console` 开关决定 EXE 子系统） |
| `main.py`          | 主程序，含子进程管理、日志、控制台隐藏逻辑                    |

***

## 方案一：v1.2.5 — AllocConsole（失败）

### 配置

```
spec: console=False
代码: _ensure_hidden_console() 在 main() 开头调用
      → GetConsoleWindow() 返回 None（窗口化 EXE 无控制台）
      → AllocConsole() 创建新控制台
      → ShowWindow(SW_HIDE) 隐藏
```

### 根因

```
时间线：
  1. EXE 启动（Windows loader）
  2. EXE 进入 main()，GetConsoleWindow() → None（因为 console=False）
  3. 调用 AllocConsole() ← 此时 Windows 创建新控制台，窗口先显示
  4. 调用 ShowWindow(SW_HIDE) ← 再隐藏

步骤 3 和 4 之间有不可消除的时间差（Windows 内核态 → 用户态的切换开销）
用户必然会在屏幕上看到 cmd 黑窗的闪烁。
AllocConsole 就是为了给 GUI 程序分配控制台设计的，它的行为就是创建可见窗口。
```

### 结论

**`AllocConsole`** **在窗口化 EXE 里天生不可能做到"无闪烁"**。

***

## 方案二：v1.3.3 — console=True + 继承隐藏控制台（失败）

### 配置

```
spec: console=True  ← 改成控制台子系统
代码: _hide_console_on_console_exe() 在 main() 开头调用
      → GetConsoleWindow() 返回非零（loader 预分配好了）
      → ShowWindow(SW_HIDE) 隐藏

子进程: CREATE_NO_WINDOW（让 node.exe 继承父进程隐藏控制台）
```

### 根因

```
时间线：
  1. EXE 启动（Windows loader）
  2. loader 看到 console=True → 自动创建控制台窗口 ← 窗口已经可见了！
  3. EXE 进入 main()，ShowWindow(SW_HIDE) ← 再隐藏

步骤 2 在步骤 3 之前，时机由 Windows loader 控制，我们无法干预。
无论 main() 第一行代码执行多快，loader 创建控制台的动作已经完成了。
```

### 额外隐藏 bug

v1.3.3 第一版还犯了另一个错误：给主 node.exe 进程也加了 `CREATE_NO_WINDOW`。

```
父进程有隐藏控制台
spawn node.exe + CREATE_NO_WINDOW
  → CREATE_NO_WINDOW 的含义是"子进程不要继承/创建控制台"
  → node.exe 无控制台可用
  → node.exe 内部 spawn cmd.exe 时
  → cmd.exe 需要控制台 → Windows 给它分配新的可见控制台 → 弹黑窗！
```

### 结论

**`console=True`** **方案在 Windows 上同样不可能"零闪烁"**——loader 创建控制台的时机永远早于任何用户代码。

***

## 方案三：v1.3.4 — console=False + 两档 creationflags（✅ 最终定稿）

### 配置

```
spec: console=False  ← 回到窗口化子系统

代码: 新增 _win_no_console_flags(detach: bool = False)
      短命令（npm root / where / netstat / taskkill）:
        creationflags = CREATE_NO_WINDOW            （默认 detach=False）
      长驻 node.exe 主进程:
        creationflags = CREATE_NO_WINDOW | DETACHED_PROCESS  （detach=True）
```

### 为什么可行

```
console=False EXE：
  Windows loader 看到窗口化子系统 → 不创建任何控制台 → 零闪烁 ✅

子进程分两档：
  短命令（npm root -g / where node）:
    CREATE_NO_WINDOW → 告诉 Windows "这个控制台进程不要有控制台窗口"
    同时不阻止控制台创建（如果真需要的话）
    stdout 被 PIPE/capture_output 接管 → 不需要控制台 I/O
    → 零弹窗 ✅ + stdout 正常返回 ✅

  node.exe 主进程:
    CREATE_NO_WINDOW | DETACHED_PROCESS
    DETACHED_PROCESS → 告诉子进程"不要尝试继承/创建任何控制台"
    node 内部 spawn 的 cmd/powershell/pnpm 等子孙进程也会被强制 detach
    → 整个进程树零控制台、零弹窗 ✅
    stdout 被 PIPE 接管 → 不需要控制台 I/O ✅
```

### 关键发现：DETACHED\_PROCESS 会让短命令 stdout 丢失

**这是 v1.3.4 第一版的隐藏 bug，也是本次排查中最隐蔽的问题。**

```python
# 实测
import subprocess

# 方案 A: CREATE_NO_WINDOW | DETACHED_PROCESS（全量加了）
r = subprocess.run(['cmd', '/c', 'npm', 'root', '-g', ...],
    capture_output=True, ...,
    creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS)
print(repr(r.stdout))  # → ''  ← 空！DETACHED_PROCESS 把 stdout 也丢了！

# 方案 B: 仅 CREATE_NO_WINDOW
r = subprocess.run(['cmd', '/c', 'npm', 'root', '-g', ...],
    capture_output=True, ...,
    creationflags=CREATE_NO_WINDOW)
print(repr(r.stdout))  # → 'C:\\Users\\Administrator\\npm-global\\node_modules' ✅
```

### DETACHED\_PROCESS 导致的连锁故障

```
v1.3.4 第一版代码：所有 subprocess 都加了 CREATE_NO_WINDOW | DETACHED_PROCESS

                    ↓
find_dsh_entry_path() 里的 npm root -g 命令
                    ↓
stdout 返回空串
                    ↓
candidates 列表里没有全局 npm 路径（rc.8）
                    ↓
只能扫 npx 缓存目录
                    ↓
命中旧版 rc.7（1e7f6d9597241db0）
                    ↓
rc.7 不支持 --no-open 参数！
                    ↓
[DSH] error: unknown option '--no-open'
                    ↓
rc.7 的 dsh web 默认调 start 打开浏览器
                    ↓
start 触发 cmd.exe
                    ↓
cmd.exe 弹出黑窗！！！
```

**修复**：DETACHED\_PROCESS 只用于长驻 node.exe 主进程，短命令只用 CREATE\_NO\_WINDOW。

***

## Windows 控制台子系统知识总结

### EXE 子系统（PE header IMAGE\_SUBSYSTEM）

| 值 | 名称              | 行为                                  |
| - | --------------- | ----------------------------------- |
| 2 | Windows GUI     | 双击时 Windows **不创建**控制台              |
| 3 | Windows Console | 双击时 Windows **自动创建**控制台窗口（然后程序才开始跑） |

PyInstaller 对应：

| spec 配置         | bootloader | 子系统         |
| --------------- | ---------- | ----------- |
| `console=False` | `runw.exe` | 2 (GUI)     |
| `console=True`  | `run.exe`  | 3 (Console) |

### CREATE\_NEW\_CONSOLE vs CREATE\_NO\_WINDOW vs DETACHED\_PROCESS

| Flag                 | 值          | 行为                                                      |
| -------------------- | ---------- | ------------------------------------------------------- |
| `CREATE_NEW_CONSOLE` | 0x00000010 | 强制为子进程创建**新**的控制台窗口                                     |
| `CREATE_NO_WINDOW`   | 0x08000000 | 告诉 Windows "不要为这个控制台子系统进程创建可见窗口"                        |
| `DETACHED_PROCESS`   | 0x00000008 | 告诉子进程"不要尝试继承/创建任何控制台"；**副作用**：某些情况下会影响 PIPE 子进程的 stdout |

### 进程创建时的控制台决策树

```
Windows CreateProcess 内部逻辑（简化）：

1. 如果父进程有控制台
   a. 子进程 spawn 标志包含 DETACHED_PROCESS
      → 子进程不继承，也不创建控制台
   b. 子进程 spawn 标志包含 CREATE_NEW_CONSOLE
      → 创建新控制台
   c. 子进程 spawn 标志包含 CREATE_NO_WINDOW（控制台子系统）
      → 继承父进程控制台但不显示窗口
   d. 其他
      → 继承父进程控制台

2. 如果父进程没有控制台（窗口化 EXE 或 DETACHED）
   a. 子进程 spawn 标志包含 DETACHED_PROCESS
      → 不创建控制台，也不尝试继承
   b. 子进程 spawn 标志包含 CREATE_NEW_CONSOLE
      → 创建新控制台
   c. 子进程 spawn 标志包含 CREATE_NO_WINDOW（控制台子系统）
      → 子进程无控制台可用，但也不会触发自动创建
   d. 子进程是控制台子系统 + 以上都不是
      → Windows 自动分配新的**可见**控制台 ← 这就是弹黑窗的根源！
```

### 正确搭配

| 场景                             | 子系统         | creationflags                                                          | 备注                          |
| ------------------------------ | ----------- | ---------------------------------------------------------------------- | --------------------------- |
| GUI 程序（Python/Tk）启动 node.js 服务 | 2 (GUI)     | node: `CREATE_NO_WINDOW \| DETACHED_PROCESS`；其他短命令: `CREATE_NO_WINDOW` | 本项目 v1.3.4 方案               |
| GUI 程序调用 cmd/powershell 执行短命令  | 2 (GUI)     | `CREATE_NO_WINDOW`                                                     | DETACHED\_PROCESS 会丢 stdout |
| 控制台程序（CLI 工具）正常运行              | 3 (Console) | 0（不设置）                                                                 | 正常行为                        |

***

## 最终代码实现

### DSH-Desktop.spec

```python
# -*- mode: python ; coding: utf-8 -*-
# ...
exe = EXE(
    # ...
    console=False,   # v1.3.4: 窗口化 EXE，Windows loader 永远不创建控制台
    # ...
)
```

### main.py

```python
def _win_no_console_flags(detach: bool = False) -> int:
    """Windows 子进程创建标志：阻止控制台窗口出现。

    两档：
    - detach=False（默认）: 只用 CREATE_NO_WINDOW。适用于短命令（npm root -g、
      where node、netstat、taskkill 等），这些命令 stdout 被 PIPE 捕获，不能用
      DETACHED_PROCESS（会导致 stdout 丢失）。
    - detach=True: CREATE_NO_WINDOW | DETACHED_PROCESS。仅用于长驻 node.exe
      主进程——它内部可能 spawn cmd/powershell/pnpm，必须 detach 阻止子孙
      进程各自开黑窗。
    """
    if os.name != "nt":
        return 0
    flags = subprocess.CREATE_NO_WINDOW
    if detach:
        flags |= subprocess.DETACHED_PROCESS
    return flags


# 在 _start_worker 里：
creationflags = _win_no_console_flags(detach=True)  # node.exe 主进程

# 在其他短命令里（默认 detach=False）：
r = subprocess.run(
    ["cmd", "/c", "npm", "root", "-g", ...],
    ...,
    creationflags=_win_no_console_flags(),  # 仅 CREATE_NO_WINDOW
    timeout=10,
)
```

### 受影响的 subprocess 调用清单（全部 11 处）

| #  | 位置                               | 命令                                | flags                                       | 原因                          |
| -- | -------------------------------- | --------------------------------- | ------------------------------------------- | --------------------------- |
| 1  | `find_node_executable`           | `cmd /c where node`               | CREATE\_NO\_WINDOW                          | 短命令，需 stdout                |
| 2  | `find_dsh_entry_path`            | `cmd /c npm root -g`              | CREATE\_NO\_WINDOW                          | 短命令，需 stdout（DETACHED 会丢失！） |
| 3  | `find_dsh_entry_path`            | `npm root -g`（非 Windows）          | CREATE\_NO\_WINDOW                          | 同上                          |
| 4  | `register_local_plugin` Popen    | `node dsh plugin add`             | CREATE\_NO\_WINDOW                          | 短命令，需等待结果                   |
| 5  | `register_local_plugin` taskkill | `taskkill /F /T /PID`             | CREATE\_NO\_WINDOW                          | 短命令                         |
| 6  | `fetch_latest_dsh_version`       | `npm view version`                | CREATE\_NO\_WINDOW                          | 短命令，需 stdout                |
| 7  | `find_port_owner_powershell`     | `powershell Get-NetTCPConnection` | CREATE\_NO\_WINDOW                          | 短命令，需 stdout                |
| 8  | `port_in_use` netstat            | `netstat -ano`                    | CREATE\_NO\_WINDOW                          | 短命令，需 stdout                |
| 9  | `kill_pids`                      | `taskkill /F /T /PID`             | CREATE\_NO\_WINDOW                          | 短命令                         |
| 10 | **`_start_worker`**              | **`node dsh web --no-open`**      | **CREATE\_NO\_WINDOW \| DETACHED\_PROCESS** | **长驻主进程，必须 detach**         |
| 11 | `stop` taskkill                  | `taskkill /F /T /PID`             | CREATE\_NO\_WINDOW                          | 短命令                         |

***

## 验证命令

```python
# 验证 DETACHED_PROCESS 对 stdout 的影响
import subprocess
for label, flags in [
    ("仅 CREATE_NO_WINDOW", subprocess.CREATE_NO_WINDOW),
    ("CREATE_NO_WINDOW | DETACHED_PROCESS",
     subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS),
]:
    r = subprocess.run(
        ["cmd", "/c", "npm", "root", "-g", "--no-audit", "--no-fund"],
        capture_output=True, text=True, encoding="utf-8", errors="ignore",
        creationflags=flags, timeout=10,
    )
    print(f"{label}: stdout={r.stdout!r}, rc={r.returncode}")

# 验证所有 subprocess 调用都有 creationflags
import ast, sys
src = open("main.py", encoding="utf-8").read()
tree = ast.parse(src)
issues = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr in ("run", "Popen") and node.func.value.id == "subprocess":
            if not any(kw.arg == "creationflags" for kw in node.keywords):
                issues.append(f"L{node.lineno}: subprocess.{node.func.attr} 缺 creationflags")
if issues:
    print("\n".join(issues))
else:
    print("全部 subprocess 调用均有 creationflags ✅")
```

***

## 教训与反思

### 1. Windows 控制台 API 不能想当然

AllocConsole 不是"创建一个可以隐藏的控制台"，它的语义是"为无控制台的进程分配一个控制台"，而分配过程**必然**先创建可见窗口。

### 2. console=True 不等于"隐藏控制台"

`console=True` 让 EXE 变成控制台子系统，Windows loader 会在 EXE 入口前**强制**创建可见控制台。ShowWindow 隐藏只能在窗口创建之后，永远有竞态。

### 3. DETACHED\_PROCESS 有隐藏副作用

DETACHED\_PROCESS 不只是"阻止继承控制台"，在某些情况下还会影响 PIPE 子进程的 stdout 捕获。短命令必须只加 CREATE\_NO\_WINDOW。

### 4. dsh 版本回退问题

`find_dsh_entry_path` 的候选列表里 npx 缓存排在全局 npm 之后（正确），但**当全局路径因某种原因失效时**（DETACHED\_PROCESS 导致 stdout 丢失），会静默回退到 npx 缓存里的旧版。建议：

* 启动日志里打印"实际命中的 dsh 版本号"，便于排查版本问题

* 可选：添加版本下限检查，低于 rc.8 给出警告

### 5. 为什么 node.exe 内部 spawn 的进程会弹 cmd 黑窗

node.js 的 `child_process.spawn(cmd.exe, ...)` 或 `child_process.exec()` 内部如果用了 shell（`shell=True` 或执行 `.cmd`/.bat 文件），cmd.exe 作为控制台子系统进程，如果当前没有可继承的控制台，Windows 会为它**自动分配新的可见控制台**。

解决方案就是给**最外层**的 node.exe 加 DETACHED\_PROCESS，让它整个进程树都处于"不要控制台"状态。

***

## 相关资源

* [MSDN: CreateProcess 函数](https://learn.microsoft.com/zh-cn/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)

* [MSDN: CreateProcess flags](https://learn.microsoft.com/zh-cn/windows/win32/procthread/process-creation-flags)

* [MSDN: AllocConsole](https://learn.microsoft.com/zh-cn/windows/win32/api/consoleapi/nf-consoleapi-allocconsole)

* [MSDN: FreeConsole](https://learn.microsoft.com/zh-cn/windows/win32/api/consoleapi/nf-consoleapi-freeconsole)

* [PE IMAGE\_SUBSYSTEM values](https://learn.microsoft.com/zh-cn/windows/win32/debug/pe-format#optional-header-windows-specific-fields-pe32)

* [PyInstaller console flag docs](https://pyinstaller.org/en/stable/spec-files.html#specifying-distribution-mode)

