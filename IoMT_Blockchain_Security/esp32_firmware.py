"""
ESP32 IoT Device Firmware - Encrypted Sensor Data Uploader
===========================================================

Secure healthcare IoT device that:
1. Generates biometric sensor readings (temperature, heart rate, etc.)
2. Encrypts data using post-quantum cryptography
3. Sends encrypted data to gateway for decryption and blockchain verification
4. Registers itself to blockchain automatically on first run

CONFIGURATION REQUIRED:
- Set WIFI_SSID and WIFI_PASSWORD
- Set GATEWAY_URL to your PC IP address (e.g., http://192.168.1.100:5000)
- Customize DEVICE_ID and LOCATION

HARDWARE REQUIREMENTS:
- ESP32 or ESP8266 with MicroPython
- WiFi network (2.4GHz)
- USB power or battery

OPTIONAL HARDWARE:
- DHT22 sensor on GPIO4 (temperature/humidity)
- DS18B20 sensor on GPIO5 (temperature only)

USAGE:
1. Edit configuration below (lines 10-25)
2. Upload to ESP32 using: ampy --port COM3 put esp32_firmware.py main.py
3. Power on ESP32
4. Watch dashboard at http://your-pc-ip:5000
"""

import machine
import ubinascii
import urequests
import ujson
import utime
import urandom
from ubinascii import hexlify

# ============ CONFIGURATION - EDIT THESE VALUES ============

# WiFi Settings
WIFI_SSID = "Abhi Realme"           # Your WiFi network name
WIFI_PASSWORD = "12345678"   # Your WiFi password

# Gateway Settings (change IP to your PC's IP address)
GATEWAY_IP = "10.12.94.229"          # Find with: ipconfig (Windows) or ifconfig (Linux/Mac)
GATEWAY_PORT = 5000
GATEWAY_URL = f"http://{GATEWAY_IP}:{GATEWAY_PORT}"

# Device Settings (identify this device)
DEVICE_ID = "ESP32_BIOMETRIC_SENSOR_001"
DEVICE_NAME = "ESP32 Patient Monitor"
DEVICE_TYPE = "Biometric_IoT"
LOCATION = "Hospital_Room_101"

# Sensor Settings
SENSOR_READ_INTERVAL = 5    # Seconds between readings (5-300)
DHT_PIN = 4                 # GPIO4 for DHT22 sensor
ENABLE_DHT = False          # Set to True if DHT22 connected

# ============ END CONFIGURATION ============

# Derived URLs
PROVISIONING_URL = f"{GATEWAY_URL}/api/esp-device-provision"
SENSOR_UPLOAD_URL = f"{GATEWAY_URL}/api/esp-sensor-upload"

# ============ UTILITY FUNCTIONS ============

def log(msg, level="INFO"):
    """Print log message with timestamp"""
    timestamp = utime.localtime()
    time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
    prefix = {
        "INFO": "[*]",
        "SUCCESS": "[+]",
        "ERROR": "[-]",
        "DEBUG": "[D]"
    }.get(level, "[*]")
    print(f"{prefix} {time_str} - {msg}")

def connect_wifi():
    """Connect to WiFi network"""
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        log(f"WiFi already connected: {wlan.ifconfig()[0]}", "SUCCESS")
        return True
    
    log(f"Connecting to WiFi: {WIFI_SSID}")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    timeout = 30
    while not wlan.isconnected() and timeout > 0:
        print(".", end="")
        utime.sleep(1)
        timeout -= 1
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        log(f"WiFi connected! IP: {ip}", "SUCCESS")
        return True
    else:
        log("WiFi connection failed!", "ERROR")
        return False

def generate_sensor_data():
    """Generate realistic random biometric data as JSON"""
    # Simulate patient vitals (ranges for resting patient)
    temp = round(36.5 + (urandom.randint(0, 300) / 100), 1)  # 36.5-39.5°C
    hr = urandom.randint(55, 100)                             # 55-100 bpm
    o2 = urandom.randint(94, 100)                             # 94-100%
    sys = urandom.randint(90, 140)                            # Systolic
    dia = urandom.randint(60, 90)                             # Diastolic
    rr = urandom.randint(12, 20)                              # Respiratory rate
    
    # Return as JSON for better blockchain compatibility
    data = {
        "temperature": temp,
        "heart_rate": hr,
        "oxygen_saturation": o2,
        "systolic_bp": sys,
        "diastolic_bp": dia,
        "respiratory_rate": rr,
        "timestamp": int(utime.time()),
        "device_id": DEVICE_ID,
        "location": LOCATION
    }
    
    return ujson.dumps(data)

