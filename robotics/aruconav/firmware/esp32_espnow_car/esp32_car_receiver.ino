/*
 * =========================================================================
 * ArUcoNav: ESP32-WROOM-32 Car Receiver & Navigation Firmware (ESP-NOW Mode)
 * =========================================================================
 * Board: ESP32-WROOM-32 (ESP32 Dev Module)
 * Target: Indoor Autonomous RC Robot Navigation
 * Features:
 *   - Direct 2.4GHz ESP-NOW Low-Latency Radio
 *   - Dual DC Motor Differential Drive (L298N / TB6612FNG)
 *   - Dual HC-SR04 Ultrasonic Radar Telemetry
 *   - Integrated Connecting & Connection-Lost Audio Alarm System
 * =========================================================================
 */

#include <esp_now.h>
#include <WiFi.h>

// --- HARDWARE PIN CONFIGURATION (ESP32-WROOM-32) ---
#define PIN_BUZZER         4   // Active Piezo Buzzer / Speaker Pin
#define PIN_LED_STATUS     2   // Onboard Blue LED (GPIO 2)

// Ultrasonic Sensors
#define PIN_US_LEFT_TRIG   5
#define PIN_US_LEFT_ECHO   18
#define PIN_US_RIGHT_TRIG  19
#define PIN_US_RIGHT_ECHO  21

// L298N Motor Driver Pins
#define PIN_MOTOR_L_IN1    25
#define PIN_MOTOR_L_IN2    26
#define PIN_MOTOR_L_PWM    32  // Left Enable / PWM
#define PIN_MOTOR_R_IN3    27
#define PIN_MOTOR_R_IN4    14
#define PIN_MOTOR_R_PWM    33  // Right Enable / PWM

// --- DATA STRUCTURES (Must match Transmitter) ---
typedef struct __attribute__((packed)) {
  int16_t v_left;
  int16_t v_right;
  uint32_t seq;
} DriveCommandMsg;

typedef struct __attribute__((packed)) {
  float us_left_cm;
  float us_right_cm;
  float battery_voltage;
  uint32_t seq;
} TelemetryMsg;

DriveCommandMsg rx_cmd;
TelemetryMsg tx_telem;

// Transmitter MAC Address (Set after pairing or broadcast FF:FF:FF:FF:FF:FF)
uint8_t transmitter_mac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// --- TIMERS & STATE ---
unsigned long last_cmd_time = 0;
unsigned long last_telem_time = 0;
unsigned long last_lost_alarm_time = 0;
bool is_connected = false;

// --- SOUND & ALARM HELPER FUNCTIONS ---
void soundChirp(int freq, int duration_ms) {
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    tone(PIN_BUZZER, freq, duration_ms);
  #else
    // Fallback for older ESP32 core without global tone()
    tone(PIN_BUZZER, freq, duration_ms);
  #endif
}

void playConnectionAlarm() {
  // Dual-tone high pitch ascending chime indicating successful connection
  soundChirp(2000, 70);
  delay(90);
  soundChirp(2600, 120);
  digitalWrite(PIN_LED_STATUS, HIGH);
}

void playLostConnectionAlarm() {
  // Low pitch dual warning beep: Beep-Beep indicating lost link / out-of-range
  soundChirp(800, 100);
  delay(120);
  soundChirp(600, 140);
}

void playObstacleAlarm() {
  // Urgent short beep for collision warning (< 20cm)
  soundChirp(3200, 50);
}

// --- MOTOR CONTROL ---
void setupMotorPWM() {
  pinMode(PIN_MOTOR_L_IN1, OUTPUT);
  pinMode(PIN_MOTOR_L_IN2, OUTPUT);
  pinMode(PIN_MOTOR_R_IN3, OUTPUT);
  pinMode(PIN_MOTOR_R_IN4, OUTPUT);

  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcAttach(PIN_MOTOR_L_PWM, 5000, 8);
    ledcAttach(PIN_MOTOR_R_PWM, 5000, 8);
  #else
    ledcSetup(0, 5000, 8);
    ledcAttachPin(PIN_MOTOR_L_PWM, 0);
    ledcSetup(1, 5000, 8);
    ledcAttachPin(PIN_MOTOR_R_PWM, 1);
  #endif
}

void writeMotorPWM(int pin, int channel, int val) {
  val = constrain(val, 0, 255);
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcWrite(pin, val);
  #else
    ledcWrite(channel, val);
  #endif
}

