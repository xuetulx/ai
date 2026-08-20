---
description: "Hook: 拦截直接操作 .git/ 目录"
hook_type: PreToolUse
watch_tools: [read_file, write_to_file, replace_in_file, execute_command]
version: 1.0
last_updated: 2026-07-28
---

# Hook-3：拦截直接操作 .git/

> 来源：01_core_behavior §2.1 #3 + 04_version_control §1

## 拦截逻辑

```
触发条件：任何文件操作目标路径包含 .git/（非 git 命令方式）
拦截动作：
  1. 检测路径是否为 .git/ 内部文件或目录
  2. 是 → 阻断操作
  3. 提示：应通过 git 命令间接操作版本控制
```

## 允许的操作

```
✅ git status / git log / git diff / git branch     # 通过 git 命令
❌ read_file .git/HEAD                              # 直接读取
❌ write_to_file .git/config                         # 直接写入
❌ replace_in_file .git/...                          # 直接修改
```

## 注意事项

- `.gitignore`、`.gitattributes` 不在拦截范围（它们是项目配置文件，非 .git 内部对象）
- `execute_command` 中的 git 命令需要区分：`git <subcommand>` 放行，`cat .git/HEAD` 拦截

## Claude Code 配置参考

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "read_file|write_to_file|replace_in_file",
      "hooks": [{
        "type": "command",
        "command": "python -c \"import sys; path=sys.argv[1].replace('\\\\','/'); parts=path.split('/'); exit(1 if '.git' in parts and path.endswith(('.gitignore','.gitattributes'))==False else 0)\" ${FILE_PATH}"
      }]
    }]
  }
}
```
