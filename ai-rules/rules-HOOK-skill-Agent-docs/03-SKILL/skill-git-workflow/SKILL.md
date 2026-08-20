---
name: git-workflow
description: "Git 工作流 Skill - 版本控制操作时手动触发"
version: 1.0
last_updated: 2026-07-28
---

# Skill: Git 工作流 (skill-git-workflow)

> 来源：04_version_control

## 触发条件

用户说 "提交" / "推送" / "创建分支" / "合并"，或执行 git 操作时。

## 标准工作流

```
[DO] 1. 确认当前分支: git branch --show-current
[DO] 2. 记录原分支名
[DO] 3. 创建新分支: git checkout -b <type>/<description>
[DO] 4. 在新分支上修改
[DO] 5. 提交: git add + git commit (Conventional Commits)
[ASK] 6. 询问用户是否推送或合并
[DO] 7. 任务完成后提醒用户当前分支
```

## 分支命名

```
feat/<描述>         # 新功能: feat/add-user-auth
fix/<描述>          # Bug修复: fix/null-pointer-crash
refactor/<描述>     # 重构: refactor/extract-utils
docs/<描述>         # 文档: docs/update-readme
```

## 提交格式

```
<type>: <简短描述>

[详细描述]

[关联 Issue: #123]
```

类型: feat | fix | docs | style | refactor | perf | test | chore | ci | build

## 禁止操作

```
[BLOCK] 在 main/master/develop 上直接 commit
[BLOCK] git push --force（除非用户明确要求+二次确认）
[BLOCK] git reset --hard（除非用户明确要求+二次确认）
[BLOCK] 未经确认删除任何分支
```

## 依赖镜像源

Python: `pip install <pkg> -i https://pypi.tuna.tsinghua.edu.cn/simple`
Node: `npm install <pkg> --registry https://registry.npmmirror.com`
Go: `GOPROXY=https://goproxy.cn go get <pkg>`
