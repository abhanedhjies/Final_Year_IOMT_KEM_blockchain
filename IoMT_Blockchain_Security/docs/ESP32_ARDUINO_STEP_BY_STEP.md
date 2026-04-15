# Arduino IDE - Step-by-Step Guide for ESP32 Programming

## WHAT YOU NEED

- [ ] Arduino IDE (free download)
- [ ] ESP32 Development Board
- [ ] USB Cable (USB-A to Micro-USB)
- [ ] Your WiFi network name & password
- [ ] Your PC's IP address

---

## STEP 1: DOWNLOAD ARDUINO IDE

1. Go to: https://www.arduino.cc/en/software
2. Click Download for your OS (Windows, Mac, Linux)
3. Run installer → Click "Install"
4. Launch Arduino IDE

---

## STEP 2: ADD ESP32 BOARD SUPPORT

**This is CRITICAL - don't skip!**

1. Open Arduino IDE
2. Go to: **File → Preferences**
3. Find the text field labeled "Additional Board Manager URLs"
4. Copy-paste this URL:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
5. Click **OK**
6. Wait 10 seconds for IDE to load
7. Go to: **Tools → Board Manager**
8. Search for: `ESP32`
9. Click on **esp32** by Espressif Systems
10. Click **Install** (green button)
11. Wait 2-3 minutes for installation
12. Close Board Manager

**Verify:** Go to **Tools → Board** and you should see ESP32 options

---

## STEP 3: INSTALL REQUIRED LIBRARY

1. Go to: **Sketch → Include Library → Manage Libraries**
2. Search for: `ArduinoJson`
3. Click on **ArduinoJson** by Benoit Blanchon
4. Click **Install**
5. Wait for installation
6. Close Library Manager

**Verify:** The library is installed and ready

---

## STEP 4: GET YOUR PC IP ADDRESS

**You MUST have this to connect ESP32 to your dashboard!**

### Windows:
1. Open PowerShell or Command Prompt
2. Type: `ipconfig`
3. Look for section with your WiFi network name
4. Find line: **IPv4 Address**
5. Write down the number (example: `192.168.1.100`)

### Linux/Mac:
1. Open Terminal
2. Type: `ifconfig` (or `ip addr` on Linux)
3. Look for `inet` address
4. Write down the number (example: `192.168.1.100`)

**SAVE THIS NUMBER - You'll need it in Step 7!**

---

## STEP 5: CONNECT ESP32 TO COMPUTER

1. Get your USB cable (USB-A to Micro-USB)
2. Connect ESP32 to your computer via USB
3. Wait 5 seconds for drivers to install
4. Go to: **Tools → Port**
5. You should see a new COM port (COM3, COM4, COM5, etc.)
6. Click on it to select it

**If no port appears:**
- Install CH340 driver: https://www.wemos.cc/en/latest/ch340_driver.html
- Restart Arduino IDE
- Try different USB cable
- Try different USB port on computer

---

## STEP 6: CONFIGURE BOARD SETTINGS

1. Go to: **Tools → Board**
2. Select: **ESP32 Dev Module**

3. Go to: **Tools → Upload Speed**
4. Select: **921600**

5. Go to: **Tools → CPU Frequency**
6. Select: **80 MHz**

7. Go to: **Tools → Flash Size**
8. Select: **4MB**

9. Go to: **Tools → Partition Scheme**
10. Select: **Default 4MB with spiffs**

11. Go to: **Tools → Port**
12. Select your COM port (COM3, COM4, etc.)

**Verify:** Check **Tools** menu shows correct settings

---

## STEP 7: COPY AND EDIT THE CODE

1. Open file: `ESP32_Arduino_Firmware.ino`
2. Copy ALL the code (Ctrl+A, Ctrl+C)
3. In Arduino IDE, click: **File → New**
4. A new blank sketch opens
5. Delete all default code
6. Paste the firmware code (Ctrl+V)

**Now EDIT these lines:**

### Line 45 - Your WiFi Name:
```cpp
const char* WIFI_SSID = "YourWiFiName";
```
Replace `YourWiFiName` with your actual WiFi name (keep the quotes!)

Example:
```cpp
const char* WIFI_SSID = "MyHome_WiFi";
```

### Line 46 - Your WiFi Password:
```cpp
const char* WIFI_PASSWORD = "YourWiFiPassword";
```
Replace `YourWiFiPassword` with your actual password (keep the quotes!)

Example:
```cpp
const char* WIFI_PASSWORD = "MyPassword123";
```

### Line 49 - Your PC IP (IMPORTANT!):
```cpp
const char* GATEWAY_IP = "192.168.1.100";
```
Replace `192.168.1.100` with the IP you found in Step 4 (keep the quotes!)

Example:
```cpp
const char* GATEWAY_IP = "192.168.1.50";
```

**VERIFY:** These 3 lines are correct before uploading!

---

## STEP 8: UPLOAD CODE TO ESP32

1. Make sure ESP32 is connected to USB
2. In Arduino IDE, click: **Sketch → Upload** (or press Ctrl+U)
3. Watch the progress bar at the bottom
4. You should see:
   ```
   Connecting...................
   Uploading.......................
   ```
5. Wait for: **Upload complete! (size in bytes)**

**If upload fails:**
- Try holding **BOOT button** on ESP32 while uploading
- Lower Upload Speed to 115200 in Tools
- Try different USB cable
- Check you selected correct Port

---

## STEP 9: MONITOR THE ESP32 OUTPUT

1. After successful upload, go to: **Tools → Serial Monitor** (Ctrl+Shift+M)
2. In the dropdown at bottom right, set Baud Rate to: **115200**
3. Press the **Reset button** on your ESP32 (or unplug/replug USB)
4. Watch the output in Serial Monitor

