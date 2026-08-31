"""
DSH Desktop - DeepSeek Harness 桌面控制器

功能：
  - 开启服务：后台执行 `npx -y @deepseek-ai/dsh web --no-open`（Windows 经 cmd.exe 包装）
  - 关闭服务：终止上述进程及其子进程
  - 打开DSH：在默认浏览器中打开 http://127.0.0.1:3080

依赖：仅 Python 3.8+ 标准库（tkinter / subprocess / webbrowser / threading）
"""

import os
import sys
import time
import queue
import socket
import shutil
import webbrowser
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


APP_TITLE = "DSH Desktop"
APP_VERSION = "1.0.9"
DSH_HOST = "127.0.0.1"
DSH_PORT = 3080
DSH_URL = f"http://{DSH_HOST}:{DSH_PORT}"
DSH_CMD_NAME = "npx"
DSH_PACKAGE = "@deepseek-ai/dsh"
DSH_SUBCMD = "web"
DSH_EXTRA_ARGS = ["--no-open"]  # 仅启动服务，不自动打开浏览器（避免与"打开DSH"按钮重复开标签）


def build_start_command() -> list[str]:
    """构造启动命令。

    Windows 上 npx 实际是 npx.cmd 批处理，CreateProcess 无法直接执行，
    必须经 cmd.exe 包装；`-y` 跳过 npx 首次安装包时的交互确认。
    """
    if os.name == "nt":
        return ["cmd", "/c", DSH_CMD_NAME, "-y", DSH_PACKAGE, DSH_SUBCMD, *DSH_EXTRA_ARGS]
    return [DSH_CMD_NAME, "-y", DSH_PACKAGE, DSH_SUBCMD, *DSH_EXTRA_ARGS]


