"""
闲鱼滑块验证求解器 - Windows + pyautogui 版

核心原理：
  阿里 baxia 风控能区分 CDP 注入的鼠标事件与真实硬件鼠标事件。
  Playwright/CDP 即使回放真人轨迹也被判 code=300（拒），
  而用 pyautogui 驱动物理光标回放真人轨迹则 code=0（通过）。

  因此本模块使用 pyautogui 在真实 Chrome 浏览器上驱动物理鼠标，
  完成滑块验证，绕过 CDP 检测。

依赖：
  pip install pyautogui requests selenium

  需要安装 Chrome 浏览器（不是 Chromium）
  Chrome 安装后需要先手动登录一次闲鱼，保存登录态
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import time
from typing import Dict, Optional, Tuple

import pyautogui
import requests

# 安全设置
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# 滑块相关常量
SLIDER_SELECTOR = "nc_1_n1z"  # 阿里 NoCaptcha 滑块 ID 前缀

# 真人轨迹模板（从上游 human_trails 简化而来）
# 格式: [(dx, dt_ms), ...] 表示每步的位移和间隔
_HUMAN_TRAIL = [
    (2, 12), (3, 10), (5, 8), (8, 7), (12, 6), (15, 5),
    (18, 5), (20, 4), (22, 4), (20, 4), (18, 5), (15, 5),
    (12, 6), (10, 6), (8, 7), (5, 8), (3, 10), (2, 15),
    (1, 20), (0, 50),  # 最后微调+等待
]


def _get_chrome_path() -> str:
    """获取 Chrome 可执行文件路径"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("未找到 Chrome 浏览器，请安装 Google Chrome")


def _generate_human_trail(total_distance: int = 300) -> list:
    """
    生成真人轨迹

    Args:
        total_distance: 需要滑动的总距离（像素）

    Returns:
        [(dx, dt_ms), ...] 位移-时间序列
    """
    trail = []
    remaining = total_distance

    # 加速阶段
    acceleration = random.uniform(0.8, 1.2)
    for dx, dt in _HUMAN_TRAIL[:6]:
        actual_dx = int(dx * acceleration)
        actual_dx = min(actual_dx, remaining)
        if actual_dx <= 0:
            break
        trail.append((actual_dx, int(dt * random.uniform(0.8, 1.2))))
        remaining -= actual_dx

    # 匀速阶段
    while remaining > 20:
        dx = random.randint(5, min(25, remaining))
        dt = random.randint(4, 8)
        trail.append((dx, dt))
        remaining -= dx

    # 减速阶段
    for dx, dt in _HUMAN_TRAIL[-5:]:
        actual_dx = min(dx, remaining)
        if actual_dx <= 0:
            break
        trail.append((actual_dx, int(dt * random.uniform(0.9, 1.3))))
        remaining -= actual_dx

    # 最后微调
    if remaining > 0:
        trail.append((remaining, random.randint(15, 30)))

    # 加入随机抖动
    final_trail = []
    for dx, dt in trail:
        jitter_y = random.randint(-2, 2)
        final_trail.append((dx, jitter_y, dt))

    return final_trail


def solve_slider_captcha(
    captcha_url: str,
    account_id: str = "default",
    timeout: int = 40,
    cookies_str: str = "",
) -> Tuple[bool, Optional[Dict[str, str]], str]:
    """
    使用 pyautogui 在真实 Chrome 上完成滑块验证

    Args:
        captcha_url: 风控验证链接
        account_id: 账号标识
        timeout: 超时秒数
        cookies_str: 可选，账号 cookies（用于续期链接）

    Returns:
        (success, cookies_dict, message)
    """
    print(f"[{account_id}] 开始远程过滑块: url={captcha_url[:80]}...")

    chrome_path = _get_chrome_path()
    print(f"[{account_id}] Chrome路径: {chrome_path}")

    # 启动 Chrome（带窗口，不用 headless）
    cmd = [
        chrome_path,
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        f"--app={captcha_url}",  # 以 App 模式打开，更干净
        "--window-size=800,600",
    ]

    # 如果有 cookies，先注入
    if cookies_str:
        # 用 --user-data-dir 保持登录态
        user_data_dir = os.path.join(
            os.environ.get("TEMP", "/tmp"),
            "xianyu_captcha_chrome_profile"
        )
        os.makedirs(user_data_dir, exist_ok=True)
        cmd.append(f"--user-data-dir={user_data_dir}")

    try:
        process = subprocess.Popen(cmd)
    except Exception as e:
        return False, None, f"启动Chrome失败: {e}"

    try:
        # 等待页面加载
        time.sleep(random.uniform(3, 5))

        # ====== 核心步骤：用 pyautogui 拖动滑块 ======
        success, cookies = _drag_slider_with_pyautogui(account_id, timeout)

        if success and cookies:
            print(f"[{account_id}] 滑块验证成功，获取到 {len(cookies)} 个 cookies")
            return True, cookies, "验证成功"
        else:
            print(f"[{account_id}] 滑块验证失败")
            return False, None, "验证失败，未获取到x5 cookies"

    except Exception as e:
        print(f"[{account_id}] 滑块验证异常: {e}")
        return False, None, f"验证异常: {e}"
    finally:
        # 关闭 Chrome
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


