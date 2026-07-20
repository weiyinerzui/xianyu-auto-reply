"""
远程过滑块解题客户端

当 Docker 容器中检测到风控（RGV587/sliders）时，
通过 HTTP 调用远程 Windows 上的解题服务完成验证。

远程服务协议参考上游 xianyu-auto-reply 的 remote_solver.py：
  POST /solve
  Body: { secret_key, account_id, url, browser_timeout, cookies?, device_id? }
  Response: { success, cookies?, message? }

使用流程：
  1. 在 Windows 电脑上运行 remote_captcha_server.py
  2. 在系统设置中配置 remote_captcha_url 和 remote_captcha_secret
  3. 风控触发时自动调用远程服务
"""
from __future__ import annotations

import os
import time
from typing import Dict, Optional, Tuple

import requests
from loguru import logger


class RemoteCaptchaSolver:
    """远程过滑块解题客户端"""

    def __init__(self, url: str, secret_key: str, timeout: int = 60):
        """
        Args:
            url: 远程解题服务地址，如 http://192.168.1.100:9090/solve
            secret_key: 远程服务校验密钥
            timeout: 请求超时秒数（远程需要启动浏览器+解题，给足时间）
        """
        self.url = url.rstrip('/')
        if not self.url.endswith('/solve'):
            self.url += '/solve'
        self.secret_key = secret_key
        self.timeout = timeout

    def solve(
        self,
        account_id: str,
        captcha_url: str,
        cookies_str: str = "",
        device_id: str = "",
    ) -> Tuple[str, Optional[Dict[str, str]], Optional[str]]:
        """
        调用远程过滑块接口

        Args:
            account_id: 账号标识（日志隔离）
            captcha_url: punish 验证链接
            cookies_str: 可选，当前账号 Cookie（链接过期时远程可凭此重取）
            device_id: 可选，设备 ID

        Returns:
            (status, cookies, message)
            status:
              'ok' - 远程通过，cookies 为有效 dict
              'fail' - 远程有返回但未通过
              'url_expired' - 链接已过期，调用方应刷新URL后重试
              'fallback' - 超时或网络不可用，应回退本机逻辑
              'error' - 配置或请求异常
        """
        if not self.url or not self.secret_key:
            return "error", None, "远程解题服务未配置（URL或密钥为空）"

        payload = {
            "secret_key": self.secret_key,
            "account_id": str(account_id),
            "url": captcha_url,
            "browser_timeout": min(120, max(20, self.timeout - 10)),
        }

        if cookies_str:
            payload["cookies"] = cookies_str
            payload["device_id"] = device_id or ""

        logger.info(
            f"【{account_id}】调用远程过滑块服务: url={captcha_url[:80]}..., "
            f"remote={self.url}"
        )

        start_time = time.time()
        try:
            resp = requests.post(
                self.url,
                json=payload,
                timeout=(8, self.timeout),  # 连接8秒，读取给足远程解题时间
            )
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"【{account_id}】远程过滑块服务连接失败: {e}")
            return "fallback", None, f"连接失败: {e}"
        except requests.exceptions.Timeout as e:
            logger.warning(f"【{account_id}】远程过滑块服务超时({self.timeout}s): {e}")
            return "fallback", None, f"请求超时({self.timeout}s)"
        except requests.exceptions.RequestException as e:
            logger.warning(f"【{account_id}】远程过滑块请求异常: {e}")
            return "fallback", None, f"请求异常: {e}"

        elapsed = time.time() - start_time
        logger.info(f"【{account_id}】远程过滑块响应耗时: {elapsed:.1f}s")

        try:
            data = resp.json()
        except Exception as e:
            logger.warning(f"【{account_id}】远程过滑块响应解析失败: {e}")
            return "fail", None, f"响应解析失败: {e}"

        if not isinstance(data, dict):
            return "fail", None, f"响应格式异常: {type(data)}"

        success = data.get("success", False)
        cookies = data.get("cookies") or data.get("data")
        message = data.get("message", "")

        # 检测链接过期
        url_expired_keywords = ["链接过期", "页面访问出现了问题", "url_expired", "URL_EXPIRED"]
        if any(kw in str(message) for kw in url_expired_keywords):
            logger.warning(f"【{account_id}】远程反馈验证链接已过期: {message}")
            return "url_expired", None, message

        if success and isinstance(cookies, dict) and cookies:
            # 检查是否包含 x5 相关 cookie
            has_x5 = any(
                str(k).lower().startswith("x5") or "x5sec" in str(k).lower()
                for k in cookies.keys()
            )
            if has_x5:
                logger.info(
                    f"【{account_id}】远程过滑块成功, cookies数量={len(cookies)}"
                )
                return "ok", cookies, message
            else:
                logger.warning(
                    f"【{account_id}】远程过滑块返回成功但无x5 cookie: "
                    f"keys={list(cookies.keys())[:5]}"
                )
                return "fail", cookies, "未获取到x5相关cookies"
        else:
            logger.warning(
                f"【{account_id}】远程过滑块失败: success={success}, message={message}"
            )
            return "fail", None, message

    @staticmethod
    def from_config() -> Optional["RemoteCaptchaSolver"]:
        """从系统配置创建远程解题客户端"""
        try:
            from db_manager import db_manager
            url = db_manager.get_system_setting("remote_captcha_url") or ""
            secret = db_manager.get_system_setting("remote_captcha_secret") or ""
            timeout = int(db_manager.get_system_setting("remote_captcha_timeout") or "60")
            enabled = db_manager.get_system_setting("remote_captcha_enabled") or "false"
            if str(enabled).lower() not in ("true", "1", "yes"):
                return None
            if not url or not secret:
                return None
            return RemoteCaptchaSolver(url=url, secret_key=secret, timeout=timeout)
        except Exception as e:
            logger.warning(f"读取远程解题配置失败: {e}")
            return None
