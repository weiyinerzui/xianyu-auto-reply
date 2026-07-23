"""
定时任务配置服务（轻量版）

功能：
1. 从 SQLite 读取任务配置（间隔、启用状态）
2. 内存缓存，避免每次循环查库
3. 判断任务是否到期需要执行
4. 记录最后执行时间
5. 配置更新后自动刷新缓存

设计原则：不引入 APScheduler，保留现有 while True 循环作为执行引擎，
本模块只提供配置读取和缓存能力。
"""
from __future__ import annotations

import time
from typing import Dict, Optional

from loguru import logger


# 默认配置（数据库无配置时使用）
DEFAULT_CONFIGS: Dict[str, dict] = {
    "token_renewal": {"interval_seconds": 3600, "enabled": True},
    "cookie_refresh": {"interval_seconds": 3600, "enabled": True},
    "cleanup": {"interval_seconds": 300, "enabled": True},
    "db_backup": {"interval_seconds": 86400, "enabled": True},
    "delivery_timeout": {"interval_seconds": 600, "enabled": True},
}


class ScheduledTaskService:
    """定时任务配置服务 — 单例，带内存缓存"""

    _instance: Optional["ScheduledTaskService"] = None

    def __init__(self):
        self._cache: Dict[str, dict] = {}  # task_code -> {interval_seconds, enabled}
        self._last_cache_refresh: float = 0
        self._cache_ttl: int = 30  # 缓存有效期30秒

    @classmethod
    def get_instance(cls) -> "ScheduledTaskService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _refresh_cache(self, force: bool = False) -> None:
        """从数据库刷新缓存"""
        now = time.time()
        if not force and self._cache and (now - self._last_cache_refresh) < self._cache_ttl:
            return
        try:
            from db_manager import db_manager
            tasks = db_manager.get_all_scheduled_tasks()
            if tasks:
                self._cache = {
                    t["task_code"]: {
                        "interval_seconds": t["interval_seconds"],
                        "enabled": bool(t["enabled"]),
                    }
                    for t in tasks
                }
                self._last_cache_refresh = now
        except Exception as e:
            logger.warning(f"[定时任务] 刷新缓存失败，使用默认配置: {e}")

    def get_task_config(self, task_code: str) -> dict:
        """获取单个任务配置（带缓存）"""
        self._refresh_cache()
        if task_code in self._cache:
            return self._cache[task_code]
        # 回退到默认配置
        return DEFAULT_CONFIGS.get(task_code, {"interval_seconds": 60, "enabled": True})

    def get_interval(self, task_code: str) -> int:
        """获取任务执行间隔（秒）"""
        return self.get_task_config(task_code).get("interval_seconds", 60)

    def is_enabled(self, task_code: str) -> bool:
        """判断任务是否启用"""
        return self.get_task_config(task_code).get("enabled", True)

    def should_run(self, task_code: str, last_run_time: float) -> bool:
        """判断任务是否到期需要执行"""
        if not self.is_enabled(task_code):
            return False
        interval = self.get_interval(task_code)
        return (time.time() - last_run_time) >= interval

    def record_run(self, task_code: str) -> None:
        """记录任务执行时间到数据库"""
        try:
            from db_manager import db_manager
            db_manager.record_task_run(task_code)
        except Exception as e:
            logger.warning(f"[定时任务] 记录执行时间失败: {e}")

    def reload(self, task_code: Optional[str] = None) -> None:
        """强制刷新缓存（配置更新后调用）"""
        self._refresh_cache(force=True)
        if task_code:
            logger.info(f"[定时任务] 配置已热刷新: {task_code}")
        else:
            logger.info("[定时任务] 全部配置已热刷新")

    def get_all_tasks(self) -> list:
        """获取所有任务配置（供API调用，带缓存）"""
        self._refresh_cache()
        result = []
        for code, cfg in self._cache.items():
            result.append({
                "task_code": code,
                "interval_seconds": cfg["interval_seconds"],
                "enabled": cfg["enabled"],
            })
        return result


# 全局单例
scheduled_task_service = ScheduledTaskService.get_instance()
