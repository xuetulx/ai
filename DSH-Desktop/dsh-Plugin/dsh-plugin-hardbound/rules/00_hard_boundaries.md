# 全局硬边界

> 来源：ai-configuration/02-RULE/Always/00-hard-boundaries.mdc（每次会话必加载）
> 任何任务、任何阶段均适用；违反任一条即视为任务失败。

## Never [BLOCK]

1. 禁止在项目根目录/授权目录之外创建/修改/删除文件
2. 禁止删除或覆盖用户原始文件不先创建 .bak 备份
3. 禁止读取 *.pem, *.key, *.cert, credentials.*, token*
4. 禁止直接读写 .git/ 目录内部文件（用 git 命令代替）
5. 禁止硬编码密钥/密码/Token（用环境变量）
6. 禁止创建不含语义化版本号的生产代码文件
7. 禁止对任何现有文件执行 replace_in_file / write_to_file(覆盖) 而不先创建备份
   例外：追加式文件（*.log、VERSION_LOG.md、CHANGELOG.md）只追加不覆盖，无需备份

## Ask First [ASK]

1. 修改/删除受保护文件（CLAUDE.md, AGENTS.md, package.json 等）
2. 覆盖用户已有的源代码文件
3. 读取 .env / .env.* 环境变量文件
4. 批量删除 ≥3 个文件
5. 修改构建配置/CI/CD 配置

## Always Do [DO]

1. 修改代码后立即运行 linter，展示验证结果
2. 每次文件操作后追加 .ai_audit.log 审计日志
3. 实质性变更后更新 VERSION_LOG.md

## 验证命令

修改代码后必须执行：
```bash
read_lints <修改的文件路径>
```
展示 lint 结果给用户，不可仅口头断言"通过"。
