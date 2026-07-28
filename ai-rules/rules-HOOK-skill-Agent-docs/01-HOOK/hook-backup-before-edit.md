---
description: "Hook: 修改文件前强制自动备份"
hook_type: PreToolUse
watch_tools: [replace_in_file, write_to_file]
version: 1.0
last_updated: 2026-07-28
---

# Hook-1：修改前强制备份

> 来源：01_core_behavior §2.1 #11 + 02_file_operations §3.3 #0

## 拦截逻辑

```
触发条件：调用 replace_in_file 或 write_to_file（覆盖模式）时
拦截动作：
  1. 检查目标文件是否已存在
  2. 若存在 → 检查是否已有同日 .bak 备份
  3. 若无备份 → 阻止操作，要求先执行：
     copy <原文件> <原文件名>_v{版本号}.bak
  4. 验证备份文件存在且内容一致
  5. 放行原操作
```

## 备份命名规则

```
原文件名.py          → 原文件名_v1.0.bak
原文件名_v1.0.py     → 原文件名_v1.0_backup_20260728.bak
```

## 例外放行场景

以下场景无需备份（因为是创建新文件，不会覆盖）：
- `write_to_file` 目标路径不存在（创建模式）
- 文件在 `tmp/`、`.temp/`、`.cache/` 目录下（临时文件）

## Claude Code 配置参考

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "replace_in_file|write_to_file",
        "hooks": [{
          "type": "command",
          "command": "python .claude/hooks/backup_before_edit.py ${ARGS}"
        }]
      }
    ]
  }
}
```

## 等效 Rule 表达（Cursor 等不支持 Hook 的工具）

```markdown
[BLOCK] 禁止在未创建 .bak 备份的情况下对任何现有文件
执行 replace_in_file 或 write_to_file（覆盖模式）。
修改前必须: (a) 创建备份 (b) 验证备份完整性 (c) 方可修改。
```
