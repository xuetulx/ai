<#
.SYNOPSIS
  一键部署 AI Rules 五层架构到 CodeBuddy 用户级目录（幂等，可重复执行）。

.DESCRIPTION
  将本目录（rules-HOOK-skill-Agent-docs）下的 HOOK/RULE/SKILL/AGENT 内容部署到
  $env:USERPROFILE\.codebuddy\：
  1. 复制 rules/skills/agents 源文件（frontmatter 已内置 name，符合 CodeBuddy 格式）
  2. 从 settings.json.template（单一事实源）生成 settings.json
  3. 校验：python 依赖、JSON 合法性、hooks 结构、源与部署一致性

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

# 0. 依赖检查：hooks 命令依赖 python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "未检测到 python 命令（hooks 依赖 python），请先安装并加入 PATH。"
}
Write-Host "python 可用: $((Get-Command python).Source)" -ForegroundColor Green

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

# 5. 从模板生成 settings.json（单一事实源）
$templatePath = Join-Path $src 'settings.json.template'
if (-not (Test-Path $templatePath)) { throw "模板不存在: $templatePath" }
$settingsPath = Join-Path $dst 'settings.json'
Copy-Item $templatePath $settingsPath -Force
Write-Host "已从模板生成 settings.json (Hooks)" -ForegroundColor Green

# 6. 校验
Write-Host "`n===== 部署验证 =====" -ForegroundColor Yellow

# 6.1 JSON 合法性
try {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
    Write-Host "settings.json JSON 校验: 通过" -ForegroundColor Green
} catch {
    Write-Host "settings.json JSON 校验: 失败 - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 6.2 hooks 结构（关键 matcher 齐全性）
$expectedPre = @('write_to_file|replace_in_file', 'read_file', 'delete_file')
$expectedPost = @('write_to_file|replace_in_file|delete_file', 'write_to_file|replace_in_file')
$preMatchers = @($settings.hooks.PreToolUse | ForEach-Object { $_.matcher })
$postMatchers = @($settings.hooks.PostToolUse | ForEach-Object { $_.matcher })
$preOk = ($preMatchers -join ';') -eq ($expectedPre -join ';')
$postOk = ($postMatchers -join ';') -eq ($expectedPost -join ';')
if ($preOk -and $postOk) {
    Write-Host "hooks 结构校验: 通过 (PreToolUse=$($preMatchers.Count) / PostToolUse=$($postMatchers.Count))" -ForegroundColor Green
} else {
    Write-Host "hooks 结构校验: 失败" -ForegroundColor Red
    Write-Host "  PreToolUse  实际: $($preMatchers -join ' | ')" -ForegroundColor Yellow
    Write-Host "  PostToolUse 实际: $($postMatchers -join ' | ')" -ForegroundColor Yellow
    exit 1
}

# 6.3 源与部署一致性（MD5 对比）
$mismatch = @()
foreach ($f in $files) {
    $from = Join-Path $src $f.from
    $to   = Join-Path $dst $f.to
    $h1 = (Get-FileHash $from -Algorithm MD5).Hash
    $h2 = (Get-FileHash $to -Algorithm MD5).Hash
    if ($h1 -ne $h2) { $mismatch += $f.to }
}
$hT = (Get-FileHash $templatePath -Algorithm MD5).Hash
$hS = (Get-FileHash $settingsPath -Algorithm MD5).Hash
if ($hT -ne $hS) { $mismatch += 'settings.json' }
if ($mismatch.Count -eq 0) {
    Write-Host "一致性校验: 通过（$($files.Count) 文件 + settings.json 全部与源一致）" -ForegroundColor Green
} else {
    Write-Host "一致性校验: 失败 - $($mismatch -join ', ')" -ForegroundColor Red
    exit 1
}

# 6.4 部署清单
Write-Host "`n----- 部署清单 -----" -ForegroundColor Cyan
Get-ChildItem -Path (Join-Path $dst 'rules'), (Join-Path $dst 'skills'), (Join-Path $dst 'agents') -Recurse -File |
    ForEach-Object { $_.FullName.Replace("$dst\", '') }
Get-Item $settingsPath | ForEach-Object { "$($_.Name) ($($_.Length) bytes)" }

Write-Host "`n部署完成。重新加载 CodeBuddy 后生效。" -ForegroundColor Green
