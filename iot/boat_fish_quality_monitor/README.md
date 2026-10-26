# Shakthikulangara Fishing Boat - Fish Quality & Storage Monitor 🐟⚓

A smart marine IoT monitoring device developed for fishing vessels operating from **Shakthikulangara Fishing Harbour, Kollam, Kerala**. 

The device provides continuous surveillance over the boat's insulated fish hold / ice storage box, detecting **fish spoilage volatiles (Ammonia & Methane)**, safeguarding the **ice cold chain (0°C – 4°C)**, and preventing **stagnant meltwater clogging** that ruins catch quality.

---

## 🌊 Problem Statement & Maritime Context

Shakthikulangara is one of India's premier marine landing centers, dispatching mechanized trawlers and gillnetters for voyages spanning 1 to 15 days in the Arabian Sea. High-value catch—including Tuna, Mackerel, Kingfish, Squid, and Export-Grade Prawns—must be kept fresh using crushed block ice.

At sea, three major hazards ruin fish quality:

```
                              ┌────────────────────────────────────────┐
                              │      SHAKTHIKULANGARA FISH HOLD        │
                              └──────────────────┬─────────────────────┘
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          │                                      │                                      │
          ▼                                      ▼                                      ▼
┌───────────────────────┐             ┌───────────────────────┐             ┌───────────────────────┐
│   TEMPERATURE RISE    │             │  MELTWATER CLOGGING   │             │   SPOILAGE GASES      │
│   (Ice Depletion)     │             │  ("Dirty Water Soak") │             │   (TMA, NH3 & CH4)    │
├───────────────────────┤             ├───────────────────────┤             ├───────────────────────┤
│ If hold rises > 4°C,  │             │ Melted ice must drain │             │ Rotting fish emits    │
│ psychrotrophic        │             │ freely into bilge. If │             │ Trimethylamine (TMA)  │
│ bacteria multiply     │             │ drains clog with fish │             │ and Ammonia (TVB-N).  │
│ doubling every 20-30  │             │ scales, fish soak in  │             │ Anaerobic decay       │
│ minutes, degrading    │             │ contaminated water    │             │ generates Methane     │
│ fresh fish muscle.    │             │ causing fast decay!   │             │ gas (MQ-4 / MQ-135).  │
└───────────────────────┘             └───────────────────────┘             └───────────────────────┘
```

### The "Only Ice Should Remain" Principle
> **Rule of Thumb for Marine Storage:**  
> When crushed ice absorbs latent heat, it melts into water. If this meltwater accumulates at the bottom of the hold, the bottom layer of fish gets submerged in stagnant, chilled water. This contaminated meltwater leaches soluble proteins, dissolves protective fish skin mucus, breeds pathogenic bacteria (*Pseudomonas*, *Shewanella putrefaciens*), and softens fish flesh.  
> **Only clean ice should touch the fish—meltwater must drain away immediately!**

---

## 🛠️ Hardware Components

| Component | Function in Project | Marine Purpose |
| :--- | :--- | :--- |
| **NodeMCU (ESP8266 ESP-12E)** | Main Controller & Processing Unit | Reads sensors, evaluates freshness algorithm, drives OLED & 7-segment UI |
| **MQ-135 Gas Sensor** | Volatile Amines & Ammonia Sensor | Scans headspace air for Trimethylamine (TMA), Ammonia ($NH_3$), and TVB-N |
| **MQ-4 Gas Sensor** | Methane ($CH_4$) Gas Sensor | Detects anaerobic bacterial decay and biogas build-up in deep hold pockets |
| **DHT11 Sensor** | Temperature & Humidity Sensor | Monitors hold cold chain; alerts if storage rises above 4.0°C |
| **HC-SR04 / JSN-SR04T** | Ultrasonic Distance Sensor | Measures meltwater level at the sump; sounds alarm if water is clogged |
| **SSD1306 0.96" OLED (I2C)** | 128x64 Graphical Dashboard | Multi-page real-time status, freshness gauge, alert messages, and diagnostics |
| **TM1637 4-Digit Display** | 7-Segment High-Visibility Display | Quick glance readout on deck: Temperature, Water level, or Freshness score |
| **3x Tactile Push Buttons** | Navigation Controls | **Next Page**, **Previous Page**, and **Mode / Alarm Acknowledge** |
| **Active Buzzer** *(Optional)* | Audio Alarm | High-pitch warning when water is clogged or catch is spoiling |

---

## ⚡ Circuit Pinout & Connection Table

