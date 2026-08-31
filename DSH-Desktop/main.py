"""
DSH Desktop - DeepSeek Harness 桌面控制器

功能：
  - 开启服务：后台执行 `npx -y @deepseek-ai/dsh web --no-open`（Windows 经 cmd.exe 包装）
  - 关闭服务：终止上述进程及其子进程
  - 打开DSH：在默认浏览器中打开 http://127.0.0.1:3080
  - 版本感知：启动时后台查询 npm 上 @deepseek-ai/dsh 的 latest 版本并展示

官方 CLI 对齐（deepseek-ai/deepseek-harness，核验截至 2026-08-31）：
  - `dsh web` 是 `dsh --profile web` 的官方保留别名，两者等价；
  - 官方自 v0.1.0-rc.8 起本机启动默认自动打开浏览器，`--no-open` 为官方正式参数；
  - 官方禁止 `--host 0.0.0.0`（防 RCE 暴露到网络），本工具固定 127.0.0.1:3080 符合官方安全基线；
  - npm dist-tag latest = next = v0.1.1-rc.2（2026-08-21 发布，仍为开发者预览版）：
      * rc.1：新增 DeepSeek-V4-Flash-Vision-Exp 模型；修复 Bubblewrap 沙箱 /proc/<pid>/root 逃逸（建议 Linux 用户优先升级）
      * rc.2：DeepSeek 适配器优先经 Files API 上传图片并复用；图片自动按模型要求缩放/转换格式
  - 每次启动官方会打印带 token 的 URL，浏览器凭 cookie 交接，本工具日志区实时透出。

UI v1.2.0 优化：
  - DeepSeek 品牌蓝视觉改版：渐变横幅、圆角卡片/圆角按钮、启动窗口居中
  - 启动 Splash 过渡画面（品牌渐变 + 加载指示，约 2s 淡出）
  - 版本感知增强：rc/alpha/beta/next 版本标记"预览版"徽标；一键复制安装命令
  - 状态卡片 URL 一键复制到剪贴板
  - 底部状态栏：端口、PID、运行时长
  - 日志区新增"清空"按钮

v1.2.1 修复：
  - 隐藏桌面弹出窗口：CREATE_NO_WINDOW 仅对直接子进程（外层 cmd）有效，
    npx/npm 内部 spawn 的 node.exe（控制台应用）在无控制台的 GUI 进程中会
    自动分配可见新控制台而弹黑窗；现于启动时为进程分配隐藏控制台，使所有
    孙进程 attach 到隐藏控制台，彻底不弹窗（终端运行不受影响）

v1.2.2 修复（彻底根治弹窗）：
  - 直接 node 运行 dsh 包入口：定位已缓存的 @deepseek-ai/dsh 包（npm 全局
    安装 / npx 缓存 / node_modules），执行 `node <入口> web --no-open`，
    全程仅一个 node.exe 进程，CREATE_NO_WINDOW 直接生效，不再有
    cmd→node(npx)→node(dsh) 嵌套，空白黑窗彻底消除
  - 首次运行（包未缓存）自动回退官方 npx 命令，下载一次后即走直接 node 路径
  - 保留隐藏控制台 + STARTUPINFO 兜底，覆盖回退 npx 的场景

v1.2.3 修复：
  - PyInstaller --windowed EXE 继承不到完整 PATH，导致 `shutil.which('node')`
    返回 None，实际仍回退到 `cmd /c npx ...` 而弹窗
  - 新增 `find_node_executable()`：先 PATH，再常见目录（Program Files/nodejs、
    APPDATA/npm 等），最后用 `where node` 兜底，确保打包环境下也能找到 node
  - `_start_worker` 中打印 node 路径 / dsh 入口 / 实际启动命令，便于弹窗时诊断

v1.2.4 修复：
  - 用户反馈 v1.2.3 仍弹 cmd 黑窗，但日志显示启动命令已是直接 `node <入口>`，
    说明黑窗来自 node.exe 控制台子系统进程在 GUI 父进程下被分配了新控制台
  - 改为使用 `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`，让 node 进程完全
    脱离父进程控制台且不创建新控制台，根治弹窗
  - 移除 v1.2.1 的 AllocConsole 隐藏控制台方案，避免与 --windowed 模式冲突

v1.2.5 修复：
  - 用户反馈 v1.2.4 仍弹多次 cmd 黑窗，最终仍出现可见 cmd 窗口，且窗口内显示
    DSH 日志；说明黑窗来自 node 再 spawn 的 cmd 孙进程
  - 参考 GitHub/CSDN 同类问题：PyInstaller --windowed 父进程无控制台时，
    Windows 会为孙进程自动创建可见控制台；可靠方案是父进程先 AllocConsole
    一个隐藏控制台，子进程继承该隐藏控制台，从而阻止弹出新窗口
  - 恢复并改进 `_ensure_hidden_console()`：仅在没有控制台时分配并隐藏；
    `_start_worker` 改为 `CREATE_NO_WINDOW`（让 node 继承隐藏控制台）并移除
    `DETACHED_PROCESS`（脱离控制台会导致孙进程弹窗）

v1.3.0 新增（便携插件机制）：
  - DSH-Desktop/dsh-Plugin/ 下存放便携插件源（dsh-plugin-guard、dsh-market 等，
    本地 checkout 或已构建产物），随 DSH-Desktop 文件夹一起便携迁移。
  - 点"开启服务"时弹出"便携插件管理"窗：扫描 dsh-Plugin/ 下所有含 package.json
    的子目录，显示名称/版本/已安装状态，默认勾选 dsh-plugin-guard 与 dsh-market，
    其余可手动勾选；确认后随服务启动自动 `dsh plugin --profile web add link:<path>`
    注册到 web profile，换新环境无需手动安装。
  - 跳过/取消 = 不注册直接启动；注册失败不阻断启动（仅日志告警）。
  - 已安装的插件项默认也勾选（re-add 幂等，pnpm 会跳过已存在的 link）。

依赖：仅 Python 3.8+ 标准库（tkinter / subprocess / webbrowser / threading）
"""

