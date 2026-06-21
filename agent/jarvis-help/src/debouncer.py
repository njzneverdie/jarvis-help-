"""
離散手勢確認窗 + 冷卻期。
手勢需穩定維持 confirm_seconds 才 emit 一次事件，
觸發後進入 cooldown_seconds 冷卻，避免連發。
"""

import time


class Debouncer:
    def __init__(self, confirm_seconds: float = 0.4, cooldown_seconds: float = 0.6):
        self._confirm = confirm_seconds
        self._cooldown = cooldown_seconds

        self._candidate: str | None = None
        self._candidate_since: float = 0.0
        self._last_fired: float = 0.0
        self._last_fired_gesture: str | None = None

    def update(self, gesture_name: str) -> str | None:
        """
        傳入當前幀辨識到的手勢名稱。
        若確認窗通過且不在冷卻期，回傳手勢名稱（觸發一次）；否則回傳 None。
        """
        now = time.monotonic()

        # 冷卻期內不觸發
        if now - self._last_fired < self._cooldown:
            return None

        # 手勢改變 → 重置候選
        if gesture_name != self._candidate:
            self._candidate = gesture_name
            self._candidate_since = now
            return None

        # 同一手勢穩定夠久 → 觸發，並清除候選（需放掉手勢再重比才能再次觸發）
        if now - self._candidate_since >= self._confirm:
            self._last_fired = now
            self._candidate = None
            return gesture_name

        return None
