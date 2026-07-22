"""
Captcha 引擎包 - 真实鼠标滑块验证

必须在任何子模块导入前注册 pyautogui Mock，否则 Linux 下会报错。
"""
import sys
import platform

# ==================== PyAutoGUI Linux 兼容 Mock ====================
# pyautogui 依赖 X11 桌面，Linux 下直接导入会报错。
# 在非 Windows 环境 Mock 掉，让 REAL_MOUSE_AVAILABLE 优雅返回 False。
# 必须在 __init__.py 中执行，确保在任何子模块 import pyautogui 之前生效。

if platform.system() != "Windows":
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

        def scroll(self, *args, **kwargs):
            pass

        def keyDown(self, *args, **kwargs):
            pass

        def keyUp(self, *args, **kwargs):
            pass

        def hotkey(self, *args, **kwargs):
            pass

        def press(self, *args, **kwargs):
            pass

        def moveRel(self, *args, **kwargs):
            pass

        def dragRel(self, *args, **kwargs):
            pass

        def mouseInfo(self, *args, **kwargs):
            pass

        def onScreen(self, *args, **kwargs):
            return True

        def FailSafeException(self, *args, **kwargs):
            pass

    sys.modules.setdefault("pyautogui", _MockPyAutoGUI())
