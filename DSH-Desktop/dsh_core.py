"""
DSH-Desktop 服务核心层（v1.4.0 模块化重构，归属 DSH-Desktop v1.4.0）。

纯逻辑、零 UI 依赖：node/dsh 包定位、本地便携插件扫描与注册、启动命令构造、
隐藏窗口标志、npm 版本查询、端口探测/进程查找/树杀、以及 DSHController
（子进程生命周期管理 + WindowSweeper 接入）。

依赖：仅 Python 3.8+ 标准库；引用 app_config（常量）与 win_sweeper（窗口清道夫）。
"""

import os
import shutil
import socket
import subprocess
import threading
import time

from app_config import (
    app_base_dir,
    app_cache_dir,
    app_log_dir,
    DSH_CMD_NAME,
    DSH_PACKAGE,
    DSH_SUBCMD,
    DSH_EXTRA_ARGS,
    DSH_HOST,
    DSH_PORT,
    DSH_PROFILE_NAME,
    LOCAL_PLUGINS_DIR,
    DEFAULT_LOCAL_PLUGINS,
)
from win_sweeper import WindowSweeper


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
            creationflags=_win_no_console_flags(),
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


def _parse_version_key(ver: str):
    """把 npm semver 字符串转成可比较元组，用于过滤旧版本。

    例：0.1.0-rc.8 -> ((0,1,0), ((1,'rc'),(0,8)))；0.1.0（正式版）-> ((0,1,0), (inf,))
    正式版恒大于同 core 的预发布版（如 0.1.0 > 0.1.0-rc.99）。解析失败返回 None。
    """
    import re

    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$", ver.strip())
    if not m:
        return None
    core = tuple(int(g) for g in m.groups()[:3])
    pre = m.group(4)
    if not pre:
        return (core, (float("inf"),))
    parts = []
    for seg in pre.split("."):
        parts.append((0, int(seg)) if seg.isdigit() else (1, seg))
    return (core, tuple(parts))


# --no-open 自 0.1.0-rc.8 起才是官方正式参数（v0.1.0-rc.7 及更早会报
# "unknown option '--no-open'" 并默认自动打开浏览器 → spawn start → 弹黑窗）。
# 直接定位到的入口低于该版本一律不采用，回退 npx 拉取最新版。
_MIN_DSH_VERSION = "0.1.0-rc.8"


