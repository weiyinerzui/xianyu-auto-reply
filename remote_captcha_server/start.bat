@echo off
chcp 65001 >nul
title 闲鱼远程过滑块服务

echo ======================================
echo 闲鱼远程过滑块服务
echo =======================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Python，请先安装 Python 3.11+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查依赖
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

:: 检查 Chrome
if not exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    if not exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        echo [警告] 未找到 Chrome 浏览器，请安装 Google Chrome
        echo 下载地址: https://www.google.com/chrome/
        echo.
        echo 按任意键继续启动（可能无法正常工作）...
        pause
    )
)

:: 启动服务
echo [信息] 启动远程过滑块服务...
echo [信息] 端口: 9090
echo [信息] 密钥: xianyu_remote_2026
echo [信息] 按 Ctrl+C 停止服务
echo.

python captcha_server.py --port 9090 --secret xianyu_remote_2026

pause
