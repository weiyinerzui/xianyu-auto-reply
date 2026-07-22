"""
时间工具兼容层

适配上游 common.utils.time_utils 的函数：
- get_beijing_now_naive
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

_BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_now_naive() -> datetime:
    """获取当前北京时间（去掉时区信息，便于写入 DATETIME 字段）。"""
    return datetime.now(_BEIJING_TZ).replace(tzinfo=None)
