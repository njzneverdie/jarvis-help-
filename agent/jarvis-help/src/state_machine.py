"""
控制狀態機：IDLE → ACTIVE → DRAGGING
"""

from enum import Enum, auto


class State(Enum):
    IDLE     = auto()   # 控制未啟用
    ACTIVE   = auto()   # 握拳，游標跟手移動
    DRAGGING = auto()   # 握拳 + OK，左鍵壓住拖曳


class ControlStateMachine:
    def __init__(self):
        self.state = State.IDLE

    def update(self, gesture_name: str) -> tuple[State, State]:
        """
        回傳 (前一狀態, 新狀態)，讓呼叫端判斷轉換事件。
        """
        prev = self.state

        if gesture_name == "fist_ok":
            self.state = State.DRAGGING
        elif gesture_name == "fist":
            if self.state == State.DRAGGING:
                self.state = State.ACTIVE   # 放開 OK 但還在握拳 → 結束拖曳
            else:
                self.state = State.ACTIVE
        else:
            self.state = State.IDLE

        return prev, self.state
