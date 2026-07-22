"""
闲鱼工具兼容层

适配上游 common.utils.xianyu_utils 的两个函数：
- trans_cookies
- generate_sign
"""
from __future__ import annotations

import hashlib
from typing import Dict


def trans_cookies(cookies_str: str) -> Dict[str, str]:
    """将 cookies 字符串转换为字典。

    Args:
        cookies_str: Cookie 字符串，格式如 "key1=value1; key2=value2"

    Returns:
        Cookie 字典

    Raises:
        ValueError: 如果 cookies 为空
    """
    if not cookies_str:
        raise ValueError("cookies不能为空")

    cookies: Dict[str, str] = {}
    for cookie in cookies_str.split(";"):
        cookie = cookie.strip()
        if not cookie:
            continue
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            key = key.strip()
            if key:
                cookies[key] = value.strip()
    return cookies


def generate_sign(t: str, token: str, data: str) -> str:
    """生成 API 签名。

    Args:
        t: 时间戳
        token: _m_h5_tk token
        data: 请求数据

    Returns:
        签名字符串
    """
    app_key = "34839810"
    msg = f"{token}&{t}&{app_key}&{data}"

    md5_hash = hashlib.md5()
    md5_hash.update(msg.encode("utf-8"))
    return md5_hash.hexdigest()
