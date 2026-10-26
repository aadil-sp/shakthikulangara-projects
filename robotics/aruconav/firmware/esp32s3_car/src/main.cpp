/*
 * =========================================================================
 * ArUcoNav: Autonomous RC Car ESP32-S3 Mini Receiver & Motor Controller
 * =========================================================================
 * Wireless Link: Direct 2.4GHz ESP-NOW (Communicates with M5StickC Plus 2)
 *
 * In-Built WS2812 RGB LED Status Feedback:
 *  - Pulsing Blue: Waiting for M5StickC Plus 2 radio commands
 *  - Solid Green:  Paired & Receiving active heartbeat from M5Stick
 *  - Amber/Yellow: Obstacle Warning (< 58 cm)
 *  - Solid Red:    Critical Obstacle (< 20 cm) / Emergency Stop
 *  - Cyan:         Motors actively driving
 *
 * Motor & Sensor Pins:
 *  - Left Ultrasonic:  TRIG 4, ECHO 5
 *  - Right Ultrasonic: TRIG 6, ECHO 7
 *  - Left Motor:       IN1 8, IN2 9, PWM 10
 *  - Right Motor:      IN3 11, IN4 12, PWM 13
 * =========================================================================
 */

#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

// Struct for Drive Command sent from PC/M5Stick -> Car
typedef struct __attribute__((packed)) {
  int16_t v_left;
  int16_t v_right;
  uint32_t seq;
} DriveCommandMsg;

// Struct for Telemetry sent from Car -> M5Stick/PC
typedef struct __attribute__((packed)) {
  float us_left_cm;
  float us_right_cm;
  float battery_voltage;
  uint8_t status_code; // 0=OK, 1=WARN, 2=CRITICAL
  uint32_t seq;
} TelemetryMsg;

DriveCommandMsg rx_cmd;
TelemetryMsg tx_telem;

// Broadcast MAC Address for ESP-NOW
uint8_t peer_mac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// ==================== RGB LED CONFIGURATION ====================
void setRgbColor(uint8_t r, uint8_t g, uint8_t b) {
  #if defined(RGB_BUILTIN)
    neopixelWrite(RGB_BUILTIN, r, g, b);
  #endif
  neopixelWrite(48, r, g, b);
  neopixelWrite(38, r, g, b);
}

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

// Battery ADC
#define PIN_BATTERY_ADC    1

// PWM LEDC Settings
#define PWM_CHANNEL_L      0
#define PWM_CHANNEL_R      1
#define PWM_FREQ_HZ        5000
#define PWM_RESOLUTION     8

// ==================== GLOBAL VARIABLES ====================
unsigned long last_cmd_time = 0;
unsigned long last_telem_time = 0;
const unsigned long WATCHDOG_TIMEOUT_MS = 500; // Stop if no packet in 500ms
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

  #if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcAttach(PIN_MOTOR_L_PWM, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcAttach(PIN_MOTOR_R_PWM, PWM_FREQ_HZ, PWM_RESOLUTION);
  #else
    ledcSetup(PWM_CHANNEL_L, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcSetup(PWM_CHANNEL_R, PWM_FREQ_HZ, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_L_PWM, PWM_CHANNEL_L);
    ledcAttachPin(PIN_MOTOR_R_PWM, PWM_CHANNEL_R);
  #endif

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
  pinMode(PIN_US_LEFT_ECHO, INPUT_PULLDOWN);
  pinMode(PIN_US_RIGHT_TRIG, OUTPUT);
  pinMode(PIN_US_RIGHT_ECHO, INPUT_PULLDOWN);

  digitalWrite(PIN_US_LEFT_TRIG, LOW);
  digitalWrite(PIN_US_RIGHT_TRIG, LOW);
}

float measureDistance(int trigPin, int echoPin) {
  // If pin is disconnected (LOW), return 150cm (clear) immediately
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration_us = pulseIn(echoPin, HIGH, 6000); // 6ms timeout (~100cm max range)
  if (duration_us == 0) {
    return 150.0; // Disconnected or out-of-range: return Clear
  }
  float dist_cm = (duration_us * 0.0343) / 2.0;
  return (dist_cm < 2.0) ? 150.0 : constrain(dist_cm, 2.0, 200.0);
}

// ==================== RGB STATUS UPDATE ====================
void updateRgbStatus() {
  unsigned long now = millis();
  bool is_linked = (now - last_cmd_time < WATCHDOG_TIMEOUT_MS);

  if (!is_linked) {
    // Pulsing Blue when waiting for M5Stick ESP-NOW commands
    uint8_t brightness = (sin(now / 250.0) + 1.0) * 45 + 10;
    setRgbColor(0, 0, brightness);
    return;
  }

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
    // Linked to M5Stick & Path Clear -> Solid Green
    setRgbColor(0, 255, 0);
  }
}

// ==================== ESP-NOW CALLBACKS ====================
void onDataRecv(const uint8_t *mac_addr, const uint8_t *data, int len) {
  if (len == sizeof(DriveCommandMsg)) {
    memcpy(&rx_cmd, data, sizeof(DriveCommandMsg));
    setMotors(rx_cmd.v_left, rx_cmd.v_right);
    last_cmd_time = millis();
  }
}

void setupEspNow() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);

  if (esp_now_init() != ESP_OK) {
    Serial.println("[ESP-NOW] Init failed!");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, peer_mac, 6);
  peerInfo.channel = 1;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  Serial.printf("[ESP-NOW] Car Ready! MAC: %s on Channel 1\n", WiFi.macAddress().c_str());
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n==========================================");
  Serial.println("  ArUcoNav ESP32-S3 Car Starting...       ");
  Serial.println("==========================================");

  setupMotors();
  setupUltrasonics();
  setupEspNow();
}

unsigned long last_debug_print = 0;

void loop() {
  unsigned long now = millis();

  // Watchdog: Stop motors if command timeout
  if (now - last_cmd_time > WATCHDOG_TIMEOUT_MS) {
    setMotors(0, 0);
  }

  // Periodic Telemetry Transmission (20 Hz)
  if (now - last_telem_time >= TELEM_INTERVAL_MS) {
    last_telem_time = now;

    us_left_cm = measureDistance(PIN_US_LEFT_TRIG, PIN_US_LEFT_ECHO);
    us_right_cm = measureDistance(PIN_US_RIGHT_TRIG, PIN_US_RIGHT_ECHO);

    #ifdef PIN_BATTERY_ADC
      int raw_adc = analogRead(PIN_BATTERY_ADC);
      battery_voltage = (raw_adc / 4095.0) * 3.3 * 2.5;
    #endif

    tx_telem.us_left_cm = us_left_cm;
    tx_telem.us_right_cm = us_right_cm;
    tx_telem.battery_voltage = battery_voltage;
    tx_telem.status_code = (us_left_cm < 20 || us_right_cm < 20) ? 2 : ((us_left_cm < 58 || us_right_cm < 58) ? 1 : 0);
    tx_telem.seq++;

    esp_now_send(peer_mac, (uint8_t*)&tx_telem, sizeof(TelemetryMsg));
  }

  // Periodic Serial Debug output (1 Hz)
  if (now - last_debug_print >= 1000) {
    last_debug_print = now;
    bool is_linked = (now - last_cmd_time < WATCHDOG_TIMEOUT_MS);
    Serial.printf("[Car Status] Link: %s | US_L: %.1f cm | US_R: %.1f cm | Seq: %u\n",
                  is_linked ? "ACTIVE" : "WAITING", us_left_cm, us_right_cm, tx_telem.seq);
  }

  // Update In-Built RGB LED
  updateRgbStatus();
}
