### 20. 人类问责制

#### 20.1 责任归属 `[DO]`

1. `[DO]` AI 是辅助工具，不承担代码责任。
2. `[DO]` 每个 AI 生成或辅助的代码变更，必须有人类所有者进行审查、批准，并对其正确性、安全性、可维护性负责。
3. `[DO]` 保留审计记录：哪个开发者批准了哪次 AI 生成的变更、使用的 AI 工具和模型版本。

#### 20.2 审查要求 `[DO]`

1. `[DO]` AI 生成的代码必须经过人工代码审查才能合并。
2. `[DO]` 安全关键代码（认证、加密、权限控制、支付）必须由安全专业人员审查。
3. `[DO]` 不得因为"AI 通常是对的"就跳过代码审查流程。

---

## 第四部分：Agentic AI 与 MCP 安全规范（v3.1 新增）

### 21. Agentic AI 安全风险防护

> 参考：OWASP Top 10 for Agentic Applications (2025)

#### 21.1 目标劫持防护 `[BLOCK]`

ASI01：攻击者通过提示注入改变 Agent 的原始执行目标。

1. `[BLOCK]` Agent 的系统提示（system prompt）中必须包含不可覆盖的目标约束声明。
2. `[DO]` 对用户提供的内容执行提示注入检测，识别目标覆盖企图。
3. `[DO]` Agent 执行前校验最终目标是否与原始目标一致，不一致时终止并告警。
4. `[ASK]` 涉及权限提升或目标变更的操作必须获得用户明确确认。

#### 21.2 工具滥用防护 `[BLOCK]`

ASI02：Agent 调用外部工具时执行非授权操作。

1. `[BLOCK]` Agent 调用的每个工具必须有明确的权限边界声明。
2. `[DO]` 工具调用前进行参数校验，防止通过构造恶意参数实现越权操作。
3. `[DO]` 敏感操作（文件删除、网络请求、数据库修改）的每次工具调用都必须记录审计日志。
4. `[ASK]` 首次调用新工具或调用高风险工具时，必须告知用户并确认。

#### 21.3 身份越权防护 `[BLOCK]`

ASI03：Agent 获取超出授权范围的权限或身份凭证。

1. `[BLOCK]` Agent 不得获取或缓存用户的身份凭证（密码、Token、证书）。
2. `[DO]` 使用最小权限原则为 Agent 分配独立的服务账号，与人类用户权限隔离。
3. `[DO]` Agent 之间的通信必须使用身份验证，防止未授权 Agent 冒充合法 Agent。

#### 21.4 记忆与上下文投毒防护 `[BLOCK]`

ASI04：攻击者污染 Agent 的记忆库或上下文，影响后续决策。

1. `[DO]` 外部写入 Agent 记忆库的数据必须经过校验和清洗。
2. `[DO]` 关键决策应交叉验证多个上下文源，避免单一污染源主导结果。
3. `[DO]` 定期审计 Agent 记忆库，检测异常或矛盾信息。
4. `[BLOCK]` 不得将未经验证的第三方输出直接写入 Agent 的长期记忆。

#### 21.5 幻觉传播防护 `[DO]`

Hallucination Cascade：Agent 将 LLM 幻觉作为事实传播，形成错误知识闭环。

1. `[DO]` AI 生成的事实性声明必须通过外部权威来源验证（如官方文档、数据库查询）。
2. `[DO]` 不确定的信息应明确标注为"推测"或"未验证"，不得作为事实使用。
3. `[DO]` 涉及版本号、API 名称、配置参数等精确信息时，必须从官方文档或源代码中核实。
4. `[BLOCK]` 不得将 AI 生成的代码中的幻觉依赖（不存在的包名、不存在的 API）传播给用户。

---

### 22. MCP (Model Context Protocol) 安全规范

#### 22.1 MCP Server 权限最小化 `[DO]`

