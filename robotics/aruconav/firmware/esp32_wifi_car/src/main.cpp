/*
 * =========================================================================
 * ArUcoNav: Autonomous RC Car ESP32-S3 Mini Firmware
 * =========================================================================
 * Access Point (Hotspot) Mode:
 *  - Broadcasts SSID: "ArucoNav_Car_AP"
 *  - Password:         "12345678"
 *  - Car IP Address:   192.168.4.1
 *  - UDP Command Port: 8888 (PC -> Car)
 *  - UDP Telemetry:    8889 (Car -> PC)
 *
 * RGB LED Feedback:
 *  - Pulsing Blue: Hotspot broadcasting, waiting for PC connection
 *  - Solid Green:  PC connected & active heartbeat
 *  - Amber/Yellow: Obstacle Warning (< 58 cm)
 *  - Solid Red:    Critical Obstacle (< 20 cm) or E-Stop
 *  - Cyan:         Motors actively driving
 * =========================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// ==================== RGB LED CONFIGURATION ====================
#if defined(RGB_BUILTIN)
  #define PIN_RGB_LED RGB_BUILTIN
#else
  #define PIN_RGB_LED 48
#endif

void setRgbColor(uint8_t r, uint8_t g, uint8_t b) {
  #if defined(RGB_BUILTIN)
    neopixelWrite(RGB_BUILTIN, r, g, b);
  #elif defined(PIN_RGB_LED)
    neopixelWrite(PIN_RGB_LED, r, g, b);
  #endif
}

// ==================== WIFI ACCESS POINT (HOTSPOT) ====================
const char* AP_SSID = "ArucoNav_Car_AP";
const char* AP_PASS = "12345678";

const unsigned int UDP_CMD_PORT   = 8888; // Listen for PC drive commands
const unsigned int UDP_TELEM_PORT = 8889; // Send telemetry to PC
IPAddress pc_ip(192, 168, 4, 2);          // Default PC IP in AP mode

// ==================== PIN DEFINITIONS (ESP32-S3) ====================
// Dual Ultrasonic Sensors (HC-SR04)
#define PIN_US_LEFT_TRIG   4
#define PIN_US_LEFT_ECHO   5
#define PIN_US_RIGHT_TRIG  6
#define PIN_US_RIGHT_ECHO  7

// Motor Driver (L298N / TB6612FNG)
// Left Motor
#define PIN_MOTOR_L_IN1    8
#define PIN_MOTOR_L_IN2    9
#define PIN_MOTOR_L_PWM    10
// Right Motor
#define PIN_MOTOR_R_IN3    11
#define PIN_MOTOR_R_IN4    12
#define PIN_MOTOR_R_PWM    13

// Battery ADC (Optional)
#define PIN_BATTERY_ADC    1

// PWM LEDC Settings
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
bool is_driving = false;

// ==================== MOTOR CONTROL ====================
void setupMotors() {
  pinMode(PIN_MOTOR_L_IN1, OUTPUT);
  pinMode(PIN_MOTOR_L_IN2, OUTPUT);
  pinMode(PIN_MOTOR_R_IN3, OUTPUT);
  pinMode(PIN_MOTOR_R_IN4, OUTPUT);

  // Setup ESP32-S3 PWM Channels
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcAttach(PIN_MOTOR_L_PWM, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcAttach(PIN_MOTOR_R_PWM, PWM_FREQ_HZ, PWM_RESOLUTION);
  #else
    ledcSetup(PWM_CHANNEL_L, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcSetup(PWM_CHANNEL_R, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_L_PWM, PWM_CHANNEL_L);
    ledcAttachPin(PIN_MOTOR_R_PWM, PWM_CHANNEL_R);
  #endif

  // Initial stop
  digitalWrite(PIN_MOTOR_L_IN1, LOW);
  digitalWrite(PIN_MOTOR_L_IN2, LOW);
  digitalWrite(PIN_MOTOR_R_IN3, LOW);
  digitalWrite(PIN_MOTOR_R_IN4, LOW);
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcWrite(PIN_MOTOR_L_PWM, 0);
    ledcWrite(PIN_MOTOR_R_PWM, 0);
  #else
    ledcWrite(PWM_CHANNEL_L, 0);
    ledcWrite(PWM_CHANNEL_R, 0);
  #endif
}

void setMotors(int v_left, int v_right) {
  // Proximity hard safety stop (< 8 cm)
  if ((us_left_cm < 8.0 || us_right_cm < 8.0) && (v_left > 0 || v_right > 0)) {
    v_left = 0;
    v_right = 0;
  }

  is_driving = (v_left != 0 || v_right != 0);

  int pwm_l = constrain(abs(v_left), 0, 255);
  int pwm_r = constrain(abs(v_right), 0, 255);

  // Left Motor Direction
  if (v_left > 0) {
    digitalWrite(PIN_MOTOR_L_IN1, HIGH);
    digitalWrite(PIN_MOTOR_L_IN2, LOW);
  } else if (v_left < 0) {
    digitalWrite(PIN_MOTOR_L_IN1, LOW);
    digitalWrite(PIN_MOTOR_L_IN2, HIGH);
  } else {
    digitalWrite(PIN_MOTOR_L_IN1, LOW);
    digitalWrite(PIN_MOTOR_L_IN2, LOW);
    pwm_l = 0;
  }

  // Right Motor Direction
  if (v_right > 0) {
    digitalWrite(PIN_MOTOR_R_IN3, HIGH);
    digitalWrite(PIN_MOTOR_R_IN4, LOW);
  } else if (v_right < 0) {
    digitalWrite(PIN_MOTOR_R_IN3, LOW);
    digitalWrite(PIN_MOTOR_R_IN4, HIGH);
  } else {
    digitalWrite(PIN_MOTOR_R_IN3, LOW);
    digitalWrite(PIN_MOTOR_R_IN4, LOW);
    pwm_r = 0;
  }

  // Apply PWM
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcWrite(PIN_MOTOR_L_PWM, pwm_l);
    ledcWrite(PIN_MOTOR_R_PWM, pwm_r);
  #else
    ledcWrite(PWM_CHANNEL_L, pwm_l);
    ledcWrite(PWM_CHANNEL_R, pwm_r);
  #endif
}

// ==================== ULTRASONIC SENSORS ====================
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

  long duration_us = pulseIn(echoPin, HIGH, 15000);
  if (duration_us == 0) {
    return 150.0;
  }
  float dist_cm = (duration_us * 0.0343) / 2.0;
  return constrain(dist_cm, 2.0, 200.0);
}

// ==================== RGB STATUS UPDATE ====================
void updateRgbStatus() {
  unsigned long now = millis();
  bool is_connected_to_pc = (now - last_cmd_time < WATCHDOG_TIMEOUT_MS);

  if (!is_connected_to_pc) {
    // Pulsing Blue when AP Hotspot is broadcasting & waiting for PC
    uint8_t brightness = (sin(now / 250.0) + 1.0) * 45 + 10;
    setRgbColor(0, 0, brightness);
    return;
  }

  // Active PC Connection Established
  if (us_left_cm < 20.0 || us_right_cm < 20.0) {
    // Critical Obstacle -> Red
    setRgbColor(255, 0, 0);
  } else if (us_left_cm < 58.0 || us_right_cm < 58.0) {
    // Obstacle Warning -> Amber / Yellow
    setRgbColor(230, 150, 0);
  } else if (is_driving) {
    // Driving actively -> Bright Cyan
    setRgbColor(0, 220, 255);
  } else {
    // Connected to PC & Path Clear -> Solid Green
    setRgbColor(0, 255, 0);
  }
}

// ==================== UDP NETWORK COMMUNICATION ====================
void handleIncomingPacket() {
  int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    char packetBuffer[256];
    int len = udp.read(packetBuffer, 255);
    if (len > 0) {
      packetBuffer[len] = '\0';
    }

    pc_ip = udp.remoteIP();

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

// ==================== MAIN SETUP & LOOP ====================
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n==========================================");
  Serial.println("  ArUcoNav ESP32-S3 Hotspot (AP) Mode Starting ");
  Serial.println("==========================================");

  setupMotors();
  setupUltrasonics();

  // Start WiFi Hotspot (Access Point)
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  IPAddress myIP = WiFi.softAPIP();

  Serial.println("\n==========================================");
  Serial.printf("  >>> WiFi Hotspot SSID: %s\n", AP_SSID);
  Serial.printf("  >>> Password:          %s\n", AP_PASS);
  Serial.printf("  >>> Car IP Address:    %s\n", myIP.toString().c_str());
  Serial.printf("  >>> Command Port:      %d\n", UDP_CMD_PORT);
  Serial.printf("  >>> Telemetry Port:    %d\n", UDP_TELEM_PORT);
  Serial.println("==========================================\n");

  udp.begin(UDP_CMD_PORT);
  Serial.printf("[UDP] Listening on Port %d\n", UDP_CMD_PORT);
  last_cmd_time = millis();
}

void loop() {
  unsigned long now = millis();

  // 1. Process incoming PC UDP packets
  handleIncomingPacket();

  // 2. Watchdog: Auto-stop motors if heartbeat lost
  if (now - last_cmd_time > WATCHDOG_TIMEOUT_MS) {
    setMotors(0, 0);
  }

  // 3. Periodic Ultrasonic Readings & Telemetry (20 Hz)
  if (now - last_telem_time >= TELEM_INTERVAL_MS) {
    last_telem_time = now;

    us_left_cm = measureDistance(PIN_US_LEFT_TRIG, PIN_US_LEFT_ECHO);
    us_right_cm = measureDistance(PIN_US_RIGHT_TRIG, PIN_US_RIGHT_ECHO);

    #ifdef PIN_BATTERY_ADC
      int raw_adc = analogRead(PIN_BATTERY_ADC);
      battery_voltage = (raw_adc / 4095.0) * 3.3 * 2.5;
    #endif

    sendTelemetry();
  }

  // 4. Update In-built RGB Status LED
  updateRgbStatus();
}
