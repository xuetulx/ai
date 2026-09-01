# 版本迭代日志

## v1.13 (2026-09-01)
- **变更类型**: 文档新增 + 规则同步
- **变更摘要**: 新增 GitHub 推送网络排查（Watt Toolkit 加速模式）文档，并同步至 ai-rules 与 DSH 插件规则
- **影响文件**:
  - 新增: `07-TROUBLESHOOTING/2026-09-01-GitHub推送WattToolkit加速排查.md`（frontmatter version 1.0；含现象、9 步诊断过程、识别方法、结论要点）
  - 修改: `06-MCP/Git-MCP-网络连接失败排查与修复.md`（version 1.0 → 1.1；新增 §7 Watt Toolkit 加速模式附录：方案速查/判定命令/修复动作/实战记录）
  - 修改: `ai-rules/GeneralRules/04_version_control.md`（v1.4 → v1.5；新增 §8 GitHub 网络代理排查要点）
  - 修改: `ai-rules/split/File-operation-rules/09_版本控制与Git规则.md`（新增 §10.5）
  - 修改: `DSH-Desktop/dsh-Plugin/dsh-plugin-rules/rules/File-operation-rules/09_版本控制与Git规则.md`（同步 §10.5）
  - 修改: `DSH-Desktop/dsh-Plugin/dsh-plugin-gitops/rules/02_git_mcp_troubleshooting.md`（新增 §4 Watt Toolkit 要点）
  - 修改: `DSH-Desktop/dsh-Plugin/dsh-plugin-gitops/package.json` + `README.md`（1.0.0 → 1.0.1）
- **核心要点**: Watt Toolkit（Steam++）加速 = hosts 劫持 + 本地 80/443 透明转发，git 不配代理直连即走加速；Clash 类代理才需显式 `http.proxy`；代理端口 `CONNECT 405` 禁止沿用
- **配套动作**: 已备份原文件 `*_backup_20260901.bak`

## v1.12 (2026-08-31)
- **变更类型**: 文档新增
- **变更摘要**: 新增 `07-TROUBLESHOOTING/` 问题排查归档：DSH Doctor 弹窗（计划任务）根因与方案 C（隐藏窗口）、`$` 变量被 cmd 吞掉等 Shell 踩坑清单
- **影响文件**:
  - 新增: `07-TROUBLESHOOTING/2026-08-31-DSH-Doctor弹窗与Shell变量坑.md`（frontmatter version 1.0；含排查过程、根因、方案 C 步骤、验证结果、6 个连带坑、可复用经验清单）
- **配套动作**: 无（纯文档）

## v1.11 (2026-08-31)
- **变更类型**: 部署收尾
- **变更摘要**: 运行 deploy-codebuddy.ps1 完成规则部署，清理部署脚本备份
- **影响文件**:
  - 部署: `rules\04-git-mcp-troubleshooting.md` → `C:\Users\Administrator\.codebuddy\rules\`（10 文件 + settings.json 一致性校验通过）
  - 删除: `deploy-codebuddy.ps1.bak`
- **配套动作**: 重新加载/重启 CodeBuddy 后新规则生效（按需触发：MCP 网络失败场景）

## v1.10 (2026-08-31)
- **变更类型**: 规则挂载
- **变更摘要**: 将 Git-MCP 网络排查文档挂载为 Agent-Requested 按需加载规则（单一事实源指向 06-MCP 完整指南）
- **影响文件**:
  - 新增: `02-RULE/Agent-Requested/04-git-mcp-troubleshooting.mdc`（frontmatter version 1.0，alwaysApply: false，来源指向 `06-MCP/Git-MCP-网络连接失败排查与修复.md`）
- **配套动作**: 运行 deploy-codebuddy.ps1 将规则部署到 CodeBuddy 用户级规则目录生效
- **追加变更**: deploy-codebuddy.ps1 `$files` 清单新增 `04-git-mcp-troubleshooting.mdc → rules\04-git-mcp-troubleshooting.md`（备份 `.bak`）

## v1.9 (2026-08-31)
- **变更类型**: 文档新增
- **变更摘要**: 新增 Git/GitHub MCP 网络连接失败排查与修复指南（可直接被任何 AI 工具读取应用）
- **影响文件**:
  - 新增: `06-MCP/Git-MCP-网络连接失败排查与修复.md`（诊断步骤、修复配置片段、验证脚本、踩坑清单、实战案例；frontmatter version 1.0）
- **配套动作**: 无（纯文档）

## v1.8 (2026-08-31)
- **变更类型**: 故障修复
- **变更摘要**: 修复 GitHub MCP 连接报"网络失败"——根因是 node 子进程访问 `api.github.com` TLS 证书校验失败（Clash MITM 证书不被 node 默认 CA 信任），为 GitHub server 注入代理环境变量
- **影响文件**:
  - 修改: `.mcp.json`（GitHub server `env` 新增 `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` = `127.0.0.1:7897`，保留 `NODE_OPTIONS: --use-system-ca`；原文件备份为 `.mcp.json.bak`）
- **诊断依据**: 终端实测 node 直连/走代理均报 `UNABLE_TO_VERIFY_LEAF_SIGNATURE`；`node --use-system-ca` + 代理后返回 200；git 链路正常；Windows 系统代理关闭（ProxyEnable=0），Clash Verge TUN 模式接管流量
- **配套动作**: 重载 MCP / 重启 CodeBuddy 生效；访问私有仓库需在 env 添加 `GITHUB_PERSONAL_ACCESS_TOKEN` 环境变量引用

## v1.6 (2026-08-25)
- **变更类型**: 配置修复
- **变更摘要**: 用户级 MCP 配置占位符替换为环境变量引用；新增项目级 `.mcp.json`
- **影响文件**:
  - 修改: `~/.codebuddy/mcp.json`（`<API_TOKEN_HERE>`/`<YOUR_TOKEN>` 占位符 → `${CNB_API_TOKEN}`/`${GITHUB_PERSONAL_ACCESS_TOKEN}`；原文件备份为 `mcp.json.bak`）
  - 新增: `.mcp.json`（项目级，IDE 已监听该路径，环境变量引用可安全入库）
- **配套动作**: 需设置环境变量 `CNB_API_TOKEN`、`GITHUB_PERSONAL_ACCESS_TOKEN` 后重启 CodeBuddy 生效
- **诊断依据**: IDE 日志实证 hooks/rules 一直正常执行；失效根因是 MCP token 占位符未替换（`configSource: user`）+ 废弃命名 `mcp.json`（官方推荐 `~/.codebuddy/.mcp.json`）

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

## v1.7 (2026-08-25)
- **变更类型**: 功能补充
- **变更摘要**: 补齐 06-MCP 文件操作 MCP 服务器配置；新增 DSH 工作区整理文档
- **影响文件**:
  - 新增: `06-MCP/README.md`（文件操作 MCP 说明，Claude/CodeBuddy + DSH 双格式）
  - 新增: `06-MCP/mcp.filesystem.json`（官方 filesystem server 配置片段）
  - 新增: `D:\3.aidata\dsh\docs\ai-file-operations-config.md`（Agent/Rules/MCP/Skill/插件五类总览）
- **配套动作**: 可选 —— 将 filesystem MCP 写入项目 `.mcp.json` 或 DSH `cordis.patch.yml` 启用
