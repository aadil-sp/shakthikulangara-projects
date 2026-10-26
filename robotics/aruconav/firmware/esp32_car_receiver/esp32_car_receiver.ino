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
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// --- HARDWARE PIN CONFIGURATION (ESP32-WROOM-32) ---
#define PIN_BUZZER         4   // Active Piezo Buzzer / Speaker Pin (Optional)
#define PIN_LED_STATUS     2   // Onboard Blue LED (GPIO 2)

// Ultrasonic Sensors (Angle Left, Front Center, Angle Right)
#define PIN_US_LEFT_TRIG   5
#define PIN_US_LEFT_ECHO   18
#define PIN_US_FRONT_TRIG  22
#define PIN_US_FRONT_ECHO  23
#define PIN_US_RIGHT_TRIG  19
#define PIN_US_RIGHT_ECHO  21

// Motor Driver Pins (From aadil-sp/ESP32-Bluetooth-RC-Car-with-Motor-Sound)
// ONLY 4 PINS: 27, 26, 25, 33 (No ENA / ENB wires - keep L298N jumpers attached to 5V)
#define LM1 27  // Left Motor Forward  (IN1 / LM1)
#define LM2 26  // Left Motor Backward (IN2 / LM2)
#define RM1 25  // Right Motor Forward (IN3 / RM1)
#define RM2 33  // Right Motor Backward (IN4 / RM2)

// --- DATA STRUCTURES (Must match Transmitter) ---
typedef struct __attribute__((packed)) {
  int16_t v_left;
  int16_t v_right;
  uint32_t seq;
} DriveCommandMsg;

typedef struct __attribute__((packed)) {
  float us_left_cm;
  float us_front_cm;
  float us_right_cm;
  float battery_voltage;
  uint32_t seq;
} TelemetryMsg;

DriveCommandMsg rx_cmd;
TelemetryMsg tx_telem;

// Target Host Transmitter MAC (ESP32-C3 Dongle)
uint8_t transmitter_mac[] = {0x14, 0x63, 0x93, 0xC9, 0x00, 0x8C};
uint8_t broadcast_mac[]   = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// --- TIMERS & STATE ---
unsigned long last_cmd_time = 0;
unsigned long last_telem_time = 0;
unsigned long last_serial_print = 0;
bool is_connected = false;

// --- SOUND & MOTOR CONTROL HELPER FUNCTIONS ---
void soundChirp(int freq, int duration_ms) {
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    tone(PIN_BUZZER, freq, duration_ms);
  #else
    tone(PIN_BUZZER, freq, duration_ms);
  #endif
}

// --- MOTOR CONTROL (Direct 4-wire: LM1=27, LM2=26, RM1=25, RM2=33) ---
// No ENA / ENB: Keep L298N jumpers attached to 5V
void writeMotorPWM(int pin, int channel, int val) {
  val = constrain(val, 0, 255);
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcWrite(pin, val);
  #else
    ledcWrite(channel, val);
  #endif
}

void setupMotorPWM() {
  pinMode(LM1, OUTPUT);
  pinMode(LM2, OUTPUT);
  pinMode(RM1, OUTPUT);
  pinMode(RM2, OUTPUT);

  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    ledcAttach(LM1, 5000, 8);
    ledcAttach(LM2, 5000, 8);
    ledcAttach(RM1, 5000, 8);
    ledcAttach(RM2, 5000, 8);
  #else
    ledcSetup(0, 5000, 8);
    ledcAttachPin(LM1, 0);
    ledcSetup(1, 5000, 8);
    ledcAttachPin(LM2, 1);
    ledcSetup(2, 5000, 8);
    ledcAttachPin(RM1, 2);
    ledcSetup(3, 5000, 8);
    ledcAttachPin(RM2, 3);
  #endif
}

void setMotors(int v_l, int v_r) {
  // Left Motor (LM1 = 27, LM2 = 26)
  if (v_l > 0) {
    writeMotorPWM(LM1, 0, min(255, v_l));
    writeMotorPWM(LM2, 1, 0);
  } else if (v_l < 0) {
    writeMotorPWM(LM1, 0, 0);
    writeMotorPWM(LM2, 1, min(255, -v_l));
  } else {
    writeMotorPWM(LM1, 0, 0);
    writeMotorPWM(LM2, 1, 0);
  }

  // Right Motor (RM1 = 25, RM2 = 33)
  if (v_r > 0) {
    writeMotorPWM(RM1, 2, min(255, v_r));
    writeMotorPWM(RM2, 3, 0);
  } else if (v_r < 0) {
    writeMotorPWM(RM1, 2, 0);
    writeMotorPWM(RM2, 3, min(255, -v_r));
  } else {
    writeMotorPWM(RM1, 2, 0);
    writeMotorPWM(RM2, 3, 0);
  }
}

// --- MOTOR SOUND SYSTEM (From aadil-sp/ESP32-Bluetooth-RC-Car-with-Motor-Sound) ---
void playMotorTone(int freq, int durationMs) {
  int period = 1000000L / freq;
  unsigned long cycles = (unsigned long)(durationMs * 1000L) / period;
  for (unsigned long i = 0; i < cycles; i++) {
    writeMotorPWM(LM1, 0, 255); writeMotorPWM(LM2, 1, 0);
    writeMotorPWM(RM1, 2, 255); writeMotorPWM(RM2, 3, 0);
    delayMicroseconds(period / 2);
    writeMotorPWM(LM1, 0, 0); writeMotorPWM(LM2, 1, 255);
    writeMotorPWM(RM1, 2, 0); writeMotorPWM(RM2, 3, 255);
    delayMicroseconds(period / 2);
  }
  setMotors(0, 0);
}

