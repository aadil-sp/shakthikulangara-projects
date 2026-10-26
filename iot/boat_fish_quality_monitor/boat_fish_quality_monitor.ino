/**
 * ============================================================================
 * Project: Shakthikulangara Fishing Boat - Fish Quality & Storage Monitor
 * Target: NodeMCU ESP8266 (ESP-12E / ESP-12F)
 * Location: Shakthikulangara Marine Harbour, Kollam, Kerala
 * 
 * Monitored Parameters:
 *  1. Fish Freshness / Spoilage Gases : MQ-135 (Ammonia, TMA, TVB-N) + MQ-4 (CH4)
 *  2. Ice Storage Cold Chain          : DHT11 (Temperature & Relative Humidity)
 *  3. Meltwater Clogging Prevention   : Ultrasonic Sensor (HC-SR04 / JSN-SR04T)
 *  4. High-Detail UI Dashboard        : SSD1306 0.96" OLED Display (128x64 I2C)
 *  5. Quick Glance Readout            : TM1637 4-Digit 7-Segment Display
 *  6. Marine User Controls            : 3x Push Buttons for Menu Navigation
 * ============================================================================
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <TM1637Display.h>
#include <DHT.h>
#include "config.h"

// ============================================================================
// HARDWARE INSTANCES & OBJECTS
// ============================================================================
Adafruit_SSD1306 display(OLED_SCREEN_WIDTH, OLED_SCREEN_HEIGHT, &Wire, OLED_RESET_PIN);
TM1637Display tm1637(TM1637_CLK_PIN, TM1637_DIO_PIN);
DHT dht(DHT_PIN, DHT_TYPE);

// ============================================================================
// ENUMERATIONS & DATA STRUCTURES
// ============================================================================
enum FishQualityGrade {
  GRADE_FRESH,    // Grade A: Prime Catch (0-4°C, Low Gas, Dry Ice Storage)
  GRADE_GOOD,     // Grade B: Good Catch (Commercial Grade)
  GRADE_WARNING,  // Grade C: Warning (Ice Depletion or Sluggish Drainage)
  GRADE_SPOILED   // Grade D: Critical Spoilage / Water Clogged Contamination
};

enum DrainStatus {
  DRAIN_CLEAR,    // Safe: Water <= 2.0 cm (Only ice contact with fish)
  DRAIN_RISING,   // Warning: Water 2.1 to 5.0 cm (Drain sluggish)
  DRAIN_CLOGGED   // Hazard: Water > 5.0 cm (Stagnant meltwater soaking fish!)
};

enum TempStatus {
  TEMP_OPTIMAL,   // 0.0°C to 4.0°C (Standard chilled ice hold)
  TEMP_WARM,      // 4.1°C to 8.0°C (Ice melting, temperature rising)
  TEMP_CRITICAL   // > 8.0°C (High bacterial spoilage rate)
};

enum GasStatus {
  GAS_OK,         // Clean maritime sea breeze in hold
  GAS_DETECTED,   // Early volatile amines / TVB-N detected
  GAS_ROTTING     // Putrefaction / severe decomposition odor
};

enum TMDisplayMode {
  TM_MODE_TEMP = 0,
  TM_MODE_WATER,
  TM_MODE_QUALITY,
  TM_MODE_AUTO,
  TM_MODE_COUNT
};

enum OLEDPage {
  PAGE_DASHBOARD = 0,
  PAGE_GAS_MONITOR,
  PAGE_COLD_DRAIN,
  PAGE_SYSTEM_INFO,
  PAGE_COUNT
};

// ============================================================================
// GLOBAL STATE VARIABLES
// ============================================================================
// Sensor Readings
float currentTemperature = 2.5f;   // °C
float currentHumidity    = 85.0f;  // %
float rawDistanceCm      = 38.5f;  // Ultrasonic measured clearance (cm)
float meltwaterDepthCm   = 1.5f;   // Calculated meltwater depth (cm)
int   mq135RawAdc        = 220;    // Raw 10-bit ADC (0-1023)
float mq135EstPpm        = 12.0f;  // Estimated volatile basic nitrogen / NH3 (ppm)
bool  mq4MethaneAlarm    = false;  // Methane detection state

// Evaluated Health Status
FishQualityGrade fishGrade  = GRADE_FRESH;
DrainStatus      drainState = DRAIN_CLEAR;
TempStatus       tempState  = TEMP_OPTIMAL;
GasStatus        gasState   = GAS_OK;
int              freshnessScore = 95; // 0 - 100%

// UI State
OLEDPage      currentPage   = PAGE_DASHBOARD;
TMDisplayMode tmMode        = TM_MODE_AUTO;
int           tmAutoSubMode = 0;
bool          alarmMuted    = false;
unsigned long voyageSeconds = 0;

// Timing Timestamps
unsigned long lastSensorReadTime  = 0;
unsigned long lastDisplayTime     = 0;
unsigned long lastTmCycleTime     = 0;
unsigned long lastSecondTick      = 0;

// Button Debounce Timers & States
unsigned long lastBtnNextTime   = 0;
unsigned long lastBtnPrevTime   = 0;
unsigned long lastBtnSelectTime = 0;
bool lastBtnNextState   = HIGH;
bool lastBtnPrevState   = HIGH;
bool lastBtnSelectState = HIGH;
unsigned long btnSelectPressStart = 0;

// Ultrasonic Rolling Filter Buffer
float distanceSamples[ULTRASONIC_SAMPLES];
int sampleIndex = 0;
bool samplesFilled = false;

// Custom 7-Segment Glyphs for TM1637
// Segment mapping: 0b[DP][G][F][E][D][C][B][A]
const uint8_t GLYPH_CELSIUS[] = { 0b00111001 };                         // 'C'
const uint8_t GLYPH_HEIGHT[]  = { 0b01110110 };                         // 'H'
const uint8_t GLYPH_FRESH[]   = { 0b01110001, 0b01010000 };             // 'F', 'r'
const uint8_t GLYPH_DRAN[]    = { 0b01011110, 0b01010000, 0b01110111, 0b01010100 }; // "drAn" (Drain)
const uint8_t GLYPH_HOT[]     = { 0b01110110, 0b01011100, 0b01111000, 0b00000000 }; // "Hot "
const uint8_t GLYPH_BAD[]     = { 0b01111100, 0b01110111, 0b01011110, 0b00000000 }; // "bAd "

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================
void readSensors();
void readDHT11();
void readUltrasonicDistance();
void readGasSensors();
void evaluateFishQuality();
void handleButtons();
void updateOLED();
void updateTM1637();
void renderDashboardPage();
void renderGasPage();
void renderColdDrainPage();
void renderSystemInfoPage();
void printSerialTelemetry();

// ============================================================================
// SETUP FUNCTION
// ============================================================================
void setup() {
  // Start Serial for marine telemetry output (115200 baud)
  Serial.begin(115200);
  delay(100);
  Serial.println(F("\n======================================================="));
  Serial.println(F("  SHAKTHIKULANGARA HARBOUR - FISH QUALITY MONITOR v1.0 "));
  Serial.println(F("  Smart Cold Storage & Meltwater Drainage Supervisor   "));
  Serial.println(F("======================================================="));

  // Initialize Hardware Pins
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  pinMode(BTN_NEXT_PIN, INPUT_PULLUP);
  pinMode(BTN_PREV_PIN, INPUT_PULLUP);
  #if defined(INPUT_PULLDOWN_16) && (BTN_PREV_PIN == D0)
    pinMode(BTN_PREV_PIN, INPUT_PULLUP);
  #endif
  pinMode(BTN_SELECT_PIN, INPUT_PULLUP);

  if (MQ4_DIGITAL_PIN >= 0) {
    pinMode(MQ4_DIGITAL_PIN, INPUT);
  }
  if (BUZZER_PIN >= 0) {
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);
  }

  // Initialize TM1637 7-Segment Display
  tm1637.setBrightness(0x0f); // Maximum brightness for bright boat decks
  // Test animation on TM1637
  uint8_t bootSegs[] = { 0b01110001, 0b00111000, 0b00111001, 0b01110110 }; // "FISH"
  tm1637.setSegments(bootSegs);

  // Initialize I2C Bus for SSD1306 OLED (D2 = SDA, D1 = SCL)
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);

  // Initialize OLED Display
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR)) {
    Serial.println(F("[ERR] SSD1306 OLED initialization failed at 0x3C! Check wiring."));
  } else {
    Serial.println(F("[OK] SSD1306 OLED Display initialized successfully."));
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    // Shakthikulangara Splash Screen
    display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
    display.fillRect(2, 2, 124, 14, SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(6, 5);
    display.print(F("SHAKTHIKULANGARA"));

    display.setTextColor(SSD1306_WHITE);
    display.setCursor(12, 24);
    display.print(F("BOAT CATCH MONITOR"));
    display.setCursor(12, 38);
    display.print(F("Cold & Spoilage IoT"));
    display.setCursor(18, 51);
    display.print(F("Warming Sensors..."));
    display.display();
    delay(2000);
  }

  // Initialize DHT11 Sensor
  dht.begin();
  Serial.println(F("[OK] DHT11 Temperature & Humidity Sensor initialized."));

  // Prime ultrasonic buffer
  for (int i = 0; i < ULTRASONIC_SAMPLES; i++) {
    distanceSamples[i] = TANK_DEPTH_TOTAL_CM;
  }

  Serial.println(F("[OK] System Initialized. Entering Monitoring Loop...\n"));
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
  unsigned long now = millis();

  // 1. Increment 1-Second Voyage Timer
  if (now - lastSecondTick >= 1000) {
    lastSecondTick = now;
    voyageSeconds++;
  }

  // 2. Read Sensors Periodically
  if (now - lastSensorReadTime >= SENSOR_READ_INTERVAL_MS) {
    lastSensorReadTime = now;
    readSensors();
    evaluateFishQuality();
    printSerialTelemetry();
  }

  // 3. Process Navigation Buttons
  handleButtons();

  // 4. Update OLED Display
  if (now - lastDisplayTime >= DISPLAY_UPDATE_INTERVAL_MS) {
    lastDisplayTime = now;
    updateOLED();
  }

  // 5. Update 7-Segment Display (TM1637)
  if (tmMode == TM_MODE_AUTO) {
    if (now - lastTmCycleTime >= TM1637_CYCLE_INTERVAL_MS) {
      lastTmCycleTime = now;
      tmAutoSubMode = (tmAutoSubMode + 1) % 3; // Cycle Temp -> Water -> Quality
      updateTM1637();
    }
  } else {
    updateTM1637();
  }

  // 6. Handle Audio Buzzer Alarm (if configured)
  if (BUZZER_PIN >= 0) {
    if (!alarmMuted && (drainState == DRAIN_CLOGGED || fishGrade == GRADE_SPOILED || tempState == TEMP_CRITICAL)) {
      // Intermittent beep: 500ms ON / 500ms OFF
      digitalWrite(BUZZER_PIN, ((now / 500) % 2 == 0) ? HIGH : LOW);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }
  }
}

// ============================================================================
// SENSOR ACQUISITION FUNCTIONS
// ============================================================================
void readSensors() {
  readDHT11();
  readUltrasonicDistance();
  readGasSensors();
}

/**
 * Reads Cold Hold Temperature & Humidity from DHT11
 */
