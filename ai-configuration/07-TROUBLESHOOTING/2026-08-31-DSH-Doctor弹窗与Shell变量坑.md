---
version: 1.0
last_updated: 2026-08-31
---

# DSH Doctor 弹窗与 Shell 变量坑（2026-08-31）

> 本文记录 DSH-Desktop 项目当日排查的两大问题及解决套路：
> 1. **cmd 弹窗** → 根因是 Windows 计划任务 `DSH Doctor Supervisor`（与 EXE、插件无关）
> 2. **`$` 变量被 cmd 吞掉** → execute_command 实际由 cmd 层执行，内联 PowerShell 变量被剥离为空

---

## 一、背景

- 项目：`DSH-Desktop`（Python 3.14.5 + PyInstaller，onefile + windowed）
- 现象起点：用户反馈 EXE 启动时偶发 cmd 黑窗口；v1.0.9 无弹窗、新版本有弹窗
- 排查范围：EXE 打包 → dsh npm 包 → 插件导入 → Windows 计划任务

---

## 二、问题一：cmd 弹窗（DSH Doctor 计划任务）

### 2.1 现象

登录后或 EXE 启动时弹出黑色 cmd 窗口，随即消失；用户截图确认 v1.0.9 EXE 无此弹窗。

### 2.2 排查过程（逐步排除）

| 步骤 | 实验 | 结论 |
|------|------|------|
| 1 | git 对比 v1.0.9 与 v1.1.0 启动逻辑 | 两者 `main.py` 启动链相同，EXE 侧无差异 |
| 2 | 怀疑 dsh npm 包升级后内部 spawn 行为变化 | 不确定，继续实验 |
| 3 | 导入 `dsh-plugin-guard` 插件后弹窗复现 | 疑似插件 → 实验排除 |
| 4 | 禁用 guard 插件仍弹 | 与插件导入无关 |
| 5 | 恢复到导入前 package.json 仍弹 | 彻底排除插件因素 |
| 6 | 定位 conhost/父进程链：`cmd ← svchost(2152) ← services ← wininit` | 弹窗来自**计划任务**托管进程 |
| 7 | `schtasks /query` 找到 `DSH Doctor Supervisor`（2026-08-31 14:55:44 注册，LogonTrigger） | **根因确认** |

### 2.3 根因

- 弹窗来源：Windows 计划任务 **`DSH Doctor Supervisor`**
- 执行链：
  ```
  cmd.exe /c "C:\Users\Administrator\AppData\Local\DSH Doctor\supervisor.cmd"
    → node "C:\Users\Administrator\.dsh\profiles\web\node_modules\@linxin666\dsh-doctor\lib\cli.mjs" supervisor
  ```
- 组件：`@linxin666/dsh-doctor` v0.3.6（DSH 事务性救援组件），**新装 / UI 更新时默认注册用户级计划任务**（登录触发，InteractiveToken）
- 结论：弹窗与 DSH-Desktop EXE、插件导入均无关

### 2.4 解决方案（方案 C：保留救援功能 + 隐藏窗口）

1. **备份**：`supervisor.cmd` → `supervisor.cmd.bak.20260831`
2. **创建隐藏启动器** `supervisor_hidden.vbs`：
   ```vbs
   Dim shell
   Set shell = CreateObject("WScript.Shell")
   shell.Run """C:\Users\Administrator\AppData\Local\DSH Doctor\supervisor.cmd""", 0, False
   Set shell = Nothing
   ```
   - 参数 `0` = 隐藏窗口；`False` = 不等待（wscript 立即退出）
3. **改计划任务动作**（关键：不要用 `schtasks /tr` 手工转义，见 3.3）：
   ```powershell
   $task = Get-ScheduledTask | Where-Object { $_.TaskName -eq 'DSH Doctor Supervisor' }
   $act = $task.Actions[0]
   $act.Execute = "wscript.exe"
   $act.Arguments = '"C:\Users\Administrator\AppData\Local\DSH Doctor\supervisor_hidden.vbs"'
   Set-ScheduledTask -InputObject $task | Out-Null
   ```
4. **验证**：`schtasks /run /tn "DSH Doctor Supervisor"` → Last Result = **0**（此前为 1 失败）；`tasklist | findstr node` 确认守护进程驻留

### 2.5 验证结果与后续注意

- 计划任务动作已变为：`wscript.exe "C:\Users\Administrator\AppData\Local\DSH Doctor\supervisor_hidden.vbs"`（无控制台窗口）
- 救援功能保留：node supervisor 进程正常驻留
- **若 DSH 更新重写 `supervisor.cmd`**：VBS 包装不受影响（仍指向该路径）
- **若 DSH 重新注册计划任务为 cmd 直调**：需重跑上述 2.4 步骤重建

