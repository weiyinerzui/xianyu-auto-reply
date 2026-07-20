"""
闲鱼远程过滑块服务 - Windows 端

在 Windows 电脑上运行此服务，Docker 容器遇到风控时通过 HTTP 调用它。
使用 pyautogui 驱动物理鼠标在真实浏览器上完成验证，
绕过阿里的 CDP 注入鼠标事件检测。

安装依赖：
  pip install fastapi uvicorn pyautogui requests

启动：
  python captcha_server.py
  或
  python captcha_server.py --port 9090 --secret your_secret_key

然后配置 Docker 端：
  系统设置 → 远程过滑块 → URL: http://你的IP:9090/solve
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import threading
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="闲鱼远程过滑块服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== 配置 ======
SECRET_KEY = os.getenv("CAPTCHA_SECRET_KEY", "xianyu_remote_2026")
PORT = int(os.getenv("CAPTCHA_PORT", "9090"))
BROWSER_TIMEOUT = 60  # 默认超时秒数

# ====== 全局锁（物理鼠标同一时刻只能解一个滑块）======
_mouse_lock = threading.Lock()


class SolveRequest(BaseModel):
    """过滑块请求"""
    secret_key: str
    account_id: str = ""
    url: str
    browser_timeout: int = 40
    cookies: str = ""
    device_id: str = ""


class SolveResponse(BaseModel):
    """过滑块响应"""
    success: bool
    cookies: Optional[Dict[str, str]] = None
    message: str = ""


@app.post("/solve", response_model=SolveResponse)
async def solve_captcha(req: SolveRequest):
    """处理过滑块请求"""
    # 校验密钥
    if req.secret_key != SECRET_KEY:
        return SolveResponse(success=False, message="密钥校验失败")

    if not req.url:
        return SolveResponse(success=False, message="验证链接为空")

    # 全局串行：同一时刻只解一个滑块
    if not _mouse_lock.acquire(blocking=False):
        return SolveResponse(
            success=False,
            message="当前有其他滑块正在处理，请稍后重试"
        )

    try:
        from captcha_solver import solve_slider_captcha
        success, cookies, message = solve_slider_captcha(
            captcha_url=req.url,
            account_id=req.account_id,
            timeout=min(120, max(20, req.browser_timeout)),
            cookies_str=req.cookies,
        )

        return SolveResponse(
            success=success,
            cookies=cookies if success else None,
            message=message,
        )
    except Exception as e:
        return SolveResponse(success=False, message=f"服务异常: {e}")
    finally:
        _mouse_lock.release()


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "service": "xianyu-remote-captcha",
        "version": "1.0.0",
        "lock_available": not _mouse_lock.locked(),
    }


@app.get("/test")
async def test_connection():
    """测试连通性"""
    return {"status": "ok", "message": "远程过滑块服务运行正常"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="闲鱼远程过滑块服务")
    parser.add_argument("--port", type=int, default=PORT, help="服务端口")
    parser.add_argument("--secret", type=str, default=SECRET_KEY, help="校验密钥")
    args = parser.parse_args()

    SECRET_KEY = args.secret
    print(f"="*50)
    print(f"闲鱼远程过滑块服务")
    print(f"端口: {args.port}")
    print(f"密钥: {SECRET_KEY[:4]}{'*'*(len(SECRET_KEY)-4)}")
    print(f"="*50)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)
