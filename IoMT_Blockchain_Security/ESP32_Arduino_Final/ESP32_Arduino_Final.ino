

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>

// ============ CONFIGURATION ============

const char* WIFI_SSID = "Abhi Realme";
const char* WIFI_PASSWORD = "12345678";
const char* GATEWAY_IP = "10.4.5.17";      // PC running iot_integrated_dashboard.py
const int   GATEWAY_PORT = 5000;

const char* DEVICE_ID   = "ESP8266_BIOMETRIC_SENSOR_001";
const char* DEVICE_NAME = "ESP8266 Patient Monitor";
const char* DEVICE_TYPE = "Biometric_IoT";
const char* LOCATION    = "Hospital_Room_101";

const int SENSOR_READ_INTERVAL = 5;  // seconds
const int HTTP_TIMEOUT = 10000;      // 10 seconds timeout

// ============ GLOBALS ============

String PROVISIONING_URL;
String SENSOR_UPLOAD_URL;
String deviceKey = "";
bool provisioned = false;

int readCount = 0;
int failureCount = 0;
int successCount = 0;

// ============ STRUCT ============

struct BiometricReading {
  float temperature;
  int heart_rate;
  int oxygen_saturation;
  int systolic_bp;
  int diastolic_bp;
  int respiratory_rate;
  long timestamp;
};

// ============ LOGGING ============

void log(const char* msg, const char* level = "INFO") {
  // Use NTP time if synced, else fall back to millis()
  time_t now = time(nullptr);
  char ts[16];
  if (now > 1000000000UL) {
    struct tm* t = localtime(&now);
    strftime(ts, sizeof(ts), "%H:%M:%S", t);
  } else {
    unsigned long s = millis() / 1000;
    snprintf(ts, sizeof(ts), "%02lu:%02lu:%02lu", s / 3600 % 24, s / 60 % 60, s % 60);
  }

  const char* p = "[*]";
  if (!strcmp(level, "SUCCESS")) p = "[+]";
  else if (!strcmp(level, "ERROR")) p = "[-]";
  else if (!strcmp(level, "DEBUG")) p = "[D]";

  Serial.printf("%s %s - %s\n", p, ts, msg);
}

// ============ WIFI ============

void connectWiFi() {
  log("Connecting to WiFi...");
  Serial.printf("SSID: %s\n", WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int timeout = 30;
  while (WiFi.status() != WL_CONNECTED && timeout--) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    log(WiFi.localIP().toString().c_str(), "SUCCESS");
    Serial.printf("Gateway: http://%s:%d\n", GATEWAY_IP, GATEWAY_PORT);
  } else {
    log("WiFi connection failed!", "ERROR");
  }
}

// ============ SENSOR SIMULATION ============

BiometricReading generateSensorData() {
  BiometricReading r;
  r.temperature = 36.5 + random(0, 300) / 100.0;
  r.heart_rate = random(55, 101);
  r.oxygen_saturation = random(94, 101);
  r.systolic_bp = random(90, 141);
  r.diastolic_bp = random(60, 91);
  r.respiratory_rate = random(12, 21);
  // Use NTP epoch if available, else millis-based counter
  time_t t = time(nullptr);
  r.timestamp = (t > 1000000000UL) ? (long)t : (long)(millis() / 1000);
  return r;
}

// ============ CRYPTO UTILS ============

void generateRandomIV(uint8_t* iv) {
  for (int i = 0; i < 16; i++) iv[i] = random(0, 256);
}

String bytesToHex(uint8_t* b, int len) {
  String s;
  for (int i = 0; i < len; i++) {
    if (b[i] < 16) s += "0";
    s += String(b[i], HEX);
  }
  return s;
}

// ============ PROVISIONING ============

