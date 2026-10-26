#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <TM1637Display.h>

// --- OLED Display Configuration ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1 // Reset pin # (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C // 0x3C is standard for 128x64/128x32 OLEDs

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- TM1637 4-Digit 7-Segment Display Configuration ---
#define CLK_PIN D5  // GPIO14
#define DIO_PIN D6  // GPIO12

TM1637Display tm1637(CLK_PIN, DIO_PIN);

unsigned long previousMillis = 0;
int counter = 0;
bool colonState = false;

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- NodeMCU Display Initializing ---");

  // Initialize TM1637
  tm1637.setBrightness(0x0f); // Maximum brightness
  tm1637.showNumberDec(counter, true); // Show 0000

  // Initialize I2C for OLED (D2 = SDA, D1 = SCL)
  Wire.begin(D2, D1);

  // Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed (try 0x3D if 0x3C doesn't work)"));
  } else {
    Serial.println(F("SSD1306 OLED initialized successfully!"));
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(15, 20);
    display.println("SHAKTHIKULANGARA");
    display.setCursor(30, 36);
    display.println("IoT PROJECT");
    display.display();
    delay(1500);
  }
}

void loop() {
  unsigned long currentMillis = millis();

  // Update every 1000 ms (1 second)
  if (currentMillis - previousMillis >= 1000) {
    previousMillis = currentMillis;
    counter++;
    colonState = !colonState;

    // --- Update TM1637 ---
    // Display as MM:SS or running count
    int minutes = (counter / 60) % 100;
    int seconds = counter % 60;
    int displayTime = (minutes * 100) + seconds;
    
    // Toggle colon (0x80 on the second digit)
    uint8_t colonMask = colonState ? 0b01000000 : 0;
    tm1637.showNumberDecEx(displayTime, colonMask, true);

    // --- Update OLED ---
    display.clearDisplay();

    // Top Header Banner
    display.fillRect(0, 0, 128, 14, SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(6, 3);
    display.print("SHAKTHIKULANGARA IoT");

    // Live Data Display
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 22);
    display.print("Status: ");
    display.println("ONLINE (OK)");

    display.setCursor(0, 34);
    display.print("Time:   ");
    if (minutes < 10) display.print("0");
    display.print(minutes);
    display.print(":");
    if (seconds < 10) display.print("0");
    display.println(seconds);

    display.setCursor(0, 46);
    display.print("Count:  #");
    display.println(counter);

    // Bottom progress bar
    int barWidth = (counter % 30) * (128 / 30);
    display.drawRect(0, 58, 128, 6, SSD1306_WHITE);
    display.fillRect(0, 58, barWidth, 6, SSD1306_WHITE);

    display.display();

    // Serial monitor debug output
    Serial.print("Uptime: ");
    Serial.print(counter);
    Serial.println("s");
  }
}
