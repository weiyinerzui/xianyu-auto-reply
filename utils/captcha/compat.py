"""
Captcha 引擎兼容层

将上游依赖的 common.db / common.models / common.utils / common.core.config
统一适配到本项目。单进程 + SQLite 架构下不需要异步会话，全部改为同步调用。
"""
from __future__ import annotations

import sys
import threading
from typing import Any, Optional

from loguru import logger

# db_manager 模块末尾创建了单例实例 db_manager = DBManager()
from db_manager import db_manager as _db


# ==================== 配置兼容 (Mock Settings) ====================


class MockSettings:
    """模拟上游 Settings 对象，提供 captcha 引擎所需的属性。"""

    @property
    def database_url(self) -> str:
        return "sqlite:///data/xianyu_data.db"

    @property
    def captcha_drissionpage_fallback_enabled(self) -> bool:
        return True

    @property
    def captcha_drissionpage_headless(self) -> bool:
        return True

    @property
    def captcha_drissionpage_timeout(self) -> int:
        return 25

    @property
    def db_connect_timeout(self) -> int:
        return 10


_settings_instance = MockSettings()


def get_settings():
    """替代上游 common.core.config.get_settings / app.core.config.get_settings。"""
    return _settings_instance


# ==================== PyAutoGUI Linux 兼容 Mock ====================
# pyautogui 依赖 X11 桌面，Linux 下直接导入会报错。
# 在非 Windows 环境 Mock 掉，让 REAL_MOUSE_AVAILABLE 优雅返回 False。

if sys.platform != "win32":
    class _MockPyAutoGUI:
        """Linux 下的 pyautogui 占位，所有方法空操作。"""

        def size(self):
            return (1920, 1080)

        def moveTo(self, *args, **kwargs):
            pass

        def dragTo(self, *args, **kwargs):
            pass

        def mouseDown(self, *args, **kwargs):
            pass

        def mouseUp(self, *args, **kwargs):
            pass

        def click(self, *args, **kwargs):
            pass

        def position(self):
            return (0, 0)

        def moveTo(self, *args, **kwargs):
            pass

    sys.modules.setdefault("pyautogui", _MockPyAutoGUI())


# ==================== 系统设置模型 ====================


class SystemSetting:
    """模拟上游 SystemSetting 模型，仅保留 key/value 字段。"""

    def __init__(self, key: str = "", value: str = ""):
        self.key = key
        self.value = value


# ==================== 兼容 select() 接口 ====================


class _ScalarResult:
    """模拟 SQLAlchemy 的 ScalarResult，支持 scalar_one_or_none()。"""

    def __init__(self, value: Any):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _SelectProxy:
    """模拟 SQLAlchemy select().where() 链式调用。"""

    def __init__(self, column, key_value=None):
        self._key_value = key_value

    def where(self, *conditions):
        # conditions 不解析，key_value 已在构造时传入
        return self

    async def execute(self, session=None):
        if self._key_value is None:
            return _ScalarResult(None)
        val = _db.get_system_setting(self._key_value)
        return _ScalarResult(val)


def select(column):
    """模拟 SQLAlchemy select(value)。

    上游调用方式：
        select(SystemSetting.value).where(SystemSetting.key == KEY)
    SystemSetting.value 是一个字符串属性，无法直接拿到 key，
    所以这里通过 _SelectProxy 在 execute 时直接查 system_settings 表。
    """
    # column 是 SystemSetting.value（字符串），无法拿到 key
    # 上游实际只在一个地方调用：slider_mode.py
    # 那里紧接着 .where(SystemSetting.key == SLIDER_MODE_SETTING_KEY)
    # 我们在 _SelectProxy.where 中不解析条件，而是让 slider_mode.py 直接用 compat 函数
    return _SelectProxy(column)


# ==================== 异步会话兼容 ====================


class _SyncSession:
    """模拟 async_session_maker() 返回的异步上下文管理器。"""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def execute(self, query):
        # 委托给 _SelectProxy.execute
        if isinstance(query, _SelectProxy):
            return await query.execute()
        return _ScalarResult(None)


def async_session_maker():
    """兼容上游 async_session_maker() 调用。"""
    return _SyncSession()


# ==================== 便捷函数 ====================


def get_system_setting_sync(key: str, default: str = "") -> str:
    """同步读取系统设置。"""
    val = _db.get_system_setting(key)
    return val if val is not None else default


def set_system_setting_sync(key: str, value: str) -> None:
    """同步写入系统设置。"""
    _db.set_system_setting(key, value)


async def get_system_setting(key: str, default: str = "") -> str:
    """异步读取系统设置（兼容上游 async 调用）。"""
    return get_system_setting_sync(key, default)


async def set_system_setting(key: str, value: str) -> None:
    """异步写入系统设置。"""
    set_system_setting_sync(key, value)