**You should see:**
```
ESP32 IoT Encrypted Sensor Device
======================================================
Device: ESP32_BIOMETRIC_SENSOR_001
Gateway: http://192.168.1.100:5000
Interval: 5 seconds
======================================================

Connecting to WiFi...
...................
[+] WiFi connected! IP: 192.168.1.50
Provisioning device with gateway...
[+] Device provisioned! TX: a1b2c3d4e5f6...
Starting sensor loop

[1] Reading: T=37.2C, HR=75, O2=98%, BP=123/70
  [+] Encrypted & Verified - Block 12, TX: abc123...

[2] Reading: T=37.8C, HR=72, O2=97%, BP=120/75
  [+] Encrypted & Verified - Block 13, TX: def456...
```

---

## STEP 10: VIEW DATA ON DASHBOARD

1. Open your web browser
2. Go to: `http://192.168.1.100:5000` (use YOUR PC IP)
3. You should see dashboard with:
   - Real-time sensor readings from ESP32
   - Blockchain verification status
   - Encrypted data logs
   - Device statistics

**Success!** Your ESP32 is now sending encrypted data to the blockchain!

---

## QUICK CHECKLIST

- [ ] Arduino IDE installed
- [ ] ESP32 board added to Arduino IDE
- [ ] ArduinoJson library installed
- [ ] ESP32 connected to USB
- [ ] Serial port selected in Tools
- [ ] WIFI_SSID changed to your WiFi name
- [ ] WIFI_PASSWORD changed to your password
- [ ] GATEWAY_IP changed to your PC IP
- [ ] Code uploaded successfully
- [ ] Serial Monitor shows output
- [ ] WiFi connection successful
- [ ] Device provisioned message appeared
- [ ] Sensor readings showing in Serial Monitor
- [ ] Dashboard shows real-time data
- [ ] Blockchain blocks increasing

---

## TROUBLESHOOTING

### "No serial port in Tools → Port"
```
Solution:
1. Install CH340 driver
2. Restart Arduino IDE
3. Try different USB cable
4. Try different USB port on computer
```

### "Upload failed" or "Permission denied"
```
Solution:
1. Hold BOOT button while uploading
2. Change Upload Speed to 115200
3. Close Serial Monitor (if open)
4. Restart Arduino IDE
```

### "WiFi connection failed"
```
Solution:
1. Check WIFI_SSID spelling (must be EXACT)
2. Check WIFI_PASSWORD is correct
3. ESP32 must support 2.4GHz (not 5GHz)
4. Router must be powered on
```

### "Provisioning failed: HTTP 0"
```
Solution:
1. Check GATEWAY_IP is correct (run ipconfig)
2. Make sure dashboard is running:
   python IoMT_Blockchain_Security/iot_integrated_dashboard.py
3. ESP32 and PC must be on same WiFi network
4. Check firewall isn't blocking port 5000
```

### "Data not appearing on blockchain"
```
Solution:
1. Check Ganache is running
2. Check MongoDB is running
3. Check dashboard logs for errors
4. Verify contract address is correct
```

### "esp32 board not found"
```
Solution:
1. Re-do Step 2 (Add ESP32 board support)
2. Make sure Board Manager has ESP32
3. Restart Arduino IDE
4. Try installing again
```

---

## WHAT'S HAPPENING BEHIND THE SCENES

1. **ESP32 generates** random biometric data (temperature, heart rate, etc.)
2. **ESP32 encrypts** the data using AES-256-CBC (locally)
3. **ESP32 sends** encrypted data to Python dashboard via WiFi
4. **Dashboard receives** encrypted data
5. **Dashboard decrypts** it using stored encryption key
6. **Dashboard registers** on blockchain and stores encrypted logs
7. **Dashboard returns** block number and transaction hash
8. **ESP32 displays** success message with blockchain verification
9. **Process repeats** every 5 seconds

---

## NEXT STEPS AFTER SUCCESSFUL CONNECTION

1. **Add Real Sensor:** Connect DHT22 temperature sensor to GPIO4
2. **Multiple ESP32s:** Flash same code to multiple boards with different DEVICE_IDs
3. **Production Settings:** Increase upload interval to 30-60 seconds to save battery
4. **Monitor Dashboard:** View all encrypted readings on http://your-pc-ip:5000
5. **Deploy to Cloud:** Move Python dashboard to AWS/Azure for remote access

---

## EXAMPLE SETUP SUMMARY

```
Your PC:
- WiFi IP: 192.168.1.100
- Dashboard: http://192.168.1.100:5000
- Ganache: Running locally
- MongoDB: Running locally

Your ESP32:
- Device ID: ESP32_BIOMETRIC_SENSOR_001
- WiFi SSID: MyHome_WiFi
- Gateway IP: 192.168.1.100
- Sensor Interval: 5 seconds

Data Flow:
ESP32 (WiFi) → Dashboard (http:5000) → Blockchain (Ganache) → MongoDB
```

---

## KEEP THESE NUMBERS SAFE

**Your PC IP:** _______________________

**Your WiFi SSID:** _______________________

**Your WiFi Password:** _______________________

**ESP32 Device ID:** ESP32_BIOMETRIC_SENSOR_001

**Dashboard URL:** http://_______________________:5000

---

## SUCCESS INDICATORS

- Serial Monitor shows WiFi connected message
- Serial Monitor shows "Device provisioned!" message
- Serial Monitor shows "Encrypted & Verified" for each reading
- Dashboard shows real-time sensor readings
- Blockchain block number increases
- No errors in Serial Monitor
- Data persists in MongoDB

---

**Questions?** Check the troubleshooting section above or the detailed guides in the docs folder.
