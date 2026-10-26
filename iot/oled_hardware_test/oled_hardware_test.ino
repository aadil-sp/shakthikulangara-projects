#include <Wire.h>

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  Wire.begin(D2, D1); // SDA=D2, SCL=D1
  Wire.setClockStretchLimit(1500);

  Serial.println(F("\n\n=================================================="));
  Serial.println(F("    LIVE CONTINUOUS OLED I2C SCANNER (500ms)      "));
  Serial.println(F("=================================================="));
  Serial.println(F("Wiggle the jumper wires or change VCC from 3V3 to VIN."));
  Serial.println(F("The moment the screen connects, this will print [FOUND]!\n"));
}

int scanCount = 0;
void loop() {
  scanCount++;
  bool found = false;

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    byte err = Wire.endTransmission();
    if (err == 0) {
      Serial.print(F(" -> [FOUND] Device detected at: 0x"));
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      if (addr == 0x3C || addr == 0x3D) {
        Serial.println(F("  <-- OLED CONNECTED SUCCESSFULLY!"));
        // Blink LED fast
        for (int b = 0; b < 4; b++) {
          digitalWrite(LED_BUILTIN, LOW); delay(50);
          digitalWrite(LED_BUILTIN, HIGH); delay(50);
        }
      } else {
        Serial.println();
      }
      found = true;
    }
  }

  if (!found) {
    if (scanCount % 4 == 0) {
      Serial.println(F("[NO SIGNAL] Searching... Check VCC, GND, SCL(D1), SDA(D2)"));
    }
    digitalWrite(LED_BUILTIN, (scanCount % 2 == 0) ? LOW : HIGH);
  }

  delay(500);
}
