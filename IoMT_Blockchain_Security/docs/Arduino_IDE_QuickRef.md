# Arduino IDE - 5 Minute Quick Start

## 1️⃣ Install Arduino IDE
Download: https://www.arduino.cc/en/software

## 2️⃣ Add ESP32 Board (1 minute)
```
File → Preferences
Add Board URL:
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

Tools → Board Manager → Search "ESP32" → Install
```

## 3️⃣ Install Library (30 seconds)
```
Sketch → Include Library → Manage Libraries
Search: ArduinoJson
Click Install
```

## 4️⃣ Configure Board (1 minute)
```
Tools → Board: ESP32 Dev Module
Tools → Upload Speed: 921600
Tools → CPU Frequency: 80 MHz
Tools → Port: COM3 (or your port)
```

## 5️⃣ Get Your PC IP (1 minute)
**Windows:**
```bash
ipconfig
# Find: IPv4 Address = 192.168.1.100 (example)
```

**Linux/Mac:**
```bash
ifconfig
# Find: inet 192.168.1.100 (example)
```

## 6️⃣ Edit Code (1 minute)
Open `ESP32_Arduino_Firmware.ino` and change:

```cpp
// Line 45
const char* WIFI_SSID = "YourWiFiName";

// Line 46  
const char* WIFI_PASSWORD = "YourPassword";

// Line 49 - IMPORTANT! Use YOUR PC IP
const char* GATEWAY_IP = "192.168.1.100";
```

## 7️⃣ Upload (2 minutes)
1. Connect ESP32 via USB
2. Copy code into Arduino IDE
3. Click **Upload** (Ctrl+U)
4. Wait for "Upload Complete"

## 8️⃣ Monitor Output (1 minute)
```
Tools → Serial Monitor
Set Baud: 115200
Press Reset on ESP32
Watch the output!
```

## Expected Output
```
ESP32 IoT Encrypted Sensor Device
Connecting to WiFi...
[+] WiFi connected! IP: 192.168.1.50
Provisioning device with gateway...
[+] Device provisioned! TX: a1b2c3d4e5f6...

[1] Reading: T=37.2C, HR=75, O2=98%
  [+] Encrypted & Verified - Block 12, TX: abc123...
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port not showing | Install CH340 drivers: https://www.wemos.cc/en/latest/ch340_driver.html |
| "esp32 not found" | Re-install ESP32 board support |
| Upload fails | Try lower baud rate (115200) or hold GPIO0 button |
| WiFi fails | Check SSID/password spelling (exact match!) |
| Can't connect to gateway | Verify GATEWAY_IP matches your PC IP |
| No data on blockchain | Check Ganache, MongoDB, and dashboard running |

## One-Liner Setup

1. Download: https://www.arduino.cc/en/software
2. Install it
3. Add board URL + install ESP32 board
4. Install ArduinoJson library
5. Copy code from `ESP32_Arduino_Firmware.ino`
6. Change WiFi + Gateway IP
7. Upload
8. Done!

## Key Code Lines to Edit

**CRITICAL - Must Change These:**
- Line 45: Your WiFi name
- Line 46: Your WiFi password  
- Line 49: **Your PC IP address** (find with ipconfig)

**Optional - Can Customize:**
- Line 47: Device name
- Line 48: Device location
- Line 56: Reading interval (seconds)
- Line 57: Enable DHT22 sensor (true/false)

## Testing

After upload:

1. **Serial Monitor** shows device output
2. **Dashboard** shows real-time data at http://your-pc-ip:5000
3. **Blockchain** shows new blocks and TX hashes
4. **MongoDB** stores all encrypted readings

## Multiple ESP32s

Can run on same network! Each gets unique:
- Device ID (auto-generated)
- Blockchain TX hash
- Encryption keys

Just change DEVICE_ID (line 47) for each ESP32.

## Files You Need

- `ESP32_Arduino_Firmware.ino` ← Copy this entire code
- `Arduino_IDE_Setup.md` ← Full setup guide
- `Arduino_IDE_QuickRef.md` ← This file

## Next Steps

1. Flash firmware to ESP32
2. Monitor Serial output
3. View encrypted data on dashboard
4. Verify blockchain transactions
5. Add real sensors (DHT22, BMP280, etc.)
6. Deploy to production!

---

**Total Setup Time: ~10 minutes**
