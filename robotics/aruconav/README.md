# ArUcoNav: Overhead Vision Navigation & Autonomous RC Car Control System

ArUcoNav is a high-performance Python application and ESP32 firmware suite for overhead camera-guided autonomous ground vehicles (RC cars). The system tracks an ArUco marker mounted on the car, computes real-time trajectory and motion control to user-clicked waypoints, integrates dual ultrasonic sensor telemetry, and performs reactive obstacle avoidance over WiFi or ESP-NOW.

---

## 🌟 Key Features

- **Full-Screen Interactive GUI**: Built with PyQt6 and OpenCV. Click anywhere on the live video stream to command the RC car to navigate to that point.
- **Precision ArUco Tracking**: Detects position \((X, Y)\) and heading orientation angle \((\theta)\) with sub-pixel corner refinement and Kalman/EMA smoothing.
- **Dual Ultrasonic Obstacle Avoidance**: Processes live ultrasonic distance readings (\(L\) and \(R\)) from the car, dynamically deflecting paths or stopping/reversing to avoid collisions.
- **Pluggable Communication**:
  - **WiFi (UDP / WebSocket)**: Fast low-latency wireless communication directly between PC and ESP32.
  - **ESP-NOW Gateway**: Serial gateway bridge for ultra-low latency peer-to-peer radio.
  - **Simulation Mode**: Built-in 2D kinematic simulator with virtual obstacles and raycasted ultrasonics for instant testing without hardware.
- **Comprehensive Overlays & HUD**: Marker bounding boxes, target crosshairs, heading vectors, trajectory breadcrumbs, ultrasonic sensor safety cones (Green \(\to\) Yellow \(\to\) Red), and real-time telemetry meters.
- **Bottom Status & Logging Console**: Live timestamped error logs, network stats, and sensor telemetry.
- **Ready-to-Flash ESP32 Firmware**: Arduino sketches for WiFi and ESP-NOW modes with dual HC-SR04 ultrasonic sensors and PWM motor control.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the repository
cd aruconav

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
# Launch the GUI (Simulation Mode by default if no webcam selected)
python3 aruconav/main.py

# Or launch directly with a specific camera index (e.g. webcam 0)
python3 aruconav/main.py --camera 0

# Or launch directly in pure simulator mode
python3 aruconav/main.py --sim
```

---

## 🎮 How to Use

1. **Select Camera**: Use the top-left dropdown to select your connected webcam or **"Virtual Simulator"**.
2. **Select Connection Mode**: Choose **"Simulation"**, **"WiFi UDP"**, or **"ESP-NOW (Serial)"**.
3. **Set Target Waypoint**: **Left-click** anywhere on the video screen. The RC car will automatically rotate towards the target and drive forward.
4. **Queue Multiple Waypoints**: **Shift + Left-click** to add waypoints in sequence.
5. **Clear Waypoints**: **Right-click** or click **"Clear Path"**.
6. **Emergency Stop**: Press **Spacebar** or click **"EMERGENCY STOP"** to immediately kill motor throttle.
7. **Manual Control**: Toggle **Manual Mode** and use `W`, `A`, `S`, `D` keys to steer manually.
8. **Full Screen**: Press `F11` or click the Fullscreen button.

---

## 📡 Wireless Communication Protocol

### PC \(\to\) Car (Command Packet)
Sent via UDP to car IP port `8888` (or serial gateway):
```json
{
  "cmd": "DRIVE",
  "v_l": 180,
  "v_r": 180,
  "steer": 0.0,
  "speed": 0.7,
  "ts": 1711200000.123
}
```

### Car \(\to\) PC (Telemetry Packet)
Sent via UDP from car to PC port `8889`:
```json
{
  "us_l": 42.5,
  "us_r": 85.0,
  "v_bat": 7.4,
  "status": "OK",
  "ts": 1711200000.120
}
```

---

## 🤖 ESP32 Hardware Wiring & Setup

Refer to [`firmware/esp32_wifi_car/esp32_wifi_car.ino`](firmware/esp32_wifi_car/esp32_wifi_car.ino) for complete pinout and setup instructions:
- **Left Ultrasonic (HC-SR04)**: TRIG `GPIO 5`, ECHO `GPIO 18`
- **Right Ultrasonic (HC-SR04)**: TRIG `GPIO 19`, ECHO `GPIO 21`
- **Motor Driver (L298N / TB6612FNG)**:
  - Left Motor: `IN1 (GPIO 25)`, `IN2 (GPIO 26)`, `ENA (GPIO 32)`
  - Right Motor: `IN3 (GPIO 27)`, `IN4 (GPIO 14)`, `ENB (GPIO 33)`

---

## 🧪 Testing

Run the automated test suite:
```bash
python3 -m unittest discover tests/
```
