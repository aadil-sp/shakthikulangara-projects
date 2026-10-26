/*
 * SHAKTHIKULANGARA SCHOOL STEM LAB - ROBOTICS PROJECT
 * Autonomous Obstacle Avoidance Rover & Web Telemetry Server
 * Board: NodeMCU ESP8266 (ESP-12E)
 * Features: SoftAP Web Server (192.168.4.1), Differential Drive & Ultrasonic Radar
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// --- L298N Motor Driver Pins ---
#define PIN_IN1 D1 // GPIO 5 (Left Forward)
#define PIN_IN2 D2 // GPIO 4 (Left Reverse)
#define PIN_IN3 D5 // GPIO 14 (Right Forward)
#define PIN_IN4 D6 // GPIO 12 (Right Reverse)

// --- HC-SR04 Ultrasonic Sensor Pins ---
#define PIN_TRIG D7 // GPIO 13
#define PIN_ECHO D8 // GPIO 15

ESP8266WebServer server(80);

int currentSpeed = 200; // 0 - 255 PWM
bool autoMode = false;
unsigned long lastRadarCheck = 0;

float getUltrasonicDistance() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  
  long duration = pulseIn(PIN_ECHO, HIGH, 25000); // 25ms timeout (~4m)
  if (duration == 0) return 400.0;
  return (duration * 0.0343) / 2.0; // Distance in cm
}

void stopMotors() {
  analogWrite(PIN_IN1, 0);
  analogWrite(PIN_IN2, 0);
  analogWrite(PIN_IN3, 0);
  analogWrite(PIN_IN4, 0);
}

void driveForward(int spd) {
  analogWrite(PIN_IN1, spd);
  analogWrite(PIN_IN2, 0);
  analogWrite(PIN_IN3, spd);
  analogWrite(PIN_IN4, 0);
}

void driveReverse(int spd) {
  analogWrite(PIN_IN1, 0);
  analogWrite(PIN_IN2, spd);
  analogWrite(PIN_IN3, 0);
  analogWrite(PIN_IN4, spd);
}

void turnLeft(int spd) {
  analogWrite(PIN_IN1, 0);
  analogWrite(PIN_IN2, spd);
  analogWrite(PIN_IN3, spd);
  analogWrite(PIN_IN4, 0);
}

void turnRight(int spd) {
  analogWrite(PIN_IN1, spd);
  analogWrite(PIN_IN2, 0);
  analogWrite(PIN_IN3, 0);
  analogWrite(PIN_IN4, spd);
}

// REST API Handler for Remote Web Console
void handleDrive() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  if (!server.hasArg("cmd")) {
    server.send(400, "text/plain", "Missing cmd argument");
    return;
  }
  
  String cmd = server.arg("cmd");
  if (server.hasArg("speed")) {
    currentSpeed = constrain(server.arg("speed").toInt(), 80, 255);
  }
  
  autoMode = false; // Manual command overrides auto mode
  
  if (cmd == "FORWARD") driveForward(currentSpeed);
  else if (cmd == "REVERSE") driveReverse(currentSpeed);
  else if (cmd == "LEFT") turnLeft(currentSpeed);
  else if (cmd == "RIGHT") turnRight(currentSpeed);
  else if (cmd == "STOP") stopMotors();
  else if (cmd == "AUTO") autoMode = true;
  
  float dist = getUltrasonicDistance();
  String json = "{\"status\":\"OK\",\"cmd\":\"" + cmd + "\",\"speed\":" + String(currentSpeed) + ",\"distance\":" + String(dist) + "}";
  server.send(200, "application/json", json);
}

void handleTelemetry() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  float dist = getUltrasonicDistance();
  String json = "{\"distance\":" + String(dist) + ",\"speed\":" + String(currentSpeed) + ",\"auto\":" + (autoMode ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Shakthikulangara Robotics Rover Booting ---");
  
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  stopMotors();
  
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  
  // Set up SoftAP Hotspot
  WiFi.mode(WIFI_AP);
  WiFi.softAP("Shakthikulangara-Robot", "robot1234");
  Serial.print("Access Point Started! IP: ");
  Serial.println(WiFi.softAPIP()); // 192.168.4.1
  
  server.on("/drive", handleDrive);
  server.on("/telemetry", handleTelemetry);
  server.begin();
  Serial.println("HTTP Telemetry Server Online on Port 80");
}

void loop() {
  server.handleClient();
  
  // Autonomous Obstacle Avoidance Loop
  if (autoMode) {
    if (millis() - lastRadarCheck >= 80) {
      lastRadarCheck = millis();
      float dist = getUltrasonicDistance();
      
      if (dist < 22.0) { // Obstacle within 22cm
        stopMotors();
        delay(100);
        driveReverse(180);
        delay(400);
        turnRight(200);
        delay(450);
        stopMotors();
      } else {
        driveForward(currentSpeed);
      }
    }
  }
}
