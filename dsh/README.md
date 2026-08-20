# DSH Web Server Launcher

一键启动 [DeepSeek DSH](https://www.npmjs.com/package/@deepseek-ai/dsh) Web 服务器的 Windows 批处理脚本。

## 文件说明

| 文件 | 说明 |
| ---- | ---- |
| `run-dsh-web.bat` | 一键启动脚本：启动 DSH Web 服务器并自动以应用模式打开 Edge 窗口 |

## 使用方式

双击 `run-dsh-web.bat` 即可。

启动流程：

1. 检测端口 `3080` 是否已有服务在运行
   - 若已运行，直接打开 Edge 应用窗口，跳过重复启动
   - 若未运行，继续执行后续步骤
2. 检查 `npx` 是否可用（依赖 Node.js）
3. 后台轮询等待服务就绪（最长 120 秒），就绪后自动打开 Edge 应用窗口
4. 前台运行 `npx --yes @deepseek-ai/dsh web` 启动服务器

## 前置依赖

- **Node.js**（提供 `npx` 命令）
- **Microsoft Edge**（用于打开应用窗口；未安装时会自动回退到系统默认浏览器）

## 注意事项

- 默认端口为 `3080`，如需修改可编辑脚本顶部的 `PORT` / `URL` 变量
- 服务器地址：`http://127.0.0.1:3080/`
- 首次运行 `npx` 会自动下载 `@deepseek-ai/dsh` 包，需要网络连接