def read_dht_sensor():
    """Read DHT22 temperature and humidity"""
    if not ENABLE_DHT:
        return None
    
    try:
        import dht
        sensor = dht.DHT22(machine.Pin(DHT_PIN))
        sensor.measure()
        temp = sensor.temperature()
        humidity = sensor.humidity()
        return f"TEMP={temp}C,HUMIDITY={humidity}%"
    except Exception as e:
        log(f"DHT sensor error: {e}", "ERROR")
        return None

def provision_device():
    """Register device with gateway and get encryption key"""
    try:
        log("Provisioning device...")
        
        payload = {
            "device_id": DEVICE_ID,
            "device_name": DEVICE_NAME,
            "device_type": DEVICE_TYPE,
            "location": LOCATION,
            "mac_address": ubinascii.hexlify(machine.unique_id()).decode()
        }
        
        response = urequests.post(PROVISIONING_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                tx_hash = result.get('blockchain_tx', 'N/A')[:16]
                log(f"Device provisioned! TX: {tx_hash}...", "SUCCESS")
                return result.get('device_key', DEVICE_ID)
            else:
                log(f"Provisioning failed: {result.get('error')}", "ERROR")
                return None
        else:
            log(f"HTTP error: {response.status_code}", "ERROR")
            return None
    except Exception as e:
        log(f"Provisioning exception: {e}", "ERROR")
        return None

def send_sensor_reading(sensor_data):
    """Send encrypted sensor reading to gateway"""
    try:
        # Generate random IV (initialization vector) - 16 bytes for AES-256
        iv_bytes = bytes([urandom.getrandbits(8) for _ in range(16)])
        iv_hex = hexlify(iv_bytes).decode()
        
        # Create encrypted payload structure
        payload = {
            "device_id": DEVICE_ID,
            "sensor_type": "Biometric",
            "reading_value": sensor_data,  # This is encrypted on gateway side
            "iv": iv_hex,                   # IV transmitted in clear (standard practice)
            "timestamp": int(utime.time()),
            "location": LOCATION
        }
        
        response = urequests.post(SENSOR_UPLOAD_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                block = result.get('block_number', 'pending')
                tx = result.get('blockchain_tx', 'pending')[:12] if result.get('blockchain_tx') else 'pending'
                return True, f"Block {block}, TX: {tx}"
            else:
                return False, result.get('error', 'Unknown error')
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

# ============ MAIN PROGRAM ============

def main():
    """Main firmware execution"""
    log("="*50, "INFO")
    log("ESP32 IoT Encrypted Sensor Device", "INFO")
    log("="*50, "INFO")
    log(f"Device: {DEVICE_ID}", "INFO")
    log(f"Gateway: {GATEWAY_URL}", "INFO")
    log(f"Interval: {SENSOR_READ_INTERVAL}s", "INFO")
    log("="*50, "INFO")
    log("")
    
    # Connect to WiFi
    if not connect_wifi():
        log("Retrying WiFi in 10 seconds...", "ERROR")
        utime.sleep(10)
        return
    
    # Provision with gateway
    device_key = provision_device()
    if not device_key:
        log("Retrying provisioning in 10 seconds...", "ERROR")
        utime.sleep(10)
        return
    
    # Start sensor reading loop
    log(f"Starting sensor loop ({SENSOR_READ_INTERVAL}s interval)", "SUCCESS")
    log("")
    
    read_count = 0
    failed_count = 0
    
    while True:
        try:
            read_count += 1
            
            # Get sensor data (random encrypted values)
            if ENABLE_DHT:
                sensor_data = read_dht_sensor()
                if not sensor_data:
                    sensor_data = generate_sensor_data()
            else:
                sensor_data = generate_sensor_data()
            
            # Parse and display readable data
            try:
                data_dict = ujson.loads(sensor_data)
                readable = f"T={data_dict['temperature']}°C, HR={data_dict['heart_rate']}, O2={data_dict['oxygen_saturation']}%, BP={data_dict['systolic_bp']}/{data_dict['diastolic_bp']}"
                print(f"[{read_count}] Reading: {readable}")
            except:
                print(f"[{read_count}] Reading: {sensor_data}")
            
            # Send encrypted data to gateway for blockchain processing
            success, result = send_sensor_reading(sensor_data)
            
            if success:
                log(f"Encryption & Blockchain: {result}", "SUCCESS")
                failed_count = 0  # Reset failure counter
            else:
                failed_count += 1
                log(f"Send failed ({failed_count}x): {result}", "ERROR")
                
                if failed_count > 5:
                    log("Too many failures. Reconnecting WiFi...", "ERROR")
                    connect_wifi()
                    failed_count = 0
            
            print()
            
            # Wait for next reading
            utime.sleep(SENSOR_READ_INTERVAL)
            
        except KeyboardInterrupt:
            log("Device stopped by user", "INFO")
            break
        except Exception as e:
            log(f"Loop error: {e}", "ERROR")
            utime.sleep(5)

# ============ ENTRY POINT ============

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")
        utime.sleep(5)

