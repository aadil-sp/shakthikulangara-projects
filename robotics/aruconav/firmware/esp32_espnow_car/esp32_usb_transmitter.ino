/*
 * =========================================================================
 * ArUcoNav: ESP32-WROOM-32 USB Serial Transmitter Dongle (ESP-NOW Mode)
 * =========================================================================
 * Plugs into PC USB port (USB-UART CP2102 / CH340).
 * Receives serial commands from Python ("D,v_left,v_right\n") and transmits via ESP-NOW.
 * Receives ESP-NOW telemetry from car and forwards over Serial to Python ("T,us_l,us_r,v_bat\n").
 * Target Board: ESP32-WROOM-32 (ESP32 Dev Module)
 * =========================================================================
 */

#include <esp_now.h>
#include <WiFi.h>

#define PIN_LED_STATUS 2  // Onboard blue LED on ESP32-WROOM-32

// Struct for drive command from PC
typedef struct __attribute__((packed)) {
  int16_t v_left;
  int16_t v_right;
  uint32_t seq;
} DriveCommandMsg;

// Struct for telemetry back to PC
typedef struct __attribute__((packed)) {
  float us_left_cm;
  float us_right_cm;
  float battery_voltage;
  uint32_t seq;
} TelemetryMsg;

DriveCommandMsg tx_cmd;
TelemetryMsg rx_telem;

// Target Car MAC Address (Paired directly to the RC Car ESP32)
uint8_t car_mac[] = {0x4C, 0xC3, 0x82, 0xED, 0x3D, 0x58};

unsigned long last_tx_blink = 0;

void onDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
  if (len == sizeof(TelemetryMsg)) {
    memcpy(&rx_telem, data, sizeof(TelemetryMsg));
    // Output formatted string to PC USB Serial
    Serial.printf("T,%.1f,%.1f,%.2f\n", rx_telem.us_left_cm, rx_telem.us_right_cm, rx_telem.battery_voltage);
    
    // Quick blink on telemetry receive
    digitalWrite(PIN_LED_STATUS, HIGH);
    last_tx_blink = millis();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_STATUS, OUTPUT);
  digitalWrite(PIN_LED_STATUS, LOW);

  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW init failed!");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, car_mac, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("WARN: Failed to add broadcast peer");
  }

  // Ready signal: 3 rapid LED flashes
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_LED_STATUS, HIGH);
    delay(80);
    digitalWrite(PIN_LED_STATUS, LOW);
    delay(80);
  }

  Serial.println("[ESP-NOW] ESP32-WROOM-32 USB Transmitter Gateway Online");
}

void loop() {
  // Read command line from PC Serial: "D,180,180\n"
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("D,")) {
      int comma1 = line.indexOf(',');
      int comma2 = line.indexOf(',', comma1 + 1);
      if (comma1 > 0 && comma2 > 0) {
        tx_cmd.v_left = line.substring(comma1 + 1, comma2).toInt();
        tx_cmd.v_right = line.substring(comma2 + 1).toInt();
        tx_cmd.seq++;
        esp_now_send(car_mac, (uint8_t*)&tx_cmd, sizeof(DriveCommandMsg));
        
        digitalWrite(PIN_LED_STATUS, HIGH);
        last_tx_blink = millis();
      }
    }
  }

  // Turn off LED after brief activity indicator
  if (millis() - last_tx_blink > 40) {
    digitalWrite(PIN_LED_STATUS, LOW);
  }
}
