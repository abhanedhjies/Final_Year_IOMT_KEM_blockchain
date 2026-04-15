# Arduino IDE Setup Guide for ESP32

## Step 1: Install Arduino IDE

Download from: https://www.arduino.cc/en/software

Choose your OS (Windows, Mac, Linux) and install.

## Step 2: Add ESP32 Board Support

1. Open **Arduino IDE**
2. Go to **File → Preferences**
3. Find "Additional Board Manager URLs"
4. Paste this URL:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
5. Click OK
6. Go to **Tools → Board Manager**
7. Search for "ESP32"
8. Click **Install** (Espressif Systems ESP32)
9. Wait for installation (2-3 minutes)

## Step 3: Install Required Libraries

1. Go to **Sketch → Include Library → Manage Libraries**
2. Search and install these (click Install on each):
   - **ArduinoJson** (by Benoit Blanchon) - v6.20.0 or latest
   - Others are built-in with ESP32

## Step 4: Configure Arduino IDE

1. **Tools → Board** → Select **ESP32 Dev Module**
2. **Tools → Upload Speed** → Select **921600**
3. **Tools → CPU Frequency** → Select **80 MHz**
4. **Tools → Flash Size** → Select **4MB**
5. **Tools → Partition Scheme** → Select **Default 4MB with spiffs**

## Step 5: Connect ESP32 to Computer

1. Connect ESP32 via USB cable
2. Go to **Tools → Port** → Select **COM3** (or your port)
   - On Windows: COM3, COM4, COM5, etc.
   - On Linux: /dev/ttyUSB0
   - On Mac: /dev/cu.SLAB_USBtoUART

## Step 6: Upload the Code

1. Copy code from `ESP32_Arduino_Firmware.ino`
2. Open **Arduino IDE** → New Sketch
3. **Paste the entire code**
4. **Edit these lines (REQUIRED):**
   ```cpp
   const char* WIFI_SSID = "YOUR_WIFI_NAME";           // Line 45
   const char* WIFI_PASSWORD = "YOUR_PASSWORD";        // Line 46
   const char* GATEWAY_IP = "192.168.1.100";          // Line 49 (YOUR PC IP!)
   ```
5. Click **Sketch → Upload** (or Ctrl+U)

## Step 7: Monitor Serial Output

1. Go to **Tools → Serial Monitor** (or Ctrl+Shift+M)
2. Set Baud Rate to **115200**
3. Press **Reset button on ESP32**
4. Watch for output like:

```
ESP32 IoT Encrypted Sensor Device
Connecting to WiFi...
WiFi connected! IP: 192.168.1.50
Provisioning device with gateway...
Device provisioned! TX: a1b2c3d4e5f6...
Starting sensor loop

[1] Reading: T=37.2C, HR=75, O2=98%, BP=123/70
  [+] Encrypted & Verified - Block 12, TX: abc123def...

[2] Reading: T=37.8C, HR=72, O2=97%, BP=120/75
  [+] Encrypted & Verified - Block 13, TX: def456abc...
```

## Finding Your PC IP Address

**Windows:**
```bash
ipconfig
# Look for IPv4 Address under your WiFi network
# Example: 192.168.1.100
```

**Linux/Mac:**
```bash
ifconfig
# Look for inet address
# Example: 192.168.1.100
```

## Common Issues & Solutions

### "board 'esp32' not found"
- Arduino IDE doesn't recognize ESP32
- **Fix:** Re-install ESP32 board (Step 2)

### "Port not showing in Tools → Port"
- USB drivers missing
- **Fix:** Download and install CH340 drivers from:
  https://www.wemos.cc/en/latest/ch340_driver.html

### Upload fails with "Failed uploading"
1. Try holding **GPIO0 button** while uploading
2. Try different USB cable
3. Try different USB port
4. Change Upload Speed to **115200** (slower)

### "WiFi connection failed"
- Wrong WiFi credentials
- **Fix:** Double-check WIFI_SSID and WIFI_PASSWORD (exact spelling!)

### "Provisioning failed: HTTP 0"
- Can't reach gateway
- **Fix:** Check GATEWAY_IP is correct
  - Run `ipconfig` on your PC
  - Make sure Python Flask dashboard is running
  - Both on same WiFi network

### "Data not appearing on blockchain"
- Gateway can't process request
- **Fix:** 
  - Check Ganache is running (http://localhost:7545)
  - Check MongoDB is running
  - Check dashboard logs for errors

## Hardware Setup (Optional: DHT22 Temperature Sensor)

If you want to use a real temperature sensor:

**Wiring:**
```
ESP32 Pin 3.3V -----> DHT22 VCC (pin 1)
ESP32 Pin GPIO4 ----> DHT22 DATA (pin 2)
ESP32 Pin GND ------> DHT22 GND (pin 4)
```

**Enable in code (line 57):**
```cpp
const bool ENABLE_DHT = true;  // Change false to true
```

## Verification Checklist

- [ ] Arduino IDE installed
- [ ] ESP32 board support added
- [ ] ArduinoJson library installed
- [ ] ESP32 connected to USB
- [ ] Port selected (COM3 or /dev/ttyUSB0)
- [ ] WIFI_SSID and WIFI_PASSWORD updated
- [ ] GATEWAY_IP updated to your PC IP
- [ ] Code uploaded successfully
- [ ] Serial Monitor shows output
- [ ] WiFi connection successful
- [ ] Device provisioned to blockchain
- [ ] Sensor readings appearing on dashboard
- [ ] Blockchain blocks increasing

## Dashboard Integration

Once ESP32 is sending data:

1. Open your browser
2. Go to: http://your-pc-ip:5000
3. You should see:
   - Real-time sensor readings from ESP32
   - Blockchain verification status
   - Encrypted data logs
   - Device statistics

## Next Steps

1. **Real Sensors:** Add DHT22, DS18B20, or other I2C sensors
2. **HTTPS:** Enable SSL encryption for gateway communication
3. **Battery:** Power ESP32 from battery and optimize sleep modes
4. **Multiple Devices:** Register and run multiple ESP32s
5. **Cloud:** Deploy dashboard to AWS/Azure for remote access

## Support Commands

**Reset ESP32 remotely:**
```cpp
// Add to loop() in code:
if (WiFi.isConnected()) {
  // Check for OTA updates
}
```

**View all logs:**
```
Serial Monitor shows all device activity
Copy and paste into text file for debugging
```

**Restart dashboard:**
```bash
# Windows PowerShell
taskkill /F /IM python.exe
python IoMT_Blockchain_Security/iot_integrated_dashboard.py
```

---

**Questions?** Check the troubleshooting section in the .ino file!
