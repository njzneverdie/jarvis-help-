# Jarvis Help — 手勢控制電腦系統

用 webcam 偵測手勢，即時控制電腦滑鼠與快捷操作。握拳移動游標、比手勢觸發點擊／開程式等動作。純本機執行、低延遲，手勢與動作的綁定可由使用者自訂。

---

## 功能

- 握拳移動游標（類觸控板相對移動）
- 握拳 + OK 手勢進行拖曳
- 比手勢觸發點擊、雙擊、右鍵、開啟網址等動作
- 食指指向進入捲動模式
- One-Euro Filter 平滑濾波，消除手抖造成的游標顫動
- 防誤觸確認窗（手勢需穩定維持 0.4 秒才觸發）
- 所有手勢綁定可透過 `config/bindings.json` 自訂，無需改程式碼
- 預覽視窗永遠置頂，隨時確認辨識狀態

---

## 手勢對照表

| 手勢 | 動作 |
|---|---|
| 握拳 ✊ + 移動手 | 啟用游標移動 |
| 握拳 ✊ + 拇指食指接觸 | 拖曳（壓住左鍵） |
| 數字六 🤙 | 左鍵單擊 |
| YA ✌️ | 左鍵雙擊 |
| 三指 🤟 | 右鍵單擊 |
| 食指指 ☝️ + 上下移動 | 捲動頁面 |
| 比讚 👍 | 開啟 YouTube |
| 張開手掌 🖐️ | 無動作（回到待機） |

---

## 系統需求

- Python 3.10–3.13
- Windows（主要測試平台）
- 內建或外接 webcam

---

## 安裝

```bash
git clone https://github.com/njzneverdie/jarvis-help-.git
cd jarvis-help-
pip install -r requirements.txt
```

首次執行時會自動下載 MediaPipe 手部偵測模型（約 8 MB）。

---

## 執行

```bash
python main.py
```

| 按鍵 | 功能 |
|---|---|
| `q` | 離開 |
| `p` | 暫停 / 繼續辨識 |
| `d` | 開啟 debug 模式（顯示各手指伸直狀態） |

---

## 自訂手勢綁定

編輯 `config/bindings.json`：

```json
{
  "gestures": {
    "six":       { "action": "left_click" },
    "victory":   { "action": "double_click" },
    "three":     { "action": "right_click" },
    "thumbs_up": { "action": "launch", "target": "https://youtube.com" }
  }
}
```

`action` 可選值：

| 值 | 說明 |
|---|---|
| `left_click` | 左鍵單擊 |
| `double_click` | 左鍵雙擊 |
| `right_click` | 右鍵單擊 |
| `scroll` | 捲動模式 |
| `launch` | 開啟網址或程式（需加 `"target"`） |
| `none` | 無動作 |

---

## 專案結構

```
jarvis-help/
  main.py                    # 主迴圈
  config/
    bindings.json            # 手勢綁定設定
  src/
    capture.py               # webcam 擷取
    hand_tracker.py          # MediaPipe HandLandmarker 包裝
    features.py              # 幾何特徵抽取
    gesture_classifier.py    # 手勢辨識（規則式）
    debouncer.py             # 確認窗 + 冷卻期
    state_machine.py         # IDLE / ACTIVE / DRAGGING 狀態機
    cursor_controller.py     # 相對游標移動
    smoothing.py             # One-Euro Filter
    action_executor.py       # 執行動作
    config_loader.py         # 載入 JSON 設定
```

---

## 技術架構

```
Webcam 影格
  → MediaPipe HandLandmarker（21 個 3D landmark）
  → 幾何特徵抽取（手指伸直/彎曲、指尖距離）
  → 手勢分類（規則式）
  → 確認窗去抖（離散手勢需穩定 0.4 秒）
  → 查 config 綁定表
  → 動作執行（PyAutoGUI / pynput）
  → 視覺回饋視窗（骨架 + 手勢名稱 + 信心度）
```