void readDHT11() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  // Validate readings to avoid NaN corruption
  if (!isnan(t) && t > -40.0f && t < 85.0f) {
    currentTemperature = t;
  }
  if (!isnan(h) && h >= 0.0f && h <= 100.0f) {
    currentHumidity = h;
  }
}

/**
 * Reads HC-SR04 Ultrasonic Distance with Rolling Median Filter
 * Overcomes boat wave oscillation and sloshing surface ripple
 */
void readUltrasonicDistance() {
  // Clear trigger pin
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(4);
  // Send 10µs ultrasonic trigger pulse
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  // Measure echo return pulse (timeout ~ 30,000 µs = ~5 meters)
  unsigned long durationUs = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 30000UL);

  float measuredCm = 0.0f;
  if (durationUs > 0) {
    // Speed of sound in maritime chilled hold (~338 m/s at 2°C)
    // Distance (cm) = (Duration * 0.0340) / 2
    measuredCm = (durationUs * 0.0340f) / 2.0f;
  } else {
    // Timeout fallback (hold depth)
    measuredCm = TANK_DEPTH_TOTAL_CM;
  }

  // Constrain reading to realistic fish hold boundaries (2cm to 200cm)
  if (measuredCm < 2.0f) measuredCm = 2.0f;
  if (measuredCm > TANK_DEPTH_TOTAL_CM + 10.0f) measuredCm = TANK_DEPTH_TOTAL_CM;

  // Insert into rolling filter buffer
  distanceSamples[sampleIndex] = measuredCm;
  sampleIndex = (sampleIndex + 1) % ULTRASONIC_SAMPLES;
  if (sampleIndex == 0) samplesFilled = true;

  // Compute running average of samples
  float sum = 0.0f;
  int count = samplesFilled ? ULTRASONIC_SAMPLES : sampleIndex;
  if (count <= 0) count = 1;

  for (int i = 0; i < count; i++) {
    sum += distanceSamples[i];
  }
  rawDistanceCm = sum / count;

  // Calculate Meltwater Depth:
  // Meltwater Depth = Total Hold Depth - Distance from Sensor to Surface
  meltwaterDepthCm = TANK_DEPTH_TOTAL_CM - rawDistanceCm;
  if (meltwaterDepthCm < 0.0f) meltwaterDepthCm = 0.0f;
}

