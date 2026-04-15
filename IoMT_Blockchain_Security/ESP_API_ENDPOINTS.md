# ESP8266/ESP32 Device API Endpoints

Complete list of all URLs the ESP device needs to send requests to the Dashboard.

**Base URL**: `http://<gateway-ip>:5000`

---

## 1. Device Provisioning (One-time Setup)

### Endpoint: `/api/esp-device-provision`
- **Method**: `POST`
- **Purpose**: Initial provisioning of ESP device to blockchain
- **When to call**: Once when device boots up for the first time
- **Request body**:
```json
{
  "device_id": "ESP32_SENSOR_001",
  "device_name": "My IoT Device",
  "device_type": "Temperature_Sensor",
  "location": "Room_101",
  "mac_address": "AA:BB:CC:DD:EE:FF"
}
```
- **Response**:
```json
{
  "success": true,
  "device_id": "ESP32_SENSOR_001",
  "device_key": "shared_secret_key_first_32_chars",
  "blockchain_tx": "0x123abc...",
  "block_number": 15,
  "message": "Device provisioned and registered to blockchain"
}
```
- **Required fields**: `device_id`
- **Optional fields**: `device_name`, `device_type`, `location`, `mac_address`

---

## 2. Sensor Data Upload (Continuous)

### Endpoint: `/api/esp-sensor-upload`
- **Method**: `POST`
- **Purpose**: Send sensor readings from ESP to gateway
- **When to call**: Continuously (every 5-60 seconds based on your interval)
- **Request body**:
```json
{
  "device_id": "ESP32_SENSOR_001",
  "sensor_type": "Temperature",
  "reading_value": "25.5°C",
  "timestamp": "2026-02-04T22:33:45.123456",
  "encrypted_data": "ENCRYPTED_PAYLOAD_HEX_STRING"
}
```
- **Response**:
```json
{
  "success": true,
  "device_id": "ESP32_SENSOR_001",
  "sensor_type": "Temperature",
  "reading_stored": true,
  "data_hash": "a1b2c3d4e5f6...",
  "blockchain_status": "Active",
  "block_number": 16,
  "message": "Sensor reading received and logged"
}
```
- **Required fields**: `device_id`, `reading_value`
- **Optional fields**: `sensor_type`, `timestamp`, `encrypted_data`
- **Dashboard Display**: 
  - Shows in "Connected ESP Devices" with connection status
  - Displays in "Latest Received Packets & Hashes" with the hash

---

## 3. Get Connected Devices Status (Optional Monitoring)

### Endpoint: `/api/esp-devices`
- **Method**: `GET`
- **Purpose**: Retrieve list of all connected ESP devices
- **When to call**: For monitoring/debugging (not required for device operation)
- **Response**:
```json
[
  {
    "device_id": "ESP32_SENSOR_001",
    "connection_status": "CONNECTED",
    "last_seen": "2026-02-04T22:33:45.123456",
    "last_packet": {
      "sensor_type": "Temperature",
      "reading_value": "25.5°C",
      "hash": "a1b2c3d4e5f6...",
      "encrypted_payload": "ENCRYPTED_PAYLOAD...",
      "timestamp": "2026-02-04T22:33:45.123456"
    }
  }
]
```

---

## 4. Get Specific Device Status (Optional Monitoring)

