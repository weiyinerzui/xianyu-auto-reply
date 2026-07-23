"""
定时任务执行器（轻量版）

- db_backup: SQLite 文件备份
- delivery_timeout: 检测超时未发货订单

设计原则：不依赖 MySQL/Redis，纯 SQLite + 文件操作。
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta

from loguru import logger


# ==================== 数据库备份 ====================

BACKUP_DIR = os.path.join("data", "backups")
BACKUP_RETENTION_DAYS = 10


async def execute_db_backup() -> str:
    """SQLite 数据库文件备份（使用 SQLite backup API 确保一致性）"""
    try:
        from db_manager import db_manager

        if db_manager.conn is None:
            return "数据库未初始化，跳过备份"

        db_path = db_manager.db_path
        if not os.path.exists(db_path):
            return "数据库文件不存在，跳过备份"

        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")

        start = time.monotonic()
        import sqlite3
        dest_conn = sqlite3.connect(backup_file)
        try:
            with db_manager.lock:
                db_manager.conn.backup(dest_conn)
        finally:
            dest_conn.close()

        file_size = os.path.getsize(backup_file)
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(f"[数据库备份] 完成: {backup_file}, {file_size} 字节, {duration_ms}ms")

        _cleanup_old_backups()
        return f"备份成功: {os.path.basename(backup_file)} ({file_size} 字节)"
    except Exception as e:
        logger.error(f"[数据库备份] 失败: {e}")
        return f"备份失败: {e}"


def _cleanup_old_backups() -> None:
    """清理过期备份文件（保留最近 N 天）"""
    try:
        if not os.path.isdir(BACKUP_DIR):
            return
        cutoff = time.time() - (BACKUP_RETENTION_DAYS * 86400)
        removed = 0
        for fname in os.listdir(BACKUP_DIR):
            if not fname.startswith("backup_") or not fname.endswith(".db"):
                continue
            fpath = os.path.join(BACKUP_DIR, fname)
            try:
                if os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                pass
        if removed:
            logger.info(f"[数据库备份] 清理了 {removed} 个过期备份文件")
    except Exception as e:
        logger.warning(f"[数据库备份] 清理过期备份失败: {e}")


# ==================== 发货超时检测 ====================

DELIVERY_TIMEOUT_MINUTES = 5


async def execute_delivery_timeout() -> str:
    """检测超时未发货的自动发货记录"""
    try:
        from db_manager import db_manager

        if db_manager.conn is None:
            return "数据库未初始化，跳过"

        # 检查 auto_reply_message_log 表是否存在
        with db_manager.lock:
            cursor = db_manager.conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='auto_reply_message_log'"
            )
            table_exists = cursor.fetchone()

        if table_exists:
            return await _mark_timeout_logs()
        return await _check_orders_timeout()
    except Exception as e:
        logger.error(f"[发货超时检测] 失败: {e}")
        return f"执行失败: {e}"


async def _mark_timeout_logs() -> str:
    """将超时的 unknown 发货记录标记为 timeout"""
    try:
        from db_manager import db_manager

        if db_manager.conn is None:
            return "数据库未初始化"

        threshold = datetime.now() - timedelta(minutes=DELIVERY_TIMEOUT_MINUTES)
        threshold_str = threshold.strftime("%Y-%m-%d %H:%M:%S")

        with db_manager.lock:
            cursor = db_manager.conn.cursor()
            cursor.execute(
                """UPDATE auto_reply_message_log SET send_status = 'timeout'
                   WHERE send_status = 'unknown' AND created_at < ?""",
                (threshold_str,),
            )
            count = cursor.rowcount
            db_manager.conn.commit()

        if count > 0:
            logger.info(f"[发货超时检测] 标记 {count} 条 unknown 记录为 timeout")
            return f"标记 {count} 条超时记录"
        return "无超时记录"
    except Exception as e:
        logger.warning(f"[发货超时检测] 标记超时记录失败: {e}")
        return f"检测失败: {e}"


async def _check_orders_timeout() -> str:
    """检查 orders 表中超时未处理的订单"""
    try:
        from db_manager import db_manager

        if db_manager.conn is None:
            return "数据库未初始化"

        threshold = datetime.now() - timedelta(minutes=DELIVERY_TIMEOUT_MINUTES)
        threshold_str = threshold.strftime("%Y-%m-%d %H:%M:%S")

        with db_manager.lock:
            cursor = db_manager.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM orders WHERE order_status = 'unknown' AND created_at < ?",
                (threshold_str,),
            )
            count = cursor.fetchone()[0]

        if count > 0:
            logger.info(f"[发货超时检测] 发现 {count} 条超时未处理订单")
            return f"检测到 {count} 条超时订单"
        return "无超时订单"
    except Exception as e:
        logger.warning(f"[发货超时检测] orders 表检测失败: {e}")
        return f"检测失败: {e}"