/**
 * Reads MQ-135 (Ammonia/TVOC spoilage) and MQ-4 (Methane)
 */
void readGasSensors() {
  // Read MQ-135 Analog Channel on A0 (10-bit: 0 - 1023)
  long adcAccumulator = 0;
  const int ADC_OVERSAMPLE = 8;
  for (int i = 0; i < ADC_OVERSAMPLE; i++) {
    adcAccumulator += analogRead(MQ135_ANALOG_PIN);
    delayMicroseconds(200);
  }
  mq135RawAdc = (int)(adcAccumulator / ADC_OVERSAMPLE);

  // Approximation formula for TVB-N / Ammonia headspace concentration (ppm)
  // Calibrated based on typical MQ-135 load resistance
  float voltage = (mq135RawAdc / 1023.0f) * 3.3f;
  // Estimate ppm relative to baseline
  mq135EstPpm = ((float)mq135RawAdc / (float)GAS_CLEAN_BASELINE) * 10.0f;
  if (mq135EstPpm < 0.0f) mq135EstPpm = 0.0f;

  // Check MQ-4 Methane Digital Pin (if configured)
  if (MQ4_DIGITAL_PIN >= 0) {
    // Breakout modules output LOW when gas threshold is exceeded
    mq4MethaneAlarm = (digitalRead(MQ4_DIGITAL_PIN) == LOW);
  } else {
    // If MQ-4 digital pin not wired, derive alert from severe gas elevation
    mq4MethaneAlarm = (mq135RawAdc >= GAS_ROTTING_CRITICAL);
  }
}

