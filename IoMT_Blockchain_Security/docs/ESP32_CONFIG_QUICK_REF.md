# ESP32 Configuration - Quick Reference

## 5-Minute Setup

### 1️⃣ Install Tools
```bash
pip install esptool adafruit-ampy
```

### 2️⃣ Flash MicroPython
```bash
# Download: https://micropython.org/download/esp32/
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 esp32-*.bin
```

### 3️⃣ Configure (IMPORTANT!)
Edit `esp32_firmware.py` line 30-40:

```python
# YOUR WIFI
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourPassword"

# YOUR PC IP (run: ipconfig)
GATEWAY_IP = "192.168.1.100"  # <- CHANGE THIS!

# DEVICE NAME
DEVICE_ID = "ESP32_MONITOR_001"
```

### 4️⃣ Upload
```bash
ampy --port COM3 put esp32_firmware.py main.py
```

### 5️⃣ Check It Works
```bash
# Open serial monitor at 115200 baud
# Or run:
screen /dev/ttyUSB0 115200
```

## Find Your PC IP

**Windows:**
```bash
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.100)
```

**Linux/Mac:**
```bash
ifconfig
# Look for inet address (e.g., 192.168.1.100)
```

## Common Issues

| Problem | Fix |
|---------|-----|
| `WiFi Connection Failed` | Check WIFI_SSID and WIFI_PASSWORD spelling |
| `Device not found` | Verify GATEWAY_IP is correct (should be your PC IP) |
| `Provisioning failed` | Make sure dashboard is running on PC |
| `Port COM3 not found` | Change COM3 to your actual port (COM4, COM5, etc.) |
| `ampy: command not found` | Run: `pip install adafruit-ampy` |

## Expected Output

```
[*] 14:32:45 - ESP32 IoT Encrypted Sensor Device
[+] 14:32:45 - WiFi connected! IP: 192.168.1.50
[*] 14:32:46 - Provisioning device...
[+] 14:32:47 - Device provisioned! TX: a1b2c3d4e5f6...
[*] 14:32:47 - Starting sensor loop (5s interval)

[1] Reading: TEMP=37.2C,HR=75,O2=98%,BP=120/80
[+] 14:32:48 - Sent OK - Block 12

[2] Reading: TEMP=37.1C,HR=72,O2=99%,BP=118/78
[+] 14:32:53 - Sent OK - Block 13
```

## Files to Know

| File | Purpose |
|------|---------|
| `esp32_firmware.py` | Main ESP32 code (upload this!) |
| `ESP32_SETUP_GUIDE.md` | Full detailed guide |
| `ESP32_QUICK_START.md` | Quick start guide |

## Ports to Check

```bash
# List available serial ports:

# Windows:
mode

# Linux:
ls /dev/ttyUSB*
ls /dev/ttyACM*

# Mac:
ls /dev/tty.usb*
```

## Test ESP Sensors Real-Time

Keep dashboard running:
```bash
python IoMT_Blockchain_Security/iot_integrated_dashboard.py
```

Visit: http://localhost:5000

Should show real-time sensor data from ESP32!

## Optional: Enable DHT22 Sensor

**Hardware:**
```
ESP32 3.3V ←→ DHT22 VCC
ESP32 GPIO4 ←→ DHT22 DATA
ESP32 GND   ←→ DHT22 GND
```

**Code:**
```python
ENABLE_DHT = True   # Line 45
DHT_PIN = 4         # Line 44
```

## One-Line Uploads

```bash
# Windows
ampy --port COM3 put esp32_firmware.py main.py && echo SUCCESS

# Linux/Mac
ampy --port /dev/ttyUSB0 put esp32_firmware.py main.py && echo SUCCESS
```

## Production Checklist

- [ ] WiFi credentials set correctly
- [ ] Gateway IP matches your PC
- [ ] Dashboard running and accessible
- [ ] Ganache and MongoDB running
- [ ] MicroPython flashed to ESP32
- [ ] Firmware uploaded as main.py
- [ ] Serial output shows successful WiFi connection
- [ ] Sensor data appearing on dashboard
- [ ] Blockchain verification showing "Active"
- [ ] Real-time updates every 5 seconds

## Support Commands

```bash
# Erase ESP completely
esptool.py --chip esp32 --port COM3 erase_flash

# Check connection
esptool.py --chip esp32 --port COM3 flash_id

# Reset ESP
ampy --port COM3 reset

# Delete firmware
ampy --port COM3 rm main.py
```

## Performance Tips

Reduce readings for battery:
```python
SENSOR_READ_INTERVAL = 60  # Every minute
```

Increase readings for real-time:
```python
SENSOR_READ_INTERVAL = 1   # Every second
```

Balance for production:
```python
SENSOR_READ_INTERVAL = 30  # Every 30 seconds
```
