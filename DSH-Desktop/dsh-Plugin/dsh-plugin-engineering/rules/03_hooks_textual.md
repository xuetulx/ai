# HOOK 机制文字化（文件操作硬约束）

> 来源：ai-configuration/01-HOOK/（5 个程序级 Hook 的文字化表达）
> DSH 无 Hook 机制，以下为等效 Rule 表达，由 AI 在文件操作时自觉执行。

## 1. 修改前强制备份（等效 Hook-1）

```
[BLOCK] 禁止在未创建 .bak 备份的情况下对任何现有文件
执行 replace_in_file 或 write_to_file（覆盖模式）。
修改前必须: (a) 创建备份 (b) 验证备份完整性 (c) 方可修改。
```

备份命名规则：
```
原文件名.py          → 原文件名_v1.0.bak
原文件名_v1.0.py     → 原文件名_v1.0_backup_20260101.bak
```

例外放行（无需备份）：
- `write_to_file` 目标路径不存在（创建模式）
- 文件在 `tmp/`、`.temp/`、`.cache/` 目录下（临时文件）
- **追加式文件**只追加不覆盖，原内容始终保留：`*.log`（含 `.ai_audit.log`）、`VERSION_LOG.md`、`CHANGELOG.md`

备份清理闭环：
- 修改完成后检测到 `.bak` 存在 → 询问用户是否确认修改结果无误
- 删除 `.bak` 前强制确认：用户确认"新文件已验证"后才放行删除

## 2. 拦截敏感文件读取（等效 Hook-2）

P0 级别（任何情况不得读取）：
```
*.pem  *.key  *.cert  credentials.*  token*
*.p12  *.pfx  id_rsa*  *.keystore
```

P1 级别（读取前 [ASK]，不可静默绕过）：
```
.env  .env.*  config*.yaml（含密码可能的配置）
```

## 3. 拦截直接操作 .git/（等效 Hook-3）

```
✅ git status / git log / git diff / git branch   # 通过 git 命令
❌ read_file .git/HEAD                             # 直接读取
❌ write_to_file .git/config                       # 直接写入
❌ replace_in_file .git/...                        # 直接修改
```

注意：`.gitignore`、`.gitattributes` 是项目配置文件，**不在**拦截范围。

## 4. 拦截硬编码密钥（等效 Hook-4）

扫描模式：
```
正则: (password|passwd|secret|api_key|token|private_key|access_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]
```

误报豁免（白名单）：
```
DJANGO_SECRET_KEY = 'django-insecure-xxx'   # 开发环境标记
password = os.environ.get('DB_PASSWORD')    # 从环境变量读取
api_key = 'YOUR_API_KEY_HERE'               # 占位符
```

正确做法：
```python
# ❌ 硬编码
DATABASE_PASSWORD = "MySecret123"
# ✅ 环境变量
DATABASE_PASSWORD = os.environ.get("DB_PASSWORD")
# ✅ 密钥管理服务
secret = boto3.client('secretsmanager').get_secret_value(...)
```

## 5. 自动追加审计日志（等效 Hook-5）

每次文件操作（创建/修改/删除）后，向项目根目录 `.ai_audit.log` 追加记录：

```
============================================================
[日期时间] | 操作: 创建/修改/删除 | 结果: 成功/失败
  路径: <完整路径>
  摘要: <变更描述>
  验证: linter=通过, tests=通过
============================================================
```

约束：
- 仅追加（append），不得修改或删除已有记录
- 每次操作一条记录，批量操作合并为一条（标注文件数量）
