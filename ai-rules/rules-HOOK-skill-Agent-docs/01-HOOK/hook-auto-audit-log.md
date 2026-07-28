---
description: "Hook: 自动追加审计日志"
hook_type: PostToolUse
watch_tools: [write_to_file, replace_in_file, delete_file]
version: 1.0
last_updated: 2026-07-28
---

# Hook-5：自动追加审计日志

> 来源：04_version_control §5.2 + 01_core_behavior 验证闭环步骤5

## 拦截逻辑

```
触发条件：write_to_file / replace_in_file / delete_file 执行后
动作：
  1. 记录时间戳、操作类型、目标路径
  2. 追加到当前项目根目录 .ai_audit.log
  3. 格式:
     ====
     [2026-07-28 18:30:00] | 操作: 修改 | 路径: src/main.py | 结果: 成功
     ====
```

## 审计日志格式

```
============================================================
[日期时间] | 操作: 创建/修改/删除 | 结果: 成功/失败
  路径: <完整路径>
  摘要: <变更描述>
  验证: linter=通过, tests=通过
============================================================
```

## 约束

- 仅追加（append），不得修改或删除已有记录
- 日志文件：`.ai_audit.log`，存放在项目根目录
- 每次操作一条记录，批量操作合并为一条（标注文件数量）

## Claude Code 配置参考

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "write_to_file|replace_in_file|delete_file",
      "hooks": [{
        "type": "command",
        "command": "python .claude/hooks/append_audit_log.py ${TOOL} ${FILE_PATH} ${STATUS}"
      }]
    }]
  }
}
```