def _drag_slider_with_pyautogui(
    account_id: str,
    timeout: int = 40,
) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    使用 pyautogui 驱动物理鼠标完成滑块拖动

    Returns:
        (success, cookies_dict)
    """
    # 获取屏幕尺寸
    screen_w, screen_h = pyautogui.size()
    print(f"[{account_id}] 屏幕尺寸: {screen_w}x{screen_h}")

    # 查找滑块位置
    # 假设 Chrome 窗口居中，滑块大约在窗口中下部
    # 这里需要根据实际截图来定位

    # 方法1：截图后用图像识别找滑块位置
    try:
        slider_pos = _find_slider_position()
        if not slider_pos:
            print(f"[{account_id}] 未找到滑块位置，使用默认位置")
            # 默认位置：屏幕中央偏下
            slider_x = screen_w // 2 - 150
            slider_y = screen_h // 2 + 50
        else:
            slider_x, slider_y = slider_pos
    except Exception as e:
        print(f"[{account_id}] 查找滑块位置异常: {e}")
        slider_x = screen_w // 2 - 150
        slider_y = screen_h // 2 + 50

    print(f"[{account_id}] 滑块位置: ({slider_x}, {slider_y})")

    # 生成真人轨迹
    slide_distance = 260  # 默认滑动距离
    trail = _generate_human_trail(slide_distance)

    # 执行拖动
    print(f"[{account_id}] 开始拖动滑块...")

    # 移动鼠标到滑块起始位置
    pyautogui.moveTo(slider_x, slider_y, duration=random.uniform(0.3, 0.5))

    # 模拟人类按下前的短暂停顿
    time.sleep(random.uniform(0.1, 0.3))

    # 按下鼠标
    pyautogui.mouseDown()

    try:
        # 按轨迹拖动
        current_x = slider_x
        current_y = slider_y

        for dx, dy, dt in trail:
            current_x += dx
            current_y += dy
            pyautogui.moveTo(current_x, current_y, duration=0)
            # 精确等待
            time.sleep(dt / 1000.0)

        # 松手前短暂停顿（模拟人类犹豫）
        time.sleep(random.uniform(0.1, 0.3))

        # 释放鼠标
        pyautogui.mouseUp()

        # 等待验证结果
        time.sleep(random.uniform(2, 3))

        # 验证是否通过——截图检查
        success = _check_verification_result(account_id)

        # 如果成功，从浏览器获取 cookies
        cookies = None
        if success:
            cookies = _extract_cookies_from_browser(account_id)

        return success, cookies

    except Exception as e:
        print(f"[{account_id}] 拖动过程异常: {e}")
        return False, None
    finally:
        # 确保鼠标释放
        try:
            pyautogui.mouseUp()
        except Exception:
            pass


def _find_slider_position() -> Optional[Tuple[int, int]]:
    """
    通过截图和图像识别找到滑块位置

    目前简化实现：使用 pyautogui 截图 + 像素匹配
    后续可以替换为更精确的图像识别方案
    """
    try:
        # 截屏
        screenshot = pyautogui.screenshot()

        # 查找滑块图标（红色/橙色小方块）
        # 这里用颜色范围匹配
        width, height = screenshot.size

        # 遍历屏幕中下部区域
        for y in range(height // 3, height * 2 // 3):
            for x in range(width // 4, width * 3 // 4, 10):
                r, g, b = screenshot.getpixel((x, y))
                # NoCaptcha 滑块通常是暗橙色/红色
                if r > 200 and g < 100 and b < 100:
                    return (x, y)

        return None
    except Exception:
        return None


def _check_verification_result(account_id: str) -> bool:
    """
    检查滑块验证是否通过

    方法：截图后检查是否还有滑块/验证码关键词
    """
    try:
        # 简化实现：等待3秒后截图验证
        # 如果验证通过，页面会跳转，滑块消失
        screenshot = pyautogui.screenshot()
        width, height = screenshot.size

        # 查找滑块是否还在
        slider_found = False
        for y in range(height // 3, height * 2 // 3, 20):
            for x in range(width // 4, width * 3 // 4, 20):
                try:
                    r, g, b = screenshot.getpixel((x, y))
                    if r > 200 and g < 100 and b < 100:
                        slider_found = True
                        break
                except Exception:
                    pass
            if slider_found:
                break

        return not slider_found  # 滑块消失 = 验证通过

    except Exception as e:
        print(f"[{account_id}] 检查验证结果异常: {e}")
        return False


def _extract_cookies_from_browser(account_id: str) -> Optional[Dict[str, str]]:
    """
    从浏览器获取 cookies

    注意：此处在 Windows 上运行，需要从 Chrome 进程获取 cookies
    简化实现：返回 None，由 Docker 端通过刷新 token 来获取新 cookies
    """
    # 验证通过后，Docker 端会用新 cookies 自动刷新 token
    # Windows 端只需要确认"验证通过"即可
    # 不需要直接从 Windows 浏览器提取 cookies
    # 因为验证通过后，服务端会下发新的 x5sec 到请求的 cookies 中
    # Docker 端收到成功响应后可以直接刷新 token

    # 但更好的方案是：验证通过后，让浏览器访问 goofish.com
    # 然后用 Selenium/CDP 获取 cookies
    # 这需要在 Chrome 启动时启用远程调试端口

    print(f"[{account_id}] 验证通过，返回成功标志（由Docker端刷新token获取新cookies）")
    # 返回一个特殊标记，让 Docker 端知道验证通过
    # Docker 端收到后会重新尝试 refresh_token
    return {"__captcha_passed__": "true"}
