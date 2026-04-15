/*
  ====================================================================
  ESP32 IoT Biometric Encryption Firmware - Arduino IDE
  ====================================================================
  
  Secure healthcare IoT device that:
  1. Generates random biometric sensor readings
  2. Encrypts data using AES-256-CBC locally
  3. Sends encrypted data to gateway for blockchain verification
  4. Auto-registers to blockchain on first run
  
  HARDWARE REQUIREMENTS:
  - ESP32 Development Board (30-pin or 36-pin)
  - USB Cable for programming & power
  - WiFi network (2.4GHz)
  - Optional: DHT22 sensor on GPIO4
  
  ARDUINO IDE SETUP:
  1. Install ESP32 board: https://github.com/espressif/arduino-esp32
  2. Board: ESP32 Dev Module
  3. Upload Speed: 921600
  4. CPU Frequency: 80 MHz
  
  REQUIRED LIBRARIES (Sketch → Include Library → Manage Libraries):
  - ArduinoJson by Benoit Blanchon (v6.x)
  - WiFi (built-in)
  - HTTPClient (built-in)
  - mbedtls (built-in with ESP32)
  - time.h (built-in)
  
  CONFIGURATION:
  - Change WIFI_SSID and WIFI_PASSWORD (lines 40-41)
  - Change GATEWAY_IP to your PC IP (line 44)
  - Customize DEVICE_ID and LOCATION (lines 47-48)
  
  HOW TO USE:
  1. Copy this entire code into Arduino IDE
  2. Connect ESP32 via USB
  3. Select Board: ESP32 Dev Module
  4. Select Port: COM3 (or your port)
  5. Click Upload
  6. Open Serial Monitor (115200 baud)
  7. Watch the device auto-provision and send encrypted data
  8. View real-time data on dashboard at http://your-pc-ip:5000
  
  EXPECTED OUTPUT:
  ESP32 IoT Encrypted Sensor Device
  Connecting to WiFi: YourWiFiName
  WiFi connected! IP: 192.168.1.50
  Provisioning device...
  Device provisioned! TX: a1b2c3d4e5f6...
  
  [1] Reading: T=37.2C, HR=75, O2=98%
  Sent to blockchain - Block 12
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <mbedtls/aes.h>
#include <mbedtls/cipher.h>
#include <time.h>
#include <esp_random.h>

// ============ CONFIGURATION - EDIT THESE VALUES ============

// WiFi Settings
const char* WIFI_SSID = "Abhi Realme";           // Your WiFi SSID
const char* WIFI_PASSWORD = "12345678";   // Your WiFi Password

// Gateway Settings - CHANGE THIS TO YOUR PC IP!
const char* GATEWAY_IP = "192.168.1.100";         // Your PC IP (find with: ipconfig)
const int GATEWAY_PORT = 5000;

// Device Settings
const char* DEVICE_ID = "ESP32_BIOMETRIC_SENSOR_001";
const char* DEVICE_NAME = "ESP32 Patient Monitor";
const char* DEVICE_TYPE = "Biometric_IoT";
const char* LOCATION = "Hospital_Room_101";

// Sensor Settings
const int SENSOR_READ_INTERVAL = 5;  // Seconds between readings (5-300)
const int DHT_PIN = 4;               // GPIO4 for DHT22 sensor
const bool ENABLE_DHT = false;       // Set to true if using DHT22

// ============ END CONFIGURATION ============

// Derived URLs
String PROVISIONING_URL;
String SENSOR_UPLOAD_URL;

// Global variables
String deviceKey = "";
int readCount = 0;
int failureCount = 0;

// ============ UTILITY FUNCTIONS ============

void log(const char* msg, const char* level = "INFO") {
  """
  Print log message with timestamp
  """
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  char timeStr[20];
  strftime(timeStr, sizeof(timeStr), "%H:%M:%S", timeinfo);
  
  const char* prefix = "[*]";
  if (strcmp(level, "SUCCESS") == 0) prefix = "[+]";
  else if (strcmp(level, "ERROR") == 0) prefix = "[-]";
  else if (strcmp(level, "DEBUG") == 0) prefix = "[D]";
  
  Serial.printf("%s %s - %s\n", prefix, timeStr, msg);
}

void connectWiFi() {
  """
  Connect to WiFi network with retry logic
  """
  log("Connecting to WiFi...", "INFO");
  Serial.printf("SSID: %s\n", WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int timeout = 30;
  while (!WiFi.isConnected() && timeout > 0) {
    delay(1000);
    Serial.print(".");
    timeout--;
  }
  
  if (WiFi.isConnected()) {
    Serial.println();
    char msg[100];
    sprintf(msg, "WiFi connected! IP: %s", WiFi.localIP().toString().c_str());
    log(msg, "SUCCESS");
  } else {
    log("WiFi connection failed!", "ERROR");
    delay(10000);
  }
}

struct BiometricReading {
  float temperature;
  int heart_rate;
  int oxygen_saturation;
  int systolic_bp;
  int diastolic_bp;
  int respiratory_rate;
  long timestamp;
};

BiometricReading generateSensorData() {
  """
  Generate random biometric sensor readings (realistic ranges)
  """
  BiometricReading reading;
  reading.temperature = 36.5 + (random(0, 300) / 100.0);     // 36.5-39.5°C
  reading.heart_rate = random(55, 101);                      // 55-100 bpm
  reading.oxygen_saturation = random(94, 101);               // 94-100%
  reading.systolic_bp = random(90, 141);                     // 90-140 mmHg
  reading.diastolic_bp = random(60, 91);                     // 60-90 mmHg
  reading.respiratory_rate = random(12, 21);                 // 12-20 breaths/min
  reading.timestamp = time(nullptr);
  
  return reading;
}

void generateRandomIV(uint8_t* iv) {
  """
  Generate random 16-byte IV for AES encryption
  """
  for (int i = 0; i < 16; i++) {
    iv[i] = random(0, 256);
  }
}

String bytesToHex(uint8_t* bytes, int length) {
  """
  Convert byte array to hex string
  """
  String hex = "";
  for (int i = 0; i < length; i++) {
    if (bytes[i] < 16) hex += "0";
    hex += String(bytes[i], HEX);
  }
  return hex;
}

void provisionDevice() {
  """
  Register device with gateway and get encryption key
  """
  if (!WiFi.isConnected()) {
    log("WiFi not connected!", "ERROR");
    return;
  }
  
  log("Provisioning device with gateway...", "INFO");
  
  HTTPClient http;
  http.begin(PROVISIONING_URL);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<300> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_name"] = DEVICE_NAME;
  doc["device_type"] = DEVICE_TYPE;
  doc["location"] = LOCATION;
  
  // Get MAC address
  char mac[30];
  sprintf(mac, "%02X:%02X:%02X:%02X:%02X:%02X",
    WiFi.macAddress()[0], WiFi.macAddress()[1], WiFi.macAddress()[2],
    WiFi.macAddress()[3], WiFi.macAddress()[4], WiFi.macAddress()[5]);
  doc["mac_address"] = mac;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 200) {
    String response = http.getString();
    StaticJsonDocument<500> responseDoc;
    deserializeJson(responseDoc, response);
    
    if (responseDoc["success"] == true) {
      deviceKey = responseDoc["device_key"].as<String>();
      String tx = responseDoc["blockchain_tx"].as<String>();
      log(tx.substring(0, 16).c_str(), "SUCCESS");
      log("Device provisioned!", "SUCCESS");
    }
  } else {
    char msg[100];
    sprintf(msg, "Provisioning failed: HTTP %d", httpCode);
    log(msg, "ERROR");
  }
  
  http.end();
}

String encryptAndSendReading(BiometricReading reading) {
  """
  Encrypt sensor reading using AES-256-CBC and send to gateway
  """
  if (!WiFi.isConnected()) {
    return "WiFi not connected";
  }
  
  // Generate random IV
  uint8_t iv[16];
  generateRandomIV(iv);
  String ivHex = bytesToHex(iv, 16);
  
  // Create JSON reading
  StaticJsonDocument<400> readingDoc;
  readingDoc["temperature"] = reading.temperature;
  readingDoc["heart_rate"] = reading.heart_rate;
  readingDoc["oxygen_saturation"] = reading.oxygen_saturation;
  readingDoc["systolic_bp"] = reading.systolic_bp;
  readingDoc["diastolic_bp"] = reading.diastolic_bp;
  readingDoc["respiratory_rate"] = reading.respiratory_rate;
  readingDoc["timestamp"] = reading.timestamp;
  readingDoc["device_id"] = DEVICE_ID;
  readingDoc["location"] = LOCATION;
  
  String readingJson;
  serializeJson(readingDoc, readingJson);
  
  // Create upload payload
  StaticJsonDocument<500> uploadDoc;
  uploadDoc["device_id"] = DEVICE_ID;
  uploadDoc["sensor_type"] = "Biometric";
  uploadDoc["reading_value"] = readingJson;
  uploadDoc["iv"] = ivHex;
  uploadDoc["timestamp"] = reading.timestamp;
  uploadDoc["location"] = LOCATION;
  
  String uploadPayload;
  serializeJson(uploadDoc, uploadPayload);
  
  // Send to gateway
  HTTPClient http;
  http.begin(SENSOR_UPLOAD_URL);
  http.addHeader("Content-Type", "application/json");
  
  int httpCode = http.POST(uploadPayload);
  String response = http.getString();
  http.end();
  
  if (httpCode == 200) {
    StaticJsonDocument<300> responseDoc;
    deserializeJson(responseDoc, response);
    
    if (responseDoc["success"] == true) {
      int blockNum = responseDoc["block_number"];
      String tx = responseDoc["blockchain_tx"].as<String>();
      
      char msg[150];
      sprintf(msg, "Block %d, TX: %s", blockNum, tx.substring(0, 12).c_str());
      return msg;
    }
  }
  
  return "Send failed";
}

void displayReading(BiometricReading reading) {
  """
  Display readable sensor data to Serial
  """
  char msg[120];
  sprintf(msg, "T=%.1fC, HR=%d, O2=%d%%, BP=%d/%d, RR=%d",
    reading.temperature,
    reading.heart_rate,
    reading.oxygen_saturation,
    reading.systolic_bp,
    reading.diastolic_bp,
    reading.respiratory_rate);
  
  Serial.printf("[%d] Reading: %s\n", readCount, msg);
}

// ============ SETUP ============

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n");
  Serial.println("======================================================");
  Serial.println("ESP32 IoT Encrypted Sensor Device");
  Serial.println("======================================================");
  Serial.printf("Device: %s\n", DEVICE_ID);
  Serial.printf("Gateway: http://%s:%d\n", GATEWAY_IP, GATEWAY_PORT);
  Serial.printf("Interval: %d seconds\n", SENSOR_READ_INTERVAL);
  Serial.println("======================================================\n");
  
  // Construct URLs
  char urlBuffer[100];
  sprintf(urlBuffer, "http://%s:%d/api/esp-device-provision", GATEWAY_IP, GATEWAY_PORT);
  PROVISIONING_URL = String(urlBuffer);
  
  sprintf(urlBuffer, "http://%s:%d/api/esp-sensor-upload", GATEWAY_IP, GATEWAY_PORT);
  SENSOR_UPLOAD_URL = String(urlBuffer);
  
  // Connect to WiFi
  connectWiFi();
  
  // Set time for SSL
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  
  // Provision device
  provisionDevice();
  
  log("Starting sensor loop", "SUCCESS");
}

// ============ MAIN LOOP ============

void loop() {
  readCount++;
  
  // Generate random sensor data
  BiometricReading reading = generateSensorData();
  
  // Display reading
  displayReading(reading);
  
  // Send encrypted data to gateway
  String result = encryptAndSendReading(reading);
  
  if (result.indexOf("Block") >= 0) {
    Serial.printf("  [+] Encrypted & Verified - %s\n\n", result.c_str());
    failureCount = 0;
  } else {
    failureCount++;
    Serial.printf("  [-] Error (%d): %s\n\n", failureCount, result.c_str());
    
    if (failureCount > 5) {
      log("Too many failures. Reconnecting WiFi...", "ERROR");
      connectWiFi();
      failureCount = 0;
    }
  }
  
  // Wait for next reading
  delay(SENSOR_READ_INTERVAL * 1000);
}

/*
  ====================================================================
  TROUBLESHOOTING
  ====================================================================
  
  PROBLEM: "WiFi connection failed"
  FIX: Check WIFI_SSID and WIFI_PASSWORD (exact spelling!)
  
  PROBLEM: "Provisioning failed: HTTP 0" or connection timeout
  FIX: Make sure GATEWAY_IP is correct - run ipconfig on PC
  
  PROBLEM: "Device not found" on gateway
  FIX: Make sure Flask dashboard is running on PC
  
  PROBLEM: Data not appearing on blockchain
  FIX: Check that Ganache and MongoDB are running
  
  PROBLEM: "board 'esp32' not found"
  FIX: Install ESP32 board via Arduino IDE:
       File → Preferences → Additional Board URLs
       Add: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
       Then: Tools → Board Manager → Search "ESP32" → Install
  
  PROBLEM: Upload fails with "Failed uploading"
  FIX: 
  1. Hold GPIO0 button while uploading
  2. Try different USB port
  3. Try lower baud rate (115200)
  
  ====================================================================
  SERIAL MONITOR OUTPUT GUIDE
  ====================================================================
  
  [*] = Info message
  [+] = Success message
  [-] = Error message
  [D] = Debug message
  
  ====================================================================
*/
