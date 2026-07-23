"""
全局定时任务运行器

在 reply_server.py startup 时启动，负责执行全局任务（db_backup、delivery_timeout）。
per-cookie 任务（token_renewal、cookie_refresh、cleanup）仍由 XianyuAutoAsync 实例自行循环。
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional

from loguru import logger

from utils.scheduler.scheduled_task_service import scheduled_task_service
from utils.scheduler.task_executors import execute_db_backup, execute_delivery_timeout


# 任务代码 -> 执行函数映射
_TASK_EXECUTORS = {
    "db_backup": execute_db_backup,
    "delivery_timeout": execute_delivery_timeout,
}


class GlobalTaskRunner:
    """全局定时任务运行器 — 单例"""

    _instance: Optional["GlobalTaskRunner"] = None

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_run: dict[str, float] = {}  # task_code -> last run timestamp

    @classmethod
    def get_instance(cls) -> "GlobalTaskRunner":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self) -> None:
        """启动全局任务循环"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("[全局任务] 运行器已启动")

    async def stop(self) -> None:
        """停止全局任务循环"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[全局任务] 运行器已停止")

    async def _run_loop(self) -> None:
        """主循环：每 30 秒检查一次全局任务是否到期"""
        while self._running:
            try:
                for task_code, executor in _TASK_EXECUTORS.items():
                    if not scheduled_task_service.is_enabled(task_code):
                        continue

                    last_run = self._last_run.get(task_code, 0)
                    if not scheduled_task_service.should_run(task_code, last_run):
                        continue

                    # 到期，执行任务
                    logger.info(f"[全局任务] 开始执行: {task_code}")
                    try:
                        result = await executor()
                        logger.info(f"[全局任务] {task_code} 完成: {result}")
                    except Exception as e:
                        logger.error(f"[全局任务] {task_code} 执行异常: {e}")
                    finally:
                        self._last_run[task_code] = time.time()
                        scheduled_task_service.record_run(task_code)

                # 30 秒检查一次
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[全局任务] 循环异常: {e}")
                await asyncio.sleep(30)

    async def trigger_task(self, task_code: str) -> str:
        """手动触发单个全局任务"""
        executor = _TASK_EXECUTORS.get(task_code)
        if executor is None:
            return f"未知任务: {task_code}"
        logger.info(f"[全局任务] 手动触发: {task_code}")
        try:
            result = await executor()
            self._last_run[task_code] = time.time()
            scheduled_task_service.record_run(task_code)
            return result
        except Exception as e:
            logger.error(f"[全局任务] 手动触发 {task_code} 失败: {e}")
            return f"执行失败: {e}"


# 全局单例
global_task_runner = GlobalTaskRunner.get_instance()
