# 🎮 LDPlayer Auto Tool (Python)

Bot tự động điều khiển game chạy trên **LDPlayer Emulator** bằng **Python + ADB + OpenCV**.

Tool sẽ:
- Chụp màn hình emulator qua ADB
- Nhận diện **template image** (các nút trong game) bằng OpenCV
- Tự động **click** khi phát hiện đúng nút
- Lặp lại liên tục để **farm stage/map** theo workflow bạn định nghĩa

---

## 📸 Demo Workflow

Bot hoạt động theo vòng lặp:

1. Capture screen  
2. Detect template images  
3. Nếu tìm thấy template → Click vào vị trí tương ứng  
4. Repeat

Ví dụ flow farm:

`battle → ready → skip → victory → next_stage → battle → ...`

Bot sẽ tự chạy vòng lặp để farm stage liên tục.

---

## ✨ Features

- 🤖 Auto click các nút trong game
- 📸 Screenshot qua ADB
- 🔍 Image detection bằng OpenCV (template matching)
- 🖥️ GUI tool với Tkinter
- 🔌 Tự động connect ADB của LDPlayer
- 🧪 Tool test template trực tiếp trên UI
- 🛠️ Hỗ trợ lưu debug screenshot khi không match

---

## 🧱 Project Structure

```
MyAutoTool
│
├─ app
│   ├─ main.py              # Main application
│   ├─ bot.py               # Bot manager
│   ├─ game_bot.py          # Game automation logic
│   ├─ adb_client.py        # ADB communication
│   ├─ image_matcher.py     # Template matching (OpenCV)
│   ├─ ldplayer.py          # LDPlayer control
│   ├─ config_manager.py    # Config loader
│   └─ ui.py                # UI builder
│
├─ assets
│   └─ images               # Template images
│       ├─ battle.png
│       ├─ ready.png
│       ├─ skip.png
│       ├─ victory.png
│       └─ next_stage.png
│
├─ debug                    # Debug screenshots
│
├─ config.json              # Tool configuration
├─ run.py                   # Entry point
└─ README.md
```

---

## ⚙️ Requirements

- Python **3.10+**

Cài dependencies:

```bash
pip install opencv-python numpy pillow
```

---

## 🖥️ Emulator Setup

1. Cài LDPlayer: (website chính thức)
- https://www.ldplayer.net/

2. Ví dụ đường dẫn mặc định (tuỳ máy):
- LDPlayer: `E:\LDPlayer\LDPlayer9`
- ADB: `E:\LDPlayer\LDPlayer9\adb.exe`

---

## 🚀 Run the Tool

Chạy GUI:

```bash
python run.py
```

---

## 🖥️ GUI Overview

### LDPlayer Controls
- Open LDPlayer
- Focus LDPlayer
- List Instances
- Connect ADB

### Game Controls
- Open Game by Package
- Open Game by Icon
- Save Screenshot
- Test Template

### Bot Controls
- Start Bot
- Stop Bot

---

## 🖼️ Template Images

Template images được lưu tại:

- `assets/images`

Ví dụ template:
- `battle.png`
- `ready.png`
- `skip.png`
- `victory.png`
- `next_stage.png`

Bot sẽ tìm các ảnh này trên màn hình và click khi match.

---

## 🧪 Template Testing

UI có các nút test để kiểm tra khả năng nhận diện template, ví dụ:
- Test Battle
- Test Ready
- Test Skip
- Test Next Stage

Mục đích: xác nhận template vẫn khớp với UI hiện tại của game.

---

## 🔍 Debug Screenshots

Có thể lưu screenshot để debug tại:

- `debug/`

Ví dụ:
- `debug/manual_capture.png`
- `debug/battle_notfound.png`

Hữu ích khi:
- template không match
- cần kiểm tra độ lệch UI / resolution / vị trí nút

---

## ⚙️ Configuration

File: `config.json`

Ví dụ:

```json
{
  "ldplayer_path": "E:\\LDPlayer\\LDPlayer9\\dnplayer.exe",
  "adb_path": "E:\\LDPlayer\\LDPlayer9\\adb.exe",
  "game_package": "com.devsisters.ck",
  "game_activity": "com.devsisters.plugin.OvenUnityPlayerActivity",
  "default_threshold": 0.75
}
```

**Gợi ý:**
- `default_threshold`: càng cao càng khó match (ít false-positive hơn), nhưng dễ “không tìm thấy” nếu UI đổi nhẹ.

---

## 🛠️ Troubleshooting

### 1) ADB không nhận emulator

Kiểm tra:

```bash
adb devices
```

Nếu không thấy emulator, thử:

```bash
adb connect 127.0.0.1:5555
```

> Lưu ý: port có thể khác tuỳ instance/phiên bản LDPlayer.

### 2) Bot không detect được image

Nguyên nhân thường gặp:
- Template bị sai / crop chưa chuẩn
- Game update UI (đổi icon/nút)
- Resolution emulator khác lúc chụp template
- Threshold đặt quá cao

Cách xử lý:
- Chụp lại template theo đúng resolution hiện tại
- Giảm threshold, ví dụ: `0.75 → 0.65`

---

## 📌 Notes

Hiệu quả nhận diện ảnh phụ thuộc vào:
- UI game hiện tại
- Độ phân giải emulator
- Chất lượng template (crop chuẩn, không mờ)
- Ánh sáng/hiệu ứng trong game (nếu có animation overlay)

Nếu game update UI, bạn cần **chụp lại template images**.

---

## 📜 License

Dự án phục vụ mục đích học tập và thử nghiệm automation cá nhân.

---

## 👨‍💻 Author

Personal Python automation project.

---

## ⭐ Future Improvements

- Multi-instance bot (chạy nhiều LDPlayer instance)
- Tối ưu tốc độ template matching
- AI object detection thay cho template matching
- Tự động cập nhật template khi UI thay đổi
- Debug tools tốt hơn (log chi tiết, highlight vùng match, lưu history)
