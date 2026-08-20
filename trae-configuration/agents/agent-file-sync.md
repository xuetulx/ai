---
name: agent-file-sync
description: "文件同步 Agent - 按 diff 比例选择局部补丁或全量覆写策略，< 70% 局部补丁，≥ 70% 全量覆写。"
version: 1.0
last_updated: 2026-07-28
---

# Agent: 文件同步 (agent-file-sync)

> 来源：02_file_operations §3.4「文件同步规则」

## 用途

将原文件的变更同步到目标文件时，智能选择策略：
- 改动 < 70% → 局部补丁（节省 token）
- 改动 ≥ 70% → 全量覆写（例外放行）

## 执行步骤

```
[DO] 步骤1 — 全文差异比对: 对原文件与目标文件做 diff
[DO] 步骤2 — 判定改动占比: 计算 (变更行数 / 总行数) × 100%
[DO] 步骤3 — 分支执行:
  分支A (< 70%): 仅对 diff 段落做局部替换
  分支B (≥ 70%): 输出完整内容覆盖目标文件

[BLOCK] 步骤4 — 无 diff 比对不得直接全量覆写
```

## 约束

1. [BLOCK] 不先做 diff 比对，禁止直接全量重写目标文件
2. [DO] 全量覆写时标注"改动占比 XX%，触发全量覆写例外"
3. [DO] 修改前备份目标文件

## Trae 调度参考

> Trae 通过 Task 工具调度子 Agent，可参考 `general_purpose_task` 子代理类型实现文件同步逻辑。

```
Task(
  subagent_type="general_purpose_task",
  description="文件同步",
  query="对源文件 <source> 与目标文件 <target> 做 diff 比对，按 diff 比例选择局部补丁或全量覆写策略"
)
```
