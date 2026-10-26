/*
 * =========================================================================
 * ArUcoNav: Autonomous RC Car ESP32 WiFi Firmware
 * =========================================================================
 * Features:
 *  - Dual HC-SR04 Ultrasonic Distance Sensors (Left & Right)
 *  - Dual H-Bridge Motor Control (L298N / TB6612FNG) via ESP32 PWM (LEDC)
 *  - UDP Low-Latency Command & Telemetry Packet Exchange
 *  - Heartbeat Failsafe Watchdog (Auto-stops motors on communication loss)
 *  - Hard Emergency Stop on ultra-close physical proximity (< 8 cm)
 * =========================================================================
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
// Set to 1 to create an Access Point (Default), or 0 to join existing WiFi router
#define USE_ACCESS_POINT 1

const char* AP_SSID = "ArucoNav_Car_AP";
const char* AP_PASS = "12345678";

const char* STA_SSID = "Your_WiFi_Name";
const char* STA_PASS = "Your_WiFi_Password";

const unsigned int UDP_CMD_PORT   = 8888; // Listen for commands from PC
const unsigned int UDP_TELEM_PORT = 8889; // Send telemetry to PC
IPAddress pc_ip(192, 168, 4, 2);          // Default PC IP on AP mode (or broadcast)

// ==================== PIN DEFINITIONS ====================
// Dual Ultrasonic Sensors (HC-SR04)
#define PIN_US_LEFT_TRIG   5
#define PIN_US_LEFT_ECHO   18
#define PIN_US_RIGHT_TRIG  19
#define PIN_US_RIGHT_ECHO  21

// Motor Driver (L298N / TB6612FNG)
// Left Motor
#define PIN_MOTOR_L_IN1    25
#define PIN_MOTOR_L_IN2    26
#define PIN_MOTOR_L_PWM    32
// Right Motor
#define PIN_MOTOR_R_IN3    27
#define PIN_MOTOR_R_IN4    14
#define PIN_MOTOR_R_PWM    33

// Battery Voltage ADC Divider (Optional)
#define PIN_BATTERY_ADC    34

// PWM LEDC Channels
#define PWM_CHANNEL_L      0
#define PWM_CHANNEL_R      1
#define PWM_FREQ_HZ        5000
#define PWM_RESOLUTION     8 // 8-bit = 0 to 255

// ==================== GLOBAL VARIABLES ====================
WiFiUDP udp;
unsigned long last_cmd_time = 0;
unsigned long last_telem_time = 0;
const unsigned long WATCHDOG_TIMEOUT_MS = 600; // Stop if no packet in 600ms
const unsigned long TELEM_INTERVAL_MS   = 50;  // 20 Hz Telemetry

float us_left_cm = 100.0;
float us_right_cm = 100.0;
float battery_voltage = 7.4;

// ==================== FUNCTION PROTOTYPES ====================
void setupMotors();
void setupUltrasonics();
void setMotors(int v_left, int v_right);
float measureDistance(int trigPin, int echoPin);
void handleIncomingPacket();
void sendTelemetry();

void setup() {
  Serial.begin(115200);
  Serial.println("\n[ArUcoNav] Starting ESP32 WiFi Firmware...");

  setupMotors();
  setupUltrasonics();

  // Initialize WiFi
  #if USE_ACCESS_POINT
    Serial.println("[WiFi] Starting Access Point: " + String(AP_SSID));
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASS);
    Serial.print("[WiFi] AP IP Address: ");
    Serial.println(WiFi.softAPIP());
  #else
    Serial.println("[WiFi] Connecting to: " + String(STA_SSID));
    WiFi.mode(WIFI_STA);
    WiFi.begin(STA_SSID, STA_PASS);
    while (WiFi.status() != WL_CONNECTED) {
      delay(250);
      Serial.print(".");
    }
    Serial.println("\n[WiFi] Connected! IP: " + WiFi.localIP().toString());
  #endif

  // Start UDP
  udp.begin(UDP_CMD_PORT);
  Serial.printf("[UDP] Listening on Port %d\n", UDP_CMD_PORT);
  last_cmd_time = millis();
}

void loop() {
  unsigned long now = millis();

  // 1. Process Incoming UDP Control Packets
  handleIncomingPacket();

  // 2. Failsafe Watchdog: Auto-stop motors if connection lost
  if (now - last_cmd_time > WATCHDOG_TIMEOUT_MS) {
    setMotors(0, 0);
  }

  // 3. Periodic Sensor Readings & Telemetry Stream (20 Hz)
  if (now - last_telem_time >= TELEM_INTERVAL_MS) {
    last_telem_time = now;

    // Read Left & Right Sensors
    us_left_cm = measureDistance(PIN_US_LEFT_TRIG, PIN_US_LEFT_ECHO);
    us_right_cm = measureDistance(PIN_US_RIGHT_TRIG, PIN_US_RIGHT_ECHO);

    // Optional Battery Read (voltage divider ~ 2:1)
    #ifdef PIN_BATTERY_ADC
      int raw_adc = analogRead(PIN_BATTERY_ADC);
      battery_voltage = (raw_adc / 4095.0) * 3.3 * 2.5; // calibrate with multimeter
    #endif

    // Send UDP Telemetry back to PC
    sendTelemetry();
  }
}

// ==================== MOTOR CONTROL ====================
void setupMotors() {
  pinMode(PIN_MOTOR_L_IN1, OUTPUT);
  pinMode(PIN_MOTOR_L_IN2, OUTPUT);
  pinMode(PIN_MOTOR_R_IN3, OUTPUT);
  pinMode(PIN_MOTOR_R_IN4, OUTPUT);

  // Setup ESP32 PWM
  ledcAttach(PIN_MOTOR_L_PWM, PWM_FREQ_HZ, PWM_RESOLUTION);
  ledcAttach(PIN_MOTOR_R_PWM, PWM_FREQ_HZ, PWM_RESOLUTION);

  setMotors(0, 0);
}

void setMotors(int v_left, int v_right) {
  // Hard physical proximity safety stop (< 7 cm)
  if ((us_left_cm < 7.0 || us_right_cm < 7.0) && (v_left > 0 || v_right > 0)) {
    v_left = 0;
    v_right = 0;
  }

  // Left Motor
  if (v_left > 0) {
    digitalWrite(PIN_MOTOR_L_IN1, HIGH);
    digitalWrite(PIN_MOTOR_L_IN2, LOW);
    ledcWrite(PIN_MOTOR_L_PWM, min(255, v_left));
  } else if (v_left < 0) {
    digitalWrite(PIN_MOTOR_L_IN1, LOW);
    digitalWrite(PIN_MOTOR_L_IN2, HIGH);
    ledcWrite(PIN_MOTOR_L_PWM, min(255, -v_left));
  } else {
    digitalWrite(PIN_MOTOR_L_IN1, LOW);
    digitalWrite(PIN_MOTOR_L_IN2, LOW);
    ledcWrite(PIN_MOTOR_L_PWM, 0);
  }

  // Right Motor
  if (v_right > 0) {
    digitalWrite(PIN_MOTOR_R_IN3, HIGH);
    digitalWrite(PIN_MOTOR_R_IN4, LOW);
    ledcWrite(PIN_MOTOR_R_PWM, min(255, v_right));
  } else if (v_right < 0) {
    digitalWrite(PIN_MOTOR_R_IN3, LOW);
    digitalWrite(PIN_MOTOR_R_IN4, HIGH);
    ledcWrite(PIN_MOTOR_R_PWM, min(255, -v_right));
  } else {
    digitalWrite(PIN_MOTOR_R_IN3, LOW);
    digitalWrite(PIN_MOTOR_R_IN4, LOW);
    ledcWrite(PIN_MOTOR_R_PWM, 0);
  }
}

// ==================== ULTRASONIC SENSOR ====================
void setupUltrasonics() {
  pinMode(PIN_US_LEFT_TRIG, OUTPUT);
  pinMode(PIN_US_LEFT_ECHO, INPUT);
  pinMode(PIN_US_RIGHT_TRIG, OUTPUT);
  pinMode(PIN_US_RIGHT_ECHO, INPUT);

  digitalWrite(PIN_US_LEFT_TRIG, LOW);
  digitalWrite(PIN_US_RIGHT_TRIG, LOW);
}

float measureDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Measure echo pulse width (timeout ~ 15ms for max ~2.5m)
  long duration_us = pulseIn(echoPin, HIGH, 15000);
  if (duration_us == 0) {
    return 150.0; // Clear / Max distance
  }
  float dist_cm = (duration_us * 0.0343) / 2.0;
  return constrain(dist_cm, 2.0, 200.0);
}

// ==================== NETWORK UDP ====================
void handleIncomingPacket() {
  int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    char packetBuffer[256];
    int len = udp.read(packetBuffer, 255);
    if (len > 0) {
      packetBuffer[len] = '\0';
    }

    // Save PC sender IP
    pc_ip = udp.remoteIP();

    // Parse JSON command: {"cmd":"DRIVE","v_l":180,"v_r":180}
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, packetBuffer);
    if (!error) {
      int v_l = doc["v_l"] | 0;
      int v_r = doc["v_r"] | 0;
      setMotors(v_l, v_r);
      last_cmd_time = millis();
    }
  }
}

void sendTelemetry() {
  StaticJsonDocument<200> doc;
  doc["us_l"] = round(us_left_cm * 10.0) / 10.0;
  doc["us_r"] = round(us_right_cm * 10.0) / 10.0;
  doc["v_bat"] = round(battery_voltage * 100.0) / 100.0;
  doc["status"] = "OK";
  doc["rssi"] = WiFi.RSSI();

  char buffer[200];
  serializeJson(doc, buffer);

  udp.beginPacket(pc_ip, UDP_TELEM_PORT);
  udp.write((const uint8_t*)buffer, strlen(buffer));
  udp.endPacket();
}