// ============================================================================
// MULTI-METRIC FISH QUALITY EVALUATION ALGORITHM
// ============================================================================
void evaluateFishQuality() {
  // 1. Evaluate Cold Chain Temperature
  if (currentTemperature <= TEMP_OPTIMAL_MAX) {
    tempState = TEMP_OPTIMAL;
  } else if (currentTemperature <= TEMP_WARNING_MAX) {
    tempState = TEMP_WARM;
  } else {
    tempState = TEMP_CRITICAL;
  }

  // 2. Evaluate Meltwater Level & Drainage Clogging
  // CRITICAL REQUIREMENT: Water must NOT remain logged in the container.
  // Stagnant meltwater leaches nutrients and breeds pathogenic bacteria. Only ice should remain!
  if (meltwaterDepthCm <= WATER_SAFE_MAX_CM) {
    drainState = DRAIN_CLEAR;
  } else if (meltwaterDepthCm <= WATER_WARN_MAX_CM) {
    drainState = DRAIN_RISING;
  } else {
    drainState = DRAIN_CLOGGED; // Drain clogged! Meltwater accumulating!
  }

  // 3. Evaluate Volatile Spoilage Gases (Ammonia / TMA / Methane)
  if (mq135RawAdc < GAS_EARLY_SPOILAGE && !mq4MethaneAlarm) {
    gasState = GAS_OK;
  } else if (mq135RawAdc < GAS_ROTTING_CRITICAL) {
    gasState = GAS_DETECTED;
  } else {
    gasState = GAS_ROTTING;
  }

  // 4. Calculate Composite Freshness Score (100 = Pristine Fresh, 0 = Spoiled)
  int score = 100;

  // Temperature penalties
  if (currentTemperature > TEMP_OPTIMAL_MAX) {
    float tempExcess = currentTemperature - TEMP_OPTIMAL_MAX;
    score -= (int)(tempExcess * 8.0f); // -8% per degree above 4°C
  }

  // Meltwater Clogging penalties (Heavy penalty: water contamination)
  if (meltwaterDepthCm > WATER_SAFE_MAX_CM) {
    float waterExcess = meltwaterDepthCm - WATER_SAFE_MAX_CM;
    score -= (int)(waterExcess * 12.0f); // -12% per cm of stagnant meltwater
  }

  // Volatile gas penalties (Ammonia / Trimethylamine / Methane)
  if (mq135RawAdc > GAS_CLEAN_BASELINE) {
    int gasExcess = mq135RawAdc - GAS_CLEAN_BASELINE;
    score -= (gasExcess / 15);
  }
  if (mq4MethaneAlarm) {
    score -= 25; // Large penalty for anaerobic biogas release
  }

  // Constrain score
  if (score < 0)   score = 0;
  if (score > 100) score = 100;
  freshnessScore = score;

  // 5. Assign Final Grade
  if (drainState == DRAIN_CLOGGED || gasState == GAS_ROTTING || freshnessScore < 40) {
    fishGrade = GRADE_SPOILED;
  } else if (tempState == TEMP_CRITICAL || drainState == DRAIN_RISING || gasState == GAS_DETECTED || freshnessScore < 70) {
    fishGrade = GRADE_WARNING;
  } else if (freshnessScore < 85) {
    fishGrade = GRADE_GOOD;
  } else {
    fishGrade = GRADE_FRESH;
  }
}

