# 版本迭代日志

## v1.5 (2026-08-20)
- **变更类型**: 流程优化
- **变更摘要**: 部署流程升级为"单一事实源 + 三重校验"
- **影响文件**:
  - 新增: settings.json.template（hooks 配置单一事实源，消除脚本/指南/部署结果三处重复维护）
  - 修改: deploy-codebuddy.ps1（改为从模板生成 settings.json；新增 python 依赖检查、hooks 结构校验、源与部署 MD5 一致性校验）
  - 修改: 05-docs/CodeBuddy-配置指南.md（8.1 一键脚本说明更新为四步流程）
- **优化收益**: 配置改动只维护一份模板；脚本自动拦截"部署结果漂移"（JSON 非法 / hook 缺失 / 文件不一致），杜绝静默失效

## v1.4 (2026-08-20)
- **变更类型**: 功能增强
- **变更摘要**: 备份文件新增确认删除机制（修改完成提示清理 + 删除时强制确认）
- **影响文件**:
  - 修改: 01-HOOK/hook-backup-before-edit.md（新增"备份清理确认流程"章节，version 1.2）
  - 修改: 05-docs/CodeBuddy-配置指南.md（settings.json 示例新增 2 个 hook；Hook 功能表/映射表/8.3 同步）
  - 修改: deploy-codebuddy.ps1（settings.json 新增 confirm-backup-delete + backup-cleanup-prompt）
- **优化收益**: 修改完成后提示清理备份；删除 `.bak` 前强制用户确认，形成"备份→修改→确认→清理"完整闭环，避免备份堆积

## v1.3 (2026-08-20)
- **变更类型**: 规则优化
- **变更摘要**: 追加式文件（日志/变更记录）免除 .bak 备份
- **影响文件**:
  - 修改: 01-HOOK/hook-backup-before-edit.md（例外放行新增"追加式文件"类别，version 1.1）
  - 修改: 02-RULE/Always/00-hard-boundaries.mdc（硬边界第 7 条补充例外，version 1.1）
  - 修改: 05-docs/CodeBuddy-配置指南.md（settings.json 示例 / 功能表 / 硬边界副本 / 8.3 注意事项同步）
  - 修改: deploy-codebuddy.ps1（backup hook 命令排除 `*.log`、`VERSION_LOG.md`、`CHANGELOG.md`）
- **优化收益**: 日志/变更记录类文件只追加不覆盖，原内容始终保留；不再产生无意义的 `*.bak` 噪音文件

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
