"""
DSH-Desktop 应用配置（v1.4.0 模块化重构，归属 DSH-Desktop v1.4.0）。

集中管理全局常量：应用元信息、DSH 服务参数、本地便携插件配置。
本模块零第三方依赖，也不依赖项目内其他模块（最底层）。

依赖：仅 Python 3.8+ 标准库
"""

import os
import sys

APP_TITLE = "DSH Desktop"
APP_VERSION = "1.4.1"
DSH_HOST = "127.0.0.1"
DSH_PORT = 3080
DSH_URL = f"http://{DSH_HOST}:{DSH_PORT}"
DSH_CMD_NAME = "npx"
DSH_PACKAGE = "@deepseek-ai/dsh"
DSH_SUBCMD = "web"
DSH_EXTRA_ARGS = ["--no-open"]  # 官方正式参数：仅启动服务，不自动打开浏览器（避免与"打开DSH"按钮重复开标签）
# 版本检查内部消息前缀（经 _msg_queue 回传，避免子线程直接操作 tkinter）
_VERSION_MSG_PREFIX = "__VERSION__|"

# ---------- 本地便携插件机制（v1.3.0）----------
# DSH-Desktop/dsh-Plugin/ 下存放便携插件源（本地 checkout / 已构建产物），
# 启动器在"开启服务"时扫描该目录，弹窗让用户勾选要注册到 web profile 的插件，
# 默认勾选 DEFAULT_LOCAL_PLUGINS 中的包。换新环境时随 DSH-Desktop 文件夹一起携带，
# 无需手动 `dsh plugin add`。
LOCAL_PLUGINS_DIR = "dsh-Plugin"  # 相对应用基准目录
DSH_PROFILE_NAME = "web"          # 目标 profile
# 默认勾选的插件子目录名（dsh-Plugin/ 下的目录名）
DEFAULT_LOCAL_PLUGINS = ["dsh-plugin-guard", "dsh-market"]

# ---------- 运行时目录（v1.4.1）----------
# 日志/缓存统一收口到应用基准目录下，便于便携携带与清理：
#   log/   程序运行日志（自动落盘 + 手动导出默认路径）
#   cache/ 运行时缓存
LOG_DIR_NAME = "log"      # 日志文件夹名（相对应用基准目录）
CACHE_DIR_NAME = "cache"  # 缓存文件夹名（相对应用基准目录）


def app_base_dir() -> str:
    """应用基准目录：PyInstaller 打包态用 EXE 所在目录，源码态用本文件所在目录。"""
    if getattr(sys, "frozen", False):  # PyInstaller 打包态
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def app_log_dir() -> str:
    """日志文件夹绝对路径（不存在则创建）。"""
    d = os.path.join(app_base_dir(), LOG_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def app_cache_dir() -> str:
    """缓存文件夹绝对路径（不存在则创建）。"""
    d = os.path.join(app_base_dir(), CACHE_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d