// ============================================================================
// NAVIGATION BUTTON HANDLER (DEBOUNCED)
// ============================================================================
void handleButtons() {
  unsigned long now = millis();

  // --- Button 1: NEXT PAGE (BTN_NEXT_PIN = D3) ---
  int btnNextReading = digitalRead(BTN_NEXT_PIN);
  if (btnNextReading == LOW && lastBtnNextState == HIGH) {
    if (now - lastBtnNextTime > BUTTON_DEBOUNCE_MS) {
      lastBtnNextTime = now;
      currentPage = (OLEDPage)((currentPage + 1) % PAGE_COUNT);
      Serial.print(F("[UI] Next Page -> "));
      Serial.println(currentPage);
    }
  }
  lastBtnNextState = btnNextReading;

  // --- Button 2: PREV PAGE (BTN_PREV_PIN = D0) ---
  int btnPrevReading = digitalRead(BTN_PREV_PIN);
  if (btnPrevReading == LOW && lastBtnPrevState == HIGH) {
    if (now - lastBtnPrevTime > BUTTON_DEBOUNCE_MS) {
      lastBtnPrevTime = now;
      currentPage = (OLEDPage)((currentPage - 1 + PAGE_COUNT) % PAGE_COUNT);
      Serial.print(F("[UI] Prev Page -> "));
      Serial.println(currentPage);
    }
  }
  lastBtnPrevState = btnPrevReading;

  // --- Button 3: SELECT / MODE / MUTE (BTN_SELECT_PIN = RX / GPIO3) ---
  int btnSelReading = digitalRead(BTN_SELECT_PIN);
  if (btnSelReading == LOW && lastBtnSelectState == HIGH) {
    btnSelectPressStart = now;
  } else if (btnSelReading == HIGH && lastBtnSelectState == LOW) {
    unsigned long pressDuration = now - btnSelectPressStart;
    if (pressDuration >= BUTTON_DEBOUNCE_MS) {
      if (pressDuration > 1500) {
        // LONG PRESS (>1.5s): Acknowledge / Mute Alarm Buzzer or Reset Baseline
        alarmMuted = !alarmMuted;
        Serial.print(F("[UI] Alarm Mute toggled: "));
        Serial.println(alarmMuted ? F("MUTED") : F("ACTIVE"));
      } else {
        // SHORT PRESS: Cycle TM1637 Display Mode (Temp -> Water -> Score -> Auto)
        tmMode = (TMDisplayMode)((tmMode + 1) % TM_MODE_COUNT);
        Serial.print(F("[UI] TM1637 Mode -> "));
        Serial.println(tmMode);
      }
    }
  }
  lastBtnSelectState = btnSelReading;
}

