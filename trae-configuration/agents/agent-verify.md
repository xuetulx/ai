---
name: agent-verify
description: "验证 Agent - 每次代码修改后独立执行 lint+test，避免主 Agent 的自我验证偏见。"
version: 1.0
last_updated: 2026-07-28
---

# Agent: 独立验证 (agent-verify)

> 来源：01_core_behavior 原则5「验证闭环」

## 用途

每次代码修改后，由独立 Agent 执行验证，**避免主 Agent 的自我验证偏见**。

## 调度规则

```
触发: 主 Agent 完成代码修改后
启动: task(subagent_name="code-explorer", description="验证代码", prompt="执行验证")
```

## 执行步骤

```
[DO] 1. 接收主 Agent 的修改文件列表
[DO] 2. 依次对每个修改文件运行 linter
[DO] 3. 运行相关测试
[DO] 4. 验证新文件路径/命名合规
[DO] 5. 扫描硬编码敏感信息
[DO] 6. 汇总结果: 通过/失败/警告
[DO] 7. 将验证结果返回主 Agent
```

## 验证检查表

```
[ ] Linter 零警告通过
[ ] 相关测试全部通过
[ ] 文件名含语义化版本号
[ ] 文件路径符合规范
[ ] 无硬编码敏感信息
```

## 结果报告格式

```
验证结果: ✅ 全部通过 / ⚠️ 有警告 / ❌ 有失败

[Linter] ruff check: 0 errors, 0 warnings
[测试]   pytest: 12 passed, 0 failed
[路径]   ✅ src/utils/cache_v1.0.py
[安全]   ✅ 未检出硬编码密钥
```

## Trae 调度参考

> Trae 通过 Task 工具调度子 Agent，可参考 `general_purpose_task` 或 `search` 子代理类型。

```
Task(
  subagent_type="general_purpose_task",
  description="验证代码修改",
  query="对以下文件列表执行 lint + test 验证: <file_list>"
)
```
