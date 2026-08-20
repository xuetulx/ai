<#
.SYNOPSIS
  一键部署 AI Rules 五层架构到 CodeBuddy 用户级目录（幂等，可重复执行）。

.DESCRIPTION
  将本目录（rules-HOOK-skill-Agent-docs）下的 HOOK/RULE/SKILL/AGENT 内容部署到
  $env:USERPROFILE\.codebuddy\，并生成/覆盖 settings.json（Hooks 配置）。
  源文件 frontmatter 已内置 name 字段，复制后即符合 CodeBuddy 格式，无需手工修改。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\deploy-codebuddy.ps1
#>
[CmdletBinding()]
param(
    [string]$UserProfile = $env:USERPROFILE
)

$ErrorActionPreference = 'Stop'
$src = $PSScriptRoot
$dst = Join-Path $UserProfile '.codebuddy'

Write-Host "源目录: $src" -ForegroundColor Cyan
Write-Host "目标目录: $dst" -ForegroundColor Cyan

# 1. 创建目录结构
$dirs = @('rules', 'skills\code-review', 'skills\security-review', 'skills\git-workflow', 'agents')
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $dst $d) | Out-Null
}

# 2-4. 部署 Rules / Skills / Agents
$files = @(
    @{ from = '02-RULE\Always\00-hard-boundaries.mdc';      to = 'rules\00-hard-boundaries.md' },
    @{ from = '02-RULE\Agent-Requested\01-py-coding.mdc';   to = 'rules\01-py-coding.md' },
    @{ from = '02-RULE\Agent-Requested\02-git-rules.mdc';   to = 'rules\02-git-rules.md' },
    @{ from = '02-RULE\Agent-Requested\03-engineering.mdc'; to = 'rules\03-engineering.md' },
    @{ from = '03-SKILL\skill-code-review\SKILL.md';        to = 'skills\code-review\SKILL.md' },
    @{ from = '03-SKILL\skill-security-review\SKILL.md';    to = 'skills\security-review\SKILL.md' },
    @{ from = '03-SKILL\skill-git-workflow\SKILL.md';       to = 'skills\git-workflow\SKILL.md' },
    @{ from = '04-AGENT\agent-verify.md';                   to = 'agents\agent-verify.md' },
    @{ from = '04-AGENT\agent-file-sync.md';                to = 'agents\agent-file-sync.md' }
)

foreach ($f in $files) {
    $from = Join-Path $src $f.from
    $to   = Join-Path $dst $f.to
    if (-not (Test-Path $from)) { throw "源文件不存在: $from" }
    Copy-Item $from $to -Force
}
Write-Host "已复制 $($files.Count) 个文件 (rules/skills/agents)" -ForegroundColor Green

# 5. 生成 settings.json（Hooks）——无 BOM UTF-8
$settingsJson = @'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "write_to_file|replace_in_file",
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import os, sys, json; data = json.load(sys.stdin); fp = data.get('tool_input', {}).get('filePath', ''); (os.path.exists(fp) and not fp.endswith('.bak') and __import__('shutil').copy2(fp, fp + '.bak') or None)\""
          }
        ]
      },
      {
        "matcher": "read_file",
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import sys, json; p = json.load(sys.stdin).get('tool_input',{}).get('filePath',''); exit(2 if any(p.endswith(x) for x in ('.pem','.key','.cert','credentials.','token')) else 0)\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "write_to_file|replace_in_file|delete_file",
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import json, sys, os; from datetime import datetime; d = json.load(sys.stdin); op = d.get('tool_name','?'); fp = d.get('tool_input',{}).get('filePath','?'); ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S'); print(f'==== {ts} | 操作: {op} | 路径: {fp} | 结果: OK ====\\n', file=open(os.path.join(os.path.dirname(fp) if os.path.dirname(fp) else '.', '.ai_audit.log'), 'a'))\""
          }
        ]
      }
    ]
  }
}
'@
$settingsPath = Join-Path $dst 'settings.json'
[System.IO.File]::WriteAllText($settingsPath, $settingsJson, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "已生成 settings.json (Hooks)" -ForegroundColor Green

# 6. 验证部署结果
Write-Host "`n===== 部署结果验证 =====" -ForegroundColor Yellow
Get-ChildItem -Path (Join-Path $dst 'rules'), (Join-Path $dst 'skills'), (Join-Path $dst 'agents') -Recurse -File |
    ForEach-Object { $_.FullName.Replace("$dst\", '') }
Get-Item $settingsPath | ForEach-Object { "$($_.Name) ($($_.Length) bytes)" }

try {
    Get-Content $settingsPath -Raw | ConvertFrom-Json | Out-Null
    Write-Host "settings.json JSON 校验: 通过" -ForegroundColor Green
} catch {
    Write-Host "settings.json JSON 校验: 失败 - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n部署完成。重新加载 CodeBuddy 后生效。" -ForegroundColor Green
