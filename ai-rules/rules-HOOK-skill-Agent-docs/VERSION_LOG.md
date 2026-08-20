# 版本迭代日志

## v1.2 (2026-08-20)
- **变更类型**: 部署优化
- **变更摘要**: 新增一键部署脚本；源文件 frontmatter 补齐 `name`；修正 settings.json 示例格式
- **影响文件**:
  - 新增: deploy-codebuddy.ps1（幂等一键部署：复制 rules/skills/agents + 生成 settings.json + JSON 校验）
  - 修改: 03-SKILL/*/SKILL.md、04-AGENT/*.md（frontmatter 补 `name`，复制后即符合 CodeBuddy 格式）
  - 修改: 05-docs/CodeBuddy-配置指南.md（matcher 改为无引号正则；敏感文件拦截退出码 1→2；第八节推荐一键脚本）
  - 修改: README.md（导航新增部署脚本入口）
- **优化收益**: 下次部署从手工 12+ 步缩短为运行 1 条命令；消除部署后手工补 `name` 的步骤；避免 matcher/退出码两个格式坑

## v1.1 (2026-07-28)
- **变更类型**: 文档完善
- **变更摘要**: 新增 CodeBuddy 用户级部署配置指南
- **影响文件**:
  - 新增: 05-docs/CodeBuddy-配置指南.md（完整部署流程、映射关系、验证步骤）
  - 修改: README.md（导航新增配置指南入口）

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