void provisionDevice() {
  if (WiFi.status() != WL_CONNECTED) {
    log("WiFi not connected, skipping provisioning", "ERROR");
    return;
  }

  log("Provisioning device...", "DEBUG");

  HTTPClient http;
  WiFiClient client;

  // Set timeout
  http.setTimeout(HTTP_TIMEOUT);
  
  bool begin_result = http.begin(client, PROVISIONING_URL);
  if (!begin_result) {
    log("Failed to begin HTTP connection", "ERROR");
    return;
  }

  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_name"] = DEVICE_NAME;
  doc["device_type"] = DEVICE_TYPE;
  doc["location"] = LOCATION;
  doc["mac_address"] = WiFi.macAddress();

  String payload;
  serializeJson(doc, payload);

  Serial.printf("[D] Provisioning payload: %s\n", payload.c_str());

  int code = http.POST(payload);
  
  Serial.printf("[D] HTTP Response Code: %d\n", code);
  
  String response = http.getString();
  Serial.printf("[D] Response: %s\n", response.c_str());

  if (code == 200) {
    StaticJsonDocument<256> res;
    DeserializationError error = deserializeJson(res, response);
    
    if (!error) {
      bool success = res["success"] | false;
      if (success) {
        deviceKey = res["device_key"].as<String>();
        provisioned = true;
        log("Device provisioned successfully", "SUCCESS");
        Serial.printf("[+] Device Key: %s\n", deviceKey.c_str());
        Serial.printf("[+] TX Hash: %s\n", res["blockchain_tx"].as<String>().c_str());
        Serial.printf("[+] Block: %d\n", res["block_number"].as<int>());
      } else {
        log("Provisioning returned success=false", "ERROR");
      }
    } else {
      log("Failed to parse provisioning response", "ERROR");
      Serial.printf("[-] JSON Error: %s\n", error.c_str());
    }
  } else {
    log("Provisioning failed with HTTP error", "ERROR");
    Serial.printf("[-] HTTP Code: %d\n", code);
  }

  http.end();
}

// ============ SEND DATA ============

String encryptAndSendReading(BiometricReading r) {
  if (!provisioned) {
    log("Device not provisioned, cannot send", "ERROR");
    failureCount++;
    return "Not provisioned";
  }

  if (WiFi.status() != WL_CONNECTED) {
    log("WiFi disconnected", "ERROR");
    failureCount++;
    return "WiFi disconnected";
  }

  uint8_t iv[16];
  generateRandomIV(iv);

  // Create reading JSON
  StaticJsonDocument<384> rd;
  rd["temperature"] = r.temperature;
  rd["heart_rate"] = r.heart_rate;
  rd["oxygen_saturation"] = r.oxygen_saturation;
  rd["systolic_bp"] = r.systolic_bp;
  rd["diastolic_bp"] = r.diastolic_bp;
  rd["respiratory_rate"] = r.respiratory_rate;
  rd["timestamp"] = r.timestamp;
  rd["device_id"] = DEVICE_ID;

  String readingJson;
  serializeJson(rd, readingJson);

  // Create upload payload
  StaticJsonDocument<512> up;
  up["device_id"] = DEVICE_ID;
  up["sensor_type"] = "Biometric";
  up["reading_value"] = readingJson;
  up["iv"] = bytesToHex(iv, 16);
  up["timestamp"] = r.timestamp;
  up["location"] = LOCATION;
  up["encrypted_data"] = "IV_" + bytesToHex(iv, 16);  // Simple encryption simulation

  String payload;
  serializeJson(up, payload);

  Serial.printf("[D] Upload payload size: %d bytes\n", payload.length());
  Serial.printf("[D] Sending to: %s\n", SENSOR_UPLOAD_URL.c_str());

  HTTPClient http;
  WiFiClient client;

  // Set timeout
  http.setTimeout(HTTP_TIMEOUT);

  bool begin_result = http.begin(client, SENSOR_UPLOAD_URL);
  if (!begin_result) {
    log("Failed to begin HTTP connection", "ERROR");
    failureCount++;
    return "Connection failed";
  }

  http.addHeader("Content-Type", "application/json");

  int code = http.POST(payload);
  
  Serial.printf("[D] HTTP Response Code: %d\n", code);

  String response = http.getString();
  Serial.printf("[D] Response: %s\n", response.c_str());

  if (code == 200) {
    StaticJsonDocument<256> res;
    DeserializationError error = deserializeJson(res, response);
    
    if (!error) {
      bool success = res["success"] | false;
      if (success) {
        successCount++;
        String data_hash = res["data_hash"].as<String>();
        int block = res["block_number"].as<int>();
        log("Data uploaded successfully", "SUCCESS");
        Serial.printf("[+] Hash: %s\n", data_hash.substring(0, 20).c_str());
        Serial.printf("[+] Block: %d\n", block);
        return "Block " + String(block);
      } else {
        log("Upload returned success=false", "ERROR");
        failureCount++;
      }
    } else {
      log("Failed to parse upload response", "ERROR");
      failureCount++;
    }
  } else if (code == 404) {
    log("Device not found on server (404)", "ERROR");
    log("Try provisioning again", "DEBUG");
    provisioned = false;
    failureCount++;
    return "Device not found";
  } else {
    log("Upload failed with HTTP error", "ERROR");
    Serial.printf("[-] HTTP Code: %d\n", code);
    failureCount++;
  }

  http.end();
  return "Send failed";
}

