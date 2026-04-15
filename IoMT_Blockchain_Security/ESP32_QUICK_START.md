# ESP32 Quick Start Guide - Encrypted IoT Device

## What You Need

1. **ESP32 Development Board** (€5-10)
2. **USB Cable** (Micro USB)
3. **Python 3.6+** on your PC
4. **WiFi Network**
5. **Ganache + MongoDB + Dashboard running**

## Step 1: Install Tools on Your PC

### Windows
```bash
# Install Python tools
pip install esptool
pip install adafruit-ampy

# Verify installation
esptool.py version
ampy --help
```

### Linux/Mac
```bash
pip3 install esptool adafruit-ampy
```

## Step 2: Flash MicroPython to ESP32

### Download MicroPython
1. Go to: https://micropython.org/download/esp32/
2. Download latest `.bin` file (e.g., `esp32-20240105.bin`)

### Flash the Firmware
```bash
# On Windows (change COM3 to your port)
esptool.py --chip esp32 --port COM3 --baud 460800 write_flash -z 0x1000 esp32-20240105.bin

# On Linux/Mac
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 esp32-20240105.bin
```

## Step 3: Configure ESP Firmware

### Edit esp32_firmware.py

Change these lines to match YOUR setup:

```python
# === CHANGE THESE ===

# Your WiFi credentials
WIFI_SSID = "YOUR_WIFI_NAME"           # Your WiFi network name
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"   # Your WiFi password

# Your PC IP address (found with ipconfig or ifconfig)
GATEWAY_URL = "http://192.168.1.100:5000"  # Change 192.168.1.100 to YOUR PC IP

# Device name (can be anything)
DEVICE_ID = "ESP32_SENSOR_LAB_001"

# === OPTIONAL ===
SENSOR_READ_INTERVAL = 5  # Seconds between readings (5-60)
```

### Find Your PC IP Address

**Windows:**
```bash
ipconfig
# Look for IPv4 Address under WiFi adapter
# Example: 192.168.1.100
```

**Linux/Mac:**
```bash
ifconfig
# or
ip addr show
# Look for inet under WiFi interface
```

### Example Configuration
```python
WIFI_SSID = "HomeWiFi"
WIFI_PASSWORD = "MyPassword123"
GATEWAY_URL = "http://192.168.1.105:5000"
DEVICE_ID = "ESP32_PATIENT_MONITOR"
SENSOR_READ_INTERVAL = 5
```

## Step 4: Upload to ESP32

```bash
# Connect ESP32 via USB

# Upload the firmware
ampy --port COM3 put esp32_firmware.py main.py

# Verify it's there
ampy --port COM3 ls
# Output should show: main.py
```

## Step 5: Connect and Test

### Start Dashboard First
```bash
cd journal_IOT_Blockchain
python IoMT_Blockchain_Security/iot_integrated_dashboard.py
```

Wait for:
```
[+] Connected to Ganache blockchain
[+] Contract loaded at: 0x8e31C82d...
[+] Application created
* Running on http://127.0.0.1:5000
```

### Power On ESP32

1. Connect ESP32 via USB
2. Open serial monitor (optional, for debugging):

**Option 1: Using esptool**
```bash
esptool.py --port COM3 --baud 115200 read_flash
```

**Option 2: Using Python**
```bash
python
>>> import serial
>>> ser = serial.Serial('COM3', 115200, timeout=1)
>>> while True:
...     print(ser.readline().decode())
```

**Option 3: Using PuTTY**
- Set Port: COM3
- Speed: 115200
- Connection Type: Serial
- Click Open

### Expected Output
```
============================================================
ESP32 IoT Device - Encrypted Sensor Uploader
============================================================
Device ID: ESP32_SENSOR_LAB_001
Gateway URL: http://192.168.1.100:5000
============================================================

[+] WiFi Connected: 192.168.1.50
[*] Provisioning device with gateway...
[+] Device provisioned successfully
[*] Starting sensor reading loop...

[1] 14:32:45 - Reading: TEMP=37.2C,HR=75,O2=98%,BP=120/80
    Status: SENT TO GATEWAY

[2] 14:32:50 - Reading: TEMP=37.1C,HR=72,O2=99%,BP=118/78
    Status: SENT TO GATEWAY
```

## Step 6: View on Dashboard

Open browser: http://localhost:5000

You should see:
- ESP32_SENSOR_LAB_001 in device list
- Real-time sensor readings
- Blockchain verification
- Encrypted payload details

## Troubleshooting

### ESP not connecting to WiFi
```python
# Problem: Wrong SSID/password
# Solution: Double-check WiFi name and password

WIFI_SSID = "YourWiFi"       # Make sure this matches exactly
WIFI_PASSWORD = "YourPass"   # Case-sensitive!
```

### ESP can't reach gateway
```python
# Problem: Wrong IP address
# Solution: Check PC IP again

# On PC, run:
ipconfig  # Windows
ifconfig  # Linux/Mac

# Update ESP:
GATEWAY_URL = "http://192.168.1.XXX:5000"
```

### "Device not found" error on dashboard
- Make sure dashboard is running
- Check WiFi connection on ESP
- Verify gateway URL is correct
- Restart ESP

