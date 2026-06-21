"""
Jarvis Help — M4 拖曳 + 食指捲動
握拳移動游標，握拳+OK 拖曳，食指指進入捲動模式，鬆拳後比手勢觸發點擊等動作。

操作:
  q — 離開
  p — 暫停/繼續
  d — debug 模式（顯示手指狀態）
"""

import sys
import cv2
import time

sys.path.insert(0, "src")
from capture import WebcamCapture
from hand_tracker import HandTracker
from features import extract
from gesture_classifier import classify
from state_machine import ControlStateMachine, State
from cursor_controller import CursorController
from debouncer import Debouncer
from action_executor import execute, drag_press, drag_release, scroll_by
from config_loader import load as load_config

WINDOW_NAME = "Jarvis Help — M4  (q: quit  p: pause  d: debug)"

CAMERA_INDEX = 0
CAMERA_W = 640
CAMERA_H = 480

# 連續手勢（由 state_machine 或特殊邏輯處理，不進 debouncer）
CONTINUOUS_GESTURES = {"fist", "fist_ok", "point_index", "none"}

# 從 ACTIVE/DRAG 回到 IDLE 後的緩衝期（防過渡幀誤觸）
IDLE_GRACE = 0.6

# 捲動：參考 landmark（食指 MCP = 5）的 y 位移累積換算捲動量
SCROLL_REF = 5
SCROLL_SENSITIVITY = 600   # 螢幕高度歸一化座標 × 此值 = 像素位移

GESTURE_LABEL = {
    "fist":        "握拳 Fist",
    "fist_ok":     "拖曳 Drag",
    "ok":          "OK",
    "open_palm":   "張開手掌 Open Palm",
    "thumbs_up":   "比讚 Thumbs Up",
    "six":         "數字六 Six",
    "victory":     "YA / Victory",
    "point_index": "食指捲動 Scroll",
    "three":       "三指 Three",
    "none":        "（無）",
}

STATE_COLOR = {
    State.IDLE:     (100, 100, 255),
    State.ACTIVE:   (0, 220, 80),
    State.DRAGGING: (0, 180, 255),
}


