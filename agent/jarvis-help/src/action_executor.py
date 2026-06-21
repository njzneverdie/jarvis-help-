"""
查 config 綁定並執行對應動作。
支援：left_click / double_click / right_click / scroll / launch / drag。
drag 的 press/release 由 drag_press() / drag_release() 直接呼叫。
"""

import webbrowser
import subprocess
import os
import pyautogui
from pynput.mouse import Controller as MouseController, Button

_mouse = MouseController()


def execute(gesture_name: str, cfg: dict) -> str | None:
    """
    執行 gesture_name 對應的動作。
    回傳動作描述字串（供 UI 顯示），無動作回傳 None。
    """
    binding = cfg.get("gestures", {}).get(gesture_name)
    if binding is None:
        return None

    action = binding.get("action", "none")

    if action == "left_click":
        pyautogui.click()
        return "左鍵點擊"

    if action == "double_click":
        pyautogui.doubleClick()
        return "左鍵雙擊"

    if action == "right_click":
        pyautogui.rightClick()
        return "右鍵點擊"

    if action == "scroll":
        # scroll 模式由 main.py 的 scroll_handler 另外處理；此處不動作
        return "捲動模式"

    if action == "launch":
        target = binding.get("target", "")
        _launch(target)
        return f"開啟 {target}"

    return None


def drag_press():
    _mouse.press(Button.left)

def drag_release():
    _mouse.release(Button.left)

def scroll_by(dy_px: float):
    """dy_px > 0 → 向上捲動，< 0 → 向下捲動"""
    clicks = int(dy_px / 30)
    if clicks != 0:
        _mouse.scroll(0, clicks)

def _launch(target: str):
    if target.startswith("http://") or target.startswith("https://"):
        webbrowser.open(target)
    elif os.path.exists(target):
        os.startfile(target)
    else:
        try:
            subprocess.Popen(target)
        except Exception as e:
            print(f"[ActionExecutor] launch 失敗: {e}")