def find_dsh_entry_path() -> str | None:
    """定位已安装的 @deepseek-ai/dsh 包的 Node 入口文件。

    依次收集候选（最终按版本降序取最新，且仅接受 >= _MIN_DSH_VERSION）：
     1. npm 全局安装目录（npm root -g 查询）
     2. npx 缓存目录 %LOCALAPPDATA%\\npm-cache\\_npx\\<hash>\\node_modules\\@deepseek-ai\\dsh
     3. 当前目录 / 脚本目录下 node_modules

    返回入口 js 的绝对路径；全部未命中返回 None（回退 npx 启动）。
    入口取自 package.json 的 bin 字段（可能是字符串或 {"dsh": "..."} 映射）。
    """
    import json

    min_key = _parse_version_key(_MIN_DSH_VERSION)

    candidates: list[str] = []
    # 1) npm 全局安装目录
    try:
        if os.name == "nt":
            r = subprocess.run(
                ["cmd", "/c", "npm", "root", "-g", "--no-audit", "--no-fund"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=_win_no_console_flags(),
                timeout=10,
            )
        else:
            r = subprocess.run(
                ["npm", "root", "-g", "--no-audit", "--no-fund"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=_win_no_console_flags(),
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
    for base in (os.getcwd(), app_base_dir()):
        candidates.append(os.path.join(base, "node_modules", *DSH_PACKAGE.split("/")))

    # 收集 (版本键, 入口) 候选；低于 _MIN_DSH_VERSION 的旧版直接跳过
    hits: list[tuple] = []
    for pkg_dir in candidates:
        pkg_json = os.path.join(pkg_dir, "package.json")
        if not os.path.isfile(pkg_json):
            continue
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            ver = str(data.get("version") or "")
            vk = _parse_version_key(ver)
            if vk is None or vk < min_key:
                continue  # 旧版不支持 --no-open，跳过（避免其自动 start 浏览器弹黑窗）
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
                    hits.append((vk, entry))
        except Exception:
            continue
    if hits:
        hits.sort(key=lambda t: t[0], reverse=True)  # 版本降序，取最新
        return hits[0][1]
    return None


def _local_plugins_root() -> str:
    """dsh-Plugin 目录的绝对路径（相对应用基准目录）。"""
    return os.path.join(app_base_dir(), LOCAL_PLUGINS_DIR)


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


# ---------- 插件指纹（v1.4.0：有改动才弹窗）----------
# 启动时对 dsh-Plugin/ 下可识别插件计算指纹，与上次保存的指纹比对：
# 无改动直接启动（不弹窗），有改动才弹 PluginScanDialog 让用户勾选注册。
# 状态文件存放在 DSH_HOME 下（随 profile 走，不污染便携应用目录）。

# 指纹扫描时跳过的生成/依赖目录（体积大且变化不代表插件内容变更）
_FINGERPRINT_SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", "__pycache__",
    ".DS_Store", "log", ".cache",
}


def _plugin_state_file() -> str:
    """插件指纹状态文件路径（DSH_HOME/dsh-desktop/plugin-state.json）。"""
    return os.path.join(_dsh_home(), "dsh-desktop", "plugin-state.json")


def _hash_file_tree(root: str, dig, prefix: str = "") -> None:
    """递归把 root 下的文件树摘要写入哈希器 dig。

    跳过 _FINGERPRINT_SKIP_DIRS 中的目录（node_modules 等生成物），
    顺序无关（外层按条目排序），单文件读取失败不中断整体。
    """
    import hashlib
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return
    for entry in entries:
        if entry in _FINGERPRINT_SKIP_DIRS:
            continue
        full = os.path.join(root, entry)
        rel = f"{prefix}/{entry}" if prefix else entry
        if os.path.isdir(full):
            _hash_file_tree(full, dig, rel)
        else:
            try:
                with open(full, "rb") as f:
                    dig.update(rel.encode("utf-8", "replace"))
                    dig.update(b"\x00")
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        dig.update(chunk)
                    dig.update(b"\x00")
            except OSError:
                continue


def compute_plugin_fingerprint() -> str | None:
    """计算 dsh-Plugin/ 下可识别插件的整体指纹（sha256 hex）。

    覆盖每个含 package.json 的顶层插件目录的（目录名 + 递归文件树内容，
    跳过 node_modules 等生成目录）。无可用插件返回 None。
    """
    import hashlib
    root = _local_plugins_root()
    if not os.path.isdir(root):
        return None
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return None
    parts: list[str] = []
    for entry in entries:
        sub = os.path.join(root, entry)
        if not os.path.isdir(sub) or not os.path.isfile(os.path.join(sub, "package.json")):
            continue
        dig = hashlib.sha256()
        dig.update(entry.encode("utf-8", "replace"))
        dig.update(b"\x00")
        _hash_file_tree(sub, dig)
        parts.append(dig.hexdigest())
    if not parts:
        return None
    dig = hashlib.sha256()
    for p in sorted(parts):
        dig.update(p.encode("ascii"))
        dig.update(b"\x00")
    return dig.hexdigest()


def _read_plugin_fingerprint() -> str | None:
    """读取上次保存的插件指纹；无状态文件或解析失败返回 None。"""
    import json
    try:
        with open(_plugin_state_file(), "r", encoding="utf-8") as f:
            data = json.load(f)
        fp = data.get("fingerprint")
        return fp if isinstance(fp, str) and fp else None
    except Exception:
        return None


def save_plugin_fingerprint(fp: str) -> bool:
    """保存当前插件指纹到状态文件；失败返回 False（不影响启动）。"""
    import json
    try:
        path = _plugin_state_file()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"fingerprint": fp, "updated": time.time()},
                f, ensure_ascii=False, indent=2,
            )
        return True
    except Exception:
        return False


def plugins_changed() -> tuple[bool, str | None]:
    """判断 dsh-Plugin/ 是否相对上次有改动。

    返回 (changed, new_fp)：
      - changed=True：首次运行（无状态文件）或指纹与上次不一致 → 应弹窗
      - changed=False：指纹一致 → 直接启动不弹窗
      - new_fp：本次计算的指纹，供弹窗后 save_plugin_fingerprint 保存；
        计算失败或无可用插件时为 None（此时调用方自行降级）
    """
    fp = compute_plugin_fingerprint()
    if fp is None:
        return False, None
    return _read_plugin_fingerprint() != fp, fp


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
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="ignore",
            creationflags=_win_no_console_flags(),
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
                        capture_output=True,
                        creationflags=_win_no_console_flags(),
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