// ============ DISPLAY ============

void displayReading(BiometricReading r) {
  Serial.printf(
    "[%d] T=%.1f HR=%d O2=%d BP=%d/%d RR=%d\n",
    readCount,
    r.temperature,
    r.heart_rate,
    r.oxygen_saturation,
    r.systolic_bp,
    r.diastolic_bp,
    r.respiratory_rate
  );
}

void displayStats() {
  Serial.printf("\n=== STATS ===\n");
  Serial.printf("Total reads: %d\n", readCount);
  Serial.printf("Success: %d\n", successCount);
  Serial.printf("Failed: %d\n", failureCount);
  Serial.printf("Success rate: %.1f%%\n", (successCount * 100.0) / max(1, readCount));
  Serial.printf("WiFi Status: %s\n", WiFi.status() == WL_CONNECTED ? "CONNECTED" : "DISCONNECTED");
  Serial.printf("Provisioned: %s\n", provisioned ? "YES" : "NO");
  Serial.printf("===============\n\n");
}

// ============ SETUP ============

void setup() {
  Serial.begin(115200);  // Changed from 9600 to 115200 for faster serial
  delay(2000);

  Serial.println("\n\n");
  log("ESP8266 Starting up...", "DEBUG");

  char buf[128];
  sprintf(buf, "http://%s:%d/api/esp-device-provision", GATEWAY_IP, GATEWAY_PORT);
  PROVISIONING_URL = buf;

  sprintf(buf, "http://%s:%d/api/esp-sensor-upload", GATEWAY_IP, GATEWAY_PORT);
  SENSOR_UPLOAD_URL = buf;

  Serial.printf("Provisioning URL: %s\n", PROVISIONING_URL.c_str());
  Serial.printf("Upload URL: %s\n", SENSOR_UPLOAD_URL.c_str());

  connectWiFi();
  delay(2000);
  
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  delay(2000);
  
  provisionDevice();

  log("ESP8266 ready", "SUCCESS");
}

// ============ LOOP ============

void loop() {
  // Auto-reconnect WiFi if dropped
  if (WiFi.status() != WL_CONNECTED) {
    log("WiFi lost — reconnecting...", "ERROR");
    WiFi.disconnect();
    connectWiFi();
    if (WiFi.status() != WL_CONNECTED) {
      delay(5000);
      return;
    }
  }

  // Re-provision if a previous 404 cleared the flag
  if (!provisioned) {
    log("Not provisioned — retrying...", "ERROR");
    provisionDevice();
    if (!provisioned) {
      delay(10000);
      return;
    }
  }

  readCount++;

  BiometricReading r = generateSensorData();
  displayReading(r);

  String res = encryptAndSendReading(r);
  Serial.println(res);

  // Display stats every 10 reads
  if (readCount % 10 == 0) {
    displayStats();
  }

  delay(SENSOR_READ_INTERVAL * 1000);
}
