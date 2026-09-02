# Git 操作规范

> 来源：ai-configuration/02-RULE/Agent-Requested/02-git-rules.mdc（执行版本控制操作时加载）
> 底层来源：ai-rules/split/04_version_control

## 核心规则

1. [BLOCK] 禁止在 main/master/develop 上直接 commit
2. [DO] 每次修改必须在新建分支上进行
3. [BLOCK] 禁止 git push --force / git reset --hard（除非用户明确要求 + 二次确认）

## 分支命名

```
feat/<描述>     # 新功能
fix/<描述>      # Bug 修复
refactor/<描述> # 重构
```

## 提交消息（Conventional Commits）

```
<type>: <description>
```
类型：feat | fix | docs | refactor | perf | test | chore

## 工作流

```
1. git branch --show-current       # 确认当前分支
2. git checkout -b feat/xxx        # 创建新分支
3. 在分支上修改
4. git add + git commit
5. [ASK] 询问是否推送
```

## Git 安全红线

- [BLOCK] 禁止直接读写 .git/ 目录内部文件（用 git 命令代替）
- [BLOCK] 禁止修改 git config 全局配置
- [BLOCK] 禁止在未询问的情况下推送或合并到 main/master
- [DO] 提交前先 git diff 审查变更内容
