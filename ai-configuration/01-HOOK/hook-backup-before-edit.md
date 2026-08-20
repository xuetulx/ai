---
description: "Hook: 修改文件前强制自动备份（追加式文件除外）+ 备份确认删除"
hook_type: [PreToolUse, PostToolUse]
watch_tools: [replace_in_file, write_to_file, delete_file]
version: 1.2
last_updated: 2026-08-20
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

以下**追加式文件**无需备份（只追加不覆盖，原内容始终保留，备份无意义）：
- `*.log` 日志文件（含 `.ai_audit.log` 审计日志）
- `VERSION_LOG.md`、`CHANGELOG.md` 变更记录文件

## 备份清理确认流程（v1.2 新增）

修改完成后，备份文件通过"确认删除"机制闭环清理，避免 `.bak` 无限堆积：

```
修改前  → 自动创建 .bak 备份
修改后  → backup-cleanup-prompt (PostToolUse)：
           检测到 .bak 存在 → 向用户显示提示，并提醒 Agent
           询问用户是否确认修改结果无误
删除时  → confirm-backup-delete (PreToolUse)：
           删除 .bak 文件前强制弹权限确认框 (permissionDecision: ask)
           用户确认"新文件已验证"后才放行删除
```

配置要点：

```json
{
  "matcher": "delete_file",
  "hooks": [{
    "type": "command",
    "command": "python -c \"... permissionDecision: 'ask', permissionDecisionReason: 'Delete backup file? Confirm the new file is verified first.' ...\""
  }]
}
```

- `permissionDecision: "ask"` 会弹出权限确认框，用户点击确认后才执行删除
- `permissionDecisionReason` 是确认框中展示给用户的说明文案
- Agent 遵循流程：修改完成 → 询问用户是否删除备份 → 用户确认后才调用 `delete_file` 清理 `.bak`

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
