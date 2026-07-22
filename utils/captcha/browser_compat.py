"""
浏览器工具兼容层

适配上游 common.utils.browser_utils 的三个函数：
- ensure_playwright_browser_path
- get_chromium_executable_path
- is_frozen
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def is_frozen() -> bool:
    """检测是否运行在编译/打包模式。"""
    if getattr(sys, "frozen", False):
        return True
    try:
        import __main__
        if hasattr(__main__, "__compiled__"):
            return True
    except Exception:
        pass
    return False


def get_playwright_browser_dir() -> Optional[Path]:
    """获取 Playwright 浏览器目录。"""
    env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate

    local_app = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app:
        candidate = Path(local_app) / "ms-playwright"
        if candidate.exists():
            return candidate

    candidate = Path.home() / ".cache" / "ms-playwright"
    if candidate.exists():
        return candidate

    return None


def ensure_playwright_browser_path() -> Optional[Path]:
    """设置 PLAYWRIGHT_BROWSERS_PATH 环境变量并返回浏览器目录。"""
    browser_dir = get_playwright_browser_dir()
    if browser_dir:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_dir)
        logger.debug(f"Playwright 浏览器目录: {browser_dir}")
    return browser_dir


def get_chromium_executable_path(
    browser_package: str = "playwright",
    *,
    strict_revision: bool = False,
) -> Optional[str]:
    """定位 Chromium 可执行文件路径。"""
    browser_dir = get_playwright_browser_dir()
    if browser_dir and browser_dir.exists():
        try:
            chromium_dirs = [
                d for d in browser_dir.iterdir()
                if d.is_dir() and "chromium" in d.name.lower()
            ]
            for cdir in chromium_dirs:
                candidates = [
                    cdir / "chrome-win64" / "chrome.exe",
                    cdir / "chrome-win" / "chrome.exe",
                    cdir / "chrome-linux" / "chrome",
                    cdir / "chrome-linux64" / "chrome",
                ]
                for candidate in candidates:
                    if candidate.exists():
                        return str(candidate)
        except Exception as e:
            logger.warning(f"查找 Chromium 可执行文件失败: {e}")
    return None
