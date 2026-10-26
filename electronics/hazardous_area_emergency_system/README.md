# HazardGuard C3 // Multi-Hazard Emergency & Safety Automation Platform 🚨⚡

**Shakthikulangara School STEM Lab • Electronics & IoT Engineering Project**  
*Target Core: ESP32-C3 RISC-V 32-bit Microcontroller (Wi-Fi 2.4GHz & Bluetooth LE)*

---

## 📌 Executive Summary & Purpose

Hazardous environments—ranging from **household kitchens and hotel central boiler rooms to industrial seafood processing plants and chemical factories**—face constant threats from explosive gas leaks, thermal runaway/fire hazards, unauthorized proximity to dangerous machinery, and toxic effluent/meltwater overflows.

**HazardGuard C3** is an integrated electronic supervisor and emergency automation station. It fuses analog and digital sensory telemetry in real time, drives audible and visual warning indicators, trips optocoupled emergency actuators (such as exhaust ventilation fans or gas solenoid shut-off valves), multiplexes status codes across a 4-digit 7-segment display, and serves an onboard, zero-dependency **Cyber-Industrial Web Dashboard** over local Wi-Fi.

```
                      ┌──────────────────────────────────────────┐
                      │    HAZARDGUARD C3 EMERGENCY SUPERVISOR   │
                      │               (ESP32-C3)                 │
                      └────────────────────┬─────────────────────┘
                                           │
         ┌──────────────────┬──────────────┴─────┬──────────────────┐
         ▼                  ▼                    ▼                  ▼
┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐
│  GAS / SMOKE     ││  THERMAL / FIRE  ││ ULTRASONIC RADAR ││ 4-DIGIT 7-SEG    │
│  (MQ-2 / MQ-135) ││  (DHT11 / DHT22) ││ (HC-SR04 / SR04P)││ (TM1637 DISPLAY) │
│  ADC1_CH1 (GPIO1)││  Data (GPIO 6)   ││ TRIG: 4, ECHO: 5 ││ CLK: 2, DIO: 3   │
└────────┬─────────┘└────────┬─────────┘└────────┬─────────┘└──────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │ Multi-Hazard Evaluation Engine
                             ▼
         ┌──────────────────────────────────────────────────────────┐
         │               ACTIVE SAFETY ACTUATION & IOT              │
         ├──────────────────────────┬───────────────────────────────┤
         │ ⚡ Emergency Relay (G10) │ Tripped (Cutoff / Exhaust)    │
         │ 🔊 Active Siren (G7)     │ Rapid Multi-Frequency Cadence │
         │ 💡 Armed / Alert LED (G8)│ Warning Pulse / Heartbeat     │
         │ 🌐 Web Dashboard (HTTP)  │ Standalone AP & Local Station │
         └──────────────────────────┴───────────────────────────────┘
```

---

## 🛡️ Target Environments & Hazard Scenarios

| Environment | Primary Hazard Monitored | Safety Actuation Trigger | Ultrasonic Dual-Role |
| :--- | :--- | :--- | :--- |
| **🏠 Household** | Kitchen LPG/Methane leaks, cooking grease fire, smoke | Trips gas shutoff solenoid valve & sounds audible alarm | Monitors safety clearance around open gas burners |
| **🏨 Hotel Commercial** | Central steam boiler overheating, commercial range LPG leakage | Disengages fuel supply and triggers rooftop exhaust blowers | Monitors grease trap / wastewater drain surge levels |
| **🏭 Industrial Plant** | Chemical vapor accumulation, toxic gas, machinery zone breach | Energizes high-flow explosion-proof ventilation system | Detects personnel breaching danger perimeters around moving machines |

---

## 🔌 Hardware Pinout & Wiring Specification

### ESP32-C3 Pin Allocation Matrix

