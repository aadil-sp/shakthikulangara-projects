/*
 * NodeMCU ESP8266 Blink Test (200ms interval)
 * School STEM Project - IoT Test
 */

// NodeMCU ESP8266 onboard LEDs:
// - LED_BUILTIN is GPIO2 (D4, blue LED on ESP-12 module) - Active LOW
// - D0 is GPIO16 (red/blue LED on NodeMCU development board) - Active LOW

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  #if defined(D0)
  pinMode(D0, OUTPUT);
  #endif
}

void loop() {
  // LED ON (Active LOW on NodeMCU)
  digitalWrite(LED_BUILTIN, LOW);
  #if defined(D0)
  digitalWrite(D0, LOW);
  #endif
  delay(200);

  // LED OFF
  digitalWrite(LED_BUILTIN, HIGH);
  #if defined(D0)
  digitalWrite(D0, HIGH);
  #endif
  delay(200);
}
