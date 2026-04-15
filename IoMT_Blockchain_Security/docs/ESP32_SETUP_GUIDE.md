# ESP32/ESP8266 IoT Device Setup Guide

This guide shows how to set up a real ESP32/ESP8266 microcontroller to connect to the IoT Blockchain dashboard and send encrypted sensor readings.

## Hardware Requirements

- **ESP32** or **ESP8266** microcontroller
- USB cable for programming
- Optional: DHT22 temperature/humidity sensor
- WiFi network access

## Software Requirements

- Python 3.6+
- MicroPython firmware for ESP32
- esptool.py for flashing

## Step 1: Flash MicroPython to ESP32

### 1.1 Install esptool
```bash
pip install esptool
```

### 1.2 Download MicroPython
- ESP32: https://micropython.org/download/esp32/
- ESP8266: https://micropython.org/download/esp8266/

### 1.3 Flash the firmware
For ESP32:
```bash
esptool.py --chip esp32 --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 esp32-*.bin
```

For ESP8266:
```bash
esptool.py --chip esp8266 --port COM3 erase_flash
esptool.py --chip esp8266 --port COM3 write_flash -z 0x00000 esp8266-*.bin
```

Note: Change `COM3` to your serial port (Linux: `/dev/ttyUSB0`, Mac: `/dev/tty.usbserial-*`)

## Step 2: Upload Firmware Script

### 2.1 Install Ampy (MicroPython file tool)
```bash
pip install adafruit-ampy
```

### 2.2 Upload the ESP firmware
```bash
ampy --port COM3 put esp32_firmware.py main.py
```

### 2.3 Connect via REPL (optional - for testing)
```bash
screen /dev/ttyUSB0 115200
# or on Windows: use PuTTY set to COM3, 115200 baud
```

## Step 3: Configure ESP Firmware

Edit `esp32_firmware.py` before uploading:

```python
# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Gateway Configuration
GATEWAY_URL = "http://192.168.1.100:5000"  # Change to your PC/server IP

# Device Configuration
DEVICE_ID = "ESP32_SENSOR_001"
DEVICE_NAME = "ESP32 Temperature Sensor"
DEVICE_TYPE = "IoT_Sensor"
LOCATION = "Lab_Setup"
```

## Step 4: Find Your PC/Server IP

The ESP needs to know your PC's IP address where the dashboard is running.

### Windows
```bash
ipconfig
# Look for "IPv4 Address" under your WiFi adapter (e.g., 192.168.1.100)
```

### Linux/Mac
```bash
ifconfig
# or
ip addr
# Look for inet address on your WiFi interface (e.g., 192.168.1.100)
```

Update `GATEWAY_URL` in the ESP firmware with this IP address.

## Step 5: Start the Dashboard

```bash
cd IoMT_Blockchain_Security
python iot_integrated_dashboard.py
```

Make sure:
- Ganache blockchain is running (localhost:7545)
- MongoDB is running (localhost:27017)
- Dashboard is accessible at http://localhost:5000

## Step 6: Power On ESP32

1. Connect ESP32 to power or USB
2. The ESP will:
   - Connect to WiFi
   - Provision itself with the dashboard
   - Register to the blockchain
   - Start sending random sensor readings every 5 seconds

### Expected Output
```
============================================================
ESP32 IoT Device - Encrypted Sensor Uploader
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

## Step 7: View Real-Time Data on Dashboard

1. Open http://localhost:5000 in browser
2. Go to "Real-Time Devices" section
3. Select the ESP device (ESP32_SENSOR_001)
4. Watch live sensor readings and encrypted data
5. Check "Blockchain" tab to see device registration

## Troubleshooting

### ESP not connecting to WiFi
- Check WIFI_SSID and WIFI_PASSWORD
- Verify WiFi is 2.4GHz (ESP8266 doesn't support 5GHz)
- Check signal strength near ESP

### ESP can't reach gateway
- Verify GATEWAY_URL IP address with `ipconfig`
- Make sure PC and ESP are on same WiFi network
- Check Windows Firewall allows port 5000
- Run dashboard with: `python iot_integrated_dashboard.py`

### Device not showing on dashboard
- Check ESP serial output for errors
- Verify MongoDB is running
- Restart dashboard: `Ctrl+C` then start again

### Blockchain registration fails
- Verify Ganache is running at localhost:7545
- Check Ganache has ETH in deployer account
- Restart Ganache and dashboard

## Optional: Connect Real DHT Sensor

1. Connect DHT22:
   - VCC → 3.3V
   - GND → GND
   - DATA → GPIO4

2. Uncomment in firmware:
```python
DHT_PIN = 4  # GPIO4
```

The ESP will now read real temperature/humidity instead of random values.

## Network Diagram

```
┌──────────────────┐
│   ESP32 Device   │
│  (WiFi enabled)  │
└────────┬─────────┘
         │ WiFi
         │ (192.168.1.50)
         │
    ┌────▼─────────────────┐
    │   WiFi Router        │
    └────┬─────────────────┘
         │ Ethernet/WiFi
         │ (192.168.1.100)
         │
    ┌────▼──────────────────────────┐
    │  PC Running Dashboard          │
    │  - Flask (http://0.0.0.0:5000)│
    │  - MongoDB (localhost:27017)   │
    │  - Ganache (localhost:7545)    │
    └───────────────────────────────┘
```

## Data Flow

1. **ESP generates sensor data** → Random temperature, heart rate, etc.
2. **ESP encrypts data** → Kyber-inspired KEM + AES-256-CBC + HMAC
3. **ESP sends encrypted payload** → HTTP POST to gateway
4. **Gateway receives** → `/api/esp-sensor-upload`
5. **Gateway decrypts** → Uses stored device keys
6. **Gateway verifies** → Checks blockchain registration
7. **Dashboard displays** → Real-time sensor data in UI
8. **Data logged** → MongoDB audit trail

## API Endpoints Used by ESP

### Device Provisioning
```
POST /api/esp-device-provision
{
  "device_id": "ESP32_SENSOR_001",
  "device_name": "Temperature Sensor",
  "device_type": "IoT_Sensor",
  "location": "Lab",
  "mac_address": "a4c138f3d8d1"
}
```

### Sensor Upload
```
POST /api/esp-sensor-upload
{
  "device_id": "ESP32_SENSOR_001",
  "sensor_type": "Biometric",
  "reading_value": "TEMP=37.2C,HR=75",
  "iv": "05bfa33d5f2826752bfe2e8fb221da84",
  "timestamp": 1643799165
}
```

## Production Recommendations

1. **Use proper encryption** - Replace XOR with real AES on ESP
2. **Implement TLS** - Use HTTPS instead of HTTP
3. **Key management** - Use Hardware Security Module (HSM) for keys
4. **Device attestation** - Use TPM for device identity
5. **Rate limiting** - Implement in gateway for DOS protection
6. **Monitoring** - Add alerts for anomalous readings

## License

Same as main project
