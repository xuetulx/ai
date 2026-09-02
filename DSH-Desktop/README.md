# DSH Desktop

> DeepSeek Harness 桌面控制器 v1.4.0

一个轻量级 Windows 桌面应用，用于控制 [DeepSeek Harness (DSH)](https://www.npmjs.com/package/@deepseek-ai/dsh) 本地服务的启停与访问。

## 功能

| 按钮       | 作用                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| 开启服务   | 扫描 `dsh-Plugin/` 插件，**有改动**才弹"便携插件管理"窗勾选注册（无改动直接启动），再后台执行 `dsh web --no-open` 启动 Web UI（端口 3080） |
| 关闭服务   | 终止本应用启动的进程树；若端口被外部实例占用，可强制结束占用进程         |
| 打开DSH    | 在系统默认浏览器中打开 `http://127.0.0.1:3080`                          |
| 版本感知   | 启动时后台查询 npm 上 `@deepseek-ai/dsh` 的 latest 版本，显示在状态卡片   |

## 便携插件机制（v1.3.0 引入，v1.4.0 指纹感知）

`DSH-Desktop/dsh-Plugin/` 下归置便携插件源（本地 checkout 或已构建产物），随 `DSH-Desktop` 文件夹一起便携迁移。换新环境时无需手动 `dsh plugin add`：

- 每次点"开启服务"扫描 `dsh-Plugin/` 下所有含 `package.json` 的子目录，计算指纹（目录名 + 文件树内容 sha256，跳过 `node_modules` 等生成目录）
- **插件无改动** → 不弹窗，直接启动；**有改动**（新增/移除插件、改 `package.json` 或插件内文件）→ 弹出**便携插件管理**窗，显示名称 / 版本 / 已安装状态
- 默认勾选 `dsh-plugin-guard` 与 `dsh-market`（已安装项也默认勾选，重复注册幂等）
- 确认后随服务启动自动 `dsh plugin --profile web add link:<路径>` 注册到 web profile
- 跳过 / 取消 = 不注册直接启动；注册失败不阻断启动（仅日志告警）
- 指纹状态存于 `$DSH_HOME/dsh-desktop/plugin-state.json`；删除该文件可强制下次启动重新弹窗

当前 `dsh-Plugin/` 下内置：

| 目录              | 包名             | 版本   | 说明                                   |
| ----------------- | ---------------- | ------ | -------------------------------------- |
| dsh-plugin-guard  | dsh-plugin-guard | 1.3.0  | 插件冲突 / 启动风险监控器，一键禁用启用 |
| dsh-market        | dshmarket        | 1.15.0 | 可视化插件市场，浏览 / 搜索 / 一键安装  |
| dsh-plugin-rules  | dsh-plugin-rules | 1.0.0  | 规则注入：同步 `rules/` 到 `$DSH_HOME/AGENTS.md`（零依赖，自启动生效） |
| dsh-plugin-hardbound | dsh-plugin-hardbound | 1.0.0 | 全局硬边界规则插件（零依赖） |
| dsh-plugin-gitops | dsh-plugin-gitops | 1.0.0 | Git 工作流规则插件（零依赖） |
| dsh-plugin-engineering | dsh-plugin-engineering | 1.0.0 | 工程质量规则插件（零依赖） |

> 规则类插件（rules/hardbound/gitops/engineering）启动时自动把规则合并写入 `$DSH_HOME/AGENTS.md`，**不依赖弹窗注册**也随服务生效；弹窗勾选主要用于 guard / market 的 `dsh plugin add link:` 注册。

> 要新增便携插件：把插件源（含 `package.json`，声明 `dsh.bundle.patch`）放入 `dsh-Plugin/`，启动器会自动识别。如需默认勾选，把目录名加入 `app_config.py` 的 `DEFAULT_LOCAL_PLUGINS`。

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

> **重要**：EXE 必须与 `dsh-Plugin/` **同级摆放**（放到 `DSH-Desktop/` 根目录），否则便携插件扫描会指向 EXE 所在目录下不存在的 `dsh-Plugin/`（如 `dist/dsh-Plugin/`），导致插件管理弹窗不出现、guard/market 无法自动注册。这是 v1.3.9 已知坑，v1.4.0 未改变该约束。

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
