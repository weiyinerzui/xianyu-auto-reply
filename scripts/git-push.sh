#!/usr/bin/env bash
# 从 .env 读取 GitHub 凭证并推送（GIT_ASKPASS 模式，token 不进 URL/进程列表）
# 用法:
#   bash scripts/git-push.sh                    # 只推送已有 commits
#   bash scripts/git-push.sh "commit message"   # 先 add+commit 再推送

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$REPO_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ 未找到 .env 文件: $ENV_FILE"
  echo "   请复制 .env.example 为 .env 并填写 GitHub Token"
  exit 1
fi

# 读取 .env
set -a
source "$ENV_FILE"
set +a

if [ -z "${GITHUB_TOKEN:-}" ] || [ -z "${GITHUB_USER:-}" ] || [ -z "${GITHUB_REPO:-}" ]; then
  echo "❌ .env 缺少 GITHUB_TOKEN / GITHUB_USER / GITHUB_REPO"
  exit 1
fi

cd "$REPO_DIR"

# 如果提供了 commit message，先提交
if [ -n "${1:-}" ]; then
  git add -A
  git commit -m "$1"
fi

# 使用 GIT_ASKPASS 传递凭证，token 不出现在 URL 或命令行参数中
echo "🚀 推送到 origin main..."
GIT_ASKPASS="$SCRIPT_DIR/git-askpass.sh" \
GIT_USERNAME="$GITHUB_USER" \
GIT_PASSWORD="$GITHUB_TOKEN" \
git push "https://github.com/${GITHUB_REPO}.git" main

echo "✅ 推送完成"
