---
name: hook-block-git-manipulation
description: "Hook: 拦截直接操作 .git/ 目录。阻止直接读写 .git/ 内部文件，必须通过 git 命令间接操作。"
hook_type: PreToolUse
watch_tools: [Read, Write, Edit, RunCommand]
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
❌ Read .git/HEAD                                   # 直接读取
❌ Write .git/config                                # 直接写入
❌ Edit .git/...                                    # 直接修改
```

## 注意事项

- `.gitignore`、`.gitattributes` 不在拦截范围（它们是项目配置文件，非 .git 内部对象）
- `RunCommand` 中的 git 命令需要区分：`git <subcommand>` 放行，`cat .git/HEAD` 拦截

## Trae 配置参考

> Trae IDE 不直接支持用户级 Hook，需通过插件或项目级 settings.json 实现。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import sys; path=sys.argv[1].replace('\\\\','/'); parts=path.split('/'); exit(1 if '.git' in parts and path.endswith(('.gitignore','.gitattributes'))==False else 0)\" ${FILE_PATH}"
          }
        ]
      }
    ]
  }
}
```
