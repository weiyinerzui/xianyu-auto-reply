# Git credential helper for PowerShell — 通过环境变量提供凭证
# 由 git-push.ps1 设置 $env:GIT_USERNAME / $env:GIT_PASSWORD 后调用
param([string]$Prompt)
switch -Wildcard ($Prompt) {
    "Username*" { Write-Output $env:GIT_USERNAME; break }
    "Password*" { Write-Output $env:GIT_PASSWORD; break }
}