### ESP keeps disconnecting
- Move ESP closer to WiFi router
- Check if WiFi is 2.4GHz (ESP8266/32 don't support 5GHz)
- Try different SENSOR_READ_INTERVAL (increase if unstable)

## Files Explained

### esp32_firmware.py (Main Code)
```
Lines 1-50:      Configuration (change these!)
Lines 51-100:    WiFi connection
Lines 101-150:   Sensor data generation
Lines 151-200:   Device provisioning
Lines 201-250:   Sending encrypted data
Lines 251-300:   Main loop
```

### What Happens On Startup
1. **Connect to WiFi** → Shows IP address
2. **Provision with Gateway** → Gets encryption keys
3. **Register to Blockchain** → Gets registered to Ganache
4. **Start Reading Loop** → Sends sensor data every 5 seconds

### Data Flow
```
ESP32 Device
   ↓
Generate Random Sensor Data (TEMP, HR, O2, BP)
   ↓
Create Plaintext Payload
   ↓
Encrypt with Session Key
   ↓
Send HTTP POST to Gateway
   ↓
Gateway
   ↓
Decrypt Using Device Keys
   ↓
Verify on Blockchain
   ↓
Store in MongoDB
   ↓
Display on Dashboard
```

## Real Sensor Integration (Optional)

### DHT22 Temperature/Humidity

**Wiring:**
```
DHT22 Pin Layout:
1 - VCC (3.3V)
2 - DATA (GPIO4)
3 - NC
4 - GND

ESP32 Pinout:
3.3V ← DHT22 VCC
GPIO4 ← DHT22 DATA (with 4.7k pullup)
GND ← DHT22 GND
```

**Enable in Firmware:**
```python
# Uncomment this line:
DHT_PIN = 4  # GPIO4

# The firmware will auto-detect DHT22 and use real data
```

### DS18B20 Temperature Only

**Wiring:**
```
DS18B20 (Waterproof):
1 - GND (Black)
2 - DATA (Yellow) → GPIO5 with 4.7k pullup
3 - VCC (Red) → 3.3V
```

**Enable in Firmware:**
```python
# Add to configuration:
ONEWIRE_PIN = 5  # GPIO5
```

## Performance Tuning

### Reduce Power Consumption
```python
SENSOR_READ_INTERVAL = 60  # Send every 60 seconds instead of 5
```

### Faster Response
```python
SENSOR_READ_INTERVAL = 1   # Send every second
```

### Stable for Production
```python
SENSOR_READ_INTERVAL = 30  # Balance between updates and battery
```

## Security Notes

### Current Implementation
- Uses simple encryption for demo
- HTTP (not HTTPS)
- Credentials in code

### For Production
1. Use HTTPS/TLS
2. Store credentials in secure storage
3. Implement certificate pinning
4. Use Hardware Security Module (HSM)
5. Regular firmware updates

## Complete Configuration Example

```python
# esp32_firmware.py - COMPLETE SETUP

import machine
import ubinascii
import urequests
import ujson
import utime
import urandom
from ubinascii import hexlify

# ============ CONFIGURATION ============
DEVICE_ID = "ESP32_HOSPITAL_ICU_01"
DEVICE_NAME = "Patient Monitor - Room 101"
DEVICE_TYPE = "Biometric_Sensor"
LOCATION = "ICU_Ward_A"

# WiFi Configuration
WIFI_SSID = "HospitalWiFi"
WIFI_PASSWORD = "SecurePassword123"

# Gateway Configuration
GATEWAY_URL = "http://192.168.1.50:5000"
PROVISIONING_URL = f"{GATEWAY_URL}/api/esp-device-provision"
SENSOR_UPLOAD_URL = f"{GATEWAY_URL}/api/esp-sensor-upload"

# Sensor Configuration
SENSOR_READ_INTERVAL = 10  # 10 seconds between readings
DHT_PIN = 4  # GPIO4 for DHT sensor

# [REST OF CODE - see esp32_firmware.py]
```

## Testing Without Real ESP32

Use the included test script:
```bash
cd IoMT_Blockchain_Security
python
>>> import requests
>>> requests.post('http://localhost:5000/api/esp-device-provision', json={
...     'device_id': 'SIMULATED_ESP_001',
...     'device_name': 'Virtual Device',
...     'device_type': 'Sensor',
...     'location': 'Lab',
...     'mac_address': 'aabbccddeeff'
... }).json()
```

## Next Steps

1. ✓ Install tools (esptool, ampy)
2. ✓ Flash MicroPython
3. ✓ Configure WiFi and gateway IP
4. ✓ Upload firmware
5. ✓ Power on ESP32
6. ✓ Check dashboard for real-time data
7. ✓ Optional: Connect real DHT sensor
8. ✓ Monitor blockchain verification

## Support

If something doesn't work:
1. Check ESP serial output
2. Verify WiFi credentials
3. Confirm gateway URL is correct
4. Restart dashboard
5. Re-flash ESP if needed

Questions? Check the full guide: `docs/ESP32_SETUP_GUIDE.md`