// ============================================================================
// OLED DISPLAY RENDERING (MULTI-SCREEN UI)
// ============================================================================
void updateOLED() {
  display.clearDisplay();

  // 1. Top Status Banner (Shared across all pages)
  display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(2, 2);
  display.print(F("SHAKTHI BOAT "));

  // Display Page Indicator e.g. "1/4"
  display.setCursor(102, 2);
  display.print(currentPage + 1);
  display.print(F("/"));
  display.print(PAGE_COUNT);

  // 2. Render Page-Specific Content
  display.setTextColor(SSD1306_WHITE);
  switch (currentPage) {
    case PAGE_DASHBOARD:
      renderDashboardPage();
      break;
    case PAGE_GAS_MONITOR:
      renderGasPage();
      break;
    case PAGE_COLD_DRAIN:
      renderColdDrainPage();
      break;
    case PAGE_SYSTEM_INFO:
      renderSystemInfoPage();
      break;
  }

  // 3. Urgent Water Clogged / Spoilage Warning Alert Overlay
  if (drainState == DRAIN_CLOGGED) {
    // Blink banner at bottom: 500ms ON / 500ms OFF
    if ((millis() / 500) % 2 == 0) {
      display.fillRect(0, 52, 128, 12, SSD1306_WHITE);
      display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
      display.setCursor(4, 54);
      display.print(F("! DRAIN WATER CLOG !"));
    }
  } else if (fishGrade == GRADE_SPOILED) {
    if ((millis() / 500) % 2 == 0) {
      display.fillRect(0, 52, 128, 12, SSD1306_WHITE);
      display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
      display.setCursor(8, 54);
      display.print(F("! FISH DECAY ALERT !"));
    }
  }

  display.display();
}

/**
 * Screen 1: Main Dashboard
 */
void renderDashboardPage() {
  // Catch Quality Status Box
  display.setCursor(0, 16);
  display.setTextSize(1);
  display.print(F("Quality: "));

  display.setTextSize(1);
  switch (fishGrade) {
    case GRADE_FRESH:
      display.print(F("PRIME FRESH"));
      break;
    case GRADE_GOOD:
      display.print(F("COMMERCIAL"));
      break;
    case GRADE_WARNING:
      display.print(F("WARNING"));
      break;
    case GRADE_SPOILED:
      display.print(F("SPOILED"));
      break;
  }

  // Freshness Progress Bar
  display.setCursor(0, 27);
  display.print(F("Fresh: "));
  display.print(freshnessScore);
  display.print(F("%"));

  int barW = map(freshnessScore, 0, 100, 0, 50);
  display.drawRect(74, 27, 52, 7, SSD1306_WHITE);
  display.fillRect(75, 28, barW, 5, SSD1306_WHITE);

  // Key Sensor Metric Rows
  display.setCursor(0, 38);
  display.print(F("Temp : "));
  display.print(currentTemperature, 1);
  display.print((char)247); // Degree symbol
  display.print(F("C "));
  if (tempState == TEMP_OPTIMAL) display.print(F("[OK]"));
  else if (tempState == TEMP_WARM) display.print(F("[WRN]"));
  else display.print(F("[HOT]"));

  display.setCursor(0, 48);
  display.print(F("Water: "));
  display.print(meltwaterDepthCm, 1);
  display.print(F("cm "));
  if (drainState == DRAIN_CLEAR) display.print(F("[CLEAN]"));
  else if (drainState == DRAIN_RISING) display.print(F("[POOL]"));
  else display.print(F("[CLOG!]"));
}