def _win_no_console_flags(detach: bool = False) -> int:
    """Windows 子进程创建标志：阻止控制台窗口出现。

    两种模式：
    - detach=False（默认）: 只用 CREATE_NO_WINDOW。适用于所有直接子进程
      （短命令 npm root -g、where node、netstat、taskkill 及长驻 node.exe）。
    - detach=True: CREATE_NO_WINDOW | DETACHED_PROCESS。**当前不再使用**。
      说明：DETACHED_PROCESS 只作用于直接子进程——它让 node.exe 完全失去
      控制台，但 node 内部再 spawn 的 cmd/start/guard.bat 等控制台程序
      （父进程无控制台时）会被 Windows 自动分配"可见"新控制台，反而闪黑窗，
      与"阻止子孙进程开黑窗"的初衷相反，故 v1.3.4 起弃用。

    CREATE_NO_WINDOW (0x08000000): 告诉 Windows 这个控制台进程不要有控制台窗口
    DETACHED_PROCESS (0x00000008): 仅影响直接子进程，无法阻止孙进程创建控制台
    """
    if os.name != "nt":
        return 0
    flags = subprocess.CREATE_NO_WINDOW
    if detach:
        flags |= subprocess.DETACHED_PROCESS
    return flags


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
            creationflags=_win_no_console_flags(),
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
            creationflags=_win_no_console_flags(),
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
            creationflags=_win_no_console_flags(),
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
                creationflags=_win_no_console_flags(),
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
        # v1.3.6: 窗口清道夫——DSH 启动后自动隐藏 node 内部 spawn 出来的额外 cmd.exe
        # 黑窗（DSH Desktop 自己的 GUI 窗口通过 PID 排除，不受影响）
        self._sweeper = WindowSweeper()

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
        # v1.3.6: 让 sweeper 日志也走主输出回调（带 [sweeper] 前缀）
        if cb is not None:
            self._sweeper._log = self._sweep_log

    def _emit(self, line: str):
        if self._output_callback:
            self._output_callback(line)

    def _sweep_log(self, line: str):
        """窗口清道夫的日志也走主输出回调（加 [sweeper] 前缀以示区别）。"""
        self._emit(line)

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

            # v1.3.6: Popen 前快照当前所有可见顶层窗口，作为 sweeper 基线
            # （DSH 启动后新出现的窗口 = DSH node 内部 spawn 的额外 cmd.exe 黑窗）
            self._sweeper.snapshot_baseline()

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

            # v1.3.4: console=False 窗口化 EXE。主 node.exe 仅用 CREATE_NO_WINDOW
            # （不用 DETACHED_PROCESS——它会让 node 完全失去控制台，node 内部再
            # spawn 的 cmd/start/guard.bat 等控制台子进程反而会被 Windows 分配
            # 可见新控制台而闪黑窗）。CREATE_NO_WINDOW 下 node 本身无可见窗口；
            # 短命令（npm root 等）同样用 detach=False。
            creationflags = _win_no_console_flags(detach=False)

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

            # v1.3.6: 启动窗口清道夫（隐藏 node 内部 spawn 的 cmd.exe 黑窗）
            self._sweeper.start()

            threading.Thread(target=self._read_output, daemon=True).start()
        except Exception as e:
            self.process = None
            self._emit(f"启动失败：{e}")
            # v1.3.6: Popen 失败时确保 sweeper 不会残留
            try:
                self._sweeper.stop()
            except Exception:
                pass
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
                # 即便没有服务进程，也要确保 sweeper 已停
                self._sweeper.stop()
                self.process = None
                return False, "服务未运行"

            pid = self.process.pid
            try:
                if os.name == "nt":
                    # Windows：taskkill /F /T 终止进程树（加 timeout 防挂起）
                    result = subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        text=True,
                        creationflags=_win_no_console_flags(),
                        timeout=10,
                    )
                    if result.returncode != 0:
                        self._sweeper.stop()
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
                # v1.3.6: 进程退出后停掉 sweeper，避免持续轮询
                self._sweeper.stop()
                return True, f"已关闭服务 (PID={pid})"
            except Exception as e:
                self._sweeper.stop()
                return False, f"关闭失败：{e}"
