# DSH Desktop

> DeepSeek Harness 桌面控制器 v1.0.0

一个轻量级 Windows 桌面应用，用于控制 [DeepSeek Harness (DSH)](https://www.npmjs.com/package/@deepseek-ai/dsh) 本地服务的启停与访问。

## 功能

| 按钮       | 作用                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| 开启服务   | 后台执行 `npx @deepseek-ai/dsh web --no-open`，启动 Web UI（端口 3080）  |
| 关闭服务   | 终止上述进程及其子进程树                                                 |
| 打开DSH    | 在系统默认浏览器中打开 `http://127.0.0.1:3080`                          |

## 截图（运行中）

- **标题区**：DSH Desktop · 版本号
- **状态卡片**：实时显示服务状态（未运行/运行中），右侧显示 Web UI URL
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

### 方式一：双击一键打包（推荐）

**双击 `build.bat`**，脚本会自动：
1. 检查/安装 PyInstaller
2. 打包为单文件 `dist/DSH-Desktop.exe`（无控制台窗口）

### 方式二：命令行

```bash
pip install pyinstaller
pyinstaller DSH-Desktop.spec
# 或
pyinstaller --noconfirm --onefile --windowed --name "DSH-Desktop" main.py
```

打包后产物位于 `dist/DSH-Desktop.exe`，**双击即可运行，无需 Python 环境**。可发送给他人直接使用。

## 关闭服务说明

Windows 下通过 `taskkill /F /T /PID <pid>` 终止 npx 进程树，确保 `npx`、`node` 及其子进程全部结束。

## 退出行为

- 服务**未运行**时关闭窗口 → 直接退出
- 服务**运行中**时关闭窗口 → 弹窗确认是否关闭服务并退出

## 已知限制

- 仅在 Windows 10/11 验证；其他平台代码兼容但未实测
- UI 使用 tkinter，外观较朴素

## 许可

仅供个人使用。
