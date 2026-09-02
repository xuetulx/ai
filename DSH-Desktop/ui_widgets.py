"""
DSH-Desktop UI 通用组件（v1.4.0 模块化重构，归属 DSH-Desktop v1.4.0）。

与业务无关的可复用 GUI 组件：颜色工具、渐变/圆角绘制、圆角卡片、
圆角按钮、启动 Splash 画面。仅依赖 app_config（应用元信息）。

依赖：仅 Python 3.8+ 标准库（tkinter）；引用 app_config（常量）。
"""

import tkinter as tk

from app_config import APP_TITLE, APP_VERSION


def _lighten(hex_color: str, amount: float) -> str:
    """颜色变亮 amount（0~1），返回 #RRGGBB。"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02X}{g:02X}{b:02X}"


def _round_rect_points(x1, y1, x2, y2, radius):
    """生成圆角矩形多边形顶点（配合 smooth=True 渲染圆角）。"""
    r = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


def _draw_gradient(canvas, w, h, top_color, bottom_color, steps: int = 48):
    """在 canvas 上绘制竖向渐变（top_color → bottom_color）。"""
    r1, g1, b1 = int(top_color[1:3], 16), int(top_color[3:5], 16), int(top_color[5:7], 16)
    r2, g2, b2 = int(bottom_color[1:3], 16), int(bottom_color[3:5], 16), int(bottom_color[5:7], 16)
    steps = max(2, min(steps, h))
    for i in range(steps):
        t = i / (steps - 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        color = f"#{r:02X}{g:02X}{b:02X}"
        y0 = int(h * i / steps)
        y1 = int(h * (i + 1) / steps)
        canvas.create_rectangle(0, y0, w, y1, fill=color, outline=color)


def build_rounded_card(parent, height, radius=14, fill="#FFFFFF", padx=18, pady=12):
    """创建圆角卡片：返回 (canvas, inner_frame)。

    inner_frame 通过 create_window 嵌入 canvas，随窗口尺寸变化重绘圆角背景。
    """
    canvas = tk.Canvas(parent, height=height, bg=parent.cget("bg"), highlightthickness=0, bd=0)
    inner = tk.Frame(canvas, bg=fill)

    def redraw(event=None):
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        canvas.delete("all")
        canvas.create_polygon(
            _round_rect_points(2, 2, w - 2, h - 2, radius),
            smooth=True,
            fill=fill,
            outline="",
        )
        canvas.coords(inner_id, padx, pady)
        canvas.itemconfigure(inner_id, width=max(0, w - 2 * padx), height=max(0, h - 2 * pady))

    inner_id = canvas.create_window(padx, pady, anchor="nw", window=inner)
    canvas.bind("<Configure>", redraw)
    return canvas, inner


class RoundButton(tk.Canvas):
    """圆角按钮（Canvas 自绘），支持 hover 高亮 / disabled 置灰 / 点击回调。"""

    def __init__(self, parent, text, bg_color, command=None, height=44, radius=12,
                 font=("Microsoft YaHei UI", 12, "bold")):
        super().__init__(
            parent,
            height=height,
            bg=parent.cget("bg"),
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._text = text
        self._bg = bg_color
        self._hover_bg = _lighten(bg_color, 0.12)
        self._disabled_bg = "#C4C9D4"
        self._command = command
        self._radius = radius
        self._font = font
        self._enabled = True
        self._hovered = False
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", self._on_click)
        self._redraw()

    def _set_hover(self, on):
        self._hovered = on
        if self._enabled:
            self._redraw()

    def _on_click(self, _event):
        if self._enabled and self._command:
            self._command()

    def set_enabled(self, enabled: bool):
        """启用/禁用按钮（disabled 置灰且不响应点击）。"""
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._redraw()

    def _redraw(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
        self.delete("all")
        if not self._enabled:
            color = self._disabled_bg
        elif self._hovered:
            color = self._hover_bg
        else:
            color = self._bg
        self.create_polygon(
            _round_rect_points(2, 2, w - 2, h - 2, self._radius),
            smooth=True,
            fill=color,
            outline=color,
        )
        self.create_text(w / 2, h / 2, text=self._text, fill="#FFFFFF", font=self._font)


class SplashScreen:
    """启动过渡画面：品牌渐变 + 标题 + 加载指示，duration_ms 后淡出并显示主窗口。"""

    def __init__(self, root: tk.Tk, duration_ms: int = 2000):
        self._root = root
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        w, h = 420, 240
        x = (self.win.winfo_screenwidth() - w) // 2
        y = (self.win.winfo_screenheight() - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.configure(bg="#16233A")
        self.win.attributes("-topmost", True)

        self._cv = tk.Canvas(self.win, width=w, height=h, highlightthickness=0, bd=0)
        self._cv.pack(fill="both", expand=True)
        self._bar_w = w
        self._bar_h = h
        self._bar_x = 110

        self._draw_static(w, h)
        self._animate()
        self.win.after(duration_ms, self._fade_out)

    def _draw_static(self, w, h):
        _draw_gradient(self._cv, w, h, "#16233A", "#2C3E68")
        # 左侧品牌竖条
        self._cv.create_rectangle(24, 74, 30, 166, fill="#4D6BFE", outline="")
        self._cv.create_text(48, 88, text=APP_TITLE, anchor="nw", fill="#FFFFFF",
                             font=("Microsoft YaHei UI", 24, "bold"))
        self._cv.create_text(50, 128, text="DeepSeek Harness 桌面控制器", anchor="nw",
                             fill="#A8B4CC", font=("Microsoft YaHei UI", 10))
        self._cv.create_text(50, 156, text=f"v{APP_VERSION} · 官方 CLI 对齐", anchor="nw",
                             fill="#6B7FA3", font=("Microsoft YaHei UI", 9))
        # 底部加载条
        self._bar = self._cv.create_rectangle(
            self._bar_x, h - 46, self._bar_x + 20, h - 38, fill="#4D6BFE", outline=""
        )

    def _animate(self):
        try:
            self._bar_x += 6
            if self._bar_x > self._bar_w - 40:
                self._bar_x = 110
            self._cv.coords(self._bar, self._bar_x, self._bar_h - 46,
                            self._bar_x + 20, self._bar_h - 38)
            self.win.after(30, self._animate)
        except tk.TclError:
            pass

    def _fade_out(self, alpha: float = 1.0):
        try:
            self.win.attributes("-alpha", alpha)
        except tk.TclError:
            return
        if alpha <= 0:
            self._finish()
            return
        self.win.after(40, lambda: self._fade_out(alpha - 0.2))

    def _finish(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        try:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
        except tk.TclError:
            pass
