/*
 * =========================================================================
 * ArUcoNav: M5StickC PLUS 2 USB Remote Node & ESP-NOW Gateway
 * =========================================================================
 * Functions:
 *  - High-speed USB Serial link with Python PC application (115200 baud).
 *  - Direct 2.4GHz ESP-NOW radio transceiver communicating with ESP32-S3 car.
 *  - Built-in color LCD display (135x240) rendering live HUD:
 *      * Link status & Packet Counter
 *      * Dual Ultrasonic distance bars & numbers (Left & Right)
 *      * Motor PWM values (L & R)
 *      * Battery & Power status
 * =========================================================================
 */

#include <M5Unified.h>
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

// Struct for Drive Command sent from PC -> Car
typedef struct __attribute__((packed)) {
  int16_t v_left;
  int16_t v_right;
  uint32_t seq;
} DriveCommandMsg;

// Struct for Telemetry sent from Car -> PC
typedef struct __attribute__((packed)) {
  float us_left_cm;
  float us_right_cm;
  float battery_voltage;
  uint8_t status_code; // 0=OK, 1=WARN, 2=CRITICAL
  uint32_t seq;
} TelemetryMsg;

DriveCommandMsg tx_cmd;
TelemetryMsg rx_telem;

// ESP-NOW Broadcast MAC Address (FF:FF:FF:FF:FF:FF)
uint8_t peer_mac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// Telemetry & UI Tracking
unsigned long last_telem_recv_time = 0;
unsigned long last_display_update = 0;
uint32_t tx_pkt_count = 0;
uint32_t rx_pkt_count = 0;

void onDataRecv(const uint8_t *mac_addr, const uint8_t *data, int len) {
  if (len == sizeof(TelemetryMsg)) {
    memcpy(&rx_telem, data, sizeof(TelemetryMsg));
    last_telem_recv_time = millis();
    rx_pkt_count++;

    // Forward telemetry over USB Serial to Python in clean format: "T,us_left,us_right,v_bat\n"
    Serial.printf("T,%.1f,%.1f,%.2f\n", rx_telem.us_left_cm, rx_telem.us_right_cm, rx_telem.battery_voltage);
  }
}

void setupEspNow() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed!");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, peer_mac, 6);
  peerInfo.channel = 1;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  Serial.printf("[ESP-NOW] Gateway Ready! MAC: %s on Channel 1\n", WiFi.macAddress().c_str());
}

void drawDisplay() {
  unsigned long now = millis();
  bool is_linked = (now - last_telem_recv_time < 1000 && last_telem_recv_time > 0);

  M5.Display.startWrite();
  M5.Display.fillScreen(TFT_BLACK);

  // Top Header Bar
  M5.Display.fillRect(0, 0, 240, 24, TFT_NAVY);
  M5.Display.setTextColor(TFT_CYAN, TFT_NAVY);
  M5.Display.setTextSize(1);
  M5.Display.drawString("ARUCONAV GATEWAY", 8, 5);

  if (is_linked) {
    M5.Display.setTextColor(TFT_GREEN, TFT_NAVY);
    M5.Display.drawString("LINK: OK", 175, 5);
  } else {
    M5.Display.setTextColor(TFT_RED, TFT_NAVY);
    M5.Display.drawString("NO CAR", 185, 5);
  }

  // Dual Ultrasonic Sensor Gauges
  // Left Sensor
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Display.drawString("US LEFT:", 10, 32);
  M5.Display.drawString("US RIGHT:", 130, 32);

  // Distances
  char buf[32];
  snprintf(buf, sizeof(buf), "%.1f cm", rx_telem.us_left_cm);
  uint16_t color_l = (rx_telem.us_left_cm < 20) ? TFT_RED : ((rx_telem.us_left_cm < 58) ? TFT_YELLOW : TFT_GREEN);
  M5.Display.setTextColor(color_l, TFT_BLACK);
  M5.Display.drawString(buf, 10, 48);

  snprintf(buf, sizeof(buf), "%.1f cm", rx_telem.us_right_cm);
  uint16_t color_r = (rx_telem.us_right_cm < 20) ? TFT_RED : ((rx_telem.us_right_cm < 58) ? TFT_YELLOW : TFT_GREEN);
  M5.Display.setTextColor(color_r, TFT_BLACK);
  M5.Display.drawString(buf, 130, 48);

  // Ultrasonic Visual Progress Bars
  int bar_w_l = constrain((int)(rx_telem.us_left_cm * 0.9), 4, 100);
  int bar_w_r = constrain((int)(rx_telem.us_right_cm * 0.9), 4, 100);
  M5.Display.drawRect(10, 64, 102, 8, TFT_DARKGREY);
  M5.Display.fillRect(11, 65, bar_w_l, 6, color_l);

  M5.Display.drawRect(130, 64, 102, 8, TFT_DARKGREY);
  M5.Display.fillRect(131, 65, bar_w_r, 6, color_r);

  // Motor Speeds
  M5.Display.setTextColor(TFT_SILVER, TFT_BLACK);
  M5.Display.drawString("MOTORS:", 10, 80);
  snprintf(buf, sizeof(buf), "L: %+4d  |  R: %+4d", tx_cmd.v_left, tx_cmd.v_right);
  M5.Display.setTextColor(TFT_CYAN, TFT_BLACK);
  M5.Display.drawString(buf, 70, 80);

  // Bottom Status Bar
  M5.Display.drawFastHLine(0, 98, 240, TFT_DARKGREY);
  M5.Display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
  snprintf(buf, sizeof(buf), "Bat: %.2fV | TX:%u RX:%u", rx_telem.battery_voltage, tx_pkt_count, rx_pkt_count);
  M5.Display.drawString(buf, 10, 108);

  M5.Display.endWrite();
}

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);

  Serial.begin(115200);
  M5.Display.setRotation(1); // Landscape 240x135
  M5.Display.setBrightness(180);

  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextColor(TFT_CYAN);
  M5.Display.setTextSize(2);
  M5.Display.drawString("ArUcoNav", 60, 40);
  M5.Display.setTextSize(1);
  M5.Display.setTextColor(TFT_WHITE);
  M5.Display.drawString("Initializing ESP-NOW...", 45, 75);

  setupEspNow();
  delay(600);
}

void loop() {
  M5.update();

  // Read drive commands from PC USB Serial: "D,v_left,v_right\n"
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.startsWith("D,")) {
      int c1 = line.indexOf(',');
      int c2 = line.indexOf(',', c1 + 1);
      if (c1 > 0 && c2 > 0) {
        tx_cmd.v_left = line.substring(c1 + 1, c2).toInt();
        tx_cmd.v_right = line.substring(c2 + 1).toInt();
        tx_cmd.seq++;

        // Send packet to RC car via ESP-NOW
        esp_now_send(peer_mac, (uint8_t*)&tx_cmd, sizeof(DriveCommandMsg));
        tx_pkt_count++;
      }
    }
  }

  // Refresh display at 15 Hz
  unsigned long now = millis();
  if (now - last_display_update >= 66) {
    last_display_update = now;
    drawDisplay();
  }
}
