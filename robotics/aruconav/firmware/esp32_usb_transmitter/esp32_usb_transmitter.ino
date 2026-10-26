/*
 * =========================================================================
 * ArUcoNav: ESP32-C3 USB Serial Transmitter Dongle (ESP-NOW Mode)
 * =========================================================================
 * Plugs into PC USB port (USB CDC / USB-UART).
 * Receives serial commands from Python ("D,v_left,v_right\n") and transmits via ESP-NOW.
 * Receives ESP-NOW telemetry from car and forwards over Serial to Python ("T,us_l,us_f,us_r,v_bat\n").
 * Target Board: ESP32-C3 Dev Module (or ESP32-WROOM-32)
 * =========================================================================
 */

#include <esp_now.h>
#include <WiFi.h>

#if defined(CONFIG_IDF_TARGET_ESP32C3)
  #define PIN_LED_STATUS 8  // ESP32-C3 SuperMini onboard LED
#else
  #define PIN_LED_STATUS 2  // ESP32-WROOM-32 onboard LED
#endif

// Struct for drive command from PC
typedef struct __attribute__((packed)) {
  int16_t v_left;
  int16_t v_right;
  uint32_t seq;
} DriveCommandMsg;

// Struct for telemetry back to PC (3 Ultrasonic Sensors: Angle Left, Front, Angle Right)
typedef struct __attribute__((packed)) {
  float us_left_cm;
  float us_front_cm;
  float us_right_cm;
  float battery_voltage;
  uint32_t seq;
} TelemetryMsg;

DriveCommandMsg tx_cmd;
TelemetryMsg rx_telem;

// Target Car MAC Address (Paired directly to the RC Car ESP32)
uint8_t car_mac[] = {0x4C, 0xC3, 0x82, 0xED, 0x3D, 0x58};
uint8_t broadcast_mac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

unsigned long last_tx_blink = 0;
unsigned long last_heartbeat = 0;
unsigned long last_pc_cmd_time = 0;
unsigned long last_telem_recv = 0;

void onDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
  if (len == sizeof(TelemetryMsg)) {
    memcpy(&rx_telem, data, sizeof(TelemetryMsg));
    last_telem_recv = millis();

    // Output formatted string to PC USB Serial: T,us_l,us_f,us_r,v_bat
    Serial.printf("T,%.1f,%.1f,%.1f,%.2f\n", rx_telem.us_left_cm, rx_telem.us_front_cm, rx_telem.us_right_cm, rx_telem.battery_voltage);
    
    // Quick blink on telemetry receive
    digitalWrite(PIN_LED_STATUS, !digitalRead(PIN_LED_STATUS));
    last_tx_blink = millis();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_STATUS, OUTPUT);
  digitalWrite(PIN_LED_STATUS, LOW);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW init failed!");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);

  // Add unicast car peer
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, car_mac, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  // Add broadcast peer as fallback
  memcpy(peerInfo.peer_addr, broadcast_mac, 6);
  esp_now_add_peer(&peerInfo);

  // Ready signal: 3 rapid LED flashes
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_LED_STATUS, HIGH);
    delay(80);
    digitalWrite(PIN_LED_STATUS, LOW);
    delay(80);
  }

  Serial.println("\n[ESP-NOW] ESP32-C3 USB Transmitter Gateway Online");
  Serial.printf("[ESP-NOW] Target Car MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                car_mac[0], car_mac[1], car_mac[2], car_mac[3], car_mac[4], car_mac[5]);
}

void loop() {
  unsigned long now = millis();

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
        last_pc_cmd_time = now;
      }
    }
  }

  // Failsafe: if PC stops sending commands for > 400ms, set motors to 0
  if (now - last_pc_cmd_time > 400) {
    tx_cmd.v_left = 0;
    tx_cmd.v_right = 0;
  }

  // Automatic 20 Hz (50ms) Radio Heartbeat:
  // Keeps the radio link alive instantly even before Python starts!
  if (now - last_heartbeat >= 50) {
    last_heartbeat = now;
    tx_cmd.seq++;
    esp_now_send(car_mac, (uint8_t*)&tx_cmd, sizeof(DriveCommandMsg));
  }

  // Diagnostics if car telemetry hasn't been received in 2.5 seconds
  static unsigned long last_diag = 0;
  if (now - last_telem_recv > 2500 && now - last_diag > 2500) {
    last_diag = now;
    Serial.println("[GATEWAY] Heartbeat active -> Searching for Car on ESP-NOW...");
  }
}