def put_text(frame, text: str, row: int, color=(0, 255, 0)):
    cv2.putText(frame, text, (10, 30 + row * 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, color, 2, cv2.LINE_AA)


def draw_conf_bar(frame, conf: float, row: int):
    bx, by = 10, 30 + row * 28 + 6
    cv2.rectangle(frame, (bx, by), (bx + 200, by + 10), (50, 50, 50), -1)
    cv2.rectangle(frame, (bx, by), (bx + int(200 * conf), by + 10), (0, 200, 100), -1)


def main():
    cfg    = load_config()
    db_cfg = cfg.get("debounce", {})

    paused   = False
    debug    = False
    last_action_msg  = ""
    last_action_time = 0.0

    sm              = ControlStateMachine()
    last_active_time = 0.0
    prev_drag       = False   # 追蹤拖曳狀態，處理 press/release 事件

    # 捲動模式狀態
    scrolling       = False
    scroll_ref_y: float | None = None

    cursor = CursorController(
        sensitivity=cfg["cursor"]["sensitivity"],
        min_cutoff=cfg["cursor"]["min_cutoff"],
        beta=cfg["cursor"]["beta"],
    )
    debouncer = Debouncer(
        confirm_seconds=db_cfg.get("confirm_seconds", 0.4),
        cooldown_seconds=db_cfg.get("cooldown_seconds", 0.6),
    )

    with WebcamCapture(CAMERA_INDEX, CAMERA_W, CAMERA_H, flip_horizontal=True) as cam, \
         HandTracker(max_num_hands=1) as tracker:

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_TOPMOST, 1)

        print("[Jarvis] M4 啟動")
        print("  握拳=移動  握拳+OK=拖曳  食指=捲動  鬆拳比手勢=點擊/開程式")
        print("  q=離開  p=暫停  d=debug")

        while True:
            frame = cam.read()
            if frame is None:
                break

            if not paused:
                hand = tracker.process(frame)
                tracker.draw_landmarks(frame, hand)

                if hand:
                    feat    = extract(hand.landmarks)
                    gesture = classify(feat)

                    # 狀態機
                    prev_state, state = sm.update(gesture.name)

                    # 記錄最後一次離開 ACTIVE/DRAG 的時間
                    if prev_state != State.IDLE and state == State.IDLE:
                        last_active_time = time.monotonic()

                    # --- 拖曳 press / release ---
                    is_dragging = (state == State.DRAGGING)
                    if is_dragging and not prev_drag:
                        drag_press()
                        last_action_msg  = "拖曳開始"
                        last_action_time = time.monotonic()
                    elif not is_dragging and prev_drag:
                        drag_release()
                        last_action_msg  = "拖曳結束"
                        last_action_time = time.monotonic()
                    prev_drag = is_dragging

                    # --- 游標移動（ACTIVE / DRAGGING 都移動）---
                    cursor.update(hand.landmarks, state)

                    # --- 捲動模式（食指指，IDLE 狀態）---
                    if state == State.IDLE and gesture.name == "point_index":
                        cur_y = hand.landmarks[SCROLL_REF].y
                        if scroll_ref_y is None:
                            scroll_ref_y = cur_y
                        else:
                            dy = (scroll_ref_y - cur_y) * SCROLL_SENSITIVITY
                            scroll_by(dy)
                            scroll_ref_y = cur_y
                        scrolling = True
                    else:
                        scroll_ref_y = None
                        scrolling    = False

                    # --- 離散手勢 debounce ---
                    idle_ready = (state == State.IDLE and
                                  time.monotonic() - last_active_time >= IDLE_GRACE)
                    if idle_ready and gesture.name not in CONTINUOUS_GESTURES:
                        fired = debouncer.update(gesture.name)
                        if fired:
                            msg = execute(fired, cfg)
                            if msg:
                                last_action_msg  = msg
                                last_action_time = time.monotonic()
                                print(f"[Jarvis] 執行：{msg}")
                    else:
                        debouncer.update("none")

                    # --- UI ---
                    label = GESTURE_LABEL.get(gesture.name, gesture.name)
                    sc    = STATE_COLOR[state]
                    if scrolling:
                        sc = (0, 220, 220)
                    put_text(frame, f"State: {'SCROLL' if scrolling else state.name}", row=0, color=sc)
                    put_text(frame, f"Gesture: {label}",               row=1, color=(0, 255, 100))
                    put_text(frame, f"Conf: {gesture.confidence:.0%}", row=2, color=(0, 200, 255))
                    draw_conf_bar(frame, gesture.confidence, row=3)

                    if debug:
                        flags = (
                            f"T={'1' if feat.thumb_up else '0'} "
                            f"I={'1' if feat.index_extended else '0'} "
                            f"M={'1' if feat.middle_extended else '0'} "
                            f"R={'1' if feat.ring_extended else '0'} "
                            f"P={'1' if feat.pinky_extended else '0'}  "
                            f"ti={feat.thumb_index_dist:.2f}"
                        )
                        put_text(frame, flags, row=5, color=(255, 200, 0))
                else:
                    # 手消失：確保拖曳釋放
                    if prev_drag:
                        drag_release()
                        prev_drag = False
                    sm.update("none")
                    cursor.reset()
                    debouncer.update("none")
                    scroll_ref_y = None
                    scrolling    = False
                    put_text(frame, "No hand detected", row=0, color=(100, 100, 255))

                # 動作回饋訊息（顯示 1.5 秒）
                if time.monotonic() - last_action_time < 1.5:
                    put_text(frame, f">> {last_action_msg}", row=7, color=(0, 255, 255))

            else:
                # 暫停時確保拖曳釋放
                if prev_drag:
                    drag_release()
                    prev_drag = False
                put_text(frame, "PAUSED", row=0, color=(0, 100, 255))

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('p'):
                paused = not paused
                if paused:
                    cursor.reset()
                print(f"[Jarvis] {'暫停' if paused else '繼續'}")
            elif key == ord('d'):
                debug = not debug

    # 安全退出：確保左鍵不卡住
    if prev_drag:
        drag_release()
    cv2.destroyAllWindows()
    print("[Jarvis] 結束。")


if __name__ == "__main__":
    main()
