#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ==============================================================================
// 1. HARDWARE PIN DEFINITIONS (Optimized for ESP32-C3 SuperMini / DevKit)
// ==============================================================================
// Analog Sensor Pins
#define PIN_GAS_ANALOG       1   // ADC1_CH1: Gas Sensor (MQ-2 / MQ-135 / MQ-4) Analog Out

// Digital Sensors & Displays
#define PIN_TM_CLK           2   // TM1637 4-digit 7-segment Display Clock (CLK)
#define PIN_TM_DIO           3   // TM1637 4-digit 7-segment Display Data (DIO)
#define PIN_US_TRIG          4   // HC-SR04 Ultrasonic Trigger Pin (Pulse output)
#define PIN_US_ECHO          5   // HC-SR04 Ultrasonic Echo Pin (Input via 1k:2k divider)
#define PIN_DHT              6   // DHT11 / DHT22 Digital Temperature & Humidity Data
#define PIN_BUZZER           7   // Active Piezo Buzzer / Alarm Siren
#define PIN_STATUS_LED       8   // Tri-color Warning / Armed LED (Active LOW on SuperMini)
#define PIN_RELAY            10  // Emergency Actuator Relay (Exhaust Fan / Gas Solenoid)

// ==============================================================================
// 2. RELAY & ACTUATOR CONFIGURATION
// ==============================================================================
// Standard relay modules are ACTIVE LOW (LOW = Relay Energized/Tripped, HIGH = De-energized)
#define RELAY_ACTIVE_LEVEL   LOW
#define RELAY_INACTIVE_LEVEL HIGH

// Sensor Hardware Type
#define DHT_TYPE             DHT11   // Options: DHT11, DHT22, AM2302

// ==============================================================================
// 3. NETWORK & WI-FI CONNECTIVITY
// ==============================================================================
// Station Mode (Connects to Local Facility Wi-Fi)
#define DEFAULT_WIFI_SSID    "Shakthikulangara_Lab"
#define DEFAULT_WIFI_PASS    "StemLab2026"
#define WIFI_CONNECT_TIMEOUT 12000   // 12 seconds attempt before starting Fallback AP

// Standalone Access Point Mode (Zero-Router Laboratory & Field Hotspot)
#define AP_SSID              "HazardGuard-C3-AP"
#define AP_PASS              "emergency123"
#define AP_CHANNEL           1
#define AP_MAX_CONN          4

#define WEB_SERVER_PORT      80
#define MDNS_HOSTNAME        "hazardguard"  // Accessible at http://hazardguard.local

// ==============================================================================
// 4. MULTI-ENVIRONMENT HAZARD THRESHOLD PROFILES
// ==============================================================================
enum OperatingMode {
  MODE_HOUSEHOLD  = 0,  // Household: Focus on Kitchen LPG leaks, cooking smoke & room fire
  MODE_HOTEL      = 1,  // Hotel: Central commercial kitchens, boiler room overheating
  MODE_INDUSTRIAL = 2   // Industrial: Machinery danger perimeter & chemical tank overflow
};

struct HazardThresholds {
  const char* name;
  int   gasWarning;     // Gas ADC raw warning threshold (0-4095)
  int   gasAlarm;       // Gas ADC critical trip threshold (0-4095)
  float tempWarning;    // Overheat caution threshold (°C)
  float tempAlarm;      // Critical fire/burn threshold (°C)
  int   distIntrusion;  // Proximity breach zone (cm) - Worker/person too close
  int   tankOverflow;   // Liquid/meltwater tank level limit (cm from sensor)
};

// Preset Profiles for instant switching via Web Dashboard or Hardware Button
static const HazardThresholds DEFAULT_PROFILES[] = {
  // 0: Household Kitchen & Living
  {
    .name          = "Household",
    .gasWarning    = 1200,   // ~29% full ADC scale
    .gasAlarm      = 2100,   // ~51% full scale (LPG leak / thick smoke)
    .tempWarning   = 40.0,   // Elevated room heat
    .tempAlarm     = 52.0,   // Kitchen flash fire risk
    .distIntrusion = 30,     // 30 cm stove / hazard clearance
    .tankOverflow  = 12      // 12 cm domestic sump/drain overflow
  },
  // 1: Hotel Kitchen & Boiler Room
  {
    .name          = "Hotel Commercial",
    .gasWarning    = 1000,   // Stricter safety margin
    .gasAlarm      = 1800,   // Rapid commercial stove leak trip
    .tempWarning   = 38.0,   // Boiler ambient limit
    .tempAlarm     = 48.0,   // Boiler room overheat
    .distIntrusion = 45,     // 45 cm equipment perimeter
    .tankOverflow  = 10      // 10 cm grease trap / drain surge
  },
  // 2: Industrial Manufacturing & Marine Processing
  {
    .name          = "Industrial Factory",
    .gasWarning    = 800,    // High sensitivity to toxic/flammable fumes
    .gasAlarm      = 1500,   // Fast emergency vent trigger
    .tempWarning   = 44.0,   // Furnace/panel warning
    .tempAlarm     = 60.0,   // Machine overheating
    .distIntrusion = 65,     // 65 cm heavy robotic/cutting clearance
    .tankOverflow  = 8       // 8 cm hazardous effluent tank spillage
  }
};

// ==============================================================================
// 5. TIMINGS & SIGNAL PROCESSING CONSTANTS
// ==============================================================================
#define INTERVAL_SENSOR_READ   400   // Read analog and ultrasonic every 400ms
#define INTERVAL_DHT_READ      2000  // Read DHT every 2.0s (DHT sensor minimum cycle)
#define INTERVAL_DISPLAY_CYCLE 2500  // Cycle TM1637 metric screens every 2.5s
#define GAS_MOVING_AVG_SAMPLES 8     // Moving average buffer size for smooth gas reading
#define ULTRASONIC_TIMEOUT_US  25000 // 25ms ultrasonic echo timeout (~430cm max)

#endif // CONFIG_H
