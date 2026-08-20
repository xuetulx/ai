---
name: hook-block-hardcoded-secrets
description: "Hook: 拦截硬编码密钥/密码/Token。Write/Edit 执行后扫描代码变更，阻断硬编码敏感信息。"
hook_type: PostToolUse
watch_tools: [Write, Edit]
version: 1.0
last_updated: 2026-07-28
---

# Hook-4：拦截硬编码密钥

> 来源：06_engineering §5 + 05_security §4.2

## 扫描模式

```
正则: (password|passwd|secret|api_key|token|private_key|access_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]
描述: 检测等号或冒号后跟引号包裹的 8+ 字符字符串
```

## 拦截逻辑

```
触发条件：Write / Edit 执行后
拦截动作：
  1. 读取变更内容
  2. 正则扫描硬编码模式
  3. 命中 → 警告 + 阻断（PostToolUse 撤销变更）
  4. 未命中 → 放行
```

## 误报豁免场景（白名单）

```
# 常量定义中的无害字符串
DJANGO_SECRET_KEY = 'django-insecure-xxx'  # 开发环境标记

# 变量引用
password = os.environ.get('DB_PASSWORD')   # 从环境变量读取

# 占位符
api_key = 'YOUR_API_KEY_HERE'              # 占位符
```

## 正确做法

```python
# ❌ 硬编码
DATABASE_PASSWORD = "MySecret123"

# ✅ 环境变量
DATABASE_PASSWORD = os.environ.get("DB_PASSWORD")

# ✅ 密钥管理服务
secret = boto3.client('secretsmanager').get_secret_value(...)
```

## Trae 配置参考

> Trae IDE 不直接支持用户级 Hook，需通过插件或项目级 settings.json 实现。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import sys, re; content=open(sys.argv[1]).read(); pattern=r'(password|passwd|secret|api_key|token|private_key|access_key)\\s*[:=]\\s*[\\'\"][^\\'\\\"]{8,}[\\'\"]'; exit(1 if re.search(pattern, content) else 0)\" ${FILE_PATH}"
          }
        ]
      }
    ]
  }
}
```
