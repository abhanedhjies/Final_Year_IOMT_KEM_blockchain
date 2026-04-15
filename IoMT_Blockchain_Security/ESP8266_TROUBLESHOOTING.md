# ESP8266 "Send Failed" - Troubleshooting Guide

## Common Issues & Solutions

### 1. **Dashboard Not Running**
**Symptom**: "Send failed" immediately on every request

**Check**:
```bash
# Terminal 1: Check if dashboard is running
curl http://10.73.161.229:5000/api/esp-devices
```

**Solution**:
```bash
# In the project folder, start dashboard:
python iot_integrated_dashboard.py
```

You should see:
```
[+] Dashboard: http://localhost:5000
[*] Running on http://10.73.161.229:5000
```

---

### 2. **Provisioning Failed (Device Not Found Error)**
**Symptom**: First request works, but subsequent sends return 404

**Cause**: Device was provisioned but data persists differently

**Solution**: Check if device exists in dashboard:
```bash
curl http://10.73.161.229:5000/api/esp-devices
```

If empty, manually create device first:
```bash
curl -X POST http://10.73.161.229:5000/api/create-device \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP8266_BIOMETRIC_SENSOR_001",
    "device_type": "Biometric_IoT"
  }'

# Then register to blockchain:
curl -X POST http://10.73.161.229:5000/api/register-blockchain \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP8266_BIOMETRIC_SENSOR_001",
    "gateway_id": "GATEWAY_HUB_001"
  }'
```

---

### 3. **Timeout Issues (HTTP Response: 0)**
**Symptom**: No HTTP response code, connection times out

**Cause**: 
- Gateway IP unreachable
- WiFi network issues
- HTTP request too large

**Solution**:
```
1. Verify gateway IP is correct:
   - Your PC IP: 10.73.161.229 ✓
   - Dashboard running on: 0.0.0.0:5000 ✓

2. Test from ESP serial monitor:
   - Should show: "Sending to: http://10.73.161.229:5000/api/esp-sensor-upload"
   
3. Reduce JSON payload size if needed
```

---

### 4. **JSON Parse Error**
**Symptom**: Dashboard receives request but returns error

**Check ESP8266 output**:
```
[D] Upload payload size: X bytes
[D] Response: {"error": "..."}
```

**Solution**: Verify JSON format matches expected fields:
```json
{
  "device_id": "ESP8266_BIOMETRIC_SENSOR_001",
  "sensor_type": "Biometric",
  "reading_value": "{full JSON here}",
  "iv": "hex_string",
  "timestamp": 1707081225,
  "location": "Hospital_Room_101",
  "encrypted_data": "IV_hex_string"
}
```

---

### 5. **WiFi Connected but Send Fails**
**Symptom**: WiFi shows connected, but HTTP requests fail

**Check ESP8266 output**:
```
[+] Connected to: 192.168.x.x
[D] HTTP Response Code: -1 or 0
```

**Solutions**:
```cpp
// A) Increase HTTP timeout
const int HTTP_TIMEOUT = 30000;  // 30 seconds instead of 10

// B) Check gateway connectivity
// Add this to setup():
HTTPClient http;
http.begin(client, "http://10.73.161.229:5000/api/esp-devices");
int code = http.GET();
Serial.println("Gateway ping: " + String(code));
```

---

## Debug Steps (In Order)

### Step 1: Check WiFi
```
Expected output:
[*] Connecting to WiFi...
[+] 192.168.x.x
[+] Connected to: Abhi Realme
```

### Step 2: Check Dashboard URL
```
Expected output:
Provisioning URL: http://10.73.161.229:5000/api/esp-device-provision
Upload URL: http://10.73.161.229:5000/api/esp-sensor-upload
```

### Step 3: Check Provisioning
```
Expected output:
[D] HTTP Response Code: 200
[+] Device provisioned successfully
[+] Device Key: ...
[+] TX Hash: 0x...
[+] Block: 15
```

### Step 4: Check Sensor Upload
```
Expected output:
[D] HTTP Response Code: 200
[+] Data uploaded successfully
[+] Hash: a1b2c3d4e5...
[+] Block: 16
```