def port_in_use(host: str = DSH_HOST, port: int = DSH_PORT, timeout: float = 0.3) -> bool:
    """探测端口是否已有服务监听（本地回环，开销极小）。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def find_pids_by_port(host: str = DSH_HOST, port: int = DSH_PORT) -> list[int]:
    """通过 PowerShell Get-NetTCPConnection 查找占用指定端口的进程 PID（仅 Windows）。

    优先用 PowerShell（稳定、跨中英文 Windows），失败时回退到 netstat 解析。
    """
    if os.name != "nt":
        return []

    # 主方案：PowerShell Get-NetTCPConnection（Windows 8+ 内置）
    try:
        ps_cmd = (
            f"Get-NetTCPConnection -LocalPort {port} -State Listen "
            f"-ErrorAction SilentlyContinue "
            f"| Select-Object -ExpandProperty OwningProcess -Unique"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
        pids: set[int] = set()
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                pids.add(int(line))
        if pids:
            return sorted(pids)
    except Exception:
        pass

    # 兜底：netstat -ano（兼容中英文 LISTENING 状态字）
    try:
        r = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5,
        )
        pids = set()
        needle = f":{port} "
        for line in r.stdout.splitlines():
            if needle not in line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            # 兼容英文 LISTENING 与中文 Windows 的 "侦听"
            state = parts[-1].upper()
            if state not in ("LISTENING", "侦听".upper()):
                continue
            try:
                pids.add(int(parts[-2]))
            except ValueError:
                pass
        return sorted(pids)
    except Exception:
        return []


def kill_pids(pids: list[int]) -> tuple[bool, str]:
    """通过 taskkill /F /T 批量结束进程树，返回 (全成功, 详情)。"""
    if not pids:
        return False, "无可终止的进程"
    msgs: list[str] = []
    all_ok = True
    for pid in pids:
        try:
            r = subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                text=True,
                encoding="gbk",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            if r.returncode == 0:
                msgs.append(f"PID={pid} 已终止")
            else:
                all_ok = False
                err = (r.stdout or r.stderr or "").strip()
                # 进程已退出不视为失败
                if "找不到进程" in err or "not found" in err.lower():
                    msgs.append(f"PID={pid} 已不存在")
                else:
                    msgs.append(f"PID={pid} 失败：{err[:200]}")
        except Exception as e:
            all_ok = False
            msgs.append(f"PID={pid} 异常：{e}")
    return all_ok, "；".join(msgs)


class DSHController:
    """DSH 服务的子进程管理（所有耗时操作均在后台线程执行）。"""

    def __init__(self):
        self.process: subprocess.Popen | None = None
        self._starting = False  # 启动中（Popen 未完成）标志
        # 可重入锁：避免 start()/stop() 在持锁时调用 is_running 等 property 造成自锁死锁
        self._lock = threading.RLock()
        self._output_callback = None  # 主线程会设置

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self.process is not None and self.process.poll() is None

    @property
    def is_starting(self) -> bool:
        with self._lock:
            return self._starting

    def set_output_callback(self, cb):
        self._output_callback = cb

    def _emit(self, line: str):
        if self._output_callback:
            self._output_callback(line)

    def start(self) -> tuple[bool, str]:
        """异步启动 DSH 服务，立即返回，不阻塞调用线程。

        返回 (False, "PORT_BUSY") 表示端口已被占用（非本控制器启动的实例）。
        """
        with self._lock:
            if self._starting:
                return False, "服务正在启动中，请稍候"
            # 直接检查字段而非调用 is_running，避免锁内再次加锁（RLock 虽可重入但保持清晰）
            if self.process is not None and self.process.poll() is None:
                return False, "服务已经在运行中"

            # 端口已被其他进程占用 → 不必再启动，直接告知
            if not self.is_running and port_in_use():
                return False, "PORT_BUSY"

            npx_path = shutil.which(DSH_CMD_NAME)
            if not npx_path:
                return False, "未找到 npx 命令，请先安装 Node.js"
            self._starting = True

        threading.Thread(target=self._start_worker, daemon=True).start()
        return True, "正在启动 DSH 服务..."

    def _start_worker(self):
        """后台线程：执行 Popen 并接管输出读取。"""
        try:
            creationflags = 0
            if os.name == "nt":
                # Windows：不弹出黑色控制台窗口
                creationflags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                build_start_command(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                bufsize=1,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            self._emit(f"已启动进程 PID={self.process.pid}（首次运行若需下载依赖请耐心等待）")

            threading.Thread(target=self._read_output, daemon=True).start()
        except Exception as e:
            self.process = None
            self._emit(f"启动失败：{e}")
        finally:
            with self._lock:
                self._starting = False

    def _read_output(self):
        if not self.process or not self.process.stdout:
            return
        try:
            for raw in self.process.stdout:
                # 进度条类输出使用 \r 不换行，逐段截断避免刷屏
                for seg in raw.replace("\r", "\n").split("\n"):
                    seg = seg.rstrip()
                    if seg:
                        self._emit(f"[DSH] {seg[:500]}")
        except Exception as e:
            self._emit(f"[读取输出异常] {e}")
        finally:
            try:
                if self.process and self.process.stdout:
                    self.process.stdout.close()
            except Exception:
                pass
            # 进程已退出（非手动停止）：给出明确提示
            with self._lock:
                proc = self.process
            if proc is not None and proc.poll() is not None:
                code = proc.poll()
                self._emit(f"[DSH] 服务进程已退出 (退出码={code})")
                if port_in_use():
                    self._emit("[DSH] 检测到 3080 端口仍有服务监听，可能有外部 DSH 实例在运行")
                elif code not in (0, None):
                    self._emit("[DSH] 若日志含 EADDRINUSE，说明 3080 端口被占用导致启动失败")

    def stop(self) -> tuple[bool, str]:
        """关闭 DSH 服务。"""
        with self._lock:
            if not self.process or self.process.poll() is not None:
                self.process = None
                return False, "服务未运行"

            pid = self.process.pid
            try:
                if os.name == "nt":
                    # Windows：taskkill /F /T 终止进程树
                    result = subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    if result.returncode != 0:
                        return False, f"taskkill 失败：{result.stderr.strip() or result.stdout.strip()}"
                else:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=3)

                # 等待进程真正退出
                try:
                    self.process.wait(timeout=3)
                except Exception:
                    pass

                self.process = None
                return True, f"已关闭服务 (PID={pid})"
            except Exception as e:
                return False, f"关闭失败：{e}"


class DSHDesktopApp:
    """GUI 主类。"""

    BG_COLOR = "#F5F6F8"
    CARD_BG = "#FFFFFF"
    TEXT_COLOR = "#1F2937"
    MUTED_COLOR = "#6B7280"
    SUCCESS_COLOR = "#10B981"
    DANGER_COLOR = "#EF4444"
    PRIMARY_COLOR = "#3B82F6"
    ACCENT_COLOR = "#6366F1"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.controller = DSHController()
        self.controller.set_output_callback(self._on_subprocess_output)
        # 跨线程消息队列：子线程只入队，主线程 after 轮询取出，避免直接操作 tkinter
        self._msg_queue: "queue.Queue[str]" = queue.Queue()

        self._build_window()
        self._build_styles()
        self._build_ui()
        self._bind_close()
        self._refresh_status()
        self._drain_queue()

    # ---------- 窗口 ----------
    def _build_window(self):
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry("520x560")
        self.root.minsize(480, 520)
        self.root.configure(bg=self.BG_COLOR)
        try:
            self.root.iconbitmap(default="")  # 避免无图标时报错
        except Exception:
            pass

    def _build_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Status.TLabel",
            background=self.CARD_BG,
            foreground=self.MUTED_COLOR,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.BG_COLOR,
            foreground=self.TEXT_COLOR,
            font=("Microsoft YaHei UI", 16, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.BG_COLOR,
            foreground=self.MUTED_COLOR,
            font=("Microsoft YaHei UI", 9),
        )

    # ---------- UI ----------
    def _build_ui(self):
        # 顶部标题
        header = tk.Frame(self.root, bg=self.BG_COLOR)
        header.pack(fill="x", padx=24, pady=(20, 12))

        ttk.Label(
            header,
            text="DSH Desktop",
            style="Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text=f"DeepSeek Harness 桌面控制器 · v{APP_VERSION}",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        # 状态卡片
        status_card = tk.Frame(self.root, bg=self.CARD_BG, bd=0, highlightthickness=0)
        status_card.pack(fill="x", padx=24, pady=(4, 12))
        # 圆角替代：用 Canvas 模拟，简单起见用 Frame + padding
        inner = tk.Frame(status_card, bg=self.CARD_BG)
        inner.pack(fill="x", padx=16, pady=14)

        self.status_dot = tk.Canvas(inner, width=14, height=14, bg=self.CARD_BG, highlightthickness=0)
        self.status_dot.pack(side="left")
        self._draw_dot(self.MUTED_COLOR)

        self.status_text = tk.Label(
            inner,
            text="服务状态：未运行",
            bg=self.CARD_BG,
            fg=self.TEXT_COLOR,
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.status_text.pack(side="left", padx=(10, 0))

        self.url_text = tk.Label(
            inner,
            text="",
            bg=self.CARD_BG,
            fg=self.MUTED_COLOR,
            font=("Consolas", 10),
        )
        self.url_text.pack(side="right")

        # 按钮区
        btn_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        btn_frame.pack(fill="x", padx=24, pady=(4, 12))

        self.btn_start = self._make_button(
            btn_frame, "开启服务", self.SUCCESS_COLOR, self._on_start
        )
        self.btn_start.pack(fill="x", pady=6, ipady=10)

        self.btn_stop = self._make_button(
            btn_frame, "关闭服务", self.DANGER_COLOR, self._on_stop
        )
        self.btn_stop.pack(fill="x", pady=6, ipady=10)

        self.btn_open = self._make_button(
            btn_frame, "打开DSH", self.PRIMARY_COLOR, self._on_open
        )
        self.btn_open.pack(fill="x", pady=6, ipady=10)

        # 日志区
        log_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        log_frame.pack(fill="both", expand=True, padx=24, pady=(4, 20))

        ttk.Label(
            log_frame,
            text="运行日志",
            background=self.BG_COLOR,
            foreground=self.MUTED_COLOR,
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(0, 4))

        log_box = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Consolas", 9),
            bg="#1F2937",
            fg="#E5E7EB",
            insertbackground="#E5E7EB",
            relief="flat",
            bd=0,
            state="disabled",
        )
        log_box.pack(fill="both", expand=True)
        self.log_box = log_box

    def _make_button(self, parent, text, color, command):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        # hover 效果
        hover_color = self._lighten(color, 0.1)
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def _lighten(self, hex_color, amount):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return f"#{r:02X}{g:02X}{b:02X}"

    # ---------- 事件 ----------
    def _on_start(self):
        ok, msg = self.controller.start()
        if msg == "PORT_BUSY":
            self._log(f"启动失败：端口 {DSH_PORT} 已被占用，可能已有 DSH 实例在运行")
            if messagebox.askyesno(
                "端口已被占用",
                f"检测到 {DSH_HOST}:{DSH_PORT} 已被占用，\n"
                "可能已有 DSH 实例在运行。\n\n是否直接打开浏览器访问？",
            ):
                self._on_open()
            return
        if not ok:
            self._log(f"启动失败：{msg}")
            messagebox.showerror("启动失败", msg)
        self._refresh_status()

    def _on_stop(self):
        # 1) 本控制器管理的进程存在 → 直接 taskkill
        if self.controller.is_running:
            self._log("正在关闭 DSH 服务...")
            ok, msg = self.controller.stop()
            self._log(msg)
            if not ok:
                messagebox.showerror("关闭失败", msg)
            self._refresh_status()
            return

        # 2) 端口被外部实例占用 → 二次确认后用 netstat 找 PID 再 taskkill /T /F
        if port_in_use():
            pids = find_pids_by_port()
            if not pids:
                self._log("端口仍占用但未找到对应进程（可能是 TIME_WAIT/权限不足）")
                messagebox.showwarning(
                    "未找到进程",
                    f"{DSH_HOST}:{DSH_PORT} 仍显示占用，但无法定位进程 PID。\n"
                    "可尝试以管理员身份运行本应用，或手动结束进程。",
                )
                self._refresh_status()
                return
            detail = "、".join(str(p) for p in pids)
            if not messagebox.askyesno(
                "关闭外部 DSH 服务",
                f"检测到端口 {DSH_PORT} 被以下进程占用：\n  PID = {detail}\n\n"
                "将结束这些进程及其子进程树，是否继续？",
            ):
                return
            self._log(f"正在关闭外部 DSH 实例：{detail}")
            ok, msg = kill_pids(pids)
            self._log(f"关闭结果：{msg}")
            # 等待端口真正释放
            for _ in range(10):
                if not port_in_use():
                    break
                time.sleep(0.3)
            if port_in_use():
                self._log("端口仍被占用，关闭可能未生效")
                messagebox.showwarning("关闭未生效", "端口仍被占用，请检查权限或手动结束进程。")
            elif ok:
                messagebox.showinfo("已关闭", f"已关闭外部 DSH 服务：{detail}")
            self._refresh_status()
            return

        # 3) 都没跑
        self._log("服务未运行，无需关闭")
        self._refresh_status()

    def _on_open(self):
        self._log(f"正在打开 {DSH_URL}")
        try:
            webbrowser.open(DSH_URL)
            self._log("已调用系统默认浏览器打开 DSH")
        except Exception as e:
            self._log(f"打开失败：{e}")
            messagebox.showerror("打开失败", str(e))

    def _on_subprocess_output(self, line: str):
        # 子线程调用：只入队，不触碰 tkinter，保证线程安全
        try:
            self._msg_queue.put(line)
        except Exception:
            pass

    def _drain_queue(self):
        """主线程轮询消息队列，将子进程输出写入日志（每轮限流，避免刷屏卡顿）。"""
        drained = 0
        try:
            while drained < 300:
                line = self._msg_queue.get_nowait()
                self._log(line)
                drained += 1
        except queue.Empty:
            pass
        try:
            self.root.after(100, self._drain_queue)
        except RuntimeError:
            pass  # 窗口已关闭

    def _bind_close(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        running = self.controller.is_running
        starting = self.controller.is_starting
        if running or starting:
            if not messagebox.askyesno(
                "确认退出",
                "DSH 服务正在运行/启动中。\n退出将尝试关闭该服务，是否继续？",
            ):
                return
            ok, msg = self.controller.stop()
            self._log(msg)
        self.root.destroy()

    # ---------- 状态与日志 ----------
    def _draw_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 12, 12, fill=color, outline=color)

    def _refresh_status(self):
        if self.controller.is_starting:
            # 启动中：所有按钮禁用，等待 Popen 完成
            self._draw_dot("#F59E0B")  # 琥珀色
            self.status_text.config(text="服务状态：启动中...", fg="#B45309")
            self.url_text.config(text="")
            self.btn_start.config(state="disabled", bg="#9CA3AF")
            self.btn_stop.config(state="disabled", bg="#9CA3AF")
        elif self.controller.is_running:
            self._draw_dot(self.SUCCESS_COLOR)
            self.status_text.config(text="服务状态：运行中", fg=self.SUCCESS_COLOR)
            self.url_text.config(text=DSH_URL)
            self.btn_start.config(state="disabled", bg="#9CA3AF")
            self.btn_stop.config(state="normal", bg=self.DANGER_COLOR)
        elif port_in_use():
            # 本控制器未启动进程，但端口已有服务监听（外部实例）
            # 关闭按钮可用 → 可强制结束外部进程
            self._draw_dot(self.SUCCESS_COLOR)
            self.status_text.config(text="服务状态：运行中（外部实例）", fg=self.SUCCESS_COLOR)
            self.url_text.config(text=DSH_URL)
            self.btn_start.config(state="disabled", bg="#9CA3AF")
            self.btn_stop.config(state="normal", bg=self.DANGER_COLOR)
        else:
            self._draw_dot(self.MUTED_COLOR)
            self.status_text.config(text="服务状态：未运行", fg=self.TEXT_COLOR)
            self.url_text.config(text="")
            self.btn_start.config(state="normal", bg=self.SUCCESS_COLOR)
            self.btn_stop.config(state="disabled", bg="#9CA3AF")
        # 定期刷新（用于检测进程异常退出 / 端口状态变化）
        try:
            self.root.after(1000, self._refresh_status)
        except RuntimeError:
            pass

    def _log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        try:
            self.log_box.config(state="normal")
            self.log_box.insert("end", line)
            # 日志区行数上限，防止无限增长
            if int(self.log_box.index("end-1c").split(".")[0]) > 1000:
                self.log_box.delete("1.0", "100.0")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        except (tk.TclError, AttributeError):
            pass


def main():
    root = tk.Tk()
    DSHDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
