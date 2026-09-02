"""
DSH Desktop - DeepSeek Harness 桌面控制器（入口，v1.4.0 模块化重构）

v1.3.9：将单文件 main.py 拆分为功能模块，便于维护与扩展：
v1.4.0：插件指纹感知——启动扫描 dsh-Plugin/ 计算指纹，有改动才弹插件管理窗，无改动直接启动（见 dsh_core.plugins_changed）。
  - app_config.py   常量与配置（标题/版本/端口/插件目录等）
  - win_sweeper.py  WindowSweeper 窗口清道夫（隐藏 DSH 弹出的额外 cmd 黑窗）
  - dsh_core.py     DSH 服务核心（node 定位、插件注册、端口管理、DSHController）
  - ui_widgets.py   UI 通用组件（圆角卡片/按钮/渐变/启动 Splash）
  - dialogs.py      对话框（便携插件管理窗）
  - main_window.py  主窗口 DSHDesktopApp（GUI 布局与事件）

功能（详见 app_config 与各模块 docstring）：
  - 开启服务：后台执行 `npx -y @deepseek-ai/dsh web --no-open`（优先直接 node 运行）
  - 关闭服务：终止上述进程及其子进程树
  - 打开DSH：在默认浏览器中打开 http://127.0.0.1:3080
  - 版本感知：启动时后台查询 npm 上 @deepseek-ai/dsh 的 latest 版本并展示

依赖：仅 Python 3.8+ 标准库（tkinter / subprocess / webbrowser / threading）
"""

import tkinter as tk

from main_window import DSHDesktopApp
from ui_widgets import SplashScreen


def main():
    # v1.3.4: spec 改为 console=False（窗口化 EXE，本身无控制台），
    # 子进程用 CREATE_NO_WINDOW 阻止各自开黑窗，不再需要隐藏预分配控制台的逻辑。
    root = tk.Tk()
    root.withdraw()  # 先隐藏主窗口，Splash 过渡结束后再显示
    DSHDesktopApp(root)
    SplashScreen(root, duration_ms=2000)
    root.mainloop()


if __name__ == "__main__":
    main()