/**
 * Screen 2: Gas & Spoilage Monitor (MQ-135 & MQ-4)
 */
void renderGasPage() {
  display.setCursor(0, 16);
  display.setTextSize(1);
  display.print(F("GAS / SPOILAGE SENSOR"));

  // MQ-135 Ammonia & Volatiles
  display.setCursor(0, 27);
  display.print(F("MQ135 Raw: "));
  display.print(mq135RawAdc);

  display.setCursor(0, 37);
  display.print(F("TVB-N Est: "));
  display.print(mq135EstPpm, 1);
  display.print(F(" ppm"));

  // MQ-4 Methane State
  display.setCursor(0, 47);
  display.print(F("MQ-4 CH4 : "));
  if (mq4MethaneAlarm) {
    display.print(F("DETECTED!"));
  } else {
    display.print(F("CLEAR (OK)"));
  }

  // Spoilage Risk Bar
  int gasBar = map(constrain(mq135RawAdc, 100, 700), 100, 700, 0, 124);
  display.drawRect(0, 57, 126, 6, SSD1306_WHITE);
  display.fillRect(1, 58, gasBar, 4, SSD1306_WHITE);
}

/**
 * Screen 3: Cold Chain & Meltwater Drainage
 */
void renderColdDrainPage() {
  display.setCursor(0, 16);
  display.setTextSize(1);
  display.print(F("ICE HOLD & DRAINAGE"));

  // Temperature & Humidity
  display.setCursor(0, 26);
  display.print(F("Ice Temp: "));
  display.print(currentTemperature, 1);
  display.print((char)247);
  display.print(F("C (0-4"));
  display.print((char)247);
  display.print(F(")"));

  display.setCursor(0, 36);
  display.print(F("Humidity: "));
  display.print(currentHumidity, 0);
  display.print(F("% RH"));

  // Meltwater & Contamination Status
  display.setCursor(0, 46);
  display.print(F("Meltwater : "));
  display.print(meltwaterDepthCm, 1);
  display.print(F(" cm"));

  display.setCursor(0, 56);
  if (drainState == DRAIN_CLEAR) {
    display.print(F("Status: ICE ONLY (OK)"));
  } else if (drainState == DRAIN_RISING) {
    display.print(F("Status: WATER RISING"));
  } else {
    display.print(F("Status: CLOGGED! DRAIN"));
  }
}

/**
 * Screen 4: System Information, Trip Duration & Nav Help
 */
void renderSystemInfoPage() {
  display.setCursor(0, 16);
  display.setTextSize(1);
  display.print(F("BOAT TRIP DIAGNOSTICS"));

  // Voyage Time (HH:MM:SS)
  unsigned long hrs  = voyageSeconds / 3600;
  unsigned long mins = (voyageSeconds % 3600) / 60;
  unsigned long secs = voyageSeconds % 60;

  display.setCursor(0, 27);
  display.print(F("Voyage : "));
  if (hrs < 10) display.print(F("0"));
  display.print(hrs);
  display.print(F(":"));
  if (mins < 10) display.print(F("0"));
  display.print(mins);
  display.print(F(":"));
  if (secs < 10) display.print(F("0"));
  display.print(secs);

  display.setCursor(0, 37);
  display.print(F("Hold Depth: "));
  display.print(TANK_DEPTH_TOTAL_CM, 0);
  display.print(F(" cm"));

  display.setCursor(0, 47);
  display.print(F("7-Seg Mode: "));
  switch (tmMode) {
    case TM_MODE_TEMP:    display.print(F("TEMP")); break;
    case TM_MODE_WATER:   display.print(F("WATER")); break;
    case TM_MODE_QUALITY: display.print(F("SCORE")); break;
    case TM_MODE_AUTO:    display.print(F("AUTO")); break;
    default: break;
  }

  display.setCursor(0, 56);
  display.print(F("Nav: [D3-N] [D0-P] [RX-M]"));
}

