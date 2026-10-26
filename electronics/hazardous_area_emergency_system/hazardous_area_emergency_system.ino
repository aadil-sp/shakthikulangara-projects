/*
 * ==============================================================================
 * HazardGuard C3 // Intelligent Multi-Hazard Emergency & Safety Automation System
 * Developed for: Shakthikulangara School STEM Lab & Industrial Safety Projects
 * Target MCU: ESP32-C3 (RISC-V 160MHz, Wi-Fi 2.4GHz)
 * ==============================================================================
 * Features:
 *  1. Combustible Gas & Smoke Leak Surveillance (MQ-2 / MQ-135 on ADC1_CH1)
 *  2. Ambient Overheat & Fire Danger Detection (DHT11 / DHT22)
 *  3. Ultrasonic Danger Zone Intrusion & Liquid Sump Overflow (HC-SR04)
 *  4. Optocoupled Emergency Actuator Relay (Exhaust Fan / Solenoid Cutoff)
 *  5. 4-Digit 7-Segment Multiplexed Status & Threat Display (TM1637)
 *  6. Embedded Standalone Cyber-Industrial Web Dashboard & JSON Telemetry API
 *  7. Dual-Mode Wi-Fi: Station Client with Auto Fallback Hotspot (AP Mode)
 * ==============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <TM1637Display.h>
#include <DHT.h>

#include "config.h"
#include "webpage.h"

// ------------------------------------------------------------------------------
// Hardware Instances
// ------------------------------------------------------------------------------
TM1637Display display(PIN_TM_CLK, PIN_TM_DIO);
DHT dht(PIN_DHT, DHT_TYPE);
WebServer server(WEB_SERVER_PORT);

// ------------------------------------------------------------------------------
// 7-Segment Custom Word Bitmaps (Avishay Orpaz TM1637 Format)
// ------------------------------------------------------------------------------
// "GAS "
const uint8_t SEG_WORD_GAS[] = {
  SEG_A | SEG_C | SEG_D | SEG_E | SEG_F,          // G
  SEG_A | SEG_B | SEG_C | SEG_E | SEG_F | SEG_G,  // A
  SEG_A | SEG_C | SEG_D | SEG_F | SEG_G,          // S
  0x00                                            // blank
};

// "tEMP"
const uint8_t SEG_WORD_TEMP[] = {
  SEG_D | SEG_E | SEG_F | SEG_G,                  // t
  SEG_A | SEG_D | SEG_E | SEG_F | SEG_G,          // E
  SEG_A | SEG_B | SEG_E | SEG_F,                  // n (approx M)
  SEG_A | SEG_B | SEG_E | SEG_F | SEG_G           // P
};

// "dISt"
const uint8_t SEG_WORD_DIST[] = {
  SEG_B | SEG_C | SEG_D | SEG_E | SEG_G,          // d
  SEG_B | SEG_C,                                  // I
  SEG_A | SEG_C | SEG_D | SEG_F | SEG_G,          // S
  SEG_D | SEG_E | SEG_F | SEG_G                   // t
};

// "SAFE"
const uint8_t SEG_WORD_SAFE[] = {
  SEG_A | SEG_C | SEG_D | SEG_F | SEG_G,          // S
  SEG_A | SEG_B | SEG_C | SEG_E | SEG_F | SEG_G,  // A
  SEG_A | SEG_E | SEG_F | SEG_G,                  // F
  SEG_A | SEG_D | SEG_E | SEG_F | SEG_G           // E
};

// "FIrE"
const uint8_t SEG_WORD_FIRE[] = {
  SEG_A | SEG_E | SEG_F | SEG_G,                  // F
  SEG_B | SEG_C,                                  // I
  SEG_E | SEG_G,                                  // r
  SEG_A | SEG_D | SEG_E | SEG_F | SEG_G           // E
};

// "trIP"
const uint8_t SEG_WORD_TRIP[] = {
  SEG_D | SEG_E | SEG_F | SEG_G,                  // t
  SEG_E | SEG_G,                                  // r
  SEG_B | SEG_C,                                  // I
  SEG_A | SEG_B | SEG_E | SEG_F | SEG_G           // P
};

// "Inrt" (Intrusion)
const uint8_t SEG_WORD_INTR[] = {
  SEG_B | SEG_C,                                  // I
  SEG_C | SEG_E | SEG_G,                          // n
  SEG_D | SEG_E | SEG_F | SEG_G,                  // t
  SEG_E | SEG_G                                   // r
};

// ------------------------------------------------------------------------------
// Global State & Telemetry Variables
// ------------------------------------------------------------------------------
OperatingMode currentMode = MODE_HOUSEHOLD;
HazardThresholds activeThresholds = DEFAULT_PROFILES[0];

// Telemetry values
int   gasRaw         = 0;
int   gasPpm         = 0;
float currentTemp    = 25.0;
float currentHum     = 60.0;
int   currentDist    = 100; // cm

// Moving average buffer for gas ADC
int  gasHistory[GAS_MOVING_AVG_SAMPLES] = {0};
int  gasHistIndex = 0;
long gasHistTotal = 0;

// Threat assessment: 0 = Normal, 1 = Warning, 2 = Critical Alarm
int    hazardLevel = 0;
String activeHazards = "None";

// Actuator State
bool   relayActive = false;
bool   relayManualOverride = false;
String relayReason = "Standby Safe";

// Timers for non-blocking execution
unsigned long lastSensorPoll  = 0;
unsigned long lastDhtPoll     = 0;
unsigned long lastDisplayStep = 0;
unsigned long lastBuzzerStep  = 0;
bool buzzerState              = false;
int  displayCycleStep         = 0;
bool displaySubStep           = false; // Toggles label vs numeric value

// ------------------------------------------------------------------------------
// Ultrasonic Distance Measurement
// ------------------------------------------------------------------------------
int readUltrasonicDistance() {
  digitalWrite(PIN_US_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_US_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_US_TRIG, LOW);

  long duration = pulseIn(PIN_US_ECHO, HIGH, ULTRASONIC_TIMEOUT_US);
  if (duration == 0) {
    return 999; // Out of range or sensor disconnected
  }
  int cm = (int)(duration * 0.0343 / 2.0);
  if (cm < 2 || cm > 400) return 999;
  return cm;
}

// ------------------------------------------------------------------------------
// Gas Sensor Moving Average & Estimated PPM
// ------------------------------------------------------------------------------
void readGasSensor() {
  int raw = analogRead(PIN_GAS_ANALOG);

  // Moving average filter to suppress electrical noise
  gasHistTotal = gasHistTotal - gasHistory[gasHistIndex];
  gasHistory[gasHistIndex] = raw;
  gasHistTotal = gasHistTotal + raw;
  gasHistIndex = (gasHistIndex + 1) % GAS_MOVING_AVG_SAMPLES;
  gasRaw = gasHistTotal / GAS_MOVING_AVG_SAMPLES;

  // Approximate relative PPM estimation (calibrated for MQ series on 3.3V ADC)
  // Clean room air baseline: ~350-500 ADC -> ~50-80 PPM
  // Flammable leak: >1800 ADC -> >1000 PPM
  gasPpm = map(constrain(gasRaw, 350, 3800), 350, 3800, 40, 4500);
}

// ------------------------------------------------------------------------------
// Multi-Hazard Evaluation Engine
// ------------------------------------------------------------------------------
void evaluateHazards() {
  bool gasCritical  = (gasRaw >= activeThresholds.gasAlarm);
  bool gasWarning   = (!gasCritical && gasRaw >= activeThresholds.gasWarning);

  bool tempCritical = (currentTemp >= activeThresholds.tempAlarm);
  bool tempWarning  = (!tempCritical && currentTemp >= activeThresholds.tempWarning);

  bool distCritical = (currentDist > 0 && currentDist <= activeThresholds.distIntrusion);
  bool tankCritical = (currentDist > 0 && currentDist <= activeThresholds.tankOverflow);

  // Build hazard status text
  String hazards = "";
  if (gasCritical) hazards += "[GAS LEAK DETECTED] ";
  else if (gasWarning) hazards += "[Gas Vapor Elevated] ";

  if (tempCritical) hazards += "[FIRE/OVERHEAT CRITICAL] ";
  else if (tempWarning) hazards += "[Ambient Heat Warning] ";

  if (distCritical) hazards += "[PERIMETER BREACH] ";
  if (tankCritical) hazards += "[SUMP OVERFLOW RISK] ";

  if (hazards.length() == 0) hazards = "All Parameters Normal";
  activeHazards = hazards;

  // Set overall threat level
  if (gasCritical || tempCritical || distCritical || tankCritical) {
    hazardLevel = 2; // Critical Alarm
  } else if (gasWarning || tempWarning) {
    hazardLevel = 1; // Warning
  } else {
    hazardLevel = 0; // Normal
  }

  // Automatic Relay Safety Action
  if (!relayManualOverride) {
    if (hazardLevel == 2) {
      if (!relayActive) {
        relayActive = true;
        if (gasCritical) relayReason = "Triggered: Gas Leak (Exhaust Active)";
        else if (tempCritical) relayReason = "Triggered: Thermal/Fire Safety Cutoff";
        else if (distCritical) relayReason = "Triggered: Danger Perimeter Proximity";
        else relayReason = "Triggered: Hazardous Tank Overflow";
        digitalWrite(PIN_RELAY, RELAY_ACTIVE_LEVEL);
      }
    } else {
      if (relayActive) {
        relayActive = false;
        relayReason = "Standby Safe (Auto Restored)";
        digitalWrite(PIN_RELAY, RELAY_INACTIVE_LEVEL);
      }
    }
  }
}

// ------------------------------------------------------------------------------
// Non-Blocking Audible Buzzer & Visual Indicator Engine
// ------------------------------------------------------------------------------
void updateAlertSignaling() {
  unsigned long now = millis();

  if (hazardLevel == 2) {
    // Rapid Emergency Pulse (120ms cadence)
    if (now - lastBuzzerStep >= 120) {
      lastBuzzerStep = now;
      buzzerState = !buzzerState;
      digitalWrite(PIN_BUZZER, buzzerState ? HIGH : LOW);
      digitalWrite(PIN_STATUS_LED, buzzerState ? LOW : HIGH); // Active LOW LED
    }
  } else if (hazardLevel == 1) {
    // Intermittent Caution Pulse (400ms cadence)
    if (now - lastBuzzerStep >= 400) {
      lastBuzzerStep = now;
      buzzerState = !buzzerState;
      digitalWrite(PIN_BUZZER, buzzerState ? HIGH : LOW);
      digitalWrite(PIN_STATUS_LED, buzzerState ? LOW : HIGH);
    }
  } else {
    // Normal Safe: LED solid ON (or slow heartbeat), Buzzer completely silent
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_STATUS_LED, LOW); // Active LOW on ESP32-C3
  }
}

// ------------------------------------------------------------------------------
// TM1637 Dynamic Display Multiplexer
// ------------------------------------------------------------------------------
void updateDisplay() {
  unsigned long now = millis();

  // If in Critical Alarm: Flash priority hazard codes
  if (hazardLevel == 2) {
    if (now - lastDisplayStep >= 500) {
      lastDisplayStep = now;
      displaySubStep = !displaySubStep;

      if (displaySubStep) {
        if (gasRaw >= activeThresholds.gasAlarm) {
          display.setSegments(SEG_WORD_GAS);
        } else if (currentTemp >= activeThresholds.tempAlarm) {
          display.setSegments(SEG_WORD_FIRE);
        } else if (currentDist <= activeThresholds.distIntrusion) {
          display.setSegments(SEG_WORD_INTR);
        } else {
          display.setSegments(SEG_WORD_TRIP);
        }
      } else {
        display.clear();
      }
    }
    return;
  }

  // Normal / Warning: Cycle through Gas -> Temp -> Dist -> Safe every 2.5s
  if (now - lastDisplayStep >= INTERVAL_DISPLAY_CYCLE) {
    lastDisplayStep = now;
    displayCycleStep = (displayCycleStep + 1) % 4;
    displaySubStep = false;
  }

  // Sub-step: alternating label and numeric value every 1.25s
  if (now - lastDisplayStep >= (INTERVAL_DISPLAY_CYCLE / 2) && !displaySubStep) {
    displaySubStep = true;
  }

  switch (displayCycleStep) {
    case 0: // Gas screen
      if (!displaySubStep) display.setSegments(SEG_WORD_GAS);
      else display.showNumberDec(constrain(gasRaw, 0, 9999), false);
      break;

    case 1: // Temperature screen
      if (!displaySubStep) display.setSegments(SEG_WORD_TEMP);
      else {
        int t = (int)currentTemp;
        display.showNumberDec(constrain(t, -99, 999), false);
      }
      break;

    case 2: // Ultrasonic Distance screen
      if (!displaySubStep) display.setSegments(SEG_WORD_DIST);
      else {
        int d = (currentDist > 999) ? 999 : currentDist;
        display.showNumberDec(d, false);
      }
      break;

    case 3: // System Status screen
      if (hazardLevel == 1) {
        display.showNumberDec(8888, false); // Warning indicator
      } else {
        display.setSegments(SEG_WORD_SAFE);
      }
      break;
  }
}

// ------------------------------------------------------------------------------
// Web Server REST API Handlers
// ------------------------------------------------------------------------------
void handleRoot() {
  server.send_P(200, "text/html", INDEX_HTML);
}

void handleApiData() {
  String json = "{";
  json += "\"uptime\":" + String(millis() / 1000) + ",";
  json += "\"mode\":" + String((int)currentMode) + ",";
  json += "\"modeName\":\"" + String(activeThresholds.name) + "\",";
  json += "\"gasRaw\":" + String(gasRaw) + ",";
  json += "\"gasPpm\":" + String(gasPpm) + ",";
  json += "\"temp\":" + String(currentTemp, 1) + ",";
  json += "\"humidity\":" + String(currentHum, 1) + ",";
  json += "\"distance\":" + String(currentDist) + ",";
  json += "\"relayActive\":" + String(relayActive ? "true" : "false") + ",";
  json += "\"relayReason\":\"" + relayReason + "\",";
  json += "\"hazardLevel\":" + String(hazardLevel) + ",";
  json += "\"activeHazards\":\"" + activeHazards + "\",";
  json += "\"gasWarnThresh\":" + String(activeThresholds.gasWarning) + ",";
  json += "\"gasAlarmThresh\":" + String(activeThresholds.gasAlarm) + ",";
  json += "\"tempWarnThresh\":" + String(activeThresholds.tempWarning, 1) + ",";
  json += "\"tempAlarmThresh\":" + String(activeThresholds.tempAlarm, 1) + ",";
  json += "\"distThresh\":" + String(activeThresholds.distIntrusion);
  json += "}";

  server.send(200, "application/json", json);
}

void handleApiRelay() {
  if (server.hasArg("state")) {
    int state = server.arg("state").toInt();
    relayManualOverride = true;
    relayActive = (state == 1);
    digitalWrite(PIN_RELAY, relayActive ? RELAY_ACTIVE_LEVEL : RELAY_INACTIVE_LEVEL);
    relayReason = relayActive ? "Manual Override (User Tripped)" : "Manual Override (User Reset)";
  }
  handleApiData();
}

void handleApiMode() {
  if (server.hasArg("mode")) {
    int m = server.arg("mode").toInt();
    if (m >= 0 && m <= 2) {
      currentMode = (OperatingMode)m;
      activeThresholds = DEFAULT_PROFILES[m];
    }
  }
  handleApiData();
}

void handleApiSetThresholds() {
  if (server.hasArg("gas")) {
    activeThresholds.gasAlarm = server.arg("gas").toInt();
    activeThresholds.gasWarning = (int)(activeThresholds.gasAlarm * 0.65);
  }
  if (server.hasArg("temp")) {
    activeThresholds.tempAlarm = server.arg("temp").toFloat();
    activeThresholds.tempWarning = activeThresholds.tempAlarm - 10.0;
  }
  if (server.hasArg("dist")) {
    activeThresholds.distIntrusion = server.arg("dist").toInt();
  }
  handleApiData();
}

void handleApiReset() {
  relayManualOverride = false;
  relayActive = false;
  digitalWrite(PIN_RELAY, RELAY_INACTIVE_LEVEL);
  relayReason = "Standby Safe (Reset)";
  handleApiData();
}

// ------------------------------------------------------------------------------
// Setup Routine
// ------------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  HAZARDGUARD C3 // EMERGENCY SUPERVISOR FIRMWARE");
  Serial.println("  Shakthikulangara School STEM Lab Project");
  Serial.println("========================================================");

  // Initialize GPIO Pins
  pinMode(PIN_US_TRIG, OUTPUT);
  pinMode(PIN_US_ECHO, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);

  // Set default safe output states
  digitalWrite(PIN_US_TRIG, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_STATUS_LED, LOW);
  digitalWrite(PIN_RELAY, RELAY_INACTIVE_LEVEL);

  // Initialize TM1637 Display
  display.setBrightness(0x0a); // Medium-high brightness
  display.setSegments(SEG_WORD_SAFE);

  // Initialize DHT Sensor
  dht.begin();

  // Populate moving average buffer
  int initialGas = analogRead(PIN_GAS_ANALOG);
  for (int i = 0; i < GAS_MOVING_AVG_SAMPLES; i++) {
    gasHistory[i] = initialGas;
    gasHistTotal += initialGas;
  }
  gasRaw = initialGas;

  // Connect to Wi-Fi (Station Mode) with fallback to Standalone Access Point
  Serial.printf("[WIFI] Connecting to Station SSID: %s ...\n", DEFAULT_WIFI_SSID);
  WiFi.mode(WIFI_AP_STA);
  WiFi.begin(DEFAULT_WIFI_SSID, DEFAULT_WIFI_PASS);

  unsigned long startAttempt = millis();
  bool connected = false;
  while (millis() - startAttempt < WIFI_CONNECT_TIMEOUT) {
    if (WiFi.status() == WL_CONNECTED) {
      connected = true;
      break;
    }
    delay(250);
    Serial.print(".");
  }

  if (connected) {
    Serial.println("\n[WIFI] Connected successfully!");
    Serial.printf("[WIFI] Station IP Address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[WIFI] Station connection timed out. Activating Fallback Access Point...");
  }

  // Always enable Standalone SoftAP for lab bench direct connection
  WiFi.softAP(AP_SSID, AP_PASS, AP_CHANNEL, 0, AP_MAX_CONN);
  Serial.printf("[WIFI] Access Point Active: SSID '%s', Password '%s'\n", AP_SSID, AP_PASS);
  Serial.printf("[WIFI] Access Point IP: %s\n", WiFi.softAPIP().toString().c_str());

  // Setup mDNS Responder (http://hazardguard.local)
  if (MDNS.begin(MDNS_HOSTNAME)) {
    Serial.printf("[MDNS] Responder started: http://%s.local\n", MDNS_HOSTNAME);
    MDNS.addService("http", "tcp", WEB_SERVER_PORT);
  }

  // Configure Web Server Routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/data", HTTP_GET, handleApiData);
  server.on("/api/relay", HTTP_GET, handleApiRelay);
  server.on("/api/mode", HTTP_GET, handleApiMode);
  server.on("/api/setThresholds", HTTP_GET, handleApiSetThresholds);
  server.on("/api/reset", HTTP_GET, handleApiReset);

  server.begin();
  Serial.println("[HTTP] Web Server operational on port 80.");
  Serial.println("========================================================\n");
}

// ------------------------------------------------------------------------------
// Main Execution Loop
// ------------------------------------------------------------------------------
void loop() {
  // 1. Handle HTTP Requests
  server.handleClient();

  unsigned long currentMillis = millis();

  // 2. Read Fast Sensors (Analog Gas & Ultrasonic)
  if (currentMillis - lastSensorPoll >= INTERVAL_SENSOR_READ) {
    lastSensorPoll = currentMillis;
    readGasSensor();
    currentDist = readUltrasonicDistance();
    evaluateHazards();
  }

  // 3. Read Thermal & Humidity Sensor (DHT minimum cycle 2.0s)
  if (currentMillis - lastDhtPoll >= INTERVAL_DHT_READ) {
    lastDhtPoll = currentMillis;
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t)) currentTemp = t;
    if (!isnan(h)) currentHum  = h;
    evaluateHazards();
  }

  // 4. Update Hardware Signaling (Buzzer & Armed LED)
  updateAlertSignaling();

  // 5. Update 7-Segment Multiplexed Display
  updateDisplay();
}
