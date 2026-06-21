"""
載入並驗證 config/bindings.json。
"""

import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "bindings.json")

VALID_ACTIONS = {"activate_move", "drag", "left_click", "double_click",
                 "right_click", "scroll", "launch", "none"}


def load(path: str = DEFAULT_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)

    for gesture, binding in cfg.get("gestures", {}).items():
        action = binding.get("action", "")
        if action not in VALID_ACTIONS:
            raise ValueError(f"config: 未知 action '{action}' (gesture: {gesture})")
        if action == "launch" and "target" not in binding:
            raise ValueError(f"config: gesture '{gesture}' 的 launch 缺少 target")

    return cfg