void startupSound() {
  int notes[] = {400, 600, 800, 1000, 1200};
  int dur[] = {100, 100, 120, 150, 200};
  for (int i = 0; i < 5; i++) { playMotorTone(notes[i], dur[i]); delay(30); }
}

void connectSound() {
  int notes[] = {800, 1000, 1200};
  int dur[] = {100, 100, 200};
  for (int i = 0; i < 3; i++) { playMotorTone(notes[i], dur[i]); delay(30); }
}

void disconnectSound() {
  int notes[] = {1200, 1000, 800};
  int dur[] = {100, 100, 200};
  for (int i = 0; i < 3; i++) { playMotorTone(notes[i], dur[i]); delay(30); }
}

void playConnectionAlarm() {
  connectSound();
  soundChirp(2600, 120);
  digitalWrite(PIN_LED_STATUS, HIGH);
}

void playLostConnectionAlarm() {
  disconnectSound();
  soundChirp(600, 120);
}

void playObstacleAlarm() {
  soundChirp(3200, 50);
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

    // Dynamically register sender peer if new
    if (!esp_now_is_peer_exist(info->src_addr)) {
      esp_now_peer_info_t p = {};
      memcpy(p.peer_addr, info->src_addr, 6);
      p.channel = 0;
      p.encrypt = false;
      esp_now_add_peer(&p);
      memcpy(transmitter_mac, info->src_addr, 6);
    }

    // Check if this is the FIRST packet establishing connection
    if (!is_connected) {
      is_connected = true;
      Serial.println("[ESP-NOW] Host Link Established! Playing chime.");
      playConnectionAlarm();
    }

    // Flash blue LED in real-time sync with incoming radio commands (20Hz heartbeat)
    digitalWrite(PIN_LED_STATUS, !digitalRead(PIN_LED_STATUS));

    setMotors(rx_cmd.v_left, rx_cmd.v_right);
    last_cmd_time = millis();
  }
}

void setup() {
  // Disable brownout detector to prevent resets under motor surge
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  Serial.println("\n--- ArUcoNav ESP32-WROOM-32 Car Booting ---");

  pinMode(PIN_LED_STATUS, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_LED_STATUS, HIGH);
  digitalWrite(PIN_BUZZER, LOW);

  setupMotorPWM();
  setMotors(0, 0);

  // Motor startup melody (from git repo)
  startupSound();

  pinMode(PIN_US_LEFT_TRIG, OUTPUT);
  pinMode(PIN_US_LEFT_ECHO, INPUT);
  pinMode(PIN_US_FRONT_TRIG, OUTPUT);
  pinMode(PIN_US_FRONT_ECHO, INPUT);
  pinMode(PIN_US_RIGHT_TRIG, OUTPUT);
  pinMode(PIN_US_RIGHT_ECHO, INPUT);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW init failed!");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);

  // Register unicast C3 host peer
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, transmitter_mac, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  // Register broadcast peer as fallback
  memcpy(peerInfo.peer_addr, broadcast_mac, 6);
  esp_now_add_peer(&peerInfo);

  Serial.println("[ESP-NOW] Car Receiver Online. Waiting for Transmitter link...");
}

void loop() {
  unsigned long now = millis();

  // Watchdog & Connection Lost Logic (800ms timeout)
  if (now - last_cmd_time > 800) {
    setMotors(0, 0); // Failsafe emergency stop

    if (is_connected) {
      is_connected = false;
      Serial.println("[ESP-NOW] Connection Lost! Playing disconnect tone.");
      playLostConnectionAlarm();
    }

    // When DISCONNECTED: slow visible blink (500ms ON / 500ms OFF) so user clearly SEES it is alive
    if ((now / 500) % 2 == 0) {
      digitalWrite(PIN_LED_STATUS, HIGH);
    } else {
      digitalWrite(PIN_LED_STATUS, LOW);
    }
  }

  // Periodic Telemetry Transmission (20 Hz = 50ms)
  if (now - last_telem_time > 50) {
    last_telem_time = now;
    tx_telem.us_left_cm = measureDistance(PIN_US_LEFT_TRIG, PIN_US_LEFT_ECHO);
    tx_telem.us_front_cm = measureDistance(PIN_US_FRONT_TRIG, PIN_US_FRONT_ECHO);
    tx_telem.us_right_cm = measureDistance(PIN_US_RIGHT_TRIG, PIN_US_RIGHT_ECHO);
    tx_telem.battery_voltage = 7.4; // 2S nominal
    tx_telem.seq++;
    
    // Proximity alarm if obstacle is dangerously close while in motion
    if (is_connected && (tx_telem.us_left_cm < 18.0 || tx_telem.us_front_cm < 20.0 || tx_telem.us_right_cm < 18.0)) {
      if (rx_cmd.v_left > 0 || rx_cmd.v_right > 0) {
        playObstacleAlarm();
      }
    }

    esp_now_send(transmitter_mac, (uint8_t*)&tx_telem, sizeof(TelemetryMsg));
  }

  // Live Serial Monitor Diagnostics every 1 second
  if (now - last_serial_print > 1000) {
    last_serial_print = now;
    Serial.printf("[CAR %s] Sonar -> Left: %.1f cm | Front: %.1f cm | Right: %.1f cm | Bat: %.2fV\n",
                  is_connected ? "LINK_OK" : "WAITING",
                  tx_telem.us_left_cm, tx_telem.us_front_cm, tx_telem.us_right_cm, tx_telem.battery_voltage);
  }
}
