/**
 * ============================================================================
 * Shakthikulangara Fishing Boat - Fish Quality & Storage Monitor
 * Hardware Configuration and Calibration Header
 * ============================================================================
 * 
 * Target Board: NodeMCU ESP8266 (ESP-12E / ESP-12F Module)
 * Location: Shakthikulangara Harbour, Kollam, Kerala, India
 * 
 * Hardware Peripherals:
 *  - MQ-135 Gas Sensor  : Detects Ammonia (NH3), Trimethylamine (TMA), TVB-N (Rotting)
 *  - MQ-4 Gas Sensor    : Detects Methane (CH4) & anaerobic biogas from decomposition
 *  - DHT11 Sensor       : Cold storage hold temperature and relative humidity
 *  - HC-SR04 Ultrasonic : Meltwater level in the fish hold (clogged water detection)
 *  - SSD1306 OLED (I2C) : Graphical dashboard and multi-screen navigation (128x64)
 *  - TM1637 4-Digit Display: High-visibility 7-segment numerical readout
 *  - 3x Push Buttons    : UI Navigation (Next, Previous, Select / Mode / Acknowledge)
 * ============================================================================
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ============================================================================
// 1. PIN DEFINITIONS (NodeMCU ESP8266)
// ============================================================================

// --- I2C OLED Display (SSD1306 128x64) ---
#define OLED_SCL_PIN        D1    // GPIO5 - I2C Clock
#define OLED_SDA_PIN        D2    // GPIO4 - I2C Data
#define OLED_SCREEN_WIDTH   128
#define OLED_SCREEN_HEIGHT  64
#define OLED_I2C_ADDR       0x3C  // Common addresses: 0x3C or 0x3D
#define OLED_RESET_PIN      -1    // Shared reset

// --- TM1637 4-Digit 7-Segment Display ---
#define TM1637_CLK_PIN      D5    // GPIO14 - Clock
#define TM1637_DIO_PIN      D6    // GPIO12 - Data I/O

// --- DHT11 Temperature & Humidity Sensor ---
#define DHT_PIN             D4    // GPIO2  - DHT11 Data line (ESP8266 onboard pullup)
#define DHT_TYPE            DHT11 // Sensor model DHT11

// --- Ultrasonic Sensor (HC-SR04 / JSN-SR04T) ---
#define ULTRASONIC_TRIG_PIN D7    // GPIO13 - Trigger output
#define ULTRASONIC_ECHO_PIN D8    // GPIO15 - Echo input (LOW at boot; use 1k:2k divider from 5V)

// --- Navigation Push Buttons (Active LOW - internal pull-up / pull-to-GND) ---
#define BTN_NEXT_PIN        D3    // GPIO0  - Next Page / Up (safe boot: idles HIGH)
#define BTN_PREV_PIN        D0    // GPIO16 - Previous Page / Down (pull-to-GND or ext pullup)
#define BTN_SELECT_PIN      3     // GPIO3 (RX) - Mode toggle / Mute Alert (TX remains for Serial)

// --- Gas Sensors ---
// NodeMCU has a single 10-bit ADC channel (A0).
// MQ-135 (Ammonia/TVOC spoilage) connects to Analog A0 for continuous gas monitoring.
// MQ-4 (Methane CH4) connects its Digital Out (DO) to trigger on anaerobic decomposition.
#define MQ135_ANALOG_PIN    A0    // ADC0   - Analog voltage from MQ-135
#define MQ4_DIGITAL_PIN     -1    // Optional digital alert pin (-1 if disabled or using shared bus)

// Optional Buzzer Alert (e.g. Piezo buzzer for audio alarm on boat deck)
#define BUZZER_PIN          -1    // Set to a GPIO pin if active buzzer is connected, or -1 to disable

// ============================================================================
// 2. COLD STORAGE & DRAINAGE THRESHOLDS (Marine Guidelines: FAO / MPEDA)
// ============================================================================

// --- Temperature (°C) Thresholds for Chilled Fish on Ice ---
#define TEMP_OPTIMAL_MIN    0.0f  // Minimum optimal storage temp (0°C)
#define TEMP_OPTIMAL_MAX    4.0f  // Maximum optimal cold storage temp (4°C)
#define TEMP_WARNING_MAX    8.0f  // Warning limit: ice melting fast, bacterial activity rising
                                  // Temp > 8.0°C is CRITICAL (Fish spoilage accelerates)

// --- Fish Tank / Hold Dimensions for Meltwater Calculation ---
// Sensor is mounted at the top or in the drainage sump looking down towards bottom
#define TANK_DEPTH_TOTAL_CM 40.0f // Distance from ultrasonic sensor to empty container floor (cm)
#define WATER_SAFE_MAX_CM   2.0f  // Safe meltwater depth (<= 2cm: drain working, only ice touches fish)
#define WATER_WARN_MAX_CM   5.0f  // Warning meltwater depth (2cm to 5cm: drain sluggish)
                                  // Water > 5.0cm is CLOGGED (Hazard: fish submerged in meltwater!)

// --- Gas Spoilage Thresholds (MQ-135 Analog ADC 0-1023) ---
// Calibrated for standard clean air vs rotting fish headspace volatile amines (TMA / NH3)
#define GAS_CLEAN_BASELINE  180   // Raw ADC reading in fresh maritime sea breeze
#define GAS_EARLY_SPOILAGE  350   // Raw ADC indicating initial protein breakdown / TVB-N release
#define GAS_ROTTING_CRITICAL 580  // Raw ADC indicating advanced bacterial putrefaction / spoiled catch

// ============================================================================
// 3. SYSTEM TIMINGS & DISPLAY SETTINGS
// ============================================================================
#define SENSOR_READ_INTERVAL_MS   1500  // Read sensors every 1.5 seconds
#define DISPLAY_UPDATE_INTERVAL_MS 250  // OLED refresh rate (4 FPS for smooth responsiveness)
#define TM1637_CYCLE_INTERVAL_MS  3000  // Auto-cycle TM1637 display modes every 3 seconds (if enabled)
#define BUTTON_DEBOUNCE_MS        50    // Button debounce threshold in ms
#define ULTRASONIC_SAMPLES        5     // Number of readings for rolling median/average filter

#endif // CONFIG_H
