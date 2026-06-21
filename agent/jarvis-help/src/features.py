"""
從 MediaPipe 21 個 landmark 抽取幾何特徵。
所有計算皆用相對比例，不受手部大小或距離影響。
"""

import math
from dataclasses import dataclass


# landmark 索引
WRIST = 0
# 指尖
THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP = 4, 8, 12, 16, 20
# 各指真正的 PIP 關節（食中無名小指）；拇指用 IP
THUMB_IP  = 3
INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP = 6, 10, 14, 18
# MCP 關節（指根）
THUMB_MCP, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP = 2, 5, 9, 13, 17


def _dist(a, b) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


@dataclass
class HandFeatures:
    # 各手指是否伸直（True = 伸直）
    thumb_up: bool
    index_extended: bool
    middle_extended: bool
    ring_extended: bool
    pinky_extended: bool

    # 拇指是否朝上（y 軸，翻轉後向上 = y 值減小）
    thumb_pointing_up: bool

    # 拇指指尖與食指指尖的距離（歸一化）
    thumb_index_dist: float


def extract(landmarks) -> HandFeatures:
    lm = landmarks  # 21 個 NormalizedLandmark

    def finger_extended(tip_idx, pip_idx) -> bool:
        """指尖 y < PIP y（螢幕座標，y 越小越高）→ 手指伸直。
        比距離法敏感許多，不需手指完全打直。"""
        return lm[tip_idx].y < lm[pip_idx].y

    # 掌寬（食指 MCP 到小指 MCP），用於後續歸一化
    palm_width = _dist(lm[INDEX_MCP], lm[PINKY_MCP]) or 1e-6

    # 食指、中指、無名指、小指：指尖高於 PIP → 伸直
    index_ext  = finger_extended(INDEX_TIP,  INDEX_PIP)
    middle_ext = finger_extended(MIDDLE_TIP, MIDDLE_PIP)
    ring_ext   = finger_extended(RING_TIP,   RING_PIP)
    pinky_ext  = finger_extended(PINKY_TIP,  PINKY_PIP)

    # 拇指：指尖高於 IP 關節，且指尖離食指指根（INDEX_MCP）距離超過掌寬 0.6 倍。
    # 加距離條件可過濾比食指時拇指自然微張的誤判。
    thumb_up = (
        lm[THUMB_TIP].y < lm[THUMB_IP].y
        and _dist(lm[THUMB_TIP], lm[INDEX_MCP]) > palm_width * 0.6
    )

    # 拇指是否朝上：指尖 y < MCP y
    thumb_pointing_up = lm[THUMB_TIP].y < lm[THUMB_MCP].y

    # 拇指指尖與食指指尖距離（歸一化）
    thumb_index_dist = _dist(lm[THUMB_TIP], lm[INDEX_TIP]) / palm_width

    return HandFeatures(
        thumb_up=thumb_up,
        index_extended=index_ext,
        middle_extended=middle_ext,
        ring_extended=ring_ext,
        pinky_extended=pinky_ext,
        thumb_pointing_up=thumb_pointing_up,
        thumb_index_dist=thumb_index_dist,
    )
