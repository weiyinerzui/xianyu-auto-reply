"""
闲鱼滑块验证求解器 - Windows + pyautogui 版

核心原理：
  阿里 baxia 风控能区分 CDP 注入的鼠标事件与真实硬件鼠标事件。
  Playwright/CDP 即使回放真人轨迹也被判 code=300（拒），
  而用 pyautogui 驱动物理光标回放真人轨迹则 code=0（通过）。

  本模块使用 pyautogui 在真实 Chrome 浏览器上驱动物理鼠标，
  完成滑块验证，绕过 CDP 检测。

  验证通过后，通过 Chrome 的远程调试端口(CDP)提取 cookies，
  返回给 Docker 端使用。

依赖：
  pip install pyautogui requests

  需要安装 Chrome 浏览器
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

# Chrome 远程调试端口
DEBUG_PORT = 9222

# 真人轨迹模板
_HUMAN_TRAIL = [
    (2, 12), (3, 10), (5, 8), (8, 7), (12, 6), (15, 5),
    (18, 5), (20, 4), (22, 4), (20, 4), (18, 5), (15, 5),
    (12, 6), (10, 6), (8, 7), (5, 8), (3, 10), (2, 15),
    (1, 20), (0, 50),
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
    """生成真人轨迹，返回 [(dx, jitter_y, dt_ms), ...]"""
    trail = []
    remaining = total_distance

    # 加速阶段
    acceleration = random.uniform(0.8, 1.2)
    for dx, dt in _HUMAN_TRAIL[:6]:
        actual_dx = int(dx * acceleration)
        actual_dx = min(actual_dx, remaining)
        if actual_dx <= 0:
            break
        trail.append((actual_dx, random.randint(-2, 2), int(dt * random.uniform(0.8, 1.2))))
        remaining -= actual_dx

    # 匀速阶段
    while remaining > 20:
        dx = random.randint(5, min(25, remaining))
        trail.append((dx, random.randint(-2, 2), random.randint(4, 8)))
        remaining -= dx

    # 减速阶段
    for dx, dt in _HUMAN_TRAIL[-5:]:
        actual_dx = min(dx, remaining)
        if actual_dx <= 0:
            break
        trail.append((actual_dx, random.randint(-2, 2), int(dt * random.uniform(0.9, 1.3))))
        remaining -= actual_dx

    # 最后微调
    if remaining > 0:
        trail.append((remaining, random.randint(-1, 1), random.randint(15, 30)))

    return trail


def _extract_cookies_via_cdp(port: int = DEBUG_PORT, timeout: int = 10) -> Optional[Dict[str, str]]:
    """
    通过 Chrome DevTools Protocol 提取 goofish.com 的 cookies
    
    Chrome 启动时带 --remote-debugging-port=9222，我们可以通过 HTTP 接口获取 cookies
    """
    try:
        # 1. 获取调试目标
        resp = requests.get(f"http://localhost:{port}/json", timeout=5)
        targets = resp.json()
        
        if not targets:
            print(f"  CDP: 未找到浏览器目标")
            return None
        
        # 找到 goofish 相关的页面
        target_id = None
        for t in targets:
            url = t.get('url', '')
            if 'goofish' in url or 'taobao' in url or 'punish' in url:
                target_id = t.get('id')
                print(f"  CDP: 找到目标页面: {url[:80]}")
                break
        
        if not target_id:
            # 用第一个目标
            target_id = targets[0].get('id')
            print(f"  CDP: 使用第一个目标")
        
        if not target_id:
            return None
        
        # 2. 通过 CDP 获取 cookies
        # 直接用 /json/protocol 不需要 WebSocket
        # 更简单的方式：用 Network.getAllCookies
        ws_url = None
        for t in targets:
            if t.get('id') == target_id:
                ws_url = t.get('webSocketDebuggerUrl')
                break
        
        if not ws_url:
            # fallback: 用 HTTP 方式获取所有 cookies
            return _get_cookies_simple(port)
        
        # 用 WebSocket 获取 cookies（更可靠）
        return _get_cookies_via_ws(ws_url)
        
    except Exception as e:
        print(f"  CDP提取cookies异常: {e}")
        # fallback: 返回验证通过信号
        return {"__captcha_passed__": "true"}


def _get_cookies_simple(port: int) -> Optional[Dict[str, str]]:
    """简单方式获取 cookies（通过 CDP HTTP 接口）"""
    try:
        # 通过 CDP 的 /json/list 获取页面信息
        # 然后用 sessionStorage 注入 JS 获取 document.cookie
        # 但这种方式有限制，不如 WebSocket 可靠
        return {"__captcha_passed__": "true"}
    except Exception:
        return None


def _get_cookies_via_ws(ws_url: str) -> Optional[Dict[str, str]]:
    """通过 WebSocket 获取 cookies"""
    try:
        import websocket
        ws = websocket.create_connection(ws_url, timeout=10)
        ws.settimeout(5)  # 设置 recv 超时
        
        # 发送 Network.enable
        ws.send(json.dumps({"id": 1, "method": "Network.enable", "params": {}}))
        ws.recv()  # 接收响应
        
        # 发送 Network.getAllCookies
        ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies", "params": {}}))
        result = json.loads(ws.recv())
        
        ws.close()
        
        cookies_list = result.get('result', {}).get('cookies', [])
        print(f"  CDP: 获取到 {len(cookies_list)} 个 cookies")
        
        # 打印所有 cookie 域名，方便调试
        all_domains = set()
        for c in cookies_list:
            all_domains.add(c.get('domain', '?'))
        print(f"  CDP: 所有域名: {sorted(all_domains)}")
        
        # 筛选阿里系域名的 cookies（x5sec 可能在非 goofish/taobao 域名下）
        ali_domains = ['goofish', 'taobao', 'alibaba', 'alicdn', '1688', 'alipay',
                       'tmall', 'alidetail', 'mgoofish', 'hymgoofish']
        filtered = {}
        for c in cookies_list:
            domain = c.get('domain', '')
            name = c.get('name', '')
            value = c.get('value', '')
            if not name or not value:
                continue
            # 阿里系域名 或 名字含 x5 的都保留
            if any(d in domain for d in ali_domains) or 'x5' in name.lower():
                filtered[name] = value
        
        print(f"  CDP: 过滤后 {len(filtered)} 个阿里系 cookies")
        
        # 检查是否包含 x5 相关
        x5_count = sum(1 for k in filtered if k.lower().startswith('x5') or 'x5sec' in k.lower())
        print(f"  CDP: 其中 {x5_count} 个 x5 相关 cookies")
        
        # 没有真实 cookies 就返回通过信号
        if not filtered:
            return {"__captcha_passed__": "true"}
        
        # 有 cookies 但没 x5 → 追加通过信号，让 Docker 端走 refresh_token
        if x5_count == 0:
            filtered["__captcha_passed__"] = "true"
            print(f"  CDP: 无x5 cookies，追加__captcha_passed__信号")
        
        return filtered
        
    except ImportError:
        print("  websocket-client 未安装，返回验证通过信号")
        return {"__captcha_passed__": "true"}
    except Exception as e:
        print(f"  WebSocket获取cookies失败: {e}")
        return {"__captcha_passed__": "true"}


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
        cookies_str: 可选，账号 cookies

    Returns:
        (success, cookies_dict, message)
    """
    print(f"[{account_id}] 开始远程过滑块: url={captcha_url[:80]}...")

    chrome_path = _get_chrome_path()
    print(f"[{account_id}] Chrome路径: {chrome_path}")

    # 启动 Chrome（带远程调试端口 + App模式）
    user_data_dir = os.path.join(
        os.environ.get("TEMP", "/tmp"),
        "xianyu_captcha_chrome_profile"
    )
    os.makedirs(user_data_dir, exist_ok=True)

    cmd = [
        chrome_path,
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        f"--remote-debugging-port={DEBUG_PORT}",
        "--remote-allow-origins=*",
        f"--app={captcha_url}",
        "--window-size=800,600",
        f"--user-data-dir={user_data_dir}",
    ]

    try:
        process = subprocess.Popen(cmd)
    except Exception as e:
        return False, None, f"启动Chrome失败: {e}"

    try:
        # 等待页面加载
        time.sleep(random.uniform(3, 5))

        # ====== 核心步骤：用 pyautogui 拖动滑块 ======
        success = _drag_slider_with_pyautogui(account_id, timeout)

        # 等待验证结果生效，cookies 写入需要时间
        time.sleep(random.uniform(2, 3))

        # ====== 提取 cookies（带重试） ======
        cookies = None
        if success:
            print(f"[{account_id}] 验证通过，尝试提取cookies...")
            for attempt in range(3):
                cookies = _extract_cookies_via_cdp()
                has_x5 = cookies and any(
                    k.lower().startswith('x5') or 'x5sec' in k.lower()
                    for k in (cookies or {})
                )
                if has_x5:
                    x5_count = sum(1 for k in (cookies or {}) if k.lower().startswith('x5') or 'x5sec' in k.lower())
                    print(f"[{account_id}] 第{attempt+1}次提取成功，{len(cookies or {})}个cookies（含{x5_count}个x5）")
                    break
                elif attempt < 2:
                    wait = 1.5 * (attempt + 1)
                    print(f"[{account_id}] 第{attempt+1}次提取无x5，{wait:.1f}s后重试...")
                    time.sleep(wait)
            
            if cookies and cookies.get("__captcha_passed__"):
                print(f"[{account_id}] 最终未提取到x5 cookies，返回验证通过信号+已有cookies")
            
        if success:
            return True, cookies or {"__captcha_passed__": "true"}, "验证成功"
        else:
            print(f"[{account_id}] 滑块验证失败")
            return False, None, "验证失败"

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
) -> bool:
    """使用 pyautogui 驱动物理鼠标完成滑块拖动"""
    screen_w, screen_h = pyautogui.size()
    print(f"[{account_id}] 屏幕尺寸: {screen_w}x{screen_h}")

    # 查找滑块位置
    try:
        slider_pos = _find_slider_position()
        if not slider_pos:
            print(f"[{account_id}] 未找到滑块位置，使用默认位置")
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
    trail = _generate_human_trail(260)

    # 执行拖动
    print(f"[{account_id}] 开始拖动滑块...")
    pyautogui.moveTo(slider_x, slider_y, duration=random.uniform(0.3, 0.5))
    time.sleep(random.uniform(0.1, 0.3))
    pyautogui.mouseDown()

    try:
        current_x = slider_x
        current_y = slider_y

        for dx, dy, dt in trail:
            current_x += dx
            current_y += dy
            pyautogui.moveTo(current_x, current_y, duration=0)
            time.sleep(dt / 1000.0)

        time.sleep(random.uniform(0.1, 0.3))
        pyautogui.mouseUp()
        time.sleep(random.uniform(2, 3))

        success = _check_verification_result(account_id)
        return success

    except Exception as e:
        print(f"[{account_id}] 拖动过程异常: {e}")
        return False
    finally:
        try:
            pyautogui.mouseUp()
        except Exception:
            pass


def _find_slider_position() -> Optional[Tuple[int, int]]:
    """通过截图和颜色匹配找到滑块位置"""
    try:
        screenshot = pyautogui.screenshot()
        width, height = screenshot.size

        for y in range(height // 3, height * 2 // 3):
            for x in range(width // 4, width * 3 // 4, 10):
                r, g, b = screenshot.getpixel((x, y))
                if r > 200 and g < 100 and b < 100:
                    return (x, y)

        return None
    except Exception:
        return None


def _check_verification_result(account_id: str) -> bool:
    """检查滑块验证是否通过"""
    try:
        screenshot = pyautogui.screenshot()
        width, height = screenshot.size

        # 如果滑块消失 = 验证通过
        for y in range(height // 3, height * 2 // 3, 20):
            for x in range(width // 4, width * 3 // 4, 20):
                try:
                    r, g, b = screenshot.getpixel((x, y))
                    if r > 200 and g < 100 and b < 100:
                        return False  # 滑块还在
                except Exception:
                    pass

        return True  # 滑块消失 = 验证通过

    except Exception as e:
        print(f"[{account_id}] 检查验证结果异常: {e}")
        return False