### Endpoint: `/api/esp-devices/<device_id>`
- **Method**: `GET`
- **Purpose**: Get detailed status of a specific ESP device
- **When to call**: For monitoring/debugging (not required for device operation)
- **Example**: `http://localhost:5000/api/esp-devices/ESP32_SENSOR_001`
- **Response**: Single device object (same format as endpoint #3)

---

## Recommended ESP32 Arduino Code Structure

```cpp
// Configuration
#define GATEWAY_IP "192.168.1.100"
#define GATEWAY_PORT 5000
#define DEVICE_ID "ESP32_SENSOR_001"
#define DEVICE_NAME "My IoT Device"
#define SENSOR_READ_INTERVAL 5000  // 5 seconds

// URLs for requests
String PROVISION_URL = "http://" + String(GATEWAY_IP) + ":" + String(GATEWAY_PORT) + "/api/esp-device-provision";
String UPLOAD_URL = "http://" + String(GATEWAY_IP) + ":" + String(GATEWAY_PORT) + "/api/esp-sensor-upload";
String STATUS_URL = "http://" + String(GATEWAY_IP) + ":" + String(GATEWAY_PORT) + "/api/esp-devices";

void setup() {
  // 1. Connect to WiFi
  connectWiFi();
  
  // 2. Provision device on startup
  provisionDevice();
}

void loop() {
  // 3. Read sensor data and upload continuously
  uploadSensorData();
  
  delay(SENSOR_READ_INTERVAL);
}

void provisionDevice() {
  // Send POST to /api/esp-device-provision
  HTTPClient http;
  http.begin(PROVISION_URL);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_name"] = DEVICE_NAME;
  doc["device_type"] = "Temperature_Sensor";
  doc["location"] = "Room_101";
  doc["mac_address"] = WiFi.macAddress();
  
  String payload;
  serializeJson(doc, payload);
  
  int httpResponseCode = http.POST(payload);
  // Handle response...
  http.end();
}

void uploadSensorData() {
  // Read sensor
  float temperature = readTemperatureSensor();
  
  // Send POST to /api/esp-sensor-upload
  HTTPClient http;
  http.begin(UPLOAD_URL);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["sensor_type"] = "Temperature";
  doc["reading_value"] = String(temperature) + "°C";
  doc["timestamp"] = getTimestamp();  // ISO 8601 format
  doc["encrypted_data"] = encryptData(String(temperature));
  
  String payload;
  serializeJson(doc, payload);
  
  int httpResponseCode = http.POST(payload);
  // Handle response...
  http.end();
}
```

---

## Dashboard Real-time Display

When your ESP device sends data:

### Left Panel - "Connected ESP Devices"
Shows:
- 📡 Device ID with status indicator
- Last seen timestamp
- Latest sensor type and reading value

### Right Panel - "Latest Received Packets & Hashes"
Shows:
- 📦 Device ID
- **Hash**: SHA256 hash of the received packet (first 40 characters)
- **Encrypted Payload**: The encrypted data payload sent
- **Timestamp**: When the packet was received

---

## Example cURL Commands for Testing

### 1. Provision Device
```bash
curl -X POST http://localhost:5000/api/esp-device-provision \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_TEST_001",
    "device_name": "Test Device",
    "device_type": "Temperature_Sensor",
    "location": "Lab",
    "mac_address": "AA:BB:CC:DD:EE:FF"
  }'
```

### 2. Upload Sensor Data
```bash
curl -X POST http://localhost:5000/api/esp-sensor-upload \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_TEST_001",
    "sensor_type": "Temperature",
    "reading_value": "25.5°C",
    "timestamp": "2026-02-04T22:33:45.123456",
    "encrypted_data": "ENCRYPTED_PAYLOAD_STRING"
  }'
```

### 3. Get All Connected Devices
```bash
curl http://localhost:5000/api/esp-devices
```

### 4. Get Specific Device Status
```bash
curl http://localhost:5000/api/esp-devices/ESP32_TEST_001
```

---

## Summary Table

| Purpose | Endpoint | Method | Required Fields | When to Call |
|---------|----------|--------|-----------------|--------------|
| **Provision Device** | `/api/esp-device-provision` | POST | device_id | Once at startup |
| **Send Sensor Data** | `/api/esp-sensor-upload` | POST | device_id, reading_value | Every 5-60 sec |
| **Get All Devices** | `/api/esp-devices` | GET | None | Optional (monitoring) |
| **Get Device Status** | `/api/esp-devices/<device_id>` | GET | None | Optional (monitoring) |

---

## Error Handling

**If device_id not found (404)**:
- Device has not been provisioned yet
- Call `/api/esp-device-provision` first

**If request fails (500)**:
- Check that dashboard is running
- Verify gateway IP and port are correct
- Ensure JSON format is valid

**If data hash missing**:
- The hash is calculated from: `sensor_type:reading_value:timestamp`
- Automatically generated server-side on receipt