### NodeMCU ESP8266 Pin Assignments

| Peripheral | Peripheral Pin | NodeMCU Pin | GPIO | Description / Wiring Notes |
| :--- | :--- | :--- | :--- | :--- |
| **OLED Display** | `SCL` | `D1` | `GPIO5` | I2C Clock (shares I2C bus) |
| **OLED Display** | `SDA` | `D2` | `GPIO4` | I2C Data (shares I2C bus) |
| **TM1637 7-Seg** | `CLK` | `D5` | `GPIO14` | SPI SCLK line used as display clock |
| **TM1637 7-Seg** | `DIO` | `D6` | `GPIO12` | SPI MISO line used as display data |
| **DHT11 Sensor** | `DATA` | `D4` | `GPIO2` | Uses onboard 10kΩ pullup; idles HIGH for safe boot |
| **Ultrasonic** | `TRIG` | `D7` | `GPIO13` | 10µs trigger pulse output |
| **Ultrasonic** | `ECHO` | `D8` | `GPIO15` | Echo return signal via **1kΩ : 2kΩ voltage divider** (protects 3.3V GPIO; idles LOW at boot) |
| **Button 1 (Next)** | `PIN 1` | `D3` | `GPIO0` | Switch to GND; internal pull-up enabled (safe boot: idles HIGH) |
| **Button 2 (Prev)** | `PIN 1` | `D0` | `GPIO16` | Switch to GND; external 10kΩ pullup or input mode |
| **Button 3 (Mode)** | `PIN 1` | `RX` | `GPIO3` | Switch to GND; short press = toggle 7-Seg, long press = mute/reset |
| **MQ-135 Sensor** | `AOUT` | `A0` | `ADC0` | 0-3.3V analog input for Ammonia / TMA / TVB-N spoilage |
| **MQ-4 Sensor** | `DOUT` | Configurable | - | Digital threshold trip on anaerobic methane accumulation |
| **Power Rails** | `VCC / VIN` | `5V (VIN)` | - | Powers MQ-135, MQ-4 heater coils, Ultrasonic, and Displays |
| **Ground** | `GND` | `GND` | - | Common ground for all sensors and power supplies |

> [!WARNING]
> **5V Logic Safety for Ultrasonic Echo:**  
> The HC-SR04 runs on 5V and outputs a 5V logic pulse on its `ECHO` pin. The NodeMCU ESP8266 GPIOs tolerate a maximum of 3.3V. **Always wire a voltage divider**: connect `ECHO` to a 1kΩ resistor, connect the other end to NodeMCU `D8`, and a 2kΩ resistor from `D8` to `GND`. This drops 5V to ~3.33V safely.

> [!NOTE]
> **NodeMCU Single ADC Pin (A0):**  
> NodeMCU features one analog ADC pin (`A0`). The system connects `A0` to the **MQ-135** (the primary indicator of fish decomposition volatiles). The **MQ-4** sensor uses its onboard digital comparator pin (`DOUT`) to trip on methane threshold spikes, or both can be sampled with an optional ADS1115 I2C ADC.

---

## 📱 User Interface & Screen Navigation

The device provides 4 switchable OLED screens navigated using the **Next** (`D3`) and **Prev** (`D0`) push buttons:

### Screen 1: Master Dashboard (`1/4`)
- **Quality Status:** `PRIME FRESH` (Grade A), `COMMERCIAL` (Grade B), `WARNING` (Grade C), or `SPOILED` (Grade D).
- **Freshness Gauge:** Visual progress bar (`0%` to `100%`).
- **Quick Metrics:** Current Hold Temperature (`°C`) and Meltwater Depth (`cm`).
- **Emergency Flashing Alert:** Displays `! DRAIN WATER CLOG !` if water accumulates > 5.0 cm.

### Screen 2: Gas & Spoilage Monitor (`2/4`)
- **MQ-135 TVB-N / Ammonia:** Raw 10-bit ADC reading and estimated headspace PPM.
- **MQ-4 Methane ($CH_4$):** Real-time status (`CLEAR (OK)` or `DETECTED!`).
- **Spoilage Risk Bar:** Visual fill gauge indicating proximity to putrefaction threshold.

### Screen 3: Ice Hold & Drainage Supervisor (`3/4`)
- **Ice Hold Temp:** Monitored vs optimal range ($0.0^\circ\text{C} - 4.0^\circ\text{C}$).
- **Relative Humidity:** Confirms humid ice environment ($>80\% \text{ RH}$).
- **Meltwater Clearance:** Current water depth in cm.
- **Drainage Status:** `ICE ONLY (OK)` vs `WATER RISING` vs `CLOGGED! DRAIN`.

