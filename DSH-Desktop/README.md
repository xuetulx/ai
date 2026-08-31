# DSH Desktop

> DeepSeek Harness 桌面控制器 v1.1.0

一个轻量级 Windows 桌面应用，用于控制 [DeepSeek Harness (DSH)](https://www.npmjs.com/package/@deepseek-ai/dsh) 本地服务的启停与访问。

## 功能

| 按钮       | 作用                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| 开启服务   | 后台执行 `npx -y @deepseek-ai/dsh web --no-open`，启动 Web UI（端口 3080）          |
| 关闭服务   | 终止本应用启动的进程树；若端口被外部实例占用，可强制结束占用进程         |
| 打开DSH    | 在系统默认浏览器中打开 `http://127.0.0.1:3080`                          |
| 版本感知   | 启动时后台查询 npm 上 `@deepseek-ai/dsh` 的 latest 版本，显示在状态卡片   |

## 与官方 CLI 对齐（deepseek-ai/deepseek-harness）

本工具的命令与官方最新 CLI 保持一致：

| 官方 CLI | 说明 |
| -------- | ---- |
| `dsh web` ≡ `dsh --profile web` | `dsh web` 是官方保留别名，两者等价 |
| `--no-open` | 官方正式参数；官方自 v0.1.0-rc.8 起本机启动默认自动打开浏览器，本工具用它避免与"打开DSH"按钮重复开标签 |
| `--host 127.0.0.1` | 官方默认值；**官方禁止 `0.0.0.0`**（防止把 RCE 暴露到局域网），本工具固定回环地址符合官方安全基线 |
| `--port 3080` | 官方默认端口；服务地址 `http://127.0.0.1:3080` |
| token URL | 每次启动官方打印带 token 的 URL，浏览器凭 cookie 交接；本工具日志区实时透出该输出 |

> 参考：npm dist-tag `latest` = `0.1.1-rc.2`（master 分支 `0.1.2-alpha.2`）。本工具启动时会在状态卡片显示官方最新版本，便于判断是否升级。

## 截图（运行中）

- **标题区**：DSH Desktop · 版本号
- **状态卡片**：实时显示服务状态（未运行/启动中/运行中/外部实例），右侧显示 Web UI URL
- **按钮区**：三个大尺寸按钮（开启服务-绿色 / 关闭服务-红色 / 打开DSH-蓝色）
- **日志区**：实时显示子进程 stdout/stderr

## 环境要求

- Python 3.8+
- Node.js（提供 `npx`）

## 快速开始

```bash
# 1. 安装 Python 3.8+ 与 Node.js（如未安装）
# 2. 进入项目目录
cd d:/3.aidata/ai/DSH-Desktop

# 3. 运行
python main.py
```

## 打包为 EXE（可直接双击运行）

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "DSH-Desktop" main.py
```

打包后产物位于 `dist/DSH-Desktop.exe`，**双击即可运行，无需 Python 环境**。可发送给他人直接使用。

## 关闭服务说明

- **本应用启动的服务**：Windows 下通过 `taskkill /F /T /PID <pid>` 终止 npx 进程树，确保 `npx`、`node` 及其子进程全部结束。
- **外部实例**（端口被非本应用启动的进程占用）：弹窗列出占用进程 PID，确认后执行 `taskkill /F /T` 强制结束，并等待端口释放（最多 3 秒）。

## 退出行为

- 服务**未运行**时关闭窗口 → 直接退出
- 服务**运行中**时关闭窗口 → 弹窗确认是否关闭服务并退出

## 已知限制

- 仅在 Windows 10/11 验证；其他平台代码兼容但未实测
- UI 使用 tkinter，外观较朴素

## 许可

仅供个人使用。