void setMotors(int v_l, int v_r) {
  // Left Motor
  if (v_l > 0) {
    digitalWrite(PIN_MOTOR_L_IN1, HIGH);
    digitalWrite(PIN_MOTOR_L_IN2, LOW);
    writeMotorPWM(PIN_MOTOR_L_PWM, 0, min(255, v_l));
  } else if (v_l < 0) {
    digitalWrite(PIN_MOTOR_L_IN1, LOW);
    digitalWrite(PIN_MOTOR_L_IN2, HIGH);
    writeMotorPWM(PIN_MOTOR_L_PWM, 0, min(255, -v_l));
  } else {
    digitalWrite(PIN_MOTOR_L_IN1, LOW);
    digitalWrite(PIN_MOTOR_L_IN2, LOW);
    writeMotorPWM(PIN_MOTOR_L_PWM, 0, 0);
  }

  // Right Motor
  if (v_r > 0) {
    digitalWrite(PIN_MOTOR_R_IN3, HIGH);
    digitalWrite(PIN_MOTOR_R_IN4, LOW);
    writeMotorPWM(PIN_MOTOR_R_PWM, 1, min(255, v_r));
  } else if (v_r < 0) {
    digitalWrite(PIN_MOTOR_R_IN3, LOW);
    digitalWrite(PIN_MOTOR_R_IN4, HIGH);
    writeMotorPWM(PIN_MOTOR_R_PWM, 1, min(255, -v_r));
  } else {
    digitalWrite(PIN_MOTOR_R_IN3, LOW);
    digitalWrite(PIN_MOTOR_R_IN4, LOW);
    writeMotorPWM(PIN_MOTOR_R_PWM, 1, 0);
  }
}

// --- ULTRASONIC SENSOR TELEMETRY ---
float measureDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long dur = pulseIn(echoPin, HIGH, 15000); // 15ms timeout (~2.5m)
  if (dur == 0) return 200.0;
  return constrain((dur * 0.0343) / 2.0, 2.0, 200.0);
}

// --- ESP-NOW PACKET RECEIVE CALLBACK ---
void onDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
  if (len == sizeof(DriveCommandMsg)) {
    memcpy(&rx_cmd, data, sizeof(DriveCommandMsg));

    // Check if this is the FIRST packet establishing connection
    if (!is_connected) {
      is_connected = true;
      Serial.println("[ESP-NOW] Transmitter Connection Established! Playing chime.");
      playConnectionAlarm();
    }

    setMotors(rx_cmd.v_left, rx_cmd.v_right);
    last_cmd_time = millis();
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- ArUcoNav ESP32-WROOM-32 Car Booting ---");

  pinMode(PIN_LED_STATUS, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_LED_STATUS, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  // Power on boot chirp
  soundChirp(1500, 100);

  setupMotorPWM();
  setMotors(0, 0);

  pinMode(PIN_US_LEFT_TRIG, OUTPUT);
  pinMode(PIN_US_LEFT_ECHO, INPUT);
  pinMode(PIN_US_RIGHT_TRIG, OUTPUT);
  pinMode(PIN_US_RIGHT_ECHO, INPUT);

  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW init failed!");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);

  // Register broadcast peer for telemetry output
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, transmitter_mac, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  Serial.println("[ESP-NOW] Car Receiver Online. Waiting for Transmitter link...");
}

void loop() {
  unsigned long now = millis();

  // Watchdog & Connection Lost Logic
  if (now - last_cmd_time > 800) {
    setMotors(0, 0); // Failsafe emergency stop

    if (is_connected) {
      is_connected = false;
      Serial.println("[ESP-NOW] Connection Lost! Sounding alarm.");
    }

    // Sound periodic warning alarm every 1.5 seconds if disconnected
    if (now - last_lost_alarm_time > 1500) {
      last_lost_alarm_time = now;
      digitalWrite(PIN_LED_STATUS, !digitalRead(PIN_LED_STATUS)); // Blink LED
      playLostConnectionAlarm();
    }
  } else {
    // Solid LED when connected
    digitalWrite(PIN_LED_STATUS, HIGH);
  }

  // Periodic Telemetry Transmission (20 Hz = 50ms)
  if (now - last_telem_time > 50) {
    last_telem_time = now;
    tx_telem.us_left_cm = measureDistance(PIN_US_LEFT_TRIG, PIN_US_LEFT_ECHO);
    tx_telem.us_right_cm = measureDistance(PIN_US_RIGHT_TRIG, PIN_US_RIGHT_ECHO);
    tx_telem.battery_voltage = 7.4; // 2S nominal
    tx_telem.seq++;
    
    // Proximity alarm if obstacle is dangerously close while in motion
    if (is_connected && (tx_telem.us_left_cm < 18.0 || tx_telem.us_right_cm < 18.0)) {
      if (rx_cmd.v_left > 0 || rx_cmd.v_right > 0) {
        playObstacleAlarm();
      }
    }

    esp_now_send(transmitter_mac, (uint8_t*)&tx_telem, sizeof(TelemetryMsg));
  }
}
