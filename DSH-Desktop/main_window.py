"""
DSH-Desktop 主窗口（v1.4.0 模块化重构，归属 DSH-Desktop v1.4.0）。

DSHDesktopApp：GUI 布局（banner → 状态卡 → 动作按钮 → 嵌入式终端 → 状态栏）、
事件处理（开启/关闭/打开、复制 URL/安装命令、导出/清空日志）、
跨线程消息队列驱动日志、版本感知、定时状态刷新。

依赖：tkinter + 标准库；引用 app_config（常量）、dsh_core（服务核心）、
ui_widgets（通用组件）、dialogs（对话框）。
"""

import os
import queue
import threading
import time
import webbrowser

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from app_config import (
    APP_TITLE,
    APP_VERSION,
    DSH_HOST,
    DSH_PORT,
    DSH_URL,
    DSH_PACKAGE,
    _VERSION_MSG_PREFIX,
)
from dsh_core import (
    app_log_dir,
    DSHController,
    fetch_latest_dsh_version,
    find_pids_by_port,
    kill_pids,
    plugins_changed,
    port_in_use,
    save_plugin_fingerprint,
    scan_local_plugins,
)
from ui_widgets import RoundButton, build_rounded_card, _draw_gradient
from dialogs import PluginScanDialog


class DSHDesktopApp:
    """GUI 主类（v1.2.0 品牌视觉改版）。"""

    BG_COLOR = "#F5F7FB"
    CARD_BG = "#FFFFFF"
    TEXT_COLOR = "#1F2430"
    MUTED_COLOR = "#7A8494"
    SUCCESS_COLOR = "#16A34A"
    DANGER_COLOR = "#DC2626"
    PRIMARY_COLOR = "#4D6BFE"  # DeepSeek 品牌蓝
    WARN_COLOR = "#B45309"
    BANNER_TOP = "#16233A"
    BANNER_BOTTOM = "#2C3E68"
    LOG_BG = "#101826"
    LOG_FG = "#D7DFEB"
    STATUSBAR_BG = "#E9ECF3"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.controller = DSHController()
        self.controller.set_output_callback(self._on_subprocess_output)
        # 跨线程消息队列：子线程只入队，主线程 after 轮询取出，避免直接操作 tkinter
        # 有界队列：防日志洪峰时无限积压导致内存膨胀（满则丢弃新日志，可接受）
        self._msg_queue: "queue.Queue[str]" = queue.Queue(maxsize=5000)
        self._started_at: float | None = None  # 服务启动时刻（用于状态栏运行时长）
        self._log_file = self._open_log_file()  # v1.4.1: 本次运行日志自动落盘到 log/

        self._build_window()
        self._build_styles()
        self._build_ui()
        self._bind_close()
        self._refresh_status()
        self._drain_queue()
        self._check_version()  # 后台查询官方 latest 版本，不阻塞 UI

    # ---------- 窗口 ----------
    def _build_window(self):
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        # v1.3.8: 终端区改为随窗口伸缩（expand），高度不再需要写死；
        # 默认 800 高时终端区自动填满剩余空间，窗口调小时自动收缩
        w, h = 560, 800
        self.root.minsize(520, 680)
        self.root.configure(bg=self.BG_COLOR)
        # 启动时窗口居中
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
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
        # v1.3.8 布局：终端区移到按钮下方、状态栏上方，并 expand 吸收剩余空间
        # 顺序：banner → status_card → actions → log(expand, 底部)
        # v1.3.5 曾把 log 放在按钮上方（fixed 320px）；v1.3.8 改回按钮下方，
        # 去掉固定高度——终端区自动填充窗口剩余空间，无多余空白。
        # 状态栏仍 side=bottom 优先 pack，避免挤压上方固定区域
        self._build_statusbar()
        self._build_header()
        self._build_status_card()
        self._build_actions()
        self._build_log()

    def _build_header(self):
        """顶部品牌渐变横幅。v1.3.8: 高 96→64，标题下方不再留大块空白。"""
        self.banner = tk.Canvas(self.root, height=64, bg=self.BG_COLOR, highlightthickness=0, bd=0)
        self.banner.pack(fill="x")
        self.banner.bind("<Configure>", self._draw_banner)

    def _draw_banner(self, event=None):
        w = self.banner.winfo_width()
        h = self.banner.winfo_height()
        if w <= 1:
            return
        self.banner.delete("all")
        _draw_gradient(self.banner, w, h, self.BANNER_TOP, self.BANNER_BOTTOM)
        # 左侧品牌竖条 + 标题（v1.3.8: 坐标上移适配 64px 高度）
        self.banner.create_rectangle(24, 14, 30, 50, fill=self.PRIMARY_COLOR, outline="")
        self.banner.create_text(46, 14, text=APP_TITLE, anchor="nw", fill="#FFFFFF",
                                font=("Microsoft YaHei UI", 18, "bold"))
        self.banner.create_text(46, 44, text="DeepSeek Harness 桌面控制器", anchor="nw",
                                fill="#A8B4CC", font=("Microsoft YaHei UI", 9))
        # 右侧版本号
        self.banner.create_text(w - 20, 14, text=f"v{APP_VERSION}", anchor="ne",
                                fill="#8FA3C9", font=("Microsoft YaHei UI", 9))
        # 右侧状态小字：端口
        self.banner.create_text(w - 20, 44, text=f"{DSH_HOST}:{DSH_PORT}", anchor="ne",
                                fill="#6B7FA3", font=("Consolas", 9))

    def _build_status_card(self):
        """状态卡片：状态灯 + 状态文本 + URL（可复制）+ 官方版本 + 徽标 + 复制安装命令。"""
        # v1.3.8: 卡片高 116→96，与上下区块间距收窄，去除多余空白
        self.status_canvas, card_inner = build_rounded_card(self.root, height=96)
        self.status_canvas.pack(fill="x", padx=20, pady=(6, 2))

        # 第一行：状态点 + 状态文本 + URL
        row1 = tk.Frame(card_inner, bg=self.CARD_BG)
        row1.pack(fill="x")
        self.status_dot = tk.Canvas(row1, width=14, height=14, bg=self.CARD_BG, highlightthickness=0)
        self.status_dot.pack(side="left")
        self._draw_dot(self.MUTED_COLOR)

        self.status_text = tk.Label(
            row1, text="服务状态：未运行", bg=self.CARD_BG, fg=self.TEXT_COLOR,
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.status_text.pack(side="left", padx=(10, 0))

        self.url_text = tk.Label(
            row1, text="", bg=self.CARD_BG, fg=self.PRIMARY_COLOR,
            font=("Consolas", 10), cursor="hand2",
        )
        self.url_text.pack(side="right")
        self.url_text.bind("<Button-1>", self._copy_url)

        # 第二行：官方版本 + 预览徽标 + 复制安装命令
        row2 = tk.Frame(card_inner, bg=self.CARD_BG)
        row2.pack(fill="x", pady=(6, 0))

        self.version_text = tk.Label(
            row2, text="DSH 官方版本：检查中...", bg=self.CARD_BG, fg=self.MUTED_COLOR,
            font=("Microsoft YaHei UI", 9),
        )
        self.version_text.pack(side="left")

        self.version_badge = tk.Label(
            row2, text="", bg="#FEF3C7", fg=self.WARN_COLOR, padx=6, pady=1,
            font=("Microsoft YaHei UI", 8, "bold"),
        )
        self.version_badge.pack(side="left", padx=(6, 0))

        self.copy_cmd_btn = tk.Label(
            row2, text="[复制安装命令]", bg=self.CARD_BG, fg=self.PRIMARY_COLOR,
            font=("Microsoft YaHei UI", 8), cursor="hand2",
        )
        self.copy_cmd_btn.pack(side="right")
        self.copy_cmd_btn.bind("<Button-1>", self._copy_install_cmd)

    def _build_actions(self):
        """三个圆角大按钮。"""
        actions = tk.Frame(self.root, bg=self.BG_COLOR)
        actions.pack(fill="x", padx=20, pady=(2, 6))

        self.btn_start = RoundButton(actions, "开启服务", self.SUCCESS_COLOR, self._on_start)
        self.btn_start.pack(fill="x", pady=5)
        self.btn_stop = RoundButton(actions, "关闭服务", self.DANGER_COLOR, self._on_stop)
        self.btn_stop.pack(fill="x", pady=5)
        self.btn_open = RoundButton(actions, "打开DSH", self.PRIMARY_COLOR, self._on_open)
        self.btn_open.pack(fill="x", pady=5)

    def _build_log(self):
        """嵌入式终端区（v1.3.8：移到按钮下方并随窗口伸缩）。

        位置：三个动作按钮下方、状态栏上方，expand 自动填充剩余空间
        （v1.3.5/1.3.6 曾固定在按钮上方 320px；v1.3.8 改回按钮下方并去固定高度）。
        配合窗口清道夫（WindowSweeper）让 DSH 启动时弹出的额外 cmd.exe 黑窗
        被自动隐藏后，本区域成为唯一的终端视图，看起来就像终端被嵌进了软件。
        """
        # 外层：给整个终端区一个圆角浅色边框 + 阴影背景，让它像嵌入的真终端
        terminal_frame = tk.Frame(
            self.root, bg="#1A2236",  # 深色边框（与 LOG_BG 同色系略亮）
            padx=1, pady=1,
        )
        # v1.3.8: 去掉固定 height=320 与 pack_propagate(False)，
        # 改为 expand 填充窗口剩余空间（窗口缩放时终端区自适应伸缩）
        terminal_frame.pack(fill="both", expand=True, padx=20, pady=(8, 4))

        # 内层：终端内容容器（深色）
        inner = tk.Frame(terminal_frame, bg=self.LOG_BG)
        inner.pack(fill="both", expand=True)

        # 顶部装饰条：三个圆点（仿 macOS 终端标题栏）+ 标题 + 清空/导出
        bar = tk.Frame(inner, bg="#1A2236", height=22)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # 左侧三个圆点（红/黄/绿，装饰用，不可点）
        dots = tk.Frame(bar, bg="#1A2236")
        dots.pack(side="left", padx=8, pady=6)
        for c in ("#FF5F57", "#FEBC2E", "#28C840"):
            tk.Label(dots, text="●", bg="#1A2236", fg=c,
                     font=("Microsoft YaHei UI", 8)).pack(side="left", padx=2)

        tk.Label(
            bar, text="  DSH 终端（嵌入式）", bg="#1A2236", fg="#7A8494",
            font=("Microsoft YaHei UI", 9, "bold"),
        ).pack(side="left")

        # 右侧操作按钮
        export_btn = tk.Label(
            bar, text="导出", bg="#1A2236", fg="#9AA4B5",
            font=("Microsoft YaHei UI", 8), cursor="hand2",
        )
        export_btn.pack(side="right", padx=8)
        export_btn.bind("<Button-1>", lambda e: self._export_log())

        clear_btn = tk.Label(
            bar, text="清空", bg="#1A2236", fg=self.PRIMARY_COLOR,
            font=("Microsoft YaHei UI", 8), cursor="hand2",
        )
        clear_btn.pack(side="right")
        clear_btn.bind("<Button-1>", lambda e: self._clear_log())

        # 终端内容区（深色 + 等宽字体 + 加大行间距 + 加大字号）
        log_box = scrolledtext.ScrolledText(
            inner,
            height=14,
            font=("Consolas", 10),
            bg=self.LOG_BG,
            fg=self.LOG_FG,
            insertbackground=self.LOG_FG,
            relief="flat",
            bd=0,
            padx=8, pady=6,
            spacing1=1, spacing3=2,  # 行间距，让输出更易读
            state="disabled",
        )
        log_box.pack(fill="both", expand=True)
        self.log_box = log_box

    def _build_statusbar(self):
        """底部状态栏：端口（左）+ PID/运行时长（右）。"""
        bar = tk.Frame(self.root, bg=self.STATUSBAR_BG, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.sb_left = tk.Label(
            bar, text=f"端口 {DSH_HOST}:{DSH_PORT}", bg=self.STATUSBAR_BG,
            fg=self.MUTED_COLOR, font=("Microsoft YaHei UI", 8),
        )
        self.sb_left.pack(side="left", padx=12)
        self.sb_right = tk.Label(
            bar, text="", bg=self.STATUSBAR_BG, fg=self.MUTED_COLOR,
            font=("Microsoft YaHei UI", 8),
        )
        self.sb_right.pack(side="right", padx=12)

    # ---------- 事件 ----------
    def _on_start(self):
        # 便携插件：仅在 dsh-Plugin/ 有改动时弹窗让用户勾选注册（取消/跳过 = 不注册直接启动）；
        # 无改动直接启动，避免每次多点一次
        pending = None
        # 扫描为空（dsh-Plugin 不存在/无可用插件）则跳过弹窗
        try:
            scanned = scan_local_plugins()
        except Exception:
            scanned = []
        if scanned:
            try:
                changed, fp = plugins_changed()
            except Exception:
                # 指纹状态异常按"有改动"处理，仍弹窗；不保存指纹
                changed, fp = True, None
            if changed:
                try:
                    dlg = PluginScanDialog(self.root)
                    pending = dlg.result
                except Exception as e:
                    self._log(f"插件管理窗异常（将直接启动）：{e}")
                # 已展示过插件窗，无论确认/跳过都记录新指纹，下次无新改动不再弹
                if fp:
                    save_plugin_fingerprint(fp)
            else:
                not_installed = [it for it in scanned if not it.get("installed")]
                extra = f"，其中 {len(not_installed)} 个未安装" if not_installed else ""
                self._log(f"便携插件：{len(scanned)} 个插件无改动{extra}，直接启动")
        if pending:
            names = ", ".join(it.get("name", it.get("dir", "?")) for it in pending)
            self._log(f"便携插件：勾选 {len(pending)} 个 → {names}，启动时自动注册")

        ok, msg = self.controller.start(pending_plugins=pending)
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
            if os.name == "nt":
                # Windows 下直接 ShellExecute 打开默认浏览器，不经 cmd 中转，不弹黑窗
                os.startfile(DSH_URL)
            else:
                webbrowser.open(DSH_URL)
            self._log("已调用系统默认浏览器打开 DSH")
        except Exception as e:
            self._log(f"打开失败：{e}")
            messagebox.showerror("打开失败", str(e))

    def _copy_url(self, _event=None):
        if not self.url_text.cget("text"):
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(DSH_URL)
        self._log(f"已复制 {DSH_URL} 到剪贴板")
        self.url_text.config(fg=self.SUCCESS_COLOR)
        self.root.after(1200, lambda: self.url_text.config(fg=self.PRIMARY_COLOR))

    def _copy_install_cmd(self, _event=None):
        cmd = f"npm install -g {DSH_PACKAGE}@latest"
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd)
        self._log(f"已复制安装命令：{cmd}")

    def _clear_log(self):
        try:
            self.log_box.config(state="normal")
            self.log_box.delete("1.0", "end")
            self.log_box.config(state="disabled")
        except (tk.TclError, AttributeError):
            pass

    def _export_log(self):
        """把当前日志区内容导出到用户指定位置的 .log 文件。"""
        try:
            self.log_box.config(state="normal")
            content = self.log_box.get("1.0", "end").strip()
            self.log_box.config(state="disabled")
        except (tk.TclError, AttributeError):
            return

        if not content:
            messagebox.showinfo("导出日志", "当前日志为空，无需导出。")
            return

        from datetime import datetime
        default_name = f"dsh-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

        # v1.4.1: 默认保存到应用日志文件夹 log/（仍可在弹窗中改选其他位置）
        initial_dir = app_log_dir()

        path = filedialog.asksaveasfilename(
            title="导出日志",
            defaultextension=".log",
            initialdir=initial_dir,
            initialfile=default_name,
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._log(f"日志已导出：{path}")
        except OSError as e:
            messagebox.showerror("导出失败", f"写入文件失败：{e}")

    def _on_subprocess_output(self, line: str):
        # 子线程调用：只入队，不触碰 tkinter，保证线程安全
        try:
            self._msg_queue.put_nowait(line)
        except queue.Full:
            pass  # 队列满则丢弃新日志，防内存膨胀与 drain 风暴

    # ---------- 版本感知 ----------
    def _check_version(self):
        """后台线程查询官方 latest 版本，结果经消息队列回传主线程。"""
        threading.Thread(target=self._version_worker, daemon=True).start()

    def _version_worker(self):
        v = fetch_latest_dsh_version()
        if v:
            try:
                self._msg_queue.put_nowait(f"{_VERSION_MSG_PREFIX}{v}")
            except queue.Full:
                pass

    def _show_version(self, version: str):
        self.version_text.config(text=f"DSH 官方版本：v{version}（npm latest）", fg=self.MUTED_COLOR)
        # rc/alpha/beta/next 等预发布版本标记"预览版"徽标
        low = version.lower()
        if any(tag in low for tag in ("rc", "alpha", "beta", "next", "dev")):
            self.version_badge.config(text="预览版")
        else:
            self.version_badge.config(text="")

    def _drain_queue(self):
        """主线程轮询消息队列，批量写入日志（合并 insert/see，避免高频重绘卡顿）。"""
        lines: list[str] = []
        try:
            while len(lines) < 200:
                line = self._msg_queue.get_nowait()
                if line.startswith(_VERSION_MSG_PREFIX):
                    self._show_version(line[len(_VERSION_MSG_PREFIX):])
                    continue
                lines.append(line)
        except queue.Empty:
            pass
        if lines:
            self._log_lines(lines)
        try:
            self.root.after(100, self._drain_queue)
        except RuntimeError:
            pass  # 窗口已关闭

    def _log_lines(self, lines: list[str]):
        """批量写入多行日志：一次 insert + 一次行数裁剪 + 一次滚动。

        避免逐条 _log() 时高频 Text.insert/delete/see 导致 GUI 卡死
        （DSH 启动日志洪峰场景，如 pnpm 下载依赖时可上万行/秒）。
        """
        try:
            ts = time.strftime("%H:%M:%S")
            payload = "".join(f"[{ts}] {ln}\n" for ln in lines)
            self.log_box.config(state="normal")
            self.log_box.insert("end", payload)
            # 行数上限：超过则整体裁剪（一次 delete，替代逐行检查）
            if int(self.log_box.index("end-1c").split(".")[0]) > 1000:
                self.log_box.delete("1.0", "100.0")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        except (tk.TclError, AttributeError):
            pass
        self._write_log_file(payload)

    def _bind_close(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- 运行日志自动落盘（v1.4.1）----------
    def _open_log_file(self):
        """本次运行自动落盘日志文件：log/dsh-run-YYYYmmdd-HHMMSS.log。"""
        from datetime import datetime
        try:
            path = os.path.join(
                app_log_dir(),
                f"dsh-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
            )
            return open(path, "a", encoding="utf-8")
        except OSError:
            return None

    def _write_log_file(self, text: str):
        """把日志内容同步写入自动落盘文件（失败静默，不影响 GUI）。"""
        f = getattr(self, "_log_file", None)
        if f is None:
            return
        try:
            f.write(text)
            f.flush()
        except OSError:
            pass

    def _close_log_file(self):
        f = getattr(self, "_log_file", None)
        if f is not None:
            try:
                f.close()
            except OSError:
                pass
            self._log_file = None

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
        self._close_log_file()
        self.root.destroy()

    # ---------- 状态与日志 ----------
    def _draw_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 12, 12, fill=color, outline=color)

    def _update_statusbar(self, pid):
        if pid:
            el = int(time.time() - self._started_at) if self._started_at else 0
            self.sb_right.config(
                text=f"PID {pid} · 运行 {el // 3600:02d}:{(el % 3600) // 60:02d}:{el % 60:02d}"
            )
        else:
            self.sb_right.config(text="")

    def _refresh_status(self):
        if self.controller.is_starting:
            # 启动中：所有按钮禁用，等待 Popen 完成
            self._draw_dot("#F59E0B")  # 琥珀色
            self.status_text.config(text="服务状态：启动中...", fg="#B45309")
            self.url_text.config(text="")
            self.btn_start.set_enabled(False)
            self.btn_stop.set_enabled(False)
            self._update_statusbar(None)
        elif self.controller.is_running:
            if self._started_at is None:
                self._started_at = time.time()
            self._draw_dot(self.SUCCESS_COLOR)
            self.status_text.config(text="服务状态：运行中", fg=self.SUCCESS_COLOR)
            self.url_text.config(text=DSH_URL)
            self.btn_start.set_enabled(False)
            self.btn_stop.set_enabled(True)
            pid = self.controller.process.pid if self.controller.process else None
            self._update_statusbar(pid)
        elif port_in_use():
            # 本控制器未启动进程，但端口已有服务监听（外部实例）
            # 关闭按钮可用 → 可强制结束外部进程
            self._draw_dot(self.SUCCESS_COLOR)
            self.status_text.config(text="服务状态：运行中（外部实例）", fg=self.SUCCESS_COLOR)
            self.url_text.config(text=DSH_URL)
            self.btn_start.set_enabled(False)
            self.btn_stop.set_enabled(True)
            self._update_statusbar(None)
        else:
            self._started_at = None
            self._draw_dot(self.MUTED_COLOR)
            self.status_text.config(text="服务状态：未运行", fg=self.TEXT_COLOR)
            self.url_text.config(text="")
            self.btn_start.set_enabled(True)
            self.btn_stop.set_enabled(False)
            self._update_statusbar(None)
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
        self._write_log_file(line)