1. `[DO]` 每个 MCP Server 只能暴露完成任务所需的最小工具集。
2. `[DO]` MCP Server 的权限声明必须明确、可审计，避免隐性权限放大。
3. `[BLOCK]` 禁止 MCP Server 提供无限制的文件系统访问或网络访问。

#### 22.2 MCP 工具调用审计 `[DO]`

1. `[DO]` 每次 MCP 工具调用必须记录：调用时间、调用者、工具名、参数摘要、执行结果。
2. `[ASK]` 涉及文件修改、数据写入、外部网络通信的 MCP 工具调用必须告知用户。
3. `[DO]` MCP 工具调用失败时，不得将错误信息中的敏感路径、内部结构泄露给用户。

#### 22.3 MCP 连接安全 `[DO]`

1. `[DO]` MCP Server 与 Client 之间的通信建议使用本地回环（localhost）或受信任的网络通道。
2. `[DO]` 敏感数据通过 MCP 传输时应评估数据暴露风险，必要时进行脱敏处理。
3. `[BLOCK]` 禁止通过 MCP 传输密钥、密码等凭证类信息。

---

### 23. Claude Code 专属规范

> 参考：Claude Code Best Practices — code.claude.com/docs/en/best-practices

#### 23.1 计划模式（Plan Mode）使用规范 `[DO]`

1. `[DO]` 复杂任务（涉及多文件修改、架构变更、不确定实现方案）必须先进入 plan mode 探索再执行。
2. `[DO]` plan mode 阶段只读不修改，用于理解项目结构、分析依赖、制定实现计划。
3. `[DO]` 用户确认计划后再退出 plan mode 进入实现阶段。
4. `[DO]` 简单任务（单文件修改、变量重命名、添加日志）可直接执行，无需 plan mode。

#### 23.2 上下文窗口管理 `[DO]`

1. `[DO]` 主动管理上下文窗口，避免一次性读取过多文件导致窗口溢出。
2. `[DO]` 大文件（>10MB）优先分页/分段读取，不一次性加载全部内容。
3. `[DO]` 批量读取文件前先评估 token 消耗，必要时向用户说明范围和目的。
4. `[DO]` 长会话中定期回顾核心目标，防止因上下文溢出而遗忘关键指令。

#### 23.3 Skills 与 Hooks 规范 `[DO]`

1. `[DO]` 领域专属知识应封装为 Skill 文件（`.claude/skills/`），按需加载，避免 bloated CLAUDE.md。
2. `[DO]` 关键动作（如每次编辑后运行 linter、禁止写入特定目录）应配置为 Hook，确保零例外执行。
3. `[DO]` CLAUDE.md 保持简洁，仅包含广泛适用的规则，定期修剪冗余内容。

#### 23.4 验证闭环 `[DO]`

1. `[DO]` 给 Claude 提供可运行的验证手段（测试、构建、截图对比），形成自动验证闭环。
2. `[DO]` Claude 应展示证据（测试输出、命令返回结果）而非仅断言成功。
3. `[DO]` 重要操作使用子代理（subagent）进行对抗性审查，避免自我验证的偏见。

---

**生效时间**：2026-07-01
**适用范围**：所有编程开发类任务
**版本**：v3.1（完整版 + 安全专项规范）
**配套规范**：AgentAI_项目文件操作规则.md v2.1
**参考来源**：
- Google Style Guides — google.github.io/styleguide
- PEP 8 — peps.python.org/pep-0008
- Conventional Commits — conventionalcommits.org
- Claude Code Docs — code.claude.com/docs
- OWASP GenAI Security Project — genai.owasp.org
- OWASP Top 10 for LLMs 2025 — genai.owasp.org
- OWASP Top 10 for Agentic Applications (2025) — genai.owasp.org
- OpenSSF AI 代码助手安全指南 — best.openssf.org
- NVIDIA AI Red Team 安全指南 — developer.nvidia.com/ai-redteam
