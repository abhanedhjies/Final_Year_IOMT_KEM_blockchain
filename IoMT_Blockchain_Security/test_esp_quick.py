#!/usr/bin/env python3
"""
Quick test script to verify ESP endpoints work
"""
import requests
import json
from datetime import datetime

GATEWAY = "http://10.73.161.229:5000"
DEVICE_ID = "ESP8266_BIOMETRIC_SENSOR_001"

def provision():
    """Provision the ESP device"""
    print("\n=== PROVISIONING DEVICE ===")
    url = f"{GATEWAY}/api/esp-device-provision"
    payload = {
        "device_id": DEVICE_ID,
        "device_name": "ESP8266 Patient Monitor",
        "device_type": "Biometric_IoT",
        "location": "Hospital_Room_101",
        "mac_address": "AA:BB:CC:DD:EE:FF"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        return result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def upload_sensor():
    """Upload sensor data"""
    print("\n=== UPLOADING SENSOR DATA ===")
    url = f"{GATEWAY}/api/esp-sensor-upload"
    payload = {
        "device_id": DEVICE_ID,
        "sensor_type": "Biometric",
        "reading_value": '{"temperature": 37.5, "heart_rate": 72, "oxygen": 98, "bp": "120/80"}',
        "timestamp": datetime.now().isoformat(),
        "encrypted_data": "ENCRYPTED_PAYLOAD_EXAMPLE_DATA"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        if result.get('success'):
            print(f"\n✓ Data Hash: {result['data_hash'][:40]}...")
            print(f"✓ Block Number: {result['block_number']}")
        return result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_connection():
    """Check ESP devices list"""
    print("\n=== CHECKING CONNECTED DEVICES ===")
    url = f"{GATEWAY}/api/esp-devices"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        devices = response.json()
        if devices:
            print(f"Found {len(devices)} connected device(s):")
            for device in devices:
                print(f"  - {device.get('device_id')}: {device.get('connection_status')}")
                if device.get('last_packet'):
                    print(f"    Last: {device['last_packet'].get('timestamp')}")
        else:
            print("No devices connected yet")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("ESP DEVICE TEST SCRIPT")
    print("="*60)
    print(f"Gateway: {GATEWAY}")
    print(f"Device: {DEVICE_ID}")
    
    # Test provisioning
    if provision():
        print("\n✓ Provisioning successful!")
        
        # Test sensor upload
        for i in range(3):
            print(f"\n[Attempt {i+1}/3]")
            if upload_sensor():
                print("✓ Upload successful!")
            else:
                print("✗ Upload failed")
        
        # Check devices
        check_connection()
    else:
        print("\n✗ Provisioning failed!")
    
    print("\n" + "="*60)
    print("Open dashboard at: http://10.73.161.229:5000")
    print("="*60)
