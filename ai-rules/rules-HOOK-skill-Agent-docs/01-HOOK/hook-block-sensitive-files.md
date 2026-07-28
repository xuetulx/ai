---
description: "Hook: 拦截敏感文件读取"
hook_type: PreToolUse
watch_tools: [read_file, execute_command]
version: 1.0
last_updated: 2026-07-28
---

# Hook-2：拦截敏感文件读取

> 来源：01_core_behavior §2.1 #5 + 05_security §1.1

## 敏感文件清单（P0 级别，任何情况不得读取）

```
*.pem        # 证书/私钥
*.key        # 密钥文件
*.cert       # 证书文件
credentials.* # 凭证文件（任意扩展名）
token*       # Token 文件
*.p12        # PKCS12 证书
*.pfx        # PKCS12 证书
id_rsa*      # SSH 私钥
*.keystore   # Java 密钥库
```

## 拦截逻辑

```
触发条件：read_file / execute_command 目标路径匹配以上模式
拦截动作：
  1. 检测文件路径是否命中敏感文件列表
  2. 命中 → 阻断操作，返回拒绝信息
  3. 未命中 → 放行
```

## P1 级别（需确认，不可静默绕过）

```
.env            # 环境变量（读取前 [ASK]）
.env.*          # 环境变量变体
config*.yaml    # 含密码可能的配置
```

P1 文件非 Hook 拦截范围，走 Rule 的 [ASK] 机制。

## Claude Code 配置参考

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "read_file",
      "hooks": [{
        "type": "command",
        "command": "python -c \"import sys; path=sys.argv[1]; blocked=['.pem','.key','.cert','credentials.','token']; exit(1 if any(b in path.lower() for b in blocked) else 0)\" ${FILE_PATH}"
      }]
    }]
  }
}
```
