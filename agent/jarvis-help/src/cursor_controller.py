"""
相對游標控制器（類觸控板模式）。
握拳時手部參考點的位移 → 套 One-Euro 平滑 → pyautogui 相對移動。
"""

import pyautogui
from smoothing import SmoothXY
from state_machine import State

# 參考點：食指 MCP（index 5），比掌心穩定
REF_LANDMARK = 5

pyautogui.FAILSAFE = False   # 關閉移到角落自動中斷（手勢控制不需要）
pyautogui.PAUSE = 0          # 移除預設 0.1s 延遲


class CursorController:
    def __init__(self, sensitivity: float = 2.0, min_cutoff: float = 1.0, beta: float = 0.01):
        self._sensitivity = sensitivity
        self._smoother = SmoothXY(min_cutoff=min_cutoff, beta=beta)
        self._ref_x: float | None = None
        self._ref_y: float | None = None
        self._screen_w, self._screen_h = pyautogui.size()

    def update(self, landmarks, state: State) -> None:
        if state == State.IDLE:
            # 離開 ACTIVE 時重置參考點，下次握拳重新校準
            self._ref_x = None
            self._ref_y = None
            return

        lm = landmarks[REF_LANDMARK]
        raw_x, raw_y = lm.x, lm.y

        # 套 One-Euro 平滑（在歸一化座標空間做）
        sx, sy = self._smoother.filter(raw_x, raw_y)

        if self._ref_x is None:
            # 進入 ACTIVE 的第一幀：只記錄基準，不移動
            self._ref_x, self._ref_y = sx, sy
            return

        dx = (sx - self._ref_x) * self._sensitivity * self._screen_w
        dy = (sy - self._ref_y) * self._sensitivity * self._screen_h

        self._ref_x, self._ref_y = sx, sy

        if abs(dx) > 0.5 or abs(dy) > 0.5:
            pyautogui.moveRel(int(dx), int(dy))

    def reset(self):
        self._ref_x = None
        self._ref_y = None