// ============================================================================
// TM1637 4-DIGIT 7-SEGMENT DISPLAY UPDATE
// ============================================================================
void updateTM1637() {
  // EMERGENCY OVERWRITE:
  // If meltwater is clogged, blink "drAn" (Drain) every 500ms
  if (drainState == DRAIN_CLOGGED) {
    if ((millis() / 500) % 2 == 0) {
      tm1637.setSegments(GLYPH_DRAN);
      return;
    }
  }

  // Determine current active submode
  int activeMode = tmMode;
  if (tmMode == TM_MODE_AUTO) {
    activeMode = tmAutoSubMode;
  }

  switch (activeMode) {
    case TM_MODE_TEMP: {
      // Display Temperature e.g. " 2.5C" or " 03 C"
      int tempInt = (int)(currentTemperature * 10.0f);
      if (tempInt >= 0 && tempInt < 999) {
        int whole = tempInt / 10;
        int frac  = tempInt % 10;
        // Format as [Digit1][Digit2.][Frac][C]
        uint8_t data[4];
        data[0] = (whole >= 10) ? tm1637.encodeDigit(whole / 10) : 0x00;
        data[1] = tm1637.encodeDigit(whole % 10) | 0x80; // Decimal point
        data[2] = tm1637.encodeDigit(frac);
        data[3] = GLYPH_CELSIUS[0];
        tm1637.setSegments(data);
      } else {
        tm1637.showNumberDec((int)currentTemperature, false);
      }
      break;
    }

    case TM_MODE_WATER: {
      // Display Water Level e.g. "H 1.2" (Height in cm)
      int waterInt = (int)(meltwaterDepthCm * 10.0f);
      uint8_t data[4];
      data[0] = GLYPH_HEIGHT[0]; // 'H'
      int whole = waterInt / 10;
      int frac  = waterInt % 10;
      data[1] = (whole >= 10) ? tm1637.encodeDigit(whole / 10) : 0x00;
      data[2] = tm1637.encodeDigit(whole % 10) | 0x80; // Decimal point
      data[3] = tm1637.encodeDigit(frac);
      tm1637.setSegments(data);
      break;
    }

    case TM_MODE_QUALITY: {
      // Display Freshness Quality Score e.g. "Fr85"
      uint8_t data[4];
      data[0] = GLYPH_FRESH[0]; // 'F'
      data[1] = GLYPH_FRESH[1]; // 'r'
      data[2] = tm1637.encodeDigit(freshnessScore / 10);
      data[3] = tm1637.encodeDigit(freshnessScore % 10);
      tm1637.setSegments(data);
      break;
    }
  }
}

// ============================================================================
// SERIAL TELEMETRY LOGGING (CSV / DIAGNOSTIC FORMAT)
// ============================================================================
void printSerialTelemetry() {
  Serial.print(F("[TELEMETRY] Voyage: "));
  Serial.print(voyageSeconds);
  Serial.print(F("s | Temp: "));
  Serial.print(currentTemperature, 1);
  Serial.print(F("C | Hum: "));
  Serial.print(currentHumidity, 0);
  Serial.print(F("% | Water: "));
  Serial.print(meltwaterDepthCm, 1);
  Serial.print(F("cm | Drain: "));
  switch (drainState) {
    case DRAIN_CLEAR:   Serial.print(F("CLEAR")); break;
    case DRAIN_RISING:  Serial.print(F("RISING")); break;
    case DRAIN_CLOGGED: Serial.print(F("CLOGGED_ALERT!")); break;
  }
  Serial.print(F(" | Gas_ADC: "));
  Serial.print(mq135RawAdc);
  Serial.print(F(" | CH4: "));
  Serial.print(mq4MethaneAlarm ? F("ALERT") : F("OK"));
  Serial.print(F(" | FreshScore: "));
  Serial.print(freshnessScore);
  Serial.print(F("% | Grade: "));
  switch (fishGrade) {
    case GRADE_FRESH:   Serial.println(F("A_PRIME_FRESH")); break;
    case GRADE_GOOD:    Serial.println(F("B_COMMERCIAL")); break;
    case GRADE_WARNING: Serial.println(F("C_WARNING")); break;
    case GRADE_SPOILED: Serial.println(F("D_SPOILED")); break;
  }
}
