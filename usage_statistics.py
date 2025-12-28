#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户使用统计模块
只统计有多少人在使用这个系统
"""

import asyncio
import hashlib
import platform
from datetime import datetime
from typing import Dict, Any

import aiohttp
from loguru import logger


class UsageStatistics:
    """用户使用统计收集器 - 只统计用户数量"""

    def __init__(self):
        # 默认禁用远程统计（安全修复）
        self.enabled = False
        # self.api_endpoint = "http://xianyu.zhinianblog.cn/?action=statistics"  # 已禁用
        self.api_endpoint = None  # 远程统计已禁用
        self.timeout = 5
        self.retry_count = 1

        # 生成持久化的匿名用户ID
        self.anonymous_id = self._get_or_create_anonymous_id()

    def _get_or_create_anonymous_id(self) -> str:
        """获取或创建持久化的匿名用户ID"""
        # 保存到数据库中，确保Docker重建时ID不变
        try:
            from db_manager import db_manager

            # 尝试从数据库获取ID
            existing_id = db_manager.get_system_setting('anonymous_user_id')
            if existing_id and len(existing_id) == 16:
                return existing_id

        except Exception:
            pass

        # 生成新的匿名ID
        new_id = self._generate_anonymous_id()

        # 保存到数据库
        try:
            from db_manager import db_manager
            db_manager.set_system_setting('anonymous_user_id', new_id)
        except Exception:
            pass

        return new_id

    def _generate_anonymous_id(self) -> str:
        """生成匿名用户ID（基于机器特征）"""
        try:
            # 使用系统信息生成唯一但匿名的ID
            machine_info = f"{platform.machine()}-{platform.processor()}-{platform.system()}"
            unique_str = f"{machine_info}-{platform.python_version()}"

            # 生成哈希值作为匿名ID
            anonymous_id = hashlib.sha256(unique_str.encode()).hexdigest()[:16]
            return anonymous_id
        except Exception:
            # 如果获取系统信息失败，使用随机ID
            import time
            return hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
    
    def _get_basic_info(self) -> Dict[str, Any]:
        """获取基本信息（只包含必要信息）"""
        try:
            # 从version.txt文件读取版本号
            version = self._get_version()
            return {
                "os": platform.system(),
                "version": version
            }
        except Exception:
            return {"os": "unknown", "version": "unknown"}

    def _get_version(self) -> str:
        """从static/version.txt文件获取版本号"""
        try:
            with open("static/version.txt", "r", encoding="utf-8") as f:
                version = f.read().strip()
                return version if version else "unknown"
        except Exception:
            return "unknown"
    
    def _prepare_statistics_data(self) -> Dict[str, Any]:
        """准备统计数据（只包含用户统计）"""
        return {
            "anonymous_id": self.anonymous_id,
            "timestamp": datetime.now().isoformat(),
            "project": "xianyu-auto-reply",
            "info": self._get_basic_info()
        }
    
    async def _send_statistics(self, data: Dict[str, Any]) -> bool:
        """发送统计数据到远程API"""
        if not self.enabled:
            return False

        for attempt in range(self.retry_count):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        'Content-Type': 'application/json',
                        'User-Agent': 'XianyuAutoReply/2.2.0'
                    }

                    async with session.post(
                        self.api_endpoint,
                        json=data,
                        headers=headers
                    ) as response:
                        if response.status in [200, 201]:
                            logger.debug("统计数据上报成功")
                            return True
                        else:
                            logger.debug(f"统计数据上报失败，状态码: {response.status}")

            except asyncio.TimeoutError:
                logger.debug(f"统计数据上报超时，第{attempt + 1}次尝试")
            except Exception as e:
                logger.debug(f"统计数据上报异常: {e}")

            if attempt < self.retry_count - 1:
                await asyncio.sleep(1)

        return False
    
    async def report_usage(self) -> bool:
        """报告用户使用统计"""
        try:
            data = self._prepare_statistics_data()
            return await self._send_statistics(data)
        except Exception as e:
            logger.debug(f"报告使用统计失败: {e}")
            return False


# 全局统计实例
usage_stats = UsageStatistics()


async def report_user_count():
    """报告用户数量统计"""
    try:
        logger.info("正在上报用户统计...")
        success = await usage_stats.report_usage()
        if success:
            logger.info("✅ 用户统计上报成功")
        else:
            logger.debug("用户统计上报失败")
    except Exception as e:
        logger.debug(f"用户统计异常: {e}")


def get_anonymous_id() -> str:
    """获取匿名用户ID"""
    return usage_stats.anonymous_id


# 测试函数
async def test_statistics():
    """测试统计功能"""
    print(f"匿名ID: {get_anonymous_id()}")
    await report_user_count()


if __name__ == "__main__":
    asyncio.run(test_statistics())
