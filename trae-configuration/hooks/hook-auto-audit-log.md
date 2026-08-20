---
name: hook-auto-audit-log
description: "Hook: 自动追加审计日志。Write/Edit/Delete 执行后自动追加 .ai_audit.log 审计记录。"
hook_type: PostToolUse
watch_tools: [Write, Edit, Delete]
version: 1.0
last_updated: 2026-07-28
---

# Hook-5：自动追加审计日志

> 来源：04_version_control §5.2 + 01_core_behavior 验证闭环步骤5

## 拦截逻辑

```
触发条件：Write / Edit / Delete 执行后
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

## Trae 配置参考

> Trae IDE 不直接支持用户级 Hook，需通过插件或项目级 settings.json 实现。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|Delete",
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import json, sys, os; from datetime import datetime; d = json.load(sys.stdin); op = d.get('tool_name','?'); fp = d.get('tool_input',{}).get('filePath','?'); ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S'); print(f'==== {ts} | 操作: {op} | 路径: {fp} | 结果: OK ====\\n', file=open(os.path.join(os.path.dirname(fp) if os.path.dirname(fp) else '.', '.ai_audit.log'), 'a'))\""
          }
        ]
      }
    ]
  }
}
```