import os
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
APP_VERSION = "1.3.2"
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
LOCAL_PLUGINS_DIR = "dsh-Plugin"  # 相对 main.py 所在目录
DSH_PROFILE_NAME = "web"          # 目标 profile
# 默认勾选的插件子目录名（dsh-Plugin/ 下的目录名）
DEFAULT_LOCAL_PLUGINS = ["dsh-plugin-guard", "dsh-market"]


def find_node_executable() -> str | None:
    """在 Windows 打包/受限环境中 robust 查找 node.exe 路径。

    PyInstaller --windowed 的 EXE 可能继承不到完整的系统 PATH，导致
    shutil.which('node') 返回 None。本函数按优先级：
      1. shutil.which('node')
      2. 常见安装目录（Program Files/nodejs、APPDATA/npm 等）
      3. `where node` 命令兜底（带隐藏窗口，避免弹黑窗）
    """
    # 1) PATH 查找
    node = shutil.which("node")
    if node and os.path.isfile(node):
        return os.path.abspath(node)

    if os.name != "nt":
        return node

    # 2) 常见安装目录
    candidates = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs", "node.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "nodejs", "node.exe"),
        os.path.join(os.environ.get("APPDATA", ""), "npm", "node.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", "node.exe"),
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return os.path.abspath(p)

    # 3) where node 兜底
    try:
        r = subprocess.run(
            ["cmd", "/c", "where", "node"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            for line in r.stdout.strip().splitlines():
                p = line.strip()
                if p and os.path.isfile(p):
                    return os.path.abspath(p)
    except Exception:
        pass
    return None


def find_dsh_entry_path() -> str | None:
    """定位已安装的 @deepseek-ai/dsh 包的 Node 入口文件。

    依次尝试（首次命中即返回）：
      1. npm 全局安装目录（npm root -g 查询）
      2. npx 缓存目录 %LOCALAPPDATA%\\npm-cache\\_npx\\<hash>\\node_modules\\@deepseek-ai\\dsh
      3. 当前目录 / 脚本目录下 node_modules

    返回入口 js 的绝对路径；全部未命中返回 None（回退 npx 启动）。
    入口取自 package.json 的 bin 字段（可能是字符串或 {"dsh": "..."} 映射）。
    """
    import json

    candidates: list[str] = []
    # 1) npm 全局安装目录
    try:
        if os.name == "nt":
            r = subprocess.run(
                ["cmd", "/c", "npm", "root", "-g", "--no-audit", "--no-fund"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
            )
        else:
            r = subprocess.run(
                ["npm", "root", "-g", "--no-audit", "--no-fund"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                timeout=10,
            )
        if r.returncode == 0 and r.stdout.strip():
            candidates.append(os.path.join(r.stdout.strip(), *DSH_PACKAGE.split("/")))
    except Exception:
        pass

    # 2) npx 缓存目录
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        cache = os.path.join(local, "npm-cache", "_npx")
        try:
            if os.path.isdir(cache):
                for sub in os.listdir(cache):
                    p = os.path.join(cache, sub, "node_modules", *DSH_PACKAGE.split("/"))
                    if os.path.isdir(p):
                        candidates.append(p)
        except OSError:
            pass

    # 3) 当前目录 / 应用基准目录 node_modules（打包态下用 sys.executable 所在目录）
    for base in (os.getcwd(), _app_base_dir()):
        candidates.append(os.path.join(base, "node_modules", *DSH_PACKAGE.split("/")))

    for pkg_dir in candidates:
        pkg_json = os.path.join(pkg_dir, "package.json")
        if not os.path.isfile(pkg_json):
            continue
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            bin_val = data.get("bin")
            if isinstance(bin_val, str):
                rel = bin_val
            elif isinstance(bin_val, dict) and bin_val:
                rel = next(iter(bin_val.values()))
            else:
                rel = None
            if rel:
                entry = os.path.normpath(os.path.join(pkg_dir, rel))
                if os.path.isfile(entry):
                    return entry
        except Exception:
            continue
    return None


def _app_base_dir() -> str:
    """应用基准目录：PyInstaller onefile 打包态用 sys.executable 所在目录
   （EXE 同级的便携 dsh-Plugin/ 才是用户携带的位置），源码态用 __file__ 所在目录。"""
    import sys
    if getattr(sys, "frozen", False):  # PyInstaller 打包态
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _local_plugins_root() -> str:
    """dsh-Plugin 目录的绝对路径（相对应用基准目录）。"""
    return os.path.join(_app_base_dir(), LOCAL_PLUGINS_DIR)


def _dsh_home() -> str:
    """DSH_HOME 路径（默认 ~/.dsh）。"""
    return os.environ.get("DSH_HOME") or os.path.join(
        os.path.expanduser("~"), ".dsh")


def _profile_dir() -> str:
    """web profile 目录路径。"""
    return os.path.join(_dsh_home(), "profiles", DSH_PROFILE_NAME)


def _read_profile_deps() -> dict:
    """读取 web profile 的 package.json dependencies；失败返回空 dict。"""
    import json
    pkg = os.path.join(_profile_dir(), "package.json")
    if not os.path.isfile(pkg):
        return {}
    try:
        with open(pkg, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("dependencies", {}) or {}
    except Exception:
        return {}


def scan_local_plugins() -> list[dict]:
    """扫描 dsh-Plugin/ 下每个含 package.json 的子目录，返回插件清单。

    每项：{dir, path, name, version, description, installed, default_on}
      - installed: 包名是否已在 web profile dependencies 且 node_modules 存在
      - default_on: 是否默认勾选（在 DEFAULT_LOCAL_PLUGINS 中）
    """
    import json
    import re
    root = _local_plugins_root()
    result: list[dict] = []
    if not os.path.isdir(root):
        return result
    deps = _read_profile_deps()
    nm = os.path.join(_profile_dir(), "node_modules")
    # 合法 npm 包名：不含路径分隔符/..，防止路径穿越
    name_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@/-]*$")
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return result
    for entry in entries:
        sub = os.path.join(root, entry)
        if not os.path.isdir(sub):
            continue
        pkg_json = os.path.join(sub, "package.json")
        if not os.path.isfile(pkg_json):
            continue
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 类型校验：package.json 未必是规范 dict，字段未必是 str
            raw_name = data.get("name")
            name = raw_name if isinstance(raw_name, str) and name_re.match(raw_name) else entry
            raw_ver = data.get("version")
            ver = raw_ver if isinstance(raw_ver, str) else ""
            raw_desc = data.get("description")
            desc = raw_desc if isinstance(raw_desc, str) else ""
            # installed：依赖中存在该包名，且 node_modules 里有对应目录/链接
            installed = name in deps and os.path.exists(os.path.join(nm, name))
            result.append({
                "dir": entry,
                "path": sub,
                "name": name,
                "version": ver,
                "description": desc,
                "installed": installed,
                "default_on": entry in DEFAULT_LOCAL_PLUGINS,
            })
        except Exception:
            # 单个目录解析失败不拖垮整个扫描，跳过该项
            continue
    return result


def register_local_plugin(node_path: str | None, dsh_entry: str | None,
                          plugin_path: str) -> tuple[bool, str]:
    """把单个本地插件注册到 web profile（`dsh plugin --profile web add link:<path>`）。

    依赖 node 可执行 + dsh 包入口；二者缺失则返回失败。
    用 CREATE_NO_WINDOW 隐藏控制台，避免弹黑窗；stdin=DEVNULL 避免 pnpm 交互提示挂起。
    超时 60s（N 个插件顺序注册，避免单卡死阻塞过久）；超时树杀避免孙进程残留。
    """
    if not node_path or not os.path.isfile(node_path):
        return False, "未找到 node 可执行文件"
    if not dsh_entry or not os.path.isfile(dsh_entry):
        return False, "未找到 dsh 包入口"
    spec = f"link:{plugin_path}"
    cmd = [node_path, dsh_entry, "plugin", "--profile", DSH_PROFILE_NAME, "add", spec]
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="ignore",
            creationflags=creationflags,
        )
        try:
            out, _ = proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            # 树杀：dsh CLI 内部会 spawn pnpm（shell=True）拉起进程树，
            # 仅 kill 直接子进程会留下孤儿 pnpm 占用 profile 锁
            if os.name == "nt":
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=15,
                    )
                except Exception:
                    pass
            else:
                try:
                    proc.kill()
                except Exception:
                    pass
            return False, "注册超时（60s），已树杀"
        out = out or ""
        if proc.returncode == 0:
            return True, out.strip() or "注册成功"
        return False, f"退出码 {proc.returncode}：{out.strip()[:300]}"
    except Exception as e:
        return False, f"注册异常：{e}"


def build_start_command() -> list[str]:
    """构造启动命令（v1.2.2：优先直接 node 运行 dsh 包入口）。

    npx 方式：Windows 上 npx 实际是 npx.cmd 批处理，须经 cmd.exe 包装；
    且 npx 内部还会再 spawn node.exe → cmd→node(npx)→node(dsh) 多层嵌套，
    是窗口化 EXE 下"弹空白黑窗"的根源。

    根治：定位已缓存的 @deepseek-ai/dsh 包后，直接 `node <入口> web --no-open`，
    全程只有一个 node.exe 进程，CREATE_NO_WINDOW 直接生效，不再弹窗。
    首次运行（包未缓存）自动回退官方 npx 命令，下载一次后即走直接 node 路径。
    官方命令等价性：`dsh web` ≡ `dsh --profile web`。
    """
    entry = find_dsh_entry_path()
    node = find_node_executable()
    if entry and node:
        return [node, entry, DSH_SUBCMD, *DSH_EXTRA_ARGS]
    # 回退：官方 npx 命令（首次运行下载依赖）
    if os.name == "nt":
        return ["cmd", "/c", DSH_CMD_NAME, "-y", DSH_PACKAGE, DSH_SUBCMD, *DSH_EXTRA_ARGS]
    return [DSH_CMD_NAME, "-y", DSH_PACKAGE, DSH_SUBCMD, *DSH_EXTRA_ARGS]


def build_hidden_startupinfo():
    """构造隐藏窗口的 STARTUPINFO（对直接子进程的兜底）。"""
    if os.name != "nt":
        return None
    try:
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = subprocess.SW_HIDE
        return info
    except Exception:
        return None


def _ensure_hidden_console():
    """Windows 窗口化 EXE 下分配并隐藏一个控制台，供子进程继承。

    参考 GitHub/CSDN 同类问题（PyInstaller + subprocess + node 子进程弹黑窗）：
    父进程没有控制台时，Windows 会为控制台子系统的孙进程（node → cmd）
    自动创建新的可见控制台。唯一可靠的做法是父进程先 AllocConsole 一个
    隐藏控制台，这样子进程（node 及其再 spawn 的 cmd）都会 attach 到
    这个隐藏控制台，而不再弹出新窗口。

    终端直接运行（已有控制台）时本函数不干预，避免隐藏用户自己的终端。
    """
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        if kernel32.GetConsoleWindow():
            return  # 已有控制台，保持现状
        if kernel32.AllocConsole():
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass


def fetch_latest_dsh_version(timeout: float = 8.0) -> str | None:
    """查询 npm 上 @deepseek-ai/dsh 的 latest 版本号（对应官方 dist-tag: latest）。

    失败（未装 npm / 无网络 / 超时）返回 None，调用方静默处理。
    Windows 上 npm 为 npm.cmd，CreateProcess 无法直接执行，需经 cmd /c 包装。
    """
    if os.name == "nt":
        cmd = ["cmd", "/c", "npm", "view", DSH_PACKAGE, "version", "--no-audit", "--no-fund"]
    else:
        cmd = ["npm", "view", DSH_PACKAGE, "version", "--no-audit", "--no-fund"]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            timeout=timeout,
        )
        lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
        return lines[-1] if lines else None
    except Exception:
        return None


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

    def start(self, pending_plugins: list[dict] | None = None) -> tuple[bool, str]:
        """异步启动 DSH 服务，立即返回，不阻塞调用线程。

        pending_plugins：启动前需注册到 web profile 的本地插件项列表
          （每项形如 scan_local_plugins 返回的 dict，含 path/name）；
          None 或空表示无需注册，直接启动。

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

        threading.Thread(target=self._start_worker,
                         args=(tuple(pending_plugins or []),), daemon=True).start()
        return True, "正在启动 DSH 服务..."

    def _start_worker(self, pending_plugins: list[dict] | None = None):
        """后台线程：注册待装插件（如有）后执行 Popen 并接管输出读取。"""
        try:
            node_path = find_node_executable()
            entry_path = find_dsh_entry_path()
            self._emit(f"node={node_path or '未找到'}")
            self._emit(f"entry={entry_path or '未找到'}")

            # 注册用户在插件管理弹窗中勾选的本地便携插件（v1.3.0）
            if pending_plugins:
                self._emit(f"便携插件：待注册 {len(pending_plugins)} 个")
                for it in pending_plugins:
                    name = it.get("name") or it.get("dir") or "?"
                    path = it.get("path") or ""
                    if not path:
                        self._emit(f"  - {name}：路径缺失，跳过")
                        continue
                    ok, msg = register_local_plugin(node_path, entry_path, path)
                    tag = "OK" if ok else "FAIL"
                    self._emit(f"  - {name}：{tag}（{msg[:120]}）")
                self._emit("便携插件注册流程结束")

            creationflags = 0
            if os.name == "nt":
                # Windows：不弹出黑色控制台窗口。
                # 关键：父进程必须先有隐藏控制台（见 _ensure_hidden_console），
                # 然后子进程用 CREATE_NO_WINDOW 继承该隐藏控制台，Windows 才不会
                # 为 node → cmd 等孙进程自动创建新的可见控制台。
                # DETACHED_PROCESS 会让子进程脱离父进程控制台，反而导致弹窗，
                # 因此这里不再使用。
                creationflags = subprocess.CREATE_NO_WINDOW

            cmd = build_start_command()
            cmd_display = " ".join(str(c) for c in cmd)
            self._emit(f"启动命令: {cmd_display}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                startupinfo=build_hidden_startupinfo(),
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


# ---------------------------------------------------------------------------
# UI 工具（纯标准库 tkinter）
# ---------------------------------------------------------------------------

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
        w, h = 560, 650
        self.root.minsize(520, 600)
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
        # 状态栏先 pack（side=bottom），避免挤压 expand 的日志区
        self._build_statusbar()
        self._build_header()
        self._build_status_card()
        self._build_actions()
        self._build_log()

    def _build_header(self):
        """顶部品牌渐变横幅。"""
        self.banner = tk.Canvas(self.root, height=96, bg=self.BG_COLOR, highlightthickness=0, bd=0)
        self.banner.pack(fill="x")
        self.banner.bind("<Configure>", self._draw_banner)

    def _draw_banner(self, event=None):
        w = self.banner.winfo_width()
        h = self.banner.winfo_height()
        if w <= 1:
            return
        self.banner.delete("all")
        _draw_gradient(self.banner, w, h, self.BANNER_TOP, self.BANNER_BOTTOM)
        # 左侧品牌竖条 + 标题
        self.banner.create_rectangle(24, 30, 30, 66, fill=self.PRIMARY_COLOR, outline="")
        self.banner.create_text(46, 34, text=APP_TITLE, anchor="nw", fill="#FFFFFF",
                                font=("Microsoft YaHei UI", 18, "bold"))
        self.banner.create_text(46, 62, text="DeepSeek Harness 桌面控制器", anchor="nw",
                                fill="#A8B4CC", font=("Microsoft YaHei UI", 9))
        # 右侧版本号
        self.banner.create_text(w - 20, 30, text=f"v{APP_VERSION}", anchor="ne",
                                fill="#8FA3C9", font=("Microsoft YaHei UI", 9))
        # 右侧状态小字：端口
        self.banner.create_text(w - 20, 66, text=f"{DSH_HOST}:{DSH_PORT}", anchor="ne",
                                fill="#6B7FA3", font=("Consolas", 9))

    def _build_status_card(self):
        """状态卡片：状态灯 + 状态文本 + URL（可复制）+ 官方版本 + 徽标 + 复制安装命令。"""
        self.status_canvas, card_inner = build_rounded_card(self.root, height=116)
        self.status_canvas.pack(fill="x", padx=20, pady=(14, 4))

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
        row2.pack(fill="x", pady=(12, 0))

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
        actions.pack(fill="x", padx=20, pady=(10, 4))

        self.btn_start = RoundButton(actions, "开启服务", self.SUCCESS_COLOR, self._on_start)
        self.btn_start.pack(fill="x", pady=5)
        self.btn_stop = RoundButton(actions, "关闭服务", self.DANGER_COLOR, self._on_stop)
        self.btn_stop.pack(fill="x", pady=5)
        self.btn_open = RoundButton(actions, "打开DSH", self.PRIMARY_COLOR, self._on_open)
        self.btn_open.pack(fill="x", pady=5)

    def _build_log(self):
        """运行日志区（深色主题 + 清空按钮）。"""
        log_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 6))

        bar = tk.Frame(log_frame, bg=self.BG_COLOR)
        bar.pack(fill="x", pady=(0, 4))
        tk.Label(
            bar, text="运行日志", bg=self.BG_COLOR, fg=self.MUTED_COLOR,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="left")
        clear_btn = tk.Label(
            bar, text="清空", bg=self.BG_COLOR, fg=self.PRIMARY_COLOR,
            font=("Microsoft YaHei UI", 8), cursor="hand2",
        )
        clear_btn.pack(side="right")
        clear_btn.bind("<Button-1>", lambda e: self._clear_log())

        log_box = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Consolas", 9),
            bg=self.LOG_BG,
            fg=self.LOG_FG,
            insertbackground=self.LOG_FG,
            relief="flat",
            bd=0,
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
        # 弹出便携插件管理窗，让用户勾选要注册的本地插件（取消/跳过 = 不注册直接启动）
        pending = None
        # 扫描为空（dsh-Plugin 不存在/无可用插件）则跳过弹窗，免得每次多点一次
        try:
            scanned = scan_local_plugins()
        except Exception:
            scanned = []
        if scanned:
            try:
                dlg = PluginScanDialog(self.root)
                pending = dlg.result
            except Exception as e:
                self._log(f"插件管理窗异常（将直接启动）：{e}")
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
                self._msg_queue.put(f"{_VERSION_MSG_PREFIX}{v}")
            except Exception:
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


def main():
    # Windows 窗口化 EXE 启动前分配隐藏控制台，供后续 node → cmd 子进程继承，
    # 避免 Windows 为孙进程自动创建新的可见控制台窗口（弹黑窗）。
    _ensure_hidden_console()
    root = tk.Tk()
    root.withdraw()  # 先隐藏主窗口，Splash 过渡结束后再显示
    DSHDesktopApp(root)
    SplashScreen(root, duration_ms=2000)
    root.mainloop()


if __name__ == "__main__":
    main()
