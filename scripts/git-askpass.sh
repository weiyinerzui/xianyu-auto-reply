#!/usr/bin/env bash
# Git credential helper — 通过环境变量提供凭证，避免 token 出现在命令行/remote URL
# 由 git-push.sh 设置 GIT_USERNAME / GIT_PASSWORD 环境变量后调用
case "$1" in
  Username*) echo "$GIT_USERNAME" ;;
  Password*) echo "$GIT_PASSWORD" ;;
esac
