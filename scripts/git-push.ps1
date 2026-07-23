<#
.SYNOPSIS
  从 .env 读取 GitHub 凭证并推送（GIT_ASKPASS 模式，token 不进 URL/进程列表）
.PARAMETER Message
  可选 commit message。提供则先 git add + commit 再推送；不提供则只推送已有 commits。
.EXAMPLE
  .\scripts\git-push.ps1
  .\scripts\git-push.ps1 "feat: 新功能"
#>
param(
    [Parameter(Position = 0)]
    [string]$Message
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path $PSScriptRoot -Parent
$EnvFile = Join-Path $RepoDir ".env"

if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ 未找到 .env 文件: $EnvFile" -ForegroundColor Red
    Write-Host "   请复制 .env.example 为 .env 并填写 GitHub Token" -ForegroundColor Yellow
    exit 1
}

# 读取 .env
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*)$') {
        Set-Item -Path "env:$($Matches[1])" -Value $Matches[2].Trim()
    }
}

if (-not $env:GITHUB_TOKEN -or -not $env:GITHUB_USER -or -not $env:GITHUB_REPO) {
    Write-Host "❌ .env 缺少 GITHUB_TOKEN / GITHUB_USER / GITHUB_REPO" -ForegroundColor Red
    exit 1
}

Set-Location $RepoDir

# 如果提供了 commit message，先提交
if ($Message) {
    git add -A
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# 使用 GIT_ASKPASS 传递凭证，token 不出现在 URL 或命令行参数中
$AskPass = Join-Path $PSScriptRoot "git-askpass.ps1"
if (-not (Test-Path $AskPass)) {
    Write-Host "❌ 未找到 git-askpass.ps1: $AskPass" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 推送到 origin main..." -ForegroundColor Cyan
$env:GIT_ASKPASS = $AskPass
$env:GIT_USERNAME = $env:GITHUB_USER
$env:GIT_PASSWORD = $env:GITHUB_TOKEN

git push "https://github.com/$($env:GITHUB_REPO).git" main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 推送完成" -ForegroundColor Green
} else {
    Write-Host "❌ 推送失败 (exit $LASTEXITCODE)" -ForegroundColor Red
}

# 清理环境变量
Remove-Item Env:GIT_ASKPASS -ErrorAction SilentlyContinue
Remove-Item Env:GIT_USERNAME -ErrorAction SilentlyContinue
Remove-Item Env:GIT_PASSWORD -ErrorAction SilentlyContinue
exit $LASTEXITCODE
