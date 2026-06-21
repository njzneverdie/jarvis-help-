"""
幾何規則手勢分類器。
輸入 HandFeatures，輸出 (gesture_name, confidence)。
confidence 目前為規則符合度估算（0.0~1.0），供 UI 顯示用。
"""

from dataclasses import dataclass
from typing import Optional
from features import HandFeatures

GESTURE_NONE = "none"


@dataclass
class GestureResult:
    name: str           # 手勢名稱，未辨識為 "none"
    confidence: float   # 0.0 ~ 1.0


# 拇指指尖接觸食指指尖的距離閾值（以掌寬歸一化）
OK_TOUCH_THRESHOLD = 0.4


def classify(f: HandFeatures) -> GestureResult:
    t  = f.thumb_up
    i  = f.index_extended
    m  = f.middle_extended
    r  = f.ring_extended
    p  = f.pinky_extended

    # --- 握拳 + OK（拖曳）：五指彎曲且拇指食指指尖接觸 ---
    if not i and not m and not r and not p and f.thumb_index_dist < OK_TOUCH_THRESHOLD:
        conf = 1.0 - (f.thumb_index_dist / OK_TOUCH_THRESHOLD)
        return GestureResult("fist_ok", round(conf * 0.9 + 0.05, 2))

    # --- 握拳 Fist：五指皆彎曲 ---
    if not t and not i and not m and not r and not p:
        return GestureResult("fist", 0.95)

    # --- OK：拇指+食指指尖接近成環，其餘三指伸直 ---
    if f.thumb_index_dist < OK_TOUCH_THRESHOLD and m and r and p:
        conf = 1.0 - (f.thumb_index_dist / OK_TOUCH_THRESHOLD)
        return GestureResult("ok", round(conf * 0.9 + 0.05, 2))

    # --- 張開手掌 Open Palm：五指皆伸直 ---
    if t and i and m and r and p:
        return GestureResult("open_palm", 0.95)

    # --- 比讚 ThumbsUp：僅拇指伸直且朝上，其餘彎曲 ---
    if t and not i and not m and not r and not p and f.thumb_pointing_up:
        return GestureResult("thumbs_up", 0.90)

    # --- 數字六 Six：拇指 + 小指伸直，食中無名彎曲 ---
    if t and not i and not m and not r and p:
        return GestureResult("six", 0.90)

    # --- YA / 勝利 Victory：食指 + 中指伸直，其餘彎曲 ---
    if not t and i and m and not r and not p:
        return GestureResult("victory", 0.90)

    # --- 食指指 PointIndex：僅食指伸直 ---
    if not t and i and not m and not r and not p:
        return GestureResult("point_index", 0.90)

    # --- 三指 Three：食指 + 中指 + 無名指伸直，拇指 + 小指彎曲 ---
    if not t and i and m and r and not p:
        return GestureResult("three", 0.90)

    return GestureResult(GESTURE_NONE, 0.0)
