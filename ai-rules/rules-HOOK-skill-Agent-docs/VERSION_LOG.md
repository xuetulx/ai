# 版本迭代日志

## v1.0 (2026-07-28)
- **变更类型**: 重大架构重构
- **变更摘要**: 将原 8 个 always_applied 规则文件（~2500 行）拆分为 HOOK/RULE/SKILL/AGENT/docs 五层架构
- **影响文件**:
  - 新增: 01-HOOK/ (5个Hook), 02-RULE/ (4个Rule), 03-SKILL/ (3个Skill), 04-AGENT/ (2个Agent定义)
  - 归档: 05-docs/archived/ (原8个规则文件)
  - 新增: README.md (总索引)
- **核心思路**:
  - Hook 层: 5 项「绝对不能漏的硬约束」改为程序拦截
  - Rule/Always: 极简到 ≤30 行，仅放三级边界清单
  - Rule/Agent-Requested: 代码规范类改为 glob 精准匹配
  - Skill: 安全审查、代码审查、Git 工作流改为手动触发
  - Agent: 验证、文件同步改为隔离执行
