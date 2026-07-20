"""
纯 HTTP Cookie 续期模块

通过 requests 访问 goofish.com 相关页面来续期 Cookie，
不需要启动浏览器，不会触发 Playwright CDP 检测。

已验证：requests.get(goofish.com) 返回 200 + 24个新 cookies，
可以有效延长 Cookie 有效期。

使用场景：在定时 Cookie 刷新时替代浏览器方式，大幅降低风控风险。
"""
from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

import requests
from loguru import logger


# 用于续期的 URL 列表（从轻到重）
_REFRESH_URLS = [
    "https://www.goofish.com/",           # 首页，最轻量
    "https://h5.m.goofish.com/",           # H5 首页
    "https://www.goofish.com/myfish",      # 我的闲鱼（需要登录态）
]

# 请求头，模拟正常浏览器访问
_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def parse_cookies_str(cookies_str: str) -> Dict[str, str]:
    """将 cookies 字符串解析为字典"""
    cookies = {}
    if not cookies_str:
        return cookies
    for part in cookies_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def build_cookies_str(cookies_dict: Dict[str, str]) -> str:
    """将 cookies 字典构建为字符串"""
    return "; ".join(f"{k}={v}" for k, v in cookies_dict.items())


def refresh_cookies_via_http(
    cookie_id: str,
    current_cookies_str: str,
) -> Tuple[bool, Optional[str], str]:
    """
    通过纯 HTTP 请求续期 Cookie

    Args:
        cookie_id: 账号标识（用于日志）
        current_cookies_str: 当前 cookies 字符串

    Returns:
        (success, new_cookies_str, message)
        success: True 表示获取到新 cookies
        new_cookies_str: 合并后的新 cookies 字符串
        message: 结果描述
    """
    if not current_cookies_str:
        return False, None, "当前 cookies 为空，无法续期"

    current_cookies = parse_cookies_str(current_cookies_str)
    if not current_cookies:
        return False, None, "cookies 解析为空"

    session = requests.Session()
    # 设置当前 cookies
    for k, v in current_cookies.items():
        session.cookies.set(k, v)

    updated_cookies = {}
    total_new = 0
    total_updated = 0

    for url in _REFRESH_URLS:
        try:
            logger.info(f"【{cookie_id}】HTTP Cookie续期: 访问 {url}")
            resp = session.get(
                url,
                headers=_DEFAULT_HEADERS,
                timeout=15,
                allow_redirects=True,
            )

            logger.info(
                f"【{cookie_id}】HTTP Cookie续期: {url} → "
                f"status={resp.status_code}, "
                f"session_cookies={len(session.cookies)}"
            )

            # 收集服务端返回的新 cookies
            for k, v in session.cookies.items():
                if k in current_cookies:
                    if current_cookies[k] != v:
                        updated_cookies[k] = v
                        total_updated += 1
                else:
                    updated_cookies[k] = v
                    total_new += 1

            # 如果第一个 URL 就拿到了更新的 cookies，不需要继续
            if updated_cookies:
                break

        except requests.exceptions.RequestException as e:
            logger.warning(f"【{cookie_id}】HTTP Cookie续期失败 {url}: {e}")
            continue

    if not updated_cookies:
        return False, None, "HTTP 续期未获取到新 cookies"

    # 合并：当前 cookies + 服务端更新
    merged = current_cookies.copy()
    merged.update(updated_cookies)
    new_cookies_str = build_cookies_str(merged)

    message = (
        f"HTTP Cookie续期成功: 新增{total_new}个, "
        f"更新{total_updated}个, 总计{len(merged)}个"
    )
    logger.info(f"【{cookie_id}】{message}")

    return True, new_cookies_str, message
