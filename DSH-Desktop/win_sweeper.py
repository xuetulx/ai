"""
WindowSweeper 窗口清道夫（DSH-Desktop v1.4.0 模块，归属 DSH-Desktop v1.4.0）。

隐藏 DSH 启动时弹出的额外 cmd.exe 控制台黑窗：纯 stdlib ctypes + user32.dll，
零三方依赖。非 Windows 平台自动 no-op。

依赖：仅 Python 3.8+ 标准库（os / time / threading / ctypes）
"""

import os
import time
import threading


class WindowSweeper:
    """Windows 顶层窗口清道夫（stdlib ctypes + user32.dll，零三方依赖）。

    目标场景：DSH node.exe 内部 child_process.spawn('cmd.exe', ...) 用于打印
    banner / Doctor 报告等，会在桌面弹出独立的控制台黑窗。CREATE_NO_WINDOW /
    DETACHED_PROCESS 都管不到孙进程（v1.3.4 已确认根因）。

    工作原理：
     1. snapshot_baseline() 在 DSH Popen **之前**记录当前所有**可见顶层窗口 HWND**。
     2. start() 启动后台线程，每 SCAN_INTERVAL_MS 枚举一次所有可见顶层窗口，
        只对满足**全部**条件的窗口 ShowWindow(SW_HIDE)：
         (a) 窗口类名 == "ConsoleWindowClass"（Windows 控制台黑窗，cmd/powershell）
         (b) HWND 不在 baseline（DSH 启动后**新出现**，排除用户已有的控制台）
         (c) 进程 PID 不是 DSH Desktop 自己
         (d) IsWindowVisible=True（只处理当前可见窗口）
         (e) 是顶层窗口（GetAncestor GA_ROOT）
     3. stop() 关闭扫描线程、释放 baseline。

    **v1.3.7 关键安全修复**：v1.3.6 曾按"是否新出现"一刀切，把用户点"打开DSH"
    后新开的 Edge 浏览器窗口也隐藏了（日志实锤 HWND=18059A 'Microsoft Edge'）。
    现在**必须**类名 == 'ConsoleWindowClass' 才动手——浏览器(Chrome_WidgetWin_1)、
    IDE、资源管理器、截图工具取景遮罩等非控制台窗口绝无可能被隐藏
    （"截图不好用"的根因即为 v1.3.6 误隐藏截图遮罩，v1.3.7 修复后不复现）。

    DSH node.exe 内部 spawn 的 cmd 由 conhost 承载，窗口类名固定为
    ConsoleWindowClass；Windows Terminal 类名是 CASCADIA_HOSTING_WINDOW_CLASS，
    不在处理范围（node 子进程不会走 Windows Terminal，用户主动开的终端也安全）。

    非 Windows 平台自动 no-op。
    """

    SCAN_INTERVAL_MS = 250     # 扫描周期（毫秒）
    _SW_HIDE = 0               # ShowWindow 命令：隐藏
    _GA_ROOT = 2               # GetAncestor 选项：取顶级窗口
    _CONSOLE_CLASS = "ConsoleWindowClass"  # 控制台黑窗类名（v1.3.7 唯一允许隐藏的类）
    MAX_ACTIVE_SECONDS = 30    # 扫描时间窗：DSH 启动后 30 秒内的控制台窗口才隐藏

    def __init__(self, log_fn=None):
        self._log = log_fn or (lambda msg: None)
        self._owner_pid = os.getpid()
        self._baseline: set[int] = set()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._hidden_count = 0  # 累计隐藏数（供 stop 时报告）

    @staticmethod
    def _available() -> bool:
        return os.name == "nt"

    def snapshot_baseline(self):
        """记录当前所有可见顶层窗口 HWND 作为基线。**必须在 spawn 之前调用。**"""
        if not self._available():
            return
        self._baseline = self._enum_visible_top_hwnds()
        self._log(f"[sweeper] 基线已记录：{len(self._baseline)} 个可见窗口")

    def start(self):
        """启动扫描（后台线程）。仅在 snapshot_baseline() 后调用。"""
        if not self._available():
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._hidden_count = 0
        # v1.3.7: 只扫 DSH 启动后的时间窗，避免运行期间用户手动开的 cmd 被误隐藏
        self._deadline = time.monotonic() + self.MAX_ACTIVE_SECONDS
        self._thread = threading.Thread(
            target=self._run, name="WindowSweeper", daemon=True
        )
        self._thread.start()
        self._log(f"[sweeper] 已启动（每 {self.SCAN_INTERVAL_MS}ms 扫描，仅 {self.MAX_ACTIVE_SECONDS}s 时间窗）")

    def stop(self):
        """停止扫描线程、释放资源。"""
        self._stop.set()
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=1.0)
        self._thread = None
        n = self._hidden_count
        self._baseline.clear()
        if n > 0:
            self._log(f"[sweeper] 已停止（本次启动期间共隐藏 {n} 个新窗口）")
        else:
            self._log("[sweeper] 已停止（无新窗口需要隐藏）")

    # ---------- 内部 ----------
    def _run(self):
        """扫描线程主循环。"""
        import ctypes
        from ctypes import wintypes

        u32 = ctypes.windll.user32
        IsWindowVisible = u32.IsWindowVisible
        IsWindowVisible.argtypes = [wintypes.HWND]
        IsWindowVisible.restype = wintypes.BOOL
        GetAncestor = u32.GetAncestor
        GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
        GetAncestor.restype = wintypes.HWND
        GetWindowThreadProcessId = u32.GetWindowThreadProcessId
        GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        GetWindowThreadProcessId.restype = wintypes.DWORD
        ShowWindow = u32.ShowWindow
        ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        ShowWindow.restype = wintypes.BOOL
        GetWindowTextW = u32.GetWindowTextW
        GetWindowTextW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
        GetWindowTextW.restype = ctypes.c_int
        GetClassNameW = u32.GetClassNameW
        GetClassNameW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
        GetClassNameW.restype = ctypes.c_int

        pid_self = self._owner_pid
        baseline = self._baseline
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        buf = ctypes.create_unicode_buffer(256)
        cls_buf = ctypes.create_unicode_buffer(64)

        def proc(hwnd, _lparam):
            try:
                # (d) 只处理当前可见的顶层窗口
                if not IsWindowVisible(hwnd):
                    return True
                root = GetAncestor(hwnd, self._GA_ROOT)
                if root and root != hwnd:
                    return True
                # (c) 绝不碰 DSH Desktop 自己的窗口
                pid = wintypes.DWORD()
                GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == pid_self:
                    return True
                # (a) v1.3.7 关键：只隐藏"控制台黑窗"类，浏览器/IDE/资源管理器/
                #     截图遮罩等非控制台窗口（Chrome_WidgetWin_1 等）绝无可能被隐藏。
                #     这是对 v1.3.6 误隐藏 Edge 窗口（用户点打开DSH 后新开的
                #     浏览器）与截图工具取景遮罩的根因修复。
                if GetClassNameW(hwnd, cls_buf, 64) == 0:
                    return True
                if cls_buf.value != self._CONSOLE_CLASS:
                    return True
                # (b) 只处理 DSH 启动后**新出现**的控制台窗口（排除用户已有的）
                if hwnd in baseline:
                    return True
                # 命中：DSH 启动后新出现的控制台黑窗 → 隐藏
                if ShowWindow(hwnd, self._SW_HIDE):
                    GetWindowTextW(hwnd, buf, 256)
                    self._hidden_count += 1
                    self._log(f"[sweeper] 已隐藏控制台 HWND={int(hwnd):X} 标题={buf.value!r}")
            except Exception:
                pass
            return True

        while not self._stop.is_set():
            # v1.3.7: 超过时间窗后自动退出（避免运行期间用户手动开的 cmd 被误隐藏）
            if time.monotonic() >= self._deadline:
                n = self._hidden_count
                self._log(
                    f"[sweeper] {self.MAX_ACTIVE_SECONDS}s 时间窗结束，自动停止"
                    f"（共隐藏 {n} 个控制台窗口）"
                )
                break
            try:
                u32.EnumWindows(EnumWindowsProc(proc), 0)
            except Exception:
                pass
            # 用 Event.wait 替代 sleep，可被 stop() 立即唤醒
            self._stop.wait(self.SCAN_INTERVAL_MS / 1000.0)

    @classmethod
    def _enum_visible_top_hwnds(cls):
        """枚举所有当前可见顶层窗口 HWND，返回 set（排除 DSH Desktop 自己）。"""
        import ctypes
        from ctypes import wintypes

        u32 = ctypes.windll.user32
        IsWindowVisible = u32.IsWindowVisible
        IsWindowVisible.argtypes = [wintypes.HWND]
        IsWindowVisible.restype = wintypes.BOOL
        GetAncestor = u32.GetAncestor
        GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
        GetAncestor.restype = wintypes.HWND
        GetWindowThreadProcessId = u32.GetWindowThreadProcessId
        GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        GetWindowThreadProcessId.restype = wintypes.DWORD

        pid_self = os.getpid()
        out: list[int] = []
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def proc(hwnd, _lparam):
            try:
                if not IsWindowVisible(hwnd):
                    return True
                root = GetAncestor(hwnd, cls._GA_ROOT)
                if root and root != hwnd:
                    return True
                pid = wintypes.DWORD()
                GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == pid_self:
                    return True
                out.append(int(hwnd))
            except Exception:
                pass
            return True

        try:
            u32.EnumWindows(EnumWindowsProc(proc), 0)
        except Exception:
            pass
        return set(out)
