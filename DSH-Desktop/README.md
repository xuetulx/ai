# DSH Desktop

> DeepSeek Harness 桌面控制器 v1.0.5

一个轻量级 Windows 桌面应用，用于控制 [DeepSeek Harness (DSH)](https://www.npmjs.com/package/@deepseek-ai/dsh) 本地服务的启停与访问。

## 功能

| 按钮       | 作用                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| 开启服务   | 后台执行 `npx @deepseek-ai/dsh web --no-open`，启动 Web UI（端口 3080）            |
| 关闭服务   | 终止本应用启动的进程树；若端口被外部实例占用，可强制结束占用进程         |
| 打开DSH    | 在系统默认浏览器中打开 `http://127.0.0.1:3080`                          |

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