| Component | Module Pin | ESP32-C3 Pin | Mode | Description / Voltage Precautions |
| :--- | :--- | :--- | :--- | :--- |
| **Gas Sensor (MQ Series)** | `AO` (Analog Out) | **GPIO 1** | Analog In | Connect to ADC1_CH1. (VCC: 5V, GND: Common GND) |
| **Ultrasonic Sensor (HC-SR04)** | `TRIG` | **GPIO 4** | Digital Out | 10µs trigger pulse |
| **Ultrasonic Sensor (HC-SR04)** | `ECHO` | **GPIO 5** | Digital In | **Crucial:** 5V Echo must pass through a 1kΩ / 2kΩ voltage divider to 3.3V! |
| **Temperature Sensor (DHT11)** | `DATA` | **GPIO 6** | Digital I/O | Requires 10kΩ pullup resistor to 3.3V (or breakout module with pullup) |
| **Active Buzzer / Siren** | `+ / SIG` | **GPIO 7** | Digital Out | Driven via NPN transistor or direct GPIO (if low-current buzzer) |
| **System Armed / Warning LED** | `Anode (+)` | **GPIO 8** | Digital Out | Current-limiting resistor 220Ω-330Ω to GND |
| **Emergency Relay Module** | `IN` | **GPIO 10** | Digital Out | Active LOW optocoupled trigger (LOW = Relay ON) |
| **4-Digit Display (TM1637)** | `CLK` | **GPIO 2** | Digital Out | I2C-like clock line |
| **4-Digit Display (TM1637)** | `DIO` | **GPIO 3** | Digital I/O | Bidirectional data line |
| **Power Supply** | `5V / VIN` | **VIN / 5V** | Power In | Regulated 5V 1.5A DC power rail |
| **Power Supply** | `GND` | **GND** | Ground | Common system ground bus |

> [!WARNING]
> **5V to 3.3V Logic Level Protection for HC-SR04 Echo:**
> Standard HC-SR04 echo pins output 5V logic. Connecting 5V directly to ESP32-C3 GPIO 5 can damage the MCU over time. Always connect a simple voltage divider:
> `HC-SR04 ECHO` ──▶ `[ 1 kΩ Resistor ]` ──▶ **GPIO 5** ──▶ `[ 2 kΩ Resistor ]` ──▶ `GND`

---

## 📦 Bill of Materials (BOM)

| Item | Component Description | Quantity | Approximate Cost (INR) |
| :---: | :--- | :---: | :---: |
| 1 | **ESP32-C3 SuperMini / DevKit Board** (RISC-V, Wi-Fi 2.4GHz) | 1 | ₹350 |
| 2 | **MQ-2 or MQ-135 Gas Sensor Module** (Combustible Gas & Smoke) | 1 | ₹150 |
| 3 | **DHT11 / DHT22 Digital Temperature & Humidity Sensor** | 1 | ₹120 |
| 4 | **HC-SR04 / HC-SR04P Ultrasonic Ranging Module** | 1 | ₹110 |
| 5 | **1-Channel 5V Optocoupled Relay Module** (10A 250VAC rating) | 1 | ₹75 |
| 6 | **TM1637 4-Digit 7-Segment LED Display Module** (Red/Green) | 1 | ₹110 |
| 7 | **5V Active Piezo Buzzer** | 1 | ₹25 |
| 8 | **5mm High-Intensity Red / Amber / Green LEDs** | 3 | ₹15 |
| 9 | **Resistors: 220Ω, 1kΩ, 2kΩ, 10kΩ** | 1 set | ₹10 |
| 10 | **Solderless Breadboard & Male-to-Female Jumper Wires** | 1 set | ₹120 |
| 11 | **5V 2A USB-C Power Adapter & Cable** | 1 | ₹200 |
| **Total** | **Complete Multi-Hazard Emergency System** | | **~₹1,285** |

---

## 📟 7-Segment Display Legend (TM1637)

The 4-digit display automatically cycles telemetry in normal mode and locks onto flashing emergency indicators during a hazard:

| Display Code | Mode | Meaning |
| :---: | :---: | :--- |
| `GAS ` ➔ `1240` | Normal Cycle | Displays Gas ADC concentration (0 - 4095) |
| `tEMP` ➔ `29` | Normal Cycle | Displays Ambient Temperature in °C |
| `dISt` ➔ `85` | Normal Cycle | Displays Ultrasonic Clearance Distance in cm |
| `SAFE` | Normal Cycle | All sensor parameters are within normal safety envelope |
| `GAS ` (Flashing) | **CRITICAL ALARM** | Combustible gas leak detected! Relay tripped. |
| `FIrE` (Flashing) | **CRITICAL ALARM** | Thermal runaway or fire temperature threshold breached! |
| `Inrt` (Flashing) | **CRITICAL ALARM** | Intrusion into prohibited danger perimeter detected! |
| `trIP` (Flashing) | **ACTUATOR LOCK** | Emergency relay actively engaged (Exhaust fan / Solenoid shut) |

---

## 🌐 Onboard Cyber-Industrial Web Dashboard

HazardGuard C3 operates a web server on port 80:

1. **Zero-Router Standalone Access Point**:
   - The device automatically creates its own Wi-Fi network:
     - **SSID:** `HazardGuard-C3-AP`
     - **Password:** `emergency123`
     - **IP Address:** `http://192.168.4.1`
2. **Local Facility Wi-Fi (Station Mode)**:
   - Also connects to `Shakthikulangara_Lab` and responds at `http://hazardguard.local`.
3. **Dashboard Highlights**:
   - **Real-Time Gauges**: Gas concentration, temperature (°C & °F), ultrasonic distance (cm), and relay state with smooth 800ms updates.
   - **Threat Level Banner**: Dynamic color shift from Safe Green to Caution Amber and Emergency Pulsing Red.
   - **Web Audio Emergency Siren**: Integrated JavaScript oscillator synthesizes a dual-tone evacuation siren in the user's browser.
   - **One-Touch Emergency Trip & Reset**: Allows emergency manual override of the exhaust/solenoid relay.
   - **Live Threshold Tuner**: Dynamically adjust gas, temperature, and perimeter limits right from your phone or PC.
   - **Hazard Blackbox Journal**: Timestamped terminal event log recording all state transitions.

---

## 🚀 Step-by-Step Laboratory Setup & Flashing

### 1. Arduino IDE Setup
- Open **Arduino IDE**.
- Go to `Tools` ➔ `Board` ➔ `ESP32 Arduino` ➔ Select **ESP32C3 Dev Module** (or **MakerGO ESP32 C3 SuperMini**).
- Set:
  - **CPU Frequency:** `160MHz`
  - **Flash Mode:** `QIO`
  - **Upload Speed:** `921600` or `115200`
  - **USB CDC On Boot:** `Enabled` (for native USB CDC boards)

### 2. Required Libraries
Make sure the following libraries are installed in `~/Documents/Arduino/libraries`:
- `TM1637` by Avishay Orpaz
- `DHT sensor library` by Adafruit
- `Adafruit Unified Sensor`

### 3. Uploading via CLI
Alternatively, flash directly using `arduino-cli`:
```bash
# Compile
arduino-cli compile --fqbn esp32:esp32:esp32c3 electronics/hazardous_area_emergency_system

# Upload to connected ESP32-C3 port (e.g., /dev/cu.usbmodem1101)
arduino-cli upload -p /dev/cu.usbmodem1101 --fqbn esp32:esp32:esp32c3 electronics/hazardous_area_emergency_system
```

---

## 🔬 Demonstration & Safety Drill Guide

1. **Clean Air Baseline**:
   - Power up the unit. Verify the TM1637 shows `SAFE` and cycles through `GAS`, `tEMP`, and `dISt`.
   - Access `http://192.168.4.1` on your phone to confirm live telemetry gauges.
2. **Simulating Gas Leak**:
   - Release butane vapor from an unlit lighter near the MQ-2 sensor.
   - Watch the gas gauge spike > 2100 ADC.
   - Observe: Relay clicks ON, buzzer warbles rapidly, TM1637 flashes `GAS `, and the dashboard flashes red with siren audio.
3. **Simulating Overheat / Fire**:
   - Warm the DHT11 with warm air or blow gently. As temperature exceeds 52°C, the `FIrE` alarm triggers.
4. **Simulating Danger Zone Intrusion**:
   - Move an object or hand closer than 30 cm in front of the HC-SR04 ultrasonic sensor.
   - Verify `Inrt` alarm triggers and the relay engages emergency safety shutdown.