---

## 三、问题二：`$` 变量被 cmd 吞掉（已知坑）

### 3.1 现象

在 execute_command 中执行内联 PowerShell 时，所有 `$变量` 被剥离为空，产生诡异报错：

```
$t = Get-ScheduledTask ...   →  Where-Object { .TaskName -eq ... }   （$t、$_ 全空）
New-Object System.Text.UTF8Encoding($false)  →  'False' is not recognized as a cmdlet
```

典型报错串：
- `Missing condition in if statement after 'if ('.`
- `The term 'False' is not recognized as the name of a cmdlet`

### 3.2 根因

- execute_command 的实际执行包装层是 **cmd**（尽管 user_info 声明 Shell 为 PowerShell）
- cmd 层会把 `$xxx` 当作变量引用展开为空字符串，再传给内联 PowerShell → 语法被破坏
- 这与 PowerShell 语法无关，是**外层 shell 先于内层 PowerShell 处理了 `$`**

### 3.3 解决套路（必守）

1. **不写内联 `-Command`**，一律写成 `.ps1` 脚本文件：
   ```
   write_to_file  .xxx.ps1  （纯 ASCII 内容，避免编码坑，见 4.2）
   powershell -NoProfile -ExecutionPolicy Bypass -File "绝对路径\.xxx.ps1"
   ```
2. 执行成功后**立即删除**临时脚本（或按用户确认保留/清理）
3. 需要管道结果时，脚本内 `Write-Output` 输出到 stdout 读取

正反例对比：

| 写法 | 结果 |
|------|------|
| ❌ `powershell -Command "$t = 1; Write-Output $t"` | `$t` 被剥离 → 语法错误 |
| ✅ 写 `.ps1` + `powershell -File .ps1` | 正常 |

### 3.4 连带坑：PowerShell 5.1 无 BOM UTF-8 中文注释

- 现象：同样逻辑的 Where-Object，纯 ASCII 脚本能查到任务，含中文注释的脚本返回 NOT FOUND
- 根因：PowerShell 5.1 对**无 BOM 的 UTF-8** `.ps1` 按系统 ANSI（GBK）解析，中文注释字节被误读，破坏脚本
- 规避：**`.ps1` 脚本内容保持纯 ASCII**（注释用英文）；文档类（.md）不受影响

---

## 四、附录：本次会话其他坑

| # | 坑 | 现象 | 解决 |
|---|----|------|------|
| 1 | `schtasks /tr` 引号转义 | 路径含空格时 `\"` 在嵌套 shell 下反复报 `Invalid argument/option` | 改用 PowerShell `Set-ScheduledTask`（CIM 赋值自动序列化），彻底绕开转义 |
| 2 | `Get-ScheduledTask -TaskName` 直查失败 | 返回对象 Actions 为 null / 查不到根路径任务 | 用 `Get-ScheduledTask \| Where-Object { $_.TaskName -eq '...' }` |
| 3 | `timeout` 非交互失败 | 报 `ERROR: Input redirection is not supported` | 改用 `ping -n 6 127.0.0.1 >nul` 等待 |
| 4 | `Add-Content` 无编码被拦截 | Craft 安全策略拦截无显式编码写入 | 用 `[System.IO.File]::AppendAllText(path, text, (New-Object System.Text.UTF8Encoding($false)))` 显式无 BOM UTF-8 |
| 5 | `type >>` 追加中文乱码 | GBK 代码页下追加 UTF-8 内容乱码 | 审计日志统一用无 BOM UTF-8 `AppendAllText` 追加 |
| 6 | GBK 中文日志刷屏 | 实验输出被中文日志污染 | 用写文件方式采集结果，避免直接读 stdout |

---

## 五、可复用经验清单

1. **弹窗类问题优先查计划任务**：`schtasks /query /fo LIST /v | findstr /i "Supervisor Doctor dsh"`，看 `Task To Run` 是否含 `cmd.exe` 直调
2. **隐藏窗口三件套**：VBS `Run(..., 0, False)` + 计划任务动作改 `wscript.exe` + `Set-ScheduledTask`
3. **execute_command 内联 PowerShell = 高危**：凡含 `$`、`$_`、引号嵌套、中文的命令一律落盘 `.ps1` 再 `-File` 执行
4. **`.ps1` 保持纯 ASCII**：中文注释是 PowerShell 5.1 的雷
5. **审计/日志追加用 `AppendAllText + UTF8Encoding($false)`**：兼容既有文件、不引 BOM、不被安全策略拦截
