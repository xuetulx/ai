"""
DSH-Desktop 对话框（v1.4.0 模块化重构，归属 DSH-Desktop v1.4.0）。

目前包含：便携插件管理弹窗 PluginScanDialog（v1.3.0）——
扫描 dsh-Plugin/ 下可识别插件、勾选注册到 web profile。

依赖：tkinter；引用 ui_widgets（RoundButton）与 dsh_core（scan_local_plugins）。
"""

import tkinter as tk
from tkinter import ttk

from ui_widgets import RoundButton
from dsh_core import scan_local_plugins


class PluginScanDialog:
    """扫描本地便携插件并让用户勾选注册的对话框（v1.3.0）。

    弹窗列出 dsh-Plugin/ 下所有可识别插件，显示名称/版本/已安装状态，
    DEFAULT_LOCAL_PLUGINS 中的默认勾选，其余默认不勾。用户可改选后确认。
    结果经 self.result（list[dict]）返回所选插件项；取消则返回 None。
    """

    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.result: list[dict] | None = None
        self._vars: list[tk.BooleanVar] = []
        self._items: list[dict] = []
        self.top: tk.Toplevel | None = None

        try:
            self.top = tk.Toplevel(parent)
            self.top.title("便携插件管理")
            self.top.configure(bg="#F5F7FB")
            self.top.transient(parent)
            self.top.resizable(True, True)
            w, h = 520, 460
            self.top.minsize(460, 360)
            sw = parent.winfo_screenwidth()
            sh = parent.winfo_screenheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.top.geometry(f"{w}x{h}+{x}+{y}")

            self._build_ui()
            # grab 必须在 _build_ui 成功后才设置，否则异常会留下持 grab 的幽灵窗口
            self.top.grab_set()
            self.top.protocol("WM_DELETE_WINDOW", self._cancel)
            self.top.bind("<Escape>", lambda e: self._cancel())
            self.top.wait_window()
        except Exception:
            # 任何异常都确保销毁窗口、释放 grab，避免幽灵窗口卡死主窗口
            if self.top is not None:
                try:
                    self.top.grab_release()
                except Exception:
                    pass
                try:
                    self.top.destroy()
                except Exception:
                    pass
                self.top = None
            self.result = None
            raise

    def _build_ui(self):
        c = "#F5F7FB"
        # 标题
        head = tk.Frame(self.top, bg=c)
        head.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(head, text="便携插件注册", bg=c, fg="#1F2430",
                 font=("Microsoft YaHei UI", 13, "bold")).pack(side="left")
        hint = tk.Label(
            head, text="勾选要注册到 web profile 的本地插件，确认后随服务启动。",
            bg=c, fg="#7A8494", font=("Microsoft YaHei UI", 9), wraplength=460, justify="left",
        )
        hint.pack(side="left", padx=(8, 0))

        # 列表区（滚动）
        list_frame = tk.Frame(self.top, bg=c)
        list_frame.pack(fill="both", expand=True, padx=16, pady=8)
        canvas = tk.Canvas(list_frame, bg=c, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=c)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._canvas = canvas

        items = scan_local_plugins()
        if not items:
            tk.Label(inner, text="（未在 dsh-Plugin/ 下找到任何含 package.json 的插件目录）",
                     bg=c, fg="#B45309", font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=10)
        for it in items:
            row = tk.Frame(inner, bg="#FFFFFF", relief="flat", bd=0)
            row.pack(fill="x", pady=4, ipadx=8, ipady=6)
            var = tk.BooleanVar(value=bool(it["default_on"] or it["installed"]))
            self._vars.append(var)
            self._items.append(it)
            cb = tk.Checkbutton(row, variable=var, bg="#FFFFFF", activebackground="#FFFFFF",
                                selectcolor="#FFFFFF", bd=0, highlightthickness=0)
            cb.pack(side="left", padx=(6, 4))
            name_txt = f"{it['name']}  v{it['version']}" if it["version"] else it["name"]
            tk.Label(row, text=name_txt, bg="#FFFFFF", fg="#1F2430",
                     font=("Microsoft YaHei UI", 10, "bold")).pack(side="left")
            tag = "已安装" if it["installed"] else "未安装"
            tag_fg = "#16A34A" if it["installed"] else "#B45309"
            tk.Label(row, text=tag, bg="#FFFFFF", fg=tag_fg,
                     font=("Microsoft YaHei UI", 8)).pack(side="left", padx=(8, 0))
            if it["description"]:
                tk.Label(row, text=it["description"][:60], bg="#FFFFFF", fg="#7A8494",
                         font=("Microsoft YaHei UI", 8), wraplength=360, justify="left").pack(
                         side="left", padx=(6, 0))

        # 鼠标滚轮
        self.top.bind("<MouseWheel>",
                      lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        # 底部按钮
        btns = tk.Frame(self.top, bg=c)
        btns.pack(fill="x", padx=16, pady=(4, 12))
        tk.Label(btns, text="Esc/关闭 = 跳过直接启动\n注册将执行插件安装脚本，仅勾选可信插件",
                 bg=c, fg="#7A8494", justify="left",
                 font=("Microsoft YaHei UI", 8)).pack(side="left")
        b_ok = RoundButton(btns, "注册并启动", "#16A34A", self._confirm)
        b_ok.pack(side="right", padx=(6, 0))
        b_skip = RoundButton(btns, "跳过", "#7A8494", self._cancel)
        b_skip.pack(side="right")

    def _confirm(self):
        self.result = [it for it, v in zip(self._items, self._vars) if v.get()]
        self.top.grab_release()
        self.top.destroy()

    def _cancel(self):
        self.result = None
        self.top.grab_release()
        self.top.destroy()
