"""
MediaPipe Tasks API (mediapipe >= 0.10) HandLandmarker wrapper.
Downloads hand_landmarker.task model on first run if not present.
"""

import os
import urllib.request
import cv2
import mediapipe as mp
from dataclasses import dataclass
from typing import Optional

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarksConnections = mp.tasks.vision.HandLandmarksConnections
RunningMode = mp.tasks.vision.RunningMode

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "hand_landmarker.task")

# MediaPipe landmark indices
WRIST = 0
FINGERTIP_IDS = [4, 8, 12, 16, 20]   # thumb, index, middle, ring, pinky tips
PIP_IDS       = [3, 7, 11, 15, 19]   # thumb IP, index/mid/ring/pinky PIP
MCP_IDS       = [2, 5,  9, 13, 17]   # thumb CMC, index/mid/ring/pinky MCP


@dataclass
class HandResult:
    landmarks: list       # 21 NormalizedLandmark objects (x, y, z all in [0,1])
    handedness: str       # "Left" or "Right"


def _ensure_model():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        print(f"[HandTracker] Downloading model to {MODEL_PATH} …")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[HandTracker] Download complete.")


class HandTracker:
    # HAND_CONNECTIONS list of (start_idx, end_idx) tuples for drawing
    CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),       # thumb
        (0, 5), (5, 6), (6, 7), (7, 8),        # index
        (0, 9), (9, 10), (10, 11), (11, 12),   # middle
        (0, 13), (13, 14), (14, 15), (15, 16), # ring
        (0, 17), (17, 18), (18, 19), (19, 20), # pinky
        (5, 9), (9, 13), (13, 17),             # palm cross
    ]

    def __init__(self, max_num_hands: int = 1, detection_confidence: float = 0.7, tracking_confidence: float = 0.5):
        _ensure_model()
        with open(MODEL_PATH, "rb") as f:
            model_data = f.read()
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_buffer=model_data),
            running_mode=RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._frame_ts_ms = 0

    def process(self, bgr_frame) -> Optional[HandResult]:
        self._frame_ts_ms += 33   # ~30 fps timestamp increment
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, self._frame_ts_ms)

        if not result.hand_landmarks:
            return None

        landmarks = result.hand_landmarks[0]          # NormalizedLandmark list
        raw = result.handedness[0][0].display_name   # "Left" or "Right"
        # MediaPipe 以未翻轉影像為基準判斷左右手；水平翻轉後需對調
        handedness = "Right" if raw == "Left" else "Left"
        return HandResult(landmarks=landmarks, handedness=handedness)

    def draw_landmarks(self, bgr_frame, hand_result: Optional[HandResult]) -> None:
        if hand_result is None:
            return
        h, w = bgr_frame.shape[:2]
        lms = hand_result.landmarks

        # Draw connections
        for start, end in self.CONNECTIONS:
            x0 = int(lms[start].x * w)
            y0 = int(lms[start].y * h)
            x1 = int(lms[end].x * w)
            y1 = int(lms[end].y * h)
            cv2.line(bgr_frame, (x0, y0), (x1, y1), (80, 200, 120), 2)

        # Draw landmark dots
        for i, lm in enumerate(lms):
            x, y = int(lm.x * w), int(lm.y * h)
            color = (0, 128, 255) if i in FINGERTIP_IDS else (255, 255, 255)
            cv2.circle(bgr_frame, (x, y), 5, color, -1)
            cv2.circle(bgr_frame, (x, y), 5, (0, 0, 0), 1)

    def close(self):
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