### Screen 4: Boat Voyage Diagnostics (`4/4`)
- **Voyage Duration:** Running timer (`HH:MM:SS`) since boat departure.
- **Hold Depth Calibration:** Configured empty depth ($40\text{ cm}$).
- **Active 7-Segment Mode:** Displays current TM1637 assignment.
- **Button Shortcut Guide:** Onscreen reference for boat crew.

---

## 🔢 TM1637 4-Digit 7-Segment Readouts

The TM1637 display is designed for instantaneous viewing from across the deck, especially under harsh sunlight or night operations.

Pressing **Button 3 (Select/Mode)** cycles between modes:

| Mode | Display Sample | Description |
| :--- | :--- | :--- |
| **Temperature** | ` 2.5C` | Hold ice temperature with decimal point and Celsius symbol |
| **Water Level** | `H 1.2` | Height of accumulated meltwater in centimeters |
| **Quality Score** | `Fr85` | Overall fish freshness percentage score ($85\%$) |
| **Auto Cycle** | Cycles every 3s | Automatically alternates between Temp, Water, and Score |
| **Clogged Alarm** | `drAn` *(Flashing)* | Overrides display to alert crew to drain clogged meltwater! |

---

## 🧮 Fish Freshness Scoring Algorithm

The system computes a real-time **Freshness Index ($0 - 100\%$)** using multi-metric biological decay weights:

$$\text{Freshness} = 100 - \Delta_{\text{Temp}} - \Delta_{\text{Water}} - \Delta_{\text{Ammonia}} - \Delta_{\text{Methane}}$$

1. **Temperature Penalty ($\Delta_{\text{Temp}}$):**  
   If $T > 4.0^\circ\text{C}$, deducts $8\%$ per degree Celsius above optimal:
   $$\Delta_{\text{Temp}} = (T - 4.0) \times 8$$
2. **Meltwater Contamination Penalty ($\Delta_{\text{Water}}$):**  
   If meltwater depth $> 2.0\text{ cm}$, deducts $12\%$ per centimeter of stagnant water:
   $$\Delta_{\text{Water}} = (\text{Depth} - 2.0) \times 12$$
3. **Volatile Spoilage Gas Penalty ($\Delta_{\text{Ammonia}}$):**  
   Deducts points as MQ-135 ADC rises above clean maritime baseline ($180\text{ ADC}$):
   $$\Delta_{\text{Ammonia}} = \frac{\text{ADC} - 180}{15}$$
4. **Anaerobic Biogas Penalty ($\Delta_{\text{Methane}}$):**  
   Deducts an immediate $25\%$ if MQ-4 detects methane from anaerobic putrefaction.

---

## 🚢 Quick Start & Flashing Instructions

### 1. Compile with Arduino CLI
From the project root:
```bash
/Users/aadilsp/.local/bin/arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 iot/boat_fish_quality_monitor
```

### 2. Upload to NodeMCU
Connect your NodeMCU board via Micro-USB and upload:
```bash
/Users/aadilsp/.local/bin/arduino-cli upload -p /dev/cu.usbserial-* --fqbn esp8266:esp8266:nodemcuv2 iot/boat_fish_quality_monitor
```

### 3. Open Serial Monitor (115200 Baud)
```bash
/Users/aadilsp/.local/bin/arduino-cli monitor -p /dev/cu.usbserial-* -c baudrate=115200
```

---

## 📋 Bill of Materials (BOM)

- 1x NodeMCU ESP8266 (ESP-12E / ESP-12F)
- 1x MQ-135 Air Quality / Ammonia Gas Sensor
- 1x MQ-4 Methane / Natural Gas Sensor
- 1x DHT11 Temperature & Humidity Sensor
- 1x HC-SR04 Ultrasonic Sensor (or waterproof JSN-SR04T)
- 1x 0.96" I2C SSD1306 OLED Display (128x64)
- 1x TM1637 4-Digit 7-Segment Display Module
- 3x 6mm Tactile Push Buttons
- 1x 1kΩ Resistor & 1x 2kΩ Resistor (Ultrasonic Echo divider)
- 1x 10kΩ Resistor (Pull-up for Button 2)
- 1x 5V / 2A Marine Power Supply or USB Power Bank
- Waterproof IP65 Project Enclosure with cable glands