### Step 5: Check Dashboard Display
- Open: `http://10.73.161.229:5000`
- Look for "Connected ESP Devices" section
- Should show: `📡 ESP8266_BIOMETRIC_SENSOR_001` with status `🟢 CONNECTED`
- Latest packet in "Latest Received Packets & Hashes" section

---

## If Still Getting "Send Failed"

### Test 1: Manual cURL from PC
```bash
# Create test device
curl -X POST http://10.73.161.229:5000/api/create-device \
  -H "Content-Type: application/json" \
  -d '{"device_id":"ESP8266_TEST","device_type":"Test"}'

# Register to blockchain
curl -X POST http://10.73.161.229:5000/api/register-blockchain \
  -H "Content-Type: application/json" \
  -d '{"device_id":"ESP8266_TEST"}'

# Send test data
curl -X POST http://10.73.161.229:5000/api/esp-sensor-upload \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP8266_TEST",
    "sensor_type": "Test",
    "reading_value": "25.5°C",
    "timestamp": "2026-02-04T22:33:45",
    "encrypted_data": "TEST_DATA"
  }'
```

If this works from PC but fails from ESP8266:
- **Network isolation issue** - check WiFi firewall
- **Packet fragmentation** - reduce JSON payload
- **Slow connection** - increase timeout to 30000ms

### Test 2: Check Firewall
```bash
# On Windows (from CMD)
ping 10.73.161.229

# On Linux/Mac
ping 10.73.161.229
```

Should get responses (not timeout)

### Test 3: Reduce Payload
Try sending minimal data first:
```cpp
StaticJsonDocument<256> minimal;
minimal["device_id"] = DEVICE_ID;
minimal["sensor_type"] = "Test";
minimal["reading_value"] = "25.5";
minimal["timestamp"] = time(nullptr);

String payload;
serializeJson(minimal, payload);
// Send this smaller payload
```

---

## Using the Fixed Firmware

Replace your current code with `ESP8266_Firmware_FIXED_DEBUG.ino` which includes:

✅ Better error handling  
✅ Detailed debug logging (all HTTP codes)  
✅ HTTP timeout configuration  
✅ Provisioning status tracking  
✅ Success/failure statistics  
✅ WiFi status verification  

**Key improvements**:
- Shows actual HTTP response codes
- Prints JSON payloads being sent
- Verifies provisioning before sending data
- Displays stats every 10 reads
- Handles 404 errors (device not found)

---

## Expected Serial Output

```
[D] Provisioning URL: http://10.73.161.229:5000/api/esp-device-provision
[D] Upload URL: http://10.73.161.229:5000/api/esp-sensor-upload
[*] Connecting to WiFi...
[+] 192.168.x.x
[+] Connected to: Abhi Realme
Gateway: http://10.73.161.229:5000

[D] Provisioning device...
[D] HTTP Response Code: 200
[+] Device provisioned successfully
[+] Device Key: shared_secret_key
[+] TX Hash: 0x123abc...
[+] Block: 15

[+] ESP8266 ready

[*] T=36.7 HR=72 O2=98 BP=120/80 RR=16
[D] HTTP Response Code: 200
[+] Data uploaded successfully
[+] Hash: a1b2c3d4e5f6
[+] Block: 16
Block 16

=== STATS ===
Total reads: 10
Success: 10
Failed: 0
Success rate: 100.0%
```

---

## Dashboard Display After Successful Upload

When data arrives, you'll see in the dashboard:

**Connected ESP Devices** panel:
```
📡 ESP8266_BIOMETRIC_SENSOR_001
🟢 CONNECTED
Last Seen: 22:33:45
Sensor: Biometric
Reading: {"temperature":36.7,"heart_rate":72,...}
```

**Latest Received Packets & Hashes** panel:
```
📦 ESP8266_BIOMETRIC_SENSOR_001
Hash: a1b2c3d4e5f6a1b2c3d4e5f6...
Encrypted Payload: IV_a1b2c3d4...
Timestamp: 2026-02-04T22:33:45
```

If you don't see this, the request isn't reaching the server.
